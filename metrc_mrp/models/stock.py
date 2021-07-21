# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    reported_to_metrc = fields.Boolean(help="Technical Field to determine Metrc reporting")
    bypass_metrc_reporting = fields.Boolean(help="Technical Field to determine should skip metrc reporting or not.")