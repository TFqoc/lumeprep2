# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    tier = fields.Selection(compute="_compute_tier",inverse="_inverse_tier",readonly=False)
    is_tiered = fields.Boolean(related="product_id.is_tiered")

    def _compute_tier(self):
        for record in self:
            record.tier = record.lot_id.tier

    def _inverse_tier(self):
        for record in self:
            record.lot_id.tier = record.tier