# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
import logging

_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = 'res.partner'

    is_medical = fields.Boolean()
    medical_id = fields.Char()
    medical_expiration = fields.Date()
    date_of_birth = fields.Date()
    is_over_21 = fields.Boolean(compute='_compute_21')
    drivers_license_number = fields.Char()
    drivers_license_expiration = fields.Date()

    last_visit = fields.Datetime()

    warnings = fields.Integer()
    is_banned = fields.Boolean(compute='_compute_banned', default=False)

    @api.depends('date_of_birth')#will be accurate when dob is entered, but not if they later become 21
    def _compute_21(self):
        for record in self:
            if record.date_of_birth is False:# In case dob is not set yet
                record.is_over_21 = False
            else:
                difference_in_years = (datetime.date.today() - record['date_of_birth']).days / 365.25
                record['is_over_21'] = difference_in_years >= 21


    @api.depends('warnings')
    def _compute_banned(self):
        for record in self:
            record.is_banned = self.warnings >= 3
    
    def warn(self):
        self.warnings += 1

    def verify_address(self):
        pass

class Tasks(models.Model):
    _inherit = 'project.task'
    _description = 'project.task'

    name = fields.Char(required=False)
    sales_order = fields.Many2one(comodel_name="sale.order", readonly=True)
    dummy_field = fields.Char(compute='_compute_dummy_field',store=False)

    order_type = fields.Selection(selection=[('store','In Store'),('delivery','Delivery'),('online','Website')], default='store')

    def get_message_count(self, id): #called from js widget for display purposes
        return self.browse(id).message_unread_counter
    
    def _compute_dummy_field(self):
        # Mail module > models > mail_channel.py Line 743
                # active_id = self.env.context.get('active_ids', []) #gets id of task
        # self.env['mail.channel'].search([''])   #channel_seen(None)
        message_id = self.message_ids[0].id
        for channel in self.message_channel_ids:
            channel.channel_seen(message_id) #should be the id of the message to be marked as seen.

        self.dummy_field = 'dummy'

    def build_cart(self):
        self.sales_order = self.env['sale.order'].create({
            'partner_id':self.partner_id.id,
            'task':self.id,
            'date_order': fields.datetime.now(),
            # 'picking_policy':'direct',
            # 'pricelist_id':'idk',
            # 'warehouse_id':'',
        })
        self.next_stage()

    def next_stage(self):
        if self.sage.name == 'Done':
            return

        get_next = False
        for stage in self.project_id.type_ids:
            if get_next:
                self.stage = stage
                break
            elif stage == self.stage:
                get_next = True


    # Mail module > models > mail_channel.py Line 758

    @api.model
    def delete_recent(self):
        target_record = self.env['project.task'].search([], order='id desc')[0]
        # target_record = self.env['project.task'].browse(ids)[0]
        target_record.unlink()

    @api.onchange('stage_id')
    def change_stage(self):
        new_stage = self.stage_id.name
        old_stage = self._origin.stage_id.name
        self._origin.stage_id = self.stage_id
        if self.user_timer_id.timer_start and self.display_timesheet_timer:
            self._origin.action_timer_auto_stop(old_stage+" > "+new_stage)
        if not self.stage_id.is_closed:
            self._origin.action_timer_start()
        
        return {
    'warning': {'title': "Info", 'message': old_stage+" > "+new_stage, 'type': 'notification'},
}

        # if new_stage is 'Check In':
        #     pass
        # elif new_stage is 'Build Cart':
        #     if old_stage is 'Check In':
        #         self.action_timer_start()
        #         pass
        #     pass
        # elif new_stage is 'Fulfilment':
        #     if old_stage is 'Build Cart':
        #         self.action_timer_auto_stop()
        #     pass
        # elif new_stage is 'Check Out':
        #     pass
        # elif new_stage is 'Done':
        #     self.action_timer_auto_stop()
        #     pass
    
    def save_timesheet(self, minutes, desc=None):
        values = {
            'task_id': self.id,
            'project_id': self.project_id.id,
            'date': fields.Date.context_today(self),
            'name': desc or "",
            'user_id': self.env.uid,
            'unit_amount': minutes,
        }
        self.user_timer_id.unlink()
        return self.env['account.analytic.line'].create(values)

    def action_timer_auto_stop(self, desc=None):
        # timer was either running or paused
        if self.user_timer_id.timer_start and self.display_timesheet_timer:
            minutes_spent = self.user_timer_id._get_minutes_spent()
            minimum_duration = int(self.env['ir.config_parameter'].sudo().get_param('hr_timesheet.timesheet_min_duration', 0))
            rounding = int(self.env['ir.config_parameter'].sudo().get_param('hr_timesheet.timesheet_rounding', 0))
            minutes_spent = self._timer_rounding(minutes_spent, minimum_duration, rounding)
            self.save_timesheet(minutes_spent * 60 / 3600, desc)
            #return self._action_open_new_timesheet(minutes_spent * 60 / 3600)
        #return False

class project_inherit(models.Model):
    _inherit = 'project.project'

    task_number = fields.Integer(default=0)# Used to generate a task name
    store = fields.Many2one(comodel_name='lume.store')
    
class Store(models.Model):
    _name = 'lume.store'

    name = fields.Char(required=True)
    # user_ids = fields.One2many(comodel_name='res.users',inverse_name='store')
    user_ids = fields.Many2many(comodel_name='res.users', compute='_get_users', store=True)

    def _get_users(self):
        user_ids = self.env['res.users'].search(['store','ilike',self.name])

class User(models.Model):
    _inherit='res.users'

    store = fields.Many2many(comodel_name='lume.store')

class product_addons(models.Model):
    _inherit='product.template'

    is_medical = fields.Boolean()

####
# Allow multiple task timers going at once.
####
class TimeMix(models.AbstractModel):
    _inherit='timer.mixin'

    def action_timer_start(self):
        """ Start the timer of the current record
        First, if a timer is running, stop or pause it
        If there isn't a timer for the current record, create one then start it
        Otherwise, resume or start it
        """
        #self.ensure_one()
        #self._stop_timer_in_progress()
        timer = self.user_timer_id
        if not timer:
            timer = self.env['timer.timer'].create({
                'timer_start': False,
                'timer_pause': False,
                'is_timer_running': False,
                'res_model': self._name,
                'res_id': self.id,
                'user_id': self.env.user.id,
            })
            timer.action_timer_start()
        else:
            # Check if it is in pause then resume it or start it
            if timer.timer_pause:
                timer.action_timer_resume()
            else:
                timer.action_timer_start()

    def action_timer_resume(self):
        #self.ensure_one()
        #self._stop_timer_in_progress()
        timer = self.user_timer_id
        timer.action_timer_resume()