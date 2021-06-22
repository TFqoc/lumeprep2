# -*- coding: utf-8 -*-

from odoo import fields, models


class ReceiveMetrcTransferWizard(models.TransientModel):
    _name = 'metrc.transfer.receive.wizard'
    _description = 'Metrc Transfer Receive Wizard'

    warehouse_id = fields.Many2one(comodel_name='stock.warehouse',
                                   string='Warehouse')
    partner_id = fields.Many2one(comodel_name='res.partner', 
                                 string='Vendor')
    partner_license_id = fields.Many2one(comodel_name='metrc.license',
                                         domain=[('base_type', '=', 'internal')],
                                         string='Vendor License')
    facility_license_id = fields.Many2one(related='warehouse_id.license_id',
                                          string='Facility License')
    operation_type_id = fields.Many2one(comodel_name='stock.picking.type',
                                        domain=[('code', '=', 'incoming')],
                                        string='Operation Type')
    view_location_id = fields.Many2one(related='warehouse_id.view_location_id')
    location_dest_id = fields.Many2one(comodel_name='stock.location',
                                       string='Destination Location',
                                       help='Location where you want to receive packages.')
    transfer_ids = fields.Many2many(comodel_name='metrc.transfer')

    def create_transfer(self):
        StockPicking = self.env['stock.picking']
        pick = StockPicking.create({
            'partner_id': self.partner_id.id,
            'partner_license_id': self.partner_license_id.id,
            'picking_type_id': self.operation_type_id.id,
            'location_id': self.partner_id.property_stock_supplier.id,
            'location_dest_id': self.location_dest_id.id,
            'move_lines': [(0, 0, {
                'product_id': prod.id,
                'name': prod.display_name,
                'product_uom': prod.uom_id.id,
                'product_uom_qty': sum(self.transfer_ids.filtered(lambda l: l.product_id == prod).mapped('received_quantity')),
            }) for prod in self.transfer_ids.mapped('product_id')]
        })
        move_line_vals = []
        for move in pick.move_lines:
            for line in self.transfer_ids.filtered(lambda l: l.product_id == move.product_id):
                move_line_vals.append({
                    'move_id': move.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'lot_name': line.package_label,
                    'qty_done': line.received_quantity,
                })
        pick.write({
            'move_line_ids': [(0, 0, move_line_dict) for move_line_dict in move_line_vals]
        })
        pick.action_confirm()
        pick.button_validate()
        return pick
