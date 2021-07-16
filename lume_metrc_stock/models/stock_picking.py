# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockPicking(models.Model):
    inherit = 'stock.picking'

    def _update_metrc_packages(self):
        # Overriding same method here. Hate to do this. but once QOC done with demo will improve.
        # TODO: Make it scalable to copy requested field.
        MT = self.env['metrc.transfer']
        for move_line in self.move_line_ids.filtered(lambda ml: ml.state == 'done'
                                            and ml.product_id.is_metric_product
                                            and not ml.move_id._is_dropshipped()
                                            and not ml.move_id._is_dropshipped_returned()):
            metrc_transfer = MT.search([('move_line_id', '=', move_line.id)])
            if move_line.lot_id and metrc_transfer:
                move_line.lot_id.write({
                    'thc_percent': metrc_transfer.thc_percent,
                    'thc_mg': metrc_transfer.thc_mg,
                    'expiration_date': metrc_transfer.expiration_date,
                    'harvest_date': metrc_transfer.harvest_date,
                    'metrc_product_name': metrc_transfer.product_name,
                    'tier': metrc_transfer.tier
                })