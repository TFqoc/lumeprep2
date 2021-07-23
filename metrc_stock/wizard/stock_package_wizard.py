# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPackageWizard(models.TransientModel):
    _name = 'stock.package.wizard'
    _description = 'Stock Package Wizard'

    lot_id = fields.Many2one(comodel_name='stock.production.lot', string='Package', ondelete='cascade',  required=True)
    product_id = fields.Many2one(comodel_name='product.product', related='lot_id.product_id', string='Facility License', ondelete='set null')
    product_uom_id = fields.Many2one(comodel_name='uom.uom', string='Unit of Measure', related='product_id.uom_id')
    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Inventoried Warehouse', ondelete='set null')
    location_id = fields.Many2one(comodel_name='stock.location', string='Warehouse Stock Location', domain=[('usage', 'in', ('internal', 'transit'))], ondelete='set null')
    license_id = fields.Many2one(comodel_name='metrc.license', related='lot_id.facility_license_id', string='Facility License', ondelete='set null')
    metrc_id = fields.Integer(string='Metrc ID')
    metrc_qty = fields.Float(string='Metrc Quantity', digits='Product Unit of Measure')
    metrc_uom_id = fields.Many2one(comodel_name='uom.uom', related='lot_id.metrc_uom_id')
    message = fields.Html(string='Message')
    virtual_available = fields.Float(string='Forecast Quantity', digits='Product Unit of Measure',
                                help='Forecast quantity (computed as Quantity On Hand '
                                     '- Outgoing + Incoming)\n'
                                     'In a context with a single Stock Location, this includes '
                                     'goods stored in this location, or any of its children.\n'
                                     'In a context with a single Warehouse, this includes '
                                     'goods stored in the Stock Location of this Warehouse, or any '
                                     'of its children.\n'
                                     'Otherwise, this includes goods stored in any Stock Location '
                                     'with \'internal\' type.')
    wh_qty_available = fields.Float(string="On-hand quantity", digits='Product Unit of Measure', help='On Hand Quantity for selected warehouse.')
    adjustment_required = fields.Boolean(string="Adjsutment Required", compute="_compute_adjustment_required")

    @api.depends('wh_qty_available', 'metrc_qty')
    def _compute_adjustment_required(self):
        for wiz in self:
            adjustment_required = False
            if wiz.metrc_id:
                if wiz.metrc_qty:
                    delta = wiz.virtual_available - wiz.metrc_qty
                    adjustment_required = True if delta != 0.00 else False
                else:
                    adjustment_required = True
            wiz.adjustment_required = adjustment_required

    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        self.metrc_qty = 0.0
        self.message = False
        if self.warehouse_id:
            self.location_id = self.warehouse_id.lot_stock_id or False
            product = self.product_id.with_context(lot_id=self.lot_id.id, warehouse=self.warehouse_id.id)
            self.virtual_available = product.virtual_available
            self.wh_qty_available = product.qty_available

    @api.onchange('location_id')
    def onchange_location_id(self):
        if self.location_id:
            location_warehouse = self.location_id.get_warehouse()
            if not self.warehouse_id and location_warehouse:
                self.warehouse_id = location_warehouse
            elif location_warehouse != self.warehouse_id and location_warehouse:
                self.warehouse_id = location_warehouse

            if self.product_id and self.warehouse_id:
                product = self.product_id.with_context(lot_id=self.lot_id.id, warehouse=self.warehouse_id.id)
                self.virtual_available = product.virtual_available

    def get_package_qty(self):
        # if not self.warehouse_id or not self.warehouse_id.license_id:
        #     raise UserError(_('Missing warehouse and/or facility license for the warehouse.'))
        resp = self.lot_id._fetch_metrc_package(license=self.warehouse_id.license_id)
        wizard_vals = {'message': False}
        product = self.product_id.with_context(lot_id=self.lot_id.id, warehouse=self.warehouse_id.id)
        if resp:
            if 'Quantity' in resp:
                if (resp['Item']['Name'] == product.metrc_name) or \
                   (resp['Item']['Name'] == self.lot_id.metrc_product_name):
                    self.lot_id.write({
                        'metrc_qty': resp['Quantity'],
                        'metrc_id': resp['Id'],
                    })
                    pack_detail = ''.join(['<li><strong>%s</strong>: %s</li>' % (key, val)
                                           for key, val in resp.items()])
                    wizard_vals.update({
                        'message': '<p><div><h3>Package Details (license : %s)</h3>'
                                   '</div><br/><ul>%s</ul></p>' % (self.license_id.license_number, pack_detail),
                        'virtual_available': product.virtual_available,
                        'wh_qty_available': product.qty_available,
                        'location_id': self.location_id.id if self.location_id else False,
                        'metrc_qty': resp['Quantity'],
                        'metrc_id': resp['Id'],
                    })
                    self.lot_id.message_post(body=wizard_vals['message'], message_type='notification',
                                             subtype_xmlid='mail.mt_comment')
                else:
                    wizard_vals.update({
                        'message': '<p><div><h3>Package found in METRC but with different product: <b>%s.</b><br/>'
                                   'Can not sync with <b>%s</b>.</h3></div></p>' % (resp['Item']['Name'],
                                                                                    product.metrc_name),
                        'virtual_available': product.virtual_available,
                        'wh_qty_available': product.qty_available,
                        'location_id': self.location_id.id if self.location_id else False,
                    })
            else:
                wizard_vals.update({
                    'message': '<p><div><h3>Lot %s was not found in METRC for license: %s </h3>'
                               '</div><br/></p>' % (self.lot_id._get_metrc_name(), self.license_id.license_number),
                    'virtual_available': product.virtual_available,
                    'wh_qty_available': product.qty_available,
                    'location_id': self.location_id.id if self.location_id else False,
                })
        else:
            wizard_vals['message'] = '<p><h3>Package not found in METRC for license {}.<br/>' \
                                     'Please select another License</h3></p>'.format(self.license_id.license_number)
        self.write(wizard_vals)
        action = self.env.ref('metrc_stock.action_view_stock_package_wizard').read()[0]
        action.update({
            'views': [(self.env.ref('metrc_stock.wizard_view_stock_package_wizard_form').id, 'form')],
            'res_id': self.id
        })
        return action

    def udpate_package_qty(self):
        metrc_account = self.env.user.ensure_metrc_account()
        if float_compare(self.wh_qty_available, self.metrc_qty, precision_rounding=self.product_uom_id.rounding):
            self.lot_id._adjust_in_metrc(metrc_account, self.license_id, (self.wh_qty_available - self.metrc_qty), delta=True)
            self.lot_id._update_metrc_id()
        return {'type': 'ir.actions.act_window_close'}

    def sync_package_qty(self):
        resp = self.lot_id._fetch_metrc_package(license=self.warehouse_id.license_id)
        locations = self.lot_id.sudo().quant_ids.filtered(lambda q: q.location_id.usage == 'internal')
        if not resp:
            raise UserError(_("Lot {} not found in metrc for license: {}".format(self.lot_id._get_metrc_name(), self.warehouse_id.license_id.license_number)))
        if resp and resp.get('Quantity') >= 0.00 and locations:
            self.lot_id.write({
                'labtest_state': resp['LabTestingState'],
                'testing_state_date': resp['LabTestingStateDate'],
                'metrc_qty': resp['Quantity'],
                'metrc_id': resp['Id'],
                'name_readonly': True,
                'is_production_batch': resp['IsProductionBatch'],
                'batch_number': resp['ProductionBatchNumber'],
            })
            quants = self.lot_id.sudo().quant_ids.filtered(lambda q: q.location_id.usage == 'internal')
            quants = self.env['stock.quant'].sudo().read_group([('location_id.usage', '=', 'internal'), ('id', 'in', quants.ids)], ['location_id', 'quantity'], ['location_id'])
            adjust_wizard = self.env['warehouse.package.adjustment'].create({
                'lot_id': self.lot_id.id,
                'metrc_quantity': self.product_id.from_metrc_qty(resp['Quantity']),
                'license_id': self.license_id.id,
                'line_ids': [(0, 0, {
                    'prod_lot_id': self.lot_id.id,
                    'location_id': q['location_id'][0],
                    'theoretical_qty': q['quantity'],
                    'product_qty': q['quantity']
                    }) for q in quants]
                })
            action_data = self.env.ref('metrc_stock.action_open_warehouse_package_adjustment_wizard').read()[0]
            action_data['res_id'] = adjust_wizard.id
            return action_data
        if not locations:
            raise UserError(_("Lot {} not found on any physical location under warehouse: {}".format(self.lot_id._get_metrc_name(), self.warehouse_id.name)))
        return {'type': 'ir.actions.act_window_close'}
