# -*- coding: utf-8 -*-

from odoo import fields, models


class MetrcPackageAdjustReason(models.Model):
    _name = 'metrc.package.adjust.reason'
    _description = "Metrc Package Adjust Reason"

    name = fields.Char(string='Reason', index=True)
    note_required = fields.Boolean(string='Requires Note?')
    license_id = fields.Many2one('metrc.license')
