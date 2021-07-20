# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    # def _action_assign(self):
    #     res = super(StockMove, self)._action_assign()
    #     for move in self.filtered(lambda x: x.production_id or x.raw_material_production_id):
    #         for move_line in move.move_line_ids.filtered(lambda ml: ml.lot_id and ml.product_id.is_metric_product):
    #             for quant in move_line.quant_ids:
    #                 if float_compare(quant.reserved_quantity, quant.quantity, precision_rounding=move.product_uom.rounding) != 0:
    #                     move._do_unreserve()
    #                     break
    #     return res

    lot_to_reserve = fields.Many2one('stock.production.lot', copy=False)

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        if self.env.context.get('force_lot_id') and self.product_id.is_metric_product:
            lot_obj = self.env['stock.production.lot'].browse(self.env.context.get('force_lot_id'))
            self.lot_to_reserve = lot_obj
            lot_id = lot_obj
            strict = True
        return super(StockMove, self)._update_reserved_quantity(need, available_quantity, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)


    def button_scrap(self):
        self.ensure_one()
        if any([move.product_id.is_metric_product for move in self.move_lines]):
            raise ValidationError(_('This a Metrc synced product and can not be scrapped!\n Create an inventory adjustment instead.'))
        return super(StockMove, self).button_scrap()
