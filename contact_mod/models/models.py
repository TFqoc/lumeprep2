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

    @api.depends('is_over_21')
    def _compute_21(self):
        for record in self:
            record.is_over_21 = datetime.date.today().year - self.date_of_birth.year >= 21