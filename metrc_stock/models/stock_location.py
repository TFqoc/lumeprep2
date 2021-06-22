# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockLocation(models.Model):
    _inherit = 'stock.location'

    metrc_location_id = fields.Many2one(comodel_name='metrc.location',
                                        string='Metrc Location')
    facility_license_id = fields.Many2one(comodel_name='metrc.license',
                                        domain=[('base_type', '=', 'Internal')])
