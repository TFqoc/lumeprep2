# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_purchase_order_data(self, company, company_partner):
        res = super(SaleOrder, self)._prepare_purchase_order_data(company, company_partner)
        picking_type_id = self.env['stock.picking.type'].sudo().browse(res[0]['picking_type_id'])
        if picking_type_id and picking_type_id.warehouse_id.license_id and picking_type_id.warehouse_id.license_id.metrc_type == 'metrc':
            res[0].update({'facility_license_id': picking_type_id.warehouse_id.license_id.id})
        if self.facility_license_id:
            res[0].update({'partner_license_id': self.facility_license_id.id})
        return res[0]