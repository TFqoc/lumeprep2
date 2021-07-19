# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    tier = fields.Selection(related="lot_id.tier")
