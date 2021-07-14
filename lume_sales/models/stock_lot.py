# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockLot(models.Model):
    _inherit = 'stock.production.lot'
    _order = 'create_date'

    image_128 = fields.Image(related='product_id.image_128')
    image_1920 = fields.Image(related='product_id.image_1920')
    currency_id = fields.Many2one(related='product_id.currency_id')
    # uom_id = fields.Many2one(related='product_id.uom_id')
    thc_type = fields.Selection(related='product_id.thc_type')

    # Group by fields
    categ_id = fields.Many2one('product.category',compute='_compute_groupby_fields',store=True)
    effect = fields.Selection([('unwind','Unwind'),('recover','Recover'),('move','Move'),('dream','Dream'),('focus','Focus'),('center','Center')],compute='_compute_groupby_fields',store=True)
    brand = fields.Char(compute='_compute_groupby_fields',store=True)

    price = fields.Float(compute="_compute_price")
    stock_at_store = fields.Float(compute="_compute_stock_at_store")
    lpc_quantity = fields.Integer('Product Quantity', compute="_compute_lpc_quantity", inverse="_inverse_lpc_quantity")

    # Temp fields for testing that will be added by Keyur in metrc
    tier = fields.Selection([('test','Test')], default="test")

    @api.depends('product_id.categ_id','product_id.effect','product_id.brand')
    def _compute_groupby_fields(self):
        for record in self:
            record.categ_id = record.product_id.categ_id
            record.effect = record.product_id.effect
            record.brand = record.product_id.brand

    def _compute_price(self):
        for record in self:
            # TODO more logic here for tiers and store type
            # Might depend on the context
            record.price = record.product_id.list_price

    @api.depends_context("warehouse_id")
    def _compute_stock_at_store(self):
        location_id = self.env['stock.warehouse'].browse(self.env.context.get('warehouse_id')).lot_stock_id
        for record in self:
            quants = record.quant_ids.filtered(lambda q: q.location_id.id == location_id.id)
            record.stock_at_store = sum([q.quantity for q in quants])

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
                ['product_id', 'product_uom_qty','lot_id'], ['lot_id'])
            qty_dict = dict([(x['lot_id'][0], x['product_uom_qty']) for x in products_qties])
            for lot in self:
                lot.lpc_quantity = qty_dict.get(lot.id, 0)
        else:
            self.lpc_quantity = False

    def _inverse_lpc_quantity(self):
        sale_order = self._get_contextual_lpc_sale_order()
        if sale_order:
            for lot in self:
                sale_line = self.env['sale.order.line'].search([('order_id', '=', sale_order.id),('lot_id','=',lot.id), ('product_id', '=', lot.product_id.id), '|', '|', ('qty_delivered', '=', 0.0), ('qty_delivered_method', '=', 'manual'), ('state', 'not in', ['sale', 'done'])], limit=1)
                if sale_line:  # existing line: change ordered qty (and delivered, if delivered method)
                    vals = {
                        'product_uom_qty': lot.lpc_quantity
                    }
                    if sale_line.qty_delivered_method == 'manual':
                        vals['qty_delivered'] = lot.lpc_quantity
                    if vals['product_uom_qty'] == 0:
                        sale_line.unlink()
                    else:
                        sale_line.with_context(lpc_no_message_post=True).write(vals)
                else:  # create new SOL
                    vals = {
                        'order_id': sale_order.id,
                        'product_id': lot.product_id.id,
                        'product_uom_qty': lot.lpc_quantity,
                        'product_uom': lot.product_id.uom_id.id,
                        'lot_id': lot.id,
                    }
                    if lot.product_id.service_type == 'manual':
                        vals['qty_delivered'] = lot.lpc_quantity

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
        if self.env.context.get('type') != self.thc_type and self.thc_type and self.thc_type in ['medical','adult'] and self.env.context.get('type') != 'none':
            raise ValidationError("You can't add a %s product to a cart with %s products!" % (self.thc_type,self.env.context.get('type')))
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
        self.lpc_quantity = quantity
        return True

    def lpc_add_quantity(self):
        return self.set_lpc_quantity(self.sudo().lpc_quantity + 1)

    def lpc_remove_quantity(self):
        return self.set_lpc_quantity(self.sudo().lpc_quantity - 1)
