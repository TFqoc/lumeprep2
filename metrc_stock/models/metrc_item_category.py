# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class MetrcProductCategory(models.Model):
    _inherit = 'metrc.product.category'

    is_flower = fields.Boolean()
    is_edible = fields.Boolean()