# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockLot(models.Model):
    _inherit = 'stock.production.lot'

    image_128 = fields.Image(related='product_id.image_128')
    image_1920 = fields.Image(related='product_id.image_1920')
    price = fields.Float(compute="_compute_price")
    currency_id = fields.Many2one(related='product_id.currency_id')
    uom_id = fields.Many2one(related='product_id.uom_id')
    thc_type = fields.Selection(related='product_id.thc_type')
    # Temp fields for testing that will be added by Keyur in metrc
    tier = fields.Selection([('test','Test')], default="test")

    def _compute_price(self):
        for record in self:
            # TODO more logic here for tiers and store type
            # Might depend on the context
            record.price = record.product_id.list_price