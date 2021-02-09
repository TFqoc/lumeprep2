# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime


class Partner(models.Model):
    _inherit = 'res.partner'

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

class tasks(models.Model):
    #_name = 'field_kanban.field_kanban'
    _inherit = 'project.task'
    #_description = 'field_kanban.field_kanban'

    time_counter = fields.Char(default='Size Guide')
    name = fields.Char(required=False)

    def test(self):
        pass

    # def create(self, values=None):
    #     if values == None:
    #         return
    #     """Override default Odoo create function and extend."""
    #     # Do your custom logic here
    #     raise Warning(values)
    #     return super(tasks, self).create(values)

class project_inherit(models.Model):
    _inherit = 'project.project'

    task_number = fields.Integer(default=0)

class product_addons(models.Model):
    _inherit='product.template'

    is_medical = fields.Boolean()

