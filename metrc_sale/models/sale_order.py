# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_facility_license_id(self):
        return self.warehouse_id.license_id.id if self.warehouse_id and self.warehouse_id.license_id else False

    license_required = fields.Boolean(string="Processing Metrc Products",
                                      compute='_compute_license_required',
                                      states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    license_id = fields.Many2one(comodel_name='metrc.license', string='Customer License', index=True)
    facility_license_id = fields.Many2one(comodel_name='metrc.license', string='Facility License', compute="_compute_facility_license_id", store=True, default=_default_facility_license_id)
    ecommerce_order = fields.Boolean(string='eCommerce Order')

    @api.depends('order_line', 'order_line.product_id', 'order_line.product_id.is_metric_product', 'warehouse_id')
    def _compute_license_required(self):
        for order in self:
            if order.order_line:
                order.license_required = True if any([line.product_id.is_metric_product for line in order.order_line]) and \
                                        (order.warehouse_id.license_id and order.warehouse_id.license_id.metrc_type == 'metrc') else False
            else:
                order.license_required = False

    @api.depends('warehouse_id')
    def _compute_facility_license_id(self):
        self.facility_license_id = self.warehouse_id.license_id if self.warehouse_id and self.warehouse_id.license_id else False

    def action_confirm(self):
        for order in self:
            if order.license_required and not order.license_id:
                raise UserError(_('Order can not be confirmed!\nPlease provide license of %s' % (order.partner_id.name)))
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.license_required:
                order.picking_ids.write({'partner_license_id': order.license_id.id})
        return res

    def _prepare_invoice(self):
        self.ensure_one()
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
            'partner_license_id': self.license_id.id if self.license_id else False,
            'facility_license_id': self.facility_license_id.id if self.facility_license_id else False,
        })
        return res
