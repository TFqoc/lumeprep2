# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    metrc_reported_qty = fields.Float(string='Quantity reported to Metrc', default=0.0, digits='Product Unit of Measure')
