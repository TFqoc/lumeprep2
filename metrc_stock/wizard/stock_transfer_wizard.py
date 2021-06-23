# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class StockTransferWizard(models.TransientModel):
    _name = 'stock.transfer.wizard'
    _description = 'Stock Transfer Wizard'


    picking_id = fields.Many2one(comodel_name='stock.picking', string='Transfer',
                                ondelete='cascade',  required=True)
    message = fields.Html(string='Message')
    create_extin = fields.Selection(selection=[('Yes', 'Yes (I authorize)'), ('No', 'No')],
                                    string='Do you want create external incoming for listed packages ?')
    transfer_type_id = fields.Many2one('metrc.transfer.type', string='Metrc Transfer Type', copy=False)
    transporter_license_id = fields.Many2one('metrc.license', string='Transporter License')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    driver_id = fields.Many2one('res.partner')
    driver_license_number = fields.Char(string='Driver\'s License Number')
    route = fields.Text(string='Planned Route')
    has_layover = fields.Boolean(string='Has Layover?')
        
    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        self.driver_id = self.vehicle_id.driver_id if self.vehicle_id else self.driver_id

    @api.onchange('driver_id')
    def onchange_driver_id(self):
        self.driver_license_number = self.driver_id.driver_license_number if self.driver_id else self.driver_license_number

    def action_create_valiate(self):
        if self.create_extin == 'Yes':
            self.picking_id.write({
                    'transfer_type_id': self.transfer_type_id.id,
                    'transporter_license_id': self.transporter_license_id.id,
                    'driver_id': self.driver_id.id,
                    'vehicle_id': self.vehicle_id.id,
                    'driver_license_number': self.driver_license_number,
                    'route': self.route,
                    'has_layover': self.has_layover,
                })
            self.picking_id.message_post(body=_('<p><em> %s </em> authorized creation of external incoming transfer on Metrc.</p>') % (self.env.user.name))
            self.picking_id.create_external_incoming_validate()
        return {'type': 'ir.actions.act_window_close'}

    def action_create_transfer_manifest(self):
        self.picking_id.write({
                'transfer_type_id': self.transfer_type_id.id,
                'transporter_license_id': self.transporter_license_id.id,
                'driver_id': self.driver_id.id,
                'vehicle_id': self.vehicle_id.id,
                'driver_license_number': self.driver_license_number,
                'route': self.route,
                'has_layover': self.has_layover,
            })
        ret = self.picking_id.create_transfer_template_validate()
        return ret

    def action_message_ok(self):
        self.picking_id.message_post(body=self.message)
