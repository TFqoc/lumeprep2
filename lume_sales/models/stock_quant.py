# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    is_tiered = fields.Boolean(compute="_compute_tiered")
    tier = fields.Selection(related="lot_id.tier")

    def _compute_tiered(self):
        for record in self:
            if record.product_id and record.lot_id:
                record.is_tiered = record.product_id.is_tiered
                record.tier = record.lot_id.tier
            elif record.product_id:
                record.is_tiered = record.product_id.is_tiered

    @api.onchange('tier')
    def _change_tier(self):
        if self.lot_id:
            self.lot_id.tier = self.tier