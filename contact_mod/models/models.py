# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime


class Partner(models.Model):
    _inherit = 'res.partner'

    medical_id = fields.Char()
    medical_expiration = fields.Date()
    date_of_birth = fields.Date()
    is_over_21 = fields.Boolean(compute='_compute_21')
    drivers_licence_number = fields.Char()
    drivers_licence_expiration = fields.Date()

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