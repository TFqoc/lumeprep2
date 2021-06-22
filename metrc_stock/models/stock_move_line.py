# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    no_metrc = fields.Boolean(related='picking_id.no_metrc', store=False)
    moving_metrc_product = fields.Boolean(related='product_id.is_metric_product', store=False)
    require_metrc_validation = fields.Boolean(related='picking_id.require_metrc_validation', store=False)
