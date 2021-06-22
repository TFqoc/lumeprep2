# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    metrc_manu_type_id = fields.Many2one('stock.picking.type')

    def create_sequences_and_picking_types(self):
        res = super(StockWarehouse, self).create_sequences_and_picking_types()
        self._create_batch_split_picking_type()
        return res

    def _create_batch_split_sequence(self):
        return self.env['ir.sequence'].create({
            'name': self.name + ' ' + "SPLIT",
            'code': 'batch_split',
            'prefix': self.code + '/SPLIT/',
            'padding': 5,
            'company_id': self.company_id.id,
        })

    def _create_batch_split_picking_type(self):
        # TDE CLEANME
        picking_type_obj = self.env['stock.picking.type']
        seq_obj = self.env['ir.sequence']
        for warehouse in self:
            if warehouse.metrc_manu_type_id:
                continue
            wh_stock_loc = warehouse.lot_stock_id
            seq = seq_obj.search([('code', '=', 'batch_split')], limit=1)
            if not seq:
                seq = warehouse._create_batch_split_sequence()
            other_pick_type = picking_type_obj.search([('warehouse_id', '=', warehouse.id)], order='sequence desc', limit=1)
            color = other_pick_type.color if other_pick_type else 0
            max_sequence = other_pick_type and other_pick_type.sequence or 0
            manu_type = picking_type_obj.create({
                'name': _('Batch Split'),
                'warehouse_id': warehouse.id,
                'code': 'mrp_operation',
                'use_create_lots': True,
                'use_existing_lots': False,
                'sequence_id': seq.id,
                'default_location_src_id': wh_stock_loc.id,
                'default_location_dest_id': wh_stock_loc.id,
                'sequence_code': max_sequence,
                'color': color})
            warehouse.write({'metrc_manu_type_id': manu_type.id})
