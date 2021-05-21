# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    license_id = fields.Many2one('metrc.license', string="Facility License")
    default_adjust_reason_id = fields.Many2one(comodel_name='metrc.package.adjust.reason',
                                               string='Adjustment Reason', 
                                               help='Reason used automaticallu when performing package sync.')

    @api.constrains('license_id')
    def check_license(self):
        for warehouse in self.filtered(lambda w: w.license_id):
            wh_with_same_license = self.search_count([('license_id', '=', self.license_id.id)])
            if wh_with_same_license > 1:
                raise ValidationError(_('Facility license already configured in another warehouse!\nPlease configure a different facility license.'))
