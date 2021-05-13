# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = 'res.partner'

    is_medical = fields.Boolean()
    medical_id = fields.Char()
    medical_expiration = fields.Date()
    date_of_birth = fields.Date()
    is_over_21 = fields.Boolean(compute='_compute_age', search='_search_is_over_21')
    is_over_18 = fields.Boolean(compute='_compute_age', search='_search_is_over_18')
    is_expired = fields.Boolean(compute='_compute_expired', search='_search_expired')
    drivers_license_number = fields.Char()
    drivers_license_expiration = fields.Date()
    passport = fields.Char()
    pref_name = fields.Char()
    customer_type = fields.Selection([('medical', 'Medical'),('adult','Adult'),('caregiver','Caregiver')], default="medical")

    last_visit = fields.Datetime()

    warnings = fields.Integer()
    is_banned = fields.Boolean(compute='_compute_banned', default=False)

    def _compute_expired(self):
        for record in self:
            try:
                record.is_expired = record.medical_expiration < datetime.date.today() or record.drivers_license_expiration < datetime.date.today()
            except:
                record.is_expired = True

    def _search_expired(self, operation, value):
        return [('id','=',1)]

    @api.depends('date_of_birth')#will be accurate when dob is entered, but not if they later become 21
    def _compute_age(self):
        for record in self:
            if record.date_of_birth is False:# In case dob is not set yet
                record.is_over_21 = False
                record.is_over_18 = False
            else:
                difference_in_years = (datetime.date.today() - record['date_of_birth']).days / 365.25
                record['is_over_21'] = difference_in_years >= 21
                record['is_over_18'] = difference_in_years >= 18

    def _search_is_over_21(self, operator, value):
        years_ago = datetime.datetime.now() - relativedelta(years=21)
        return [('date_of_birth', '<=', years_ago)]

    def _search_is_over_18(self, operator, value):
        years_ago = datetime.datetime.now() - relativedelta(years=18)
        return [('date_of_birth', '<=', years_ago)]


    @api.depends('warnings')
    def _compute_banned(self):
        for record in self:
            record.is_banned = self.warnings >= 3
    
    def warn(self):
        self.warnings += 1

    ###########################################################
    # Called from a button on the contact form
    # All validation checks should be done in this method
    ###########################################################
    def check_in(self):
        # Validation checks
        if self.is_banned:
            raise ValidationError("This customer has been banned and cannot be checked in!")
        if self.is_expired:
            raise ValidationError("This customer has an expired licence! Please update licence information to allow customer to check in.")
        if self._compute_age() or not self.is_over_21: # TODO: Add validation for 18 year olds with medical cards
            raise ValidationError("This customer is not old enough to buy drugs!")
        ctx = self.env.context
        # _logger.info("CTX: " + str(ctx))
        project = self.env['project.project'].search([('id','=',ctx.get('project_id'))], limit=1)
        # stage = project.type_ids.sorted(key=None)[0] # sort by default order (sequence in this case)
        self.env['project.task'].create({
            'partner_id': int(ctx['partner_id']),
            'project_id': project.id,
            'order_type': ctx['order_type'],
            'user_id': False,
            'name': self.pref_name or self.name,
        })
        return {
            "type":"ir.actions.act_window",
            "res_model":"project.task",
            "views":[[False, "kanban"]],
            "name": 'Tasks',
            "target": 'main',
            "res_id": project.id,
            "domain": [('project_id', '=', project.id)],
            "context": {'default_project_id': project.id},
        }

    def verify_address(self):
        pass

    def _compute_expirations(self):
        for record in self:
            record._compute_21()


    
# class Store(models.Model):
#     _name = 'lume.store'

#     name = fields.Char(required=True)
#     # user_ids = fields.One2many(comodel_name='res.users',inverse_name='store')
#     user_ids = fields.Many2many(comodel_name='res.users', compute='_get_users', store=True)

#     def _get_users(self):
#         user_ids = self.env['res.users'].search(['store','ilike',self.name])

class User(models.Model):
    _inherit='res.users'

    # store = fields.Many2many(comodel_name='lume.store')

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

    @api.depends_context('uid')
    def _compute_user_timer_id(self):
        """ Get the timers according these conditions
            :user_id is is the current user
            :res_id is the current record
            :res_model is the current model
            limit=1 by security but the search should never have more than one record
        """
        for record in self:
            record.user_timer_id = self.env['timer.timer'].search([
                # ('user_id', '=', record.env.user.id),
                ('res_id', '=', record.id),
                ('res_model', '=', record._name)
            ], limit=1)