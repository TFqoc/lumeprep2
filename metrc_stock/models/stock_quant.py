# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockQuant(models.Model):
    _inherit = "stock.quant"

    is_metric_product = fields.Boolean(related='product_id.is_metric_product')