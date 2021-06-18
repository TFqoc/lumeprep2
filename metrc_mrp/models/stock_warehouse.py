# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    metrc_manu_type_id = fields.Many2one(comodel_name='stock.picking.type',
                                         string='Batch Split Operation Type')
    metrc_merge_type_id = fields.Many2one(comodel_name='stock.picking.type',
                                         string='Consolidation Operation Type')

    def create_sequences_and_picking_types(self):
        res = super(StockWarehouse, self).create_sequences_and_picking_types()
        self._create_batch_split_picking_type()
        self._create_consolidation_picking_type()
        return res

    def _create_batch_split_sequence(self):
        return self.env['ir.sequence'].create({
            'name': self.name + ' ' + "SPLIT",
            'code': 'batch_split',
            'prefix': self.code + '/SPLIT/',
            'padding': 5,
            'company_id': self.company_id.id,
        })
    
    def _create_consolidation_sequence(self):
        return self.env['ir.sequence'].create({
            'name': self.name + ' ' + "CONSOLIDATION",
            'code': 'consolidation',
            'prefix': self.code + '/CON/',
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
            batch_split_seq = seq_obj.search([('code', '=', 'batch_split')], limit=1)
            if not batch_split_seq:
                batch_split_seq = warehouse._create_batch_split_sequence()
            consolidation_seq = seq_obj.search([('code', '=', 'consolidation')], limit=1)
            if not consolidation_seq:
                consolidation_seq = warehouse._create_consolidation_sequence()
            other_pick_type = picking_type_obj.search([('warehouse_id', '=', warehouse.id)], order='sequence desc', limit=1)
            color = other_pick_type.color if other_pick_type else 0
            max_sequence = other_pick_type and other_pick_type.sequence or 0
            picking_type_vals = [
                {
                    'name': _('Batch Split'),
                    'sequence_id': batch_split_seq.id,
                    'wh_field': 'metrc_manu_type_id',
                }
                {
                    'name': _('Consolidation'),
                    'sequence_id': consolidation_seq.id,
                    'wh_field': 'metrc_merge_type_id',
                }
            ]
            for picking_type_val in picking_type_vals:
                wh_field = picking_type_val.pop('wh_field')
                values = {
                    'warehouse_id': warehouse.id,
                    'code': 'mrp_operation',
                    'use_create_lots': True,
                    'use_existing_lots': False,
                    'default_location_src_id': wh_stock_loc.id,
                    'default_location_dest_id': wh_stock_loc.id,
                    'sequence_code': max_sequence,
                    'color': color}
                values.extend(picking_type_val)
                manu_type = picking_type_obj.create(values)
                warehouse.write({wh_field: manu_type.id})
