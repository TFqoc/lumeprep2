# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    license_ids = fields.One2many('metrc.license', 'company_id', string="Facility Licenses")
