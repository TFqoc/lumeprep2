# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Invoice(models.Model):
    _inherit = 'account.move'

    partner_license_id = fields.Many2one(comodel_name='metrc.license', string='Customer License',
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    facility_license_id = fields.Many2one(comodel_name='metrc.license', string='Facility License',
                                domain=[('base_type', '=', 'External')],
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
