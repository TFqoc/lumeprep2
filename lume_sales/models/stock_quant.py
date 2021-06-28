# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Quant(models.Model):
    _inherit = 'stock.quant'

    is_tiered = fields.Boolean(related='product_id.is_tiered')

    # @api.model
    # def _get_available_quantity(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False, allow_negative=False):
    #     if self.sale_line_id and self.sale_line_id.lot_id:
    #         return super(Quant, self). _get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict, allow_negative=allow_negative)
    #     else:
    #         return super(Quant, self). _get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict, allow_negative=allow_negative)