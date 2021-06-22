# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _default_facility_license_id(self):
        return self.picking_type_id.warehouse_id.license_id.id if self.picking_type_id and self.picking_type_id.warehouse_id.license_id else False

    license_vendor = fields.Boolean(related='partner_id.license_vendor')
    partner_license_id = fields.Many2one(comodel_name='metrc.license', string='Vendor License', index=True)
    facility_license_id = fields.Many2one(comodel_name='metrc.license', string='Facility License', compute="_compute_facility_license_id", store=True, default=_default_facility_license_id)
    license_require = fields.Boolean(string='Licensed Purchase', compute='_compute_license_require')

    @api.depends('picking_type_id')
    def _compute_facility_license_id(self):
        self.facility_license_id = self.picking_type_id.warehouse_id.license_id if self.picking_type_id and self.picking_type_id.warehouse_id.license_id else False

    @api.depends('order_line', 'order_line.product_id', 'picking_type_id')
    def _compute_license_require(self):
        for po in self:
            po.license_require = True if any(po.order_line.mapped('product_id.is_metric_product')) and \
                                 (po.picking_type_id._get_warehouse_license() and po.picking_type_id.warehouse_id.license_id.metrc_type == 'metrc') else False

    @api.model
    def _prepare_picking(self):
        picking_data = super(PurchaseOrder, self)._prepare_picking()
        picking_data.update({
            'partner_license_id': self.partner_license_id.id if self.partner_license_id else False,
        })
        return picking_data

    def action_view_invoice(self):
        result = super(PurchaseOrder, self).action_view_invoice()
        result['context']['default_partner_license_id'] = self.partner_license_id.id if self.partner_license_id else False
        result['context']['default_facility_license_id'] = self.facility_license_id.id if self.facility_license_id else False
        return result
