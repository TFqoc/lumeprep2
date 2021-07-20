# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

ORDER_HISTORY_DOMAIN = [('state', 'not in', ('draft', 'sent'))]

class Partner(models.Model):
    _inherit = 'res.partner'

    # is_medical = fields.Boolean()
    medical_id = fields.Char(string="Medical ID")
    medical_expiration = fields.Date(string="Medical Expiration")
    date_of_birth = fields.Date()
    is_over_21 = fields.Boolean(compute='_compute_age', search='_search_is_over_21')
    is_over_18 = fields.Boolean(compute='_compute_age', search='_search_is_over_18')
    is_expired_medical = fields.Boolean(compute='_compute_expired_medical', search='_search_expired_medical')
    is_expired_dl = fields.Boolean(compute='_compute_expired_dl', search='_search_expired_dl')
    drivers_license_number = fields.Char()
    drivers_license_expiration = fields.Date()
    passport = fields.Char()
    pref_name = fields.Char()
    can_purchase_medical = fields.Boolean(compute="_compute_medical_purchase")
    # customer_type = fields.Selection([('medical', 'Medical'),('adult','Adult'),('caregiver','Caregiver')], default="medical")
    has_online_order = fields.Boolean(compute='_compute_has_online_order')


    # name = fields.Char(compute="_change_pref_name",store=True)
    first_name = fields.Char()
    middle_name = fields.Char()
    last_name = fields.Char()

    is_caregiver = fields.Boolean()
    caregiver_license = fields.Char()
    caregiver_id = fields.Many2one('res.partner',domain="[('is_caregiver','=',True)]")
    patient_ids = fields.One2many(comodel_name="res.partner",inverse_name="caregiver_id")

    last_visit = fields.Datetime()

    warnings = fields.Integer()
    is_banned = fields.Boolean(compute='_compute_banned', default=False)

    note_ids = fields.One2many(comodel_name='lume.note',inverse_name='source_partner_id')

    # Override
    def _compute_sale_order_count(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        sale_order_groups = self.env['sale.order'].read_group(
            domain=[('partner_id', 'in', all_partners.ids)] + ORDER_HISTORY_DOMAIN,
            fields=['partner_id'], groupby=['partner_id']
        )
        partners = self.browse()
        for group in sale_order_groups:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.sale_order_count += group['partner_id_count']
                    partners |= partner
                partner = partner.parent_id
        (self - partners).sale_order_count = 0

    @api.depends('medical_expiration')
    def _compute_expired_medical(self):
        for record in self:
            if record.medical_expiration:
                record.is_expired_medical = record.medical_expiration < datetime.date.today() and record.medical_id   
            else:
                record.is_expired_medical = record.medical_id != False

    @api.depends('drivers_license_expiration')
    def _compute_expired_dl(self):
        for record in self:
            try:
                record.is_expired_dl = record.drivers_license_expiration < datetime.date.today()
            except:
                record.is_expired_dl = True

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
                record.is_over_21 = difference_in_years >= 21
                record.is_over_18 = difference_in_years >= 18
                _logger.info("AGE: " + str(difference_in_years))

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

    def _compute_medical_purchase(self):
        for record in self:
            record.can_purchase_medical = not record.is_expired_medical and record.medical_id and record.is_over_18
    
    @api.depends_context('check_in_window','project_id')
    def _compute_has_online_order(self):
        check_in = self.env.context.get('check_in_window', False)
        project_id = self.env.context.get('project_id', False)
        project_id = self.env['project.project'].browse(project_id)
        for record in self:
            if check_in:
                tasks = project_id.task_ids.filtered(lambda t: t.partner_id.id == record.id)
                record.has_online_order = len(tasks) > 0
            else:
                record.has_online_order = False

    def warn(self):
        self.warnings += 1

    def unwarn(self):
        self.warnings -= 1
        if self.warnings < 0:
            self.warnings = 0

    ###########################################################
    # Called from a button on the contact form
    # All validation checks should be done in this method
    ###########################################################
    def check_in(self):
        # Validation checks
        if self.is_banned:
            raise ValidationError("This customer has been banned and cannot be checked in!")
        # if self.is_expired_medical and self.env.context.get('order_type') == 'medical':
        #     raise ValidationError("This customer has an expired medical licence! Please update medical licence information to allow customer to check in.\nIf this is a new medical customer, please make sure to change customer type to Medical")
        # if not self.medical_id and self.env.context.get('order_type') == 'medical':
        #     raise ValidationError("Invalid medical id!")
        if not self.drivers_license_number:
            raise ValidationError("Invalid drivers licence!")
        if self.is_expired_dl:
            raise ValidationError("This customer has an expired drivers licence! Please update licence information to allow customer to check in.")
        if (not self.is_over_21 and not self.medical_id) or (self.medical_id and not self.is_expired_medical and not self.is_over_18):
            raise ValidationError("This customer is underage!")
        ctx = self.env.context
        # _logger.info("CTX: " + str(ctx))
        project = self.env['project.project'].browse(ctx.get('project_id'))
        
        if self.has_online_order:
            tasks = project.task_ids.filtered(lambda t: t.partner_id.id == self.id)
            tasks.is_checked_in = True
            return {
            "type":"ir.actions.act_window",
            "res_model":"project.task",
            "views":[[False, "kanban"],[False,"form"]],
            "name": 'Tasks',
            "target": 'main',
            "res_id": project.id,
            "domain": [('project_id', '=', project.id)],
            "context": {'default_project_id': project.id},
        }
        # stage = project.type_ids.sorted(key=None)[0] # sort by default order (sequence in this case)
        self.env['project.task'].create({
            'partner_id': self.id,
            'project_id': project.id,
            'fulfillment_type': ctx['fulfillment_type'],
            # 'order_type': ctx['order_type'],
            'user_id': False,
            'name': self.pref_name or self.name,
        })
        return {
            "type":"ir.actions.act_window",
            "res_model":"project.task",
            "views":[[False, "kanban"],[False,"form"]],
            "name": 'Tasks',
            "target": 'main',
            "res_id": project.id,
            "domain": [('project_id', '=', project.id)],
            "context": {'default_project_id': project.id},
        }

    ###########################################################
    # Called from a button on the contact form
    # All validation checks should be done in this method
    ###########################################################
    def check_in_as_patient(self):
        # Validation checks
        if self.is_banned:
            raise ValidationError("This patient has been banned and cannot be checked in!")
        if not self.medical_id:
            raise ValidationError("This patient does not have a valid medical ID!")
        if not self.medical_expiration or self.medical_expiration < datetime.date.today():
            raise ValidationError("The patient's medical id is expired!")
        ctx = self.env.context
        _logger.info("CTX: " + str(ctx))
        project = self.env['project.project'].browse(ctx.get('project_id'))
        # stage = project.type_ids.sorted(key=None)[0] # sort by default order (sequence in this case)
        self.env['project.task'].create({
            'partner_id': self.id,
            'project_id': project.id,
            'fulfillment_type': ctx['fulfillment_type'],
            # 'order_type': ctx['order_type'],
            'caregiver_id': self.caregiver_id.id,
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
    
    # Override
    def name_get(self):
        res = []
        for record in self:
            if record.pref_name:
                name = f"{record.first_name} \"{record.pref_name}\" {record.last_name}"
            else:
                name = record.name
            res.append((record.id, name))
        return res

    @api.onchange('pref_name','first_name','middle_name','last_name')
    # @api.depends('pref_name','first_name','middle_name','last_name')
    def _change_pref_name(self):
        for record in self:
            if record.name:
                # This is to rewrite the name stored as a pair in the db itself
                record.update({'name': ' '.join([record.first_name or '', record.middle_name or '', record.last_name or ''])})
    
    # This method turns out to be redundant
    # @api.onchange('patient_ids')
    # def _change_patients(self):
    #     # If patients are removed, then remove them from target
    #     for r in self._origin.patient_ids - self.patient_ids:
    #         r.caregiver_id = False
    #     # If patients were added, then add them
    #     for r in self.patient_ids - self._origin.patient_ids:
    #         r.caregiver_id = self._origin.id

    def verify_address(self):
        pass

    # def _compute_expirations(self):
    #     for record in self:
    #         record._compute_age()

    @api.model
    def create(self, vals):
        vals['type'] = False
        return super(Partner, self).create(vals)



    
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

class Picking(models.Model):
    _inherit = 'stock.picking'

    # Quick endpoint for locust testing
    def quick_validate(self):
        for line in self.move_ids_without_package:
            line.quantity_done = line.product_uom_qty
        self.button_validate()
        return True