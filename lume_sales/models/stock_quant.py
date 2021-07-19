# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    tier = fields.Selection(related="lot_id.tier")
    is_tiered = fields.Boolean(related="product_id.is_tiered",store=True)