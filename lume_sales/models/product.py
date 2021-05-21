# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit='product.template'

    is_medical = fields.Boolean()
    effect = fields.Selection([('unwind','Unwind'),('recover','Recover'),('move','Move'),('dream','Dream'),('focus','Focus'),('center','Center')])

class Product(models.Model):
    _inherit = 'product.product'

    lpc_quantity = fields.Integer('Material Quantity', compute="_compute_lpc_quantity", inverse="_inverse_lpc_quantity")
    effect = fields.Selection(related="product_tmpl_id.effect", store=True)

    @api.depends_context('lpc_sale_order_id')
    def _compute_lpc_quantity(self):
        sale_order = self._get_contextual_lpc_sale_order()
        if sale_order:

            SaleOrderLine = self.env['sale.order.line']
            if self.user_has_groups('project.group_project_user'):
                sale_order = sale_order.sudo()
                SaleOrderLine = SaleOrderLine.sudo()

            products_qties = SaleOrderLine.read_group(
                [('id', 'in', sale_order.order_line.ids)],
                ['product_id', 'product_uom_qty'], ['product_id'])
            qty_dict = dict([(x['product_id'][0], x['product_uom_qty']) for x in products_qties])
            for product in self:
                product.lpc_quantity = qty_dict.get(product.id, 0)
        else:
            self.lpc_quantity = False

    def _inverse_lpc_quantity(self):
        sale_order = self._get_contextual_lpc_sale_order()
        if sale_order:
            for product in self:
                sale_line = self.env['sale.order.line'].search([('order_id', '=', sale_order.id), ('product_id', '=', product.id), '|', '|', ('qty_delivered', '=', 0.0), ('qty_delivered_method', '=', 'manual'), ('state', 'not in', ['sale', 'done'])], limit=1)
                if sale_line:  # existing line: change ordered qty (and delivered, if delivered method)
                    vals = {
                        'product_uom_qty': product.lpc_quantity
                    }
                    if sale_line.qty_delivered_method == 'manual':
                        vals['qty_delivered'] = product.lpc_quantity
                    if vals['product_uom_qty'] == 0:
                        sale_line.unlink()
                    else:
                        sale_line.with_context(lpc_no_message_post=True).write(vals)
                else:  # create new SOL
                    vals = {
                        'order_id': sale_order.id,
                        'product_id': product.id,
                        'product_uom_qty': product.lpc_quantity,
                        'product_uom': product.uom_id.id,
                    }
                    if product.service_type == 'manual':
                        vals['qty_delivered'] = product.lpc_quantity

                    # Note: force to False to avoid changing planned hours when modifying product_uom_qty on SOL
                    # for materials. Set the current task for service to avoid re-creating a task on SO confirmation.
                    # if product.type == 'service':
                    #     vals['task_id'] = task.id
                    # else:
                    #     vals['task_id'] = False
                    if vals['product_uom_qty'] != 0:
                        sale_line = self.env['sale.order.line'].create(vals)

    @api.model
    def _get_contextual_lpc_sale_order(self):
        sale_order_id = self.env.context.get('lpc_sale_order_id')
        if sale_order_id:
            return self.env['sale.order'].browse(sale_order_id)
        return self.env['sale.order']

    def set_lpc_quantity(self, quantity):
        sale_order = self._get_contextual_lpc_sale_order()
        # project user with no sale rights should be able to change material quantities
        if not sale_order or quantity and quantity < 0 or not self.user_has_groups('project.group_project_user'):
            # if not sale_order:
            #     raise ValidationError("No sale order" + str(self.env.context))
            # if not quantity:
            #     raise ValidationError("Quantity: " + str(quantity))
            return
        self = self.sudo()
        # don't add material on confirmed/locked SO to avoid inconsistence with the stock picking
        if sale_order.state == 'done':
            return False
        wizard_product_lot = self.action_assign_serial()
        if wizard_product_lot:
            return wizard_product_lot
        self.lpc_quantity = quantity
        return True

    # Is override by lpc_stock to manage lot
    def action_assign_serial(self):
        return False

    def lpc_add_quantity(self):
        return self.set_lpc_quantity(self.sudo().lpc_quantity + 1)

    def lpc_remove_quantity(self):
        return self.set_lpc_quantity(self.sudo().lpc_quantity - 1)