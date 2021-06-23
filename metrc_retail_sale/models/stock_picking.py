# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.depends('move_lines', 'move_line_ids', 'move_line_ids.qty_done', 'move_line_ids.product_uom_qty')
    def _compute_metrc_validation(self):
        super(StockPicking, self)._compute_metrc_validation()
        for pick in self:
            if (pick.group_id and pick.group_id.sale_id and \
                pick.group_id.sale_id.team_id) and \
                pick.group_id.sale_id.team_id.metrc_retail_reporting:
                pick.require_metrc_validation = False