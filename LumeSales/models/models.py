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
    dummy_field = fields.Char(compute='_compute_dummy_field',store=False,invisible=True)

    def get_message_count(self, id):
        return self.browse(id).message_unread_counter

    def _compute_dummy_field(self):
        # self.message_unread_counter = 0 #this just gets reset back to the previous value from Odoo
        # self.message_unread = False
        self.dummy_field='dummy'

    # @api.model
    # def create(self, vals_list):
    #     """Override default Odoo create function and extend."""
    #     #Vals_list dictionary contains all the fields of the record to be created
    #     # Returns without creating if user is banned
    #     customer = self.env['res.partner'].browse(vals_list['partner_id'])
    #     if customer.is_banned is True:
    #         message_id = self.env['message.wizard'].create(
    #             {'message': ("Customer " + customer.name + " has been banned and cannot be checked in.")})
    #         return {
    #             'name': ('Customer is Banned'),
    #             'type': 'ir.actions.act_window',
    #             'view_mode': 'form',
    #             'res_model': 'message.wizard',
    #             # pass the id
    #             'res_id': message_id.id,
    #             'target': 'new'
    #         }
    #     return super(Tasks, self).create(vals_list)

    def delete_recent(self, args):
        target_record = self.env['project.task'].search([], order='id desc')[0]
        # target_record = self.env['project.task'].browse(ids)[0]
        target_record.unlink()

class project_inherit(models.Model):
    _inherit = 'project.project'

    task_number = fields.Integer(default=0)

class product_addons(models.Model):
    _inherit='product.template'

    is_medical = fields.Boolean()

class sale_inherit(models.Model):
    _inherit = 'sale.order'

    task = fields.Many2one(comodel_name="project.task", readonly=True)

    @api.onchange('order_line')
    def check_order_lines(self):
        for order in self.order_line:
            if order.product_id.is_medical is self.partner_id.is_medical:
                continue
            else:
                #TODO delete the line item that was just added.
                #self.update({'order_line': (3,order.id,0)}) #tries to access id.ref but fails since id is an integer
                return {
                'warning': {'title': "Warning", 'message': "You can't add a " + ("medical" if order.product_id.is_medical else "recreational") + " product to a " + ("medical" if self.partner_id.is_medical else "recreational") + " customer's order!",}
                }
                #https://github.com/odoo/odoo/issues/32182
                #Can't edit order_line from here because self is a copy.
                #Need a work around.

    def delete_order_line(self, line_id):

        pass

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

#####
# Allow any message to count as read if someone has looked at it.
#####
class MailOverride(models.Model):
    _inherit='mail.thread'

    #Override
    def _get_message_unread(self):
        partner_id = self.env.user.partner_id.id
        res = dict.fromkeys(self.ids, 0)
        if self.ids:
            # search for unread messages, directly in SQL to improve performances
            self._cr.execute(""" SELECT msg.res_id FROM mail_message msg
                        RIGHT JOIN mail_message_mail_channel_rel rel
                        ON rel.mail_message_id = msg.id
                        RIGHT JOIN mail_channel_partner cp
                        ON (cp.channel_id = rel.mail_channel_id AND cp.partner_id = %s AND
                        cp.seen_message_id IS NULL)
                        WHERE msg.model = %s AND msg.res_id = ANY(%s) AND
                            msg.message_type != 'user_notification' AND
                            (msg.author_id IS NULL OR msg.author_id != %s) AND
                            (msg.message_type not in ('notification', 'user_notification') OR msg.model != 'mail.channel')""",
                    (partner_id, self._name, list(self.ids), partner_id,))
            # self._cr.execute(""" SELECT msg.res_id FROM mail_message msg
            #                      RIGHT JOIN mail_message_mail_channel_rel rel
            #                      ON rel.mail_message_id = msg.id
            #                      RIGHT JOIN mail_channel_partner cp
            #                      ON (cp.channel_id = rel.mail_channel_id AND cp.partner_id = %s AND
            #                         (cp.seen_message_id IS NULL OR cp.seen_message_id < msg.id))
            #                      WHERE msg.model = %s AND msg.res_id = ANY(%s) AND
            #                             msg.message_type != 'user_notification' AND
            #                            (msg.author_id IS NULL OR msg.author_id != %s) AND
            #                            (msg.message_type not in ('notification', 'user_notification') OR msg.model != 'mail.channel')""",
            #                  (partner_id, self._name, list(self.ids), partner_id,))
            for result in self._cr.fetchall():
                res[result[0]] += 1

        for record in self:
            record.message_unread_counter = res.get(record._origin.id, 0)
            record.message_unread = bool(record.message_unread_counter)
