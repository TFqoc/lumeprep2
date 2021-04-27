# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductUoM(models.Model):
    _inherit = 'uom.uom'

    abbrv_name = fields.Char(string='Metrc Abbreviation')
    metrc_uom = fields.Boolean(string='Used with Metrc')
