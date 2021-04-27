# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MetrcPackageReceiveWizard(models.TransientModel):
    _name = 'metrc.package.receive'

    vendor_id = fields.Many2one(comodel_name='res.partner')
    vendor_license_ids = fields.One2many(related='vendor_id.license_ids')
    vendor_license_id = fields.Many2one(comodel_name='metrc.license')
    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', help="Warehouse to which packages are being received.")
    facility_license_id = fields.Many2one(related="warehouse_id.license_id")
    move_ids = fields.Many2many(comodel_name='stock.move')
    receive_line = fields.One2many(comodel_name='metrc.package.receive.line', inverse_name='receive_id')

    @api.onchange('vendor_id')
    def onchange_vendor(self):
        if self.vendor_id.license_ids:
            self.vendor_license_id = self.vendor_id.license_ids[0]

    def receive(self):
        transfer_domain = [
            ('transfer_type', '=', 'incoming'),
            ('shipment_package_state', '=', 'Accepted'),
            ('src_license', '=', self.facility_license_id.license_number),
            ('shipper_facility_license_number', '=', self.vendor_license_id.license_number),
        ]
        metrc_transfers = self.env['metrc.transfer'].search(transfer_domain)
        qty_mismatch = []
        for receive in self.receive_line:
            packages = receive.metrc_packages.split(',')
            receive_transfers = metrc_transfers.filtered(lambda mt: mt.package_label in packages)
            total_qty = sum(receive_transfers.mapped('received_quantity'))
            move_line_vals = []
            if receive.product_uom_qty == total_qty:
                for package in packages:
                    lot = self.env['stock.production.lot'].search([
                        '|', ('name', '=', package),
                        ('metrc_tag', '=', package),
                        ('product_id', '=', receive.product_id.id)], limit=1)
                    if not lot:
                        lot = self.env['stock.production.lot'].create({
                            'name': package,
                            'product_id': receive.product_id.id,
                            'company_id': self.env.company.id
                        })
                    move_line_vals = receive.stock_move_id._prepare_move_line_vals(quantity=total_qty)
                    move_line_vals['qty_done'] = move_line_vals['product_uom_qty']
                    move_line_vals['lot_id'] = lot.id
                    self.env['stock.move.line'].create(move_line_vals)
                receive.picking_id.button_validate()

    def generate_moves_to_receive(self):
        picking_domain = [
            ('state', '=', 'assigned'),
            ('picking_type_code', '=', 'incoming'),
            ('location_dest_id.usage', '=', 'internal'),
            ('facility_license_id', '=', self.facility_license_id.id),
        ]
        pickings = self.env['stock.picking'].search(picking_domain)
        metrc_moves = pickings.mapped('move_lines').filtered(lambda ml: ml.product_id.is_metric_product == True)
        receive_lines = []
        for move in metrc_moves:
            receive_lines.append((0, 0, {
                'stock_move_id': move.id,
            }))
        self.write({'receive_line': receive_lines})
        action_data = self.env.ref('metrc.action_open_metrc_package_receive_wizard').read()[0]
        action_data['res_id'] = self.id
        action_data['context'] = {'hide_receive': False}
        return action_data


class MetrcPackageReceiveWizardLine(models.TransientModel):
    _name = 'metrc.package.receive.line'

    receive_id = fields.Many2one(comodel_name='metrc.package.receive')
    package_label = fields.Char()
    shipped_qty = fields.Float()
    shipped_uom = fields.Char()
    received_qty = fields.Float()
    shipped_date = fields.Datetime()
    stock_move_id = fields.Many2one(comodel_name='stock.move')
    picking_id = fields.Many2one(related='stock_move_id.picking_id')
    product_id = fields.Many2one(related='stock_move_id.product_id')
    product_uom_qty = fields.Float(related='stock_move_id.product_uom_qty')
    product_uom = fields.Many2one(related='stock_move_id.product_uom')
    metrc_packages = fields.Text()
