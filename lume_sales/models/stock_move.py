# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        if self.sale_line_id and self.sale_line_id.lot_id:
            # self.env.context = dict(self.env.context)
            # self.env.context.update({"force_lot_id":self.sale_line_id.lot_id.id})
            # return super(StockMove, self)._action_assign()
            for r in self:
                r.env.context = dict(r.env.context)
                r.env.context.update({"force_lot_id":r.sale_line_id.lot_id.id})
                return super(StockMove, r)._action_assign()
        else:
            return super(StockMove, self)._action_assign()

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        if self.sale_line_id and self.sale_line_id.lot_id:
            lot_id = self.sale_line_id.lot_id
            return super(StockMove, self)._update_reserved_quantity(need, available_quantity, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)