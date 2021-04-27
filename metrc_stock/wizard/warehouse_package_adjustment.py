# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import float_is_zero


class WarehousePackageAdjustment(models.TransientModel):
    _name = "warehouse.package.adjustment"
    _description = "Warehouse Package Adjustment"

    lot_id = fields.Many2one("stock.production.lot")
    product_id = fields.Many2one(related="lot_id.product_id")
    license_id = fields.Many2one("metrc.license")
    line_ids = fields.One2many("warehouse.package.adjustment.line", 'adjustment_id')
    qty_available = fields.Float(compute="_compute_quantities", digits='Product Unit of Measure')
    metrc_quantity = fields.Float(string="Metrc Quantity", digits='Product Unit of Measure')
    product_uom_id = fields.Many2one(related="product_id.uom_id")
    metrc_adjust_qty = fields.Float(compute="_compute_quantities", digits='Product Unit of Measure')

    @api.depends('line_ids', 'line_ids.product_qty')
    def _compute_quantities(self):
        for adj in self:
            adj.qty_available = sum(adj.line_ids.mapped('product_qty'))
            adj.metrc_adjust_qty = adj.qty_available - adj.metrc_quantity

    def perform_adjustments(self):
        metrc_account = self.env.user.ensure_metrc_account()
        for line in self.line_ids:
            line.prod_lot_id._adjust_lot(line.product_id.to_metrc_qty(line.product_qty), downstream=True, location_id=line.location_id, warehouse_id=line.location_id.get_warehouse())
        if not float_is_zero(self.metrc_adjust_qty, precision_rounding=self.product_uom_id.rounding):
            self.lot_id._adjust_in_metrc(metrc_account, self.license_id, self.metrc_adjust_qty, delta=True)
            self.lot_id._update_metrc_id()


class WarehousePackageAdjustmentLine(models.TransientModel):
    _name = "warehouse.package.adjustment.line"
    _description = "Warehouse Package Adjustment Line"

    adjustment_id = fields.Many2one("warehouse.package.adjustment")
    prod_lot_id = fields.Many2one("stock.production.lot")
    product_id = fields.Many2one(related="prod_lot_id.product_id")
    uom_id = fields.Many2one(related="product_id.uom_id")
    location_id = fields.Many2one("stock.location")
    theoretical_qty = fields.Float(string="Theoretical Qty", digits='Product Unit of Measure')
    product_qty = fields.Float(string="Real Qty", digits='Product Unit of Measure')
