# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Quant(models.Model):
    _inherit = 'stock.quant'

    is_tiered = fields.Boolean(related='product_id.is_tiered')