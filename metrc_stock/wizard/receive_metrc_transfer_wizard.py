# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ReceiveMetrcTransferWizard(models.TransientModel):
    _name = 'metrc.transfer.receive.wizard'
    _description = 'Metrc Transfer Receive Wizard'

    facility_license_id = fields.Many2one(comodel_name='metrc.license',
                                          domain=[('base_type', '=', 'Internal')])
    operation_type_id = fields.Many2one(comodel_name='stock.picking.type',
                                        domain=[('code', '=', 'incoming')],
                                        string='Operation Type')
    location_dest_id = fields.Many2one(comodel_name='stock.location',
                                       string='Destination Location',
                                       help='Location where you want to receive packages.')
    transfer_ids = fields.Many2many(comodel_name='metrc.transfer')
    
    @api.onchange('operation_type_id')
    def onchange_operation_type(self):
        warehouse = self.operation_type_id.warehouse_id
        if warehouse:
            view_location = warehouse.view_location_id
            return {
                'domain': {
                    'location_dest_id': [('usage', '=', 'internal'), ('location_id', '=', view_location.id)]
                },
                'value': {
                    'location_dest_id': self.operation_type_id.default_location_dest_id and self.operation_type_id.default_location_dest_id.id,
                }
            }

    def create_transfer(self):
        StockPicking = self.env['stock.picking']
        ML = self.env['metrc.license']
        MT = self.env['metrc.transfer']
        supp_location = self.env.ref('stock.stock_location_suppliers')
        manifests = set(self.transfer_ids.mapped('manifest_number'))
        picking_ids = StockPicking
        for manifest in manifests:
            manifest_transfers = self.transfer_ids.filtered(lambda t: t.manifest_number == manifest)
            partner_license = ML.get_license(manifest_transfers[0].shipper_facility_license_number)
            pick = StockPicking.create({
                'partner_license_id': partner_license.id,
                'facility_license_id': self.facility_license_id.id,
                'picking_type_id': self.operation_type_id.id,
                'location_id': supp_location.id,
                'location_dest_id': self.location_dest_id.id,
                'move_lines': [(0, 0, {
                    'product_id': prod.id,
                    'name': prod.display_name,
                    'product_uom': prod.uom_id.id,
                    'product_uom_qty': sum(manifest_transfers.filtered(lambda l: l.product_id == prod).mapped('received_quantity')),
                }) for prod in manifest_transfers.mapped('product_id')]
            })
            move_line_vals = []
            for move in pick.move_lines:
                for line in manifest_transfers.filtered(lambda l: l.product_id == move.product_id):
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
            picking_ids |= pick
            all_manifest_transfers = MT.search([('manifest_number', '=', manifest)])
            processed_transfers = all_manifest_transfers.filtered(lambda t: t.move_line_id)
            if len(all_manifest_transfers) != len(manifest_transfers):
                (all_manifest_transfers - manifest_transfers).write({'manifest_status': 'Partial'})
            (manifest_transfers + processed_transfers).write({'manifest_status': 'Accepted'})
        action_data = self.env.ref('metrc_stock.action_view_metrc_transfer').read()[0]
        action_data['domain'] = [('id', 'in', picking_ids.ids)]
        return action_data
