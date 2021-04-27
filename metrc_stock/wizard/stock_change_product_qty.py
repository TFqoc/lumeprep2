# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools,  _


class ProductChangeQuantity(models.TransientModel):
    _inherit = "stock.change.product.qty"

    is_metric_product = fields.Boolean(related="product_id.is_metric_product")
    tracking = fields.Selection(related="product_id.tracking")
    facility_license_id = fields.Many2one('metrc.license', string="Facility License")
    reason_id = fields.Many2one('metrc.package.adjust.reason')

    def change_product_qty(self):
        """ Changes the Product Quantity by making a Physical Inventory. """
        Inventory = self.env['stock.inventory']
        for wizard in self:
            product = wizard.product_id.with_context(location=wizard.location_id.id, lot_id=wizard.lot_id.id)
            line_data = wizard._action_start_line()
            if wizard.product_id.id and wizard.lot_id.id:
                inventory_filter = 'none'
            elif wizard.product_id.id:
                inventory_filter = 'product'
            else:
                inventory_filter = 'none'
            inventory_values = {
                'name': _('INV: %s') % tools.ustr(wizard.product_id.display_name),
                'filter': inventory_filter,
                'product_id': wizard.product_id.id,
                'location_id': wizard.location_id.id,
                'lot_id': wizard.lot_id.id,
                'line_ids': [(0, 0, line_data)],
            }
            if wizard.is_metric_product and wizard.facility_license_id and wizard.reason_id:
                inventory_values.update({
                    'facility_license_id': wizard.facility_license_id.id,
                    'reason_id': wizard.reason_id.id,
                    })
            inventory = Inventory.with_context({'force_create_lot': True}).create(inventory_values)
            inventory.action_done()
        return {'type': 'ir.actions.act_window_close'}
