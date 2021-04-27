# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_pos_operation = fields.Boolean(string='Used in POS', compute='_compute_is_pos_operation')

    def _compute_is_pos_operation(self):
        PosConfig = self.env['pos.config'].sudo()
        for op in self:
            config = PosConfig.search([('picking_type_id', '=', op.id)], limit=1)
            op.is_pos_operation = True if config else False


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.depends('move_lines', 'move_line_ids', 'move_line_ids.qty_done', 'move_line_ids.product_uom_qty')
    def _compute_metrc_validation(self):
        super(StockPicking, self)._compute_metrc_validation()
        for pick in self:
            if (pick.group_id and pick.group_id.sale_id and \
               pick.group_id.sale_id.team_id) or \
               (pick.picking_type_id.is_pos_operation):
                pick.require_metrc_validation = False
