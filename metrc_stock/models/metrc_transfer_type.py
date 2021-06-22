# -*- coding: utf-8 -*-

from odoo import fields, models


class MetrcTransferType(models.Model):
    _name = 'metrc.transfer.type'
    _description = 'Metrc Transfer Types'
    _inherit = ['metrc.meta']
    _metrc_model_name = 'transfers'
    _metrc_license_require = True

    def _valid_field_parameter(self, field, name):
        # allow tracking on abstract models; see also 'mail.thread'
        return (
            name in ('metrc_field', 'metrc_rec_name') or super()._valid_field_parameter(field, name)
        )

    def _get_api_actions(self):
        return self._metrc_model_name, {
            'read': 'types'
        }

    name = fields.Char(metrc_rec_name=True, metrc_field='Name', index=True)
    licensed_shipments = fields.Boolean(string='For Licensed Shipments', metrc_field='ForLicensedShipments')
    external_incoming_shipments = fields.Boolean(string='For External Incoming Shipments', metrc_field='ForExternalIncomingShipments')
    external_outgoing_shipments = fields.Boolean(string='For External Outgoing Shipments', metrc_field='ForExternalOutgoingShipments')
    gross_weight_required = fields.Boolean(string='Requires Packages Gross Weight', metrc_field='RequiresPackagesGrossWeight')
