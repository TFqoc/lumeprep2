# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        res = super(PurchaseOrder, self)._prepare_sale_order_data(name, partner, company, direct_delivery_address)
        warehouse = self.env['stock.warehouse'].sudo().browse(res[0]['warehouse_id'])
        if not warehouse:

            raise Warning(_('Configure correct warehouse for company(%s) from Menu: Settings/Users/Companies' % (company.name)))
        if warehouse.license_id and warehouse.license_id.metrc_type == 'metrc':
            res[0].update({'facility_license_id': warehouse.license_id.id})
        if self.facility_license_id:
            res[0].update({'license_id': self.facility_license_id.id})
        return res[0]