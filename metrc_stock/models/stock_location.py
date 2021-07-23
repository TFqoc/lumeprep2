# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockLocation(models.Model):
    _inherit = 'stock.location'

    metrc_location_ids = fields.Many2many(comodel_name='metrc.location',
                                        string='Metrc Location(s)')
    
    def get_metrc_location(self, facility_license_id):
        if not self.metrc_location_ids:
            return False
        metrc_location = self.metrc_location_ids.filtered(lambda l: l.facility_license_id == facility_license_id)
        return metrc_location or False
