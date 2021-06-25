# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import json
import math

def get_percent_index(l, percent):
    index = math.floor(len(l) * (percent/100))
    return min((index, len(l)-1))

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit='product.template'
    _order = 'is_lume desc, brand, name, list_price, default_code, id'

    brand = fields.Char()
    # thc = fields.Float()
    thc_type = fields.Selection([('medical','Medical'),('adult','Adult Use'),('merch','Merchandise')],default="merch",required=True)
    effect = fields.Selection([('unwind','Unwind'),('recover','Recover'),('move','Move'),('dream','Dream'),('focus','Focus'),('center','Center')])
    is_lume = fields.Boolean(compute="_compute_lume", store=True)
    is_tiered = fields.Boolean()

    @api.depends('brand')
    def _compute_lume(self):
        for record in self:
            if record.brand == 'Lume': # Hardcoded value so lume brand products always appear at the top.
                record.is_lume = True
            else:
                record.is_lume = False


class Product(models.Model):
    _inherit = 'product.product'
    _order = 'is_lume desc, brand, name, tier_price desc, list_price, default_code, id'
    
    lpc_quantity = fields.Integer('Material Quantity', compute="_compute_lpc_quantity", inverse="_inverse_lpc_quantity")
    # effect = fields.Selection(related="product_tmpl_id.effect", store=True)
    quantity_at_warehouses = fields.Char(compute="_compute_qty_at_warehouses",store=True)
    quantity_at_store = fields.Float(compute="_compute_qty_at_store")
    tier = fields.Selection([('none','None'),('top','Top'),('mid','Mid'),('value','Value'),('cut','Fresh Cut')], compute="_compute_tier")
    tier_price = fields.Float(compute="_compute_tier")
    thc = fields.Float()
    # Override
    is_product_variant = fields.Boolean(compute='_compute_is_product_variant',store=True)

    @api.depends('stock_quant_ids')
    def _compute_qty_at_warehouses(self):
        # Loop all warehouses
        for record in self:
            data = {}
            warehouse_id = self.env.context.get('warehouse_id', False)
            if not warehouse_id or True: # Testing condition. Should just always run
                for warehouse in self.env['stock.warehouse'].search([]):
                    quants = self.env['stock.quant'].search([('location_id','=',warehouse.lot_stock_id.id),('product_id','=',record.id)])
                    qty = sum([q.available_quantity for q in quants])
                    if qty > 0:
                        data[str(warehouse.name)] = qty
            # else:
            #     warehouse = self.env['stock.warehouse'].browse(warehouse_id)
            #     quants = self.env['stock.quant'].search([('location_id','=',warehouse.lot_stock_id.id),('product_id','=',record.id)])
            #     data[str(warehouse.id)] = sum([q.available_quantity for q in quants])
            record.quantity_at_warehouses = json.dumps(data)
        # Test for context
        _logger.info("CONTEXT: " + str(self.env.context))

    @api.depends_context('warehouse_id')
    def _compute_qty_at_store(self):
        for record in self:
            warehouse_id = self.env.context.get('warehouse_id', False)
            if not warehouse_id:
                record.quantity_at_store = 0
            else:
                warehouse = self.env['stock.warehouse'].browse(warehouse_id)
                quants = self.env['stock.quant'].search([('location_id','=',warehouse.lot_stock_id.id),('product_id','=',record.id)])
                record.quantity_at_store = sum([q.available_quantity for q in quants])
    
    @api.depends('product_tmpl_id.product_variant_ids')
    def _compute_is_product_variant(self):
        for record in self:
            record.is_product_variant = len(record.product_tmpl_id.product_variant_ids) > 1

    @api.depends_context('store_id')
    def _compute_tier(self):
        store_id = self.env.context.get('store_id', False)
        if (store_id):
            # Calcualte tier cutoffs for this store, Then loop through records
            store_id = self.env['project.project'].browse(store_id)
            # Get all quants regardless of product. (Change as needed when we find out lume's process)
            quants = self.env['stock.quant'].search([('is_tiered','=',True),('location_id','=',store_id.warehouse_id.lot_stock_id.id)])
            # Dict of name value pairs
            tiers = {}
            # {'name':{'min':0,'max':0,'price':0}}
            values = set()
            for q in quants:
                for attr in q.product_id.product_template_attribute_value_ids:
                    try:
                        percent = float(attr.name.split('%')[0])
                        values.add(percent)
                    except ValueError as v:
                        pass
            if len(values) != 0:
                values = sorted(values, reverse=True)
                _logger.info("Values: %s" % values)
                tiers['top'] = {'min': values[get_percent_index(values, store_id.top_tier)], 'max':values[0],'price':store_id.top_tier_price}
                tiers['mid'] = {'min': values[get_percent_index(values, store_id.mid_tier)], 'max':values[get_percent_index(values, store_id.top_tier)+1],'price':store_id.mid_tier_price}
                tiers['value'] = {'min': values[get_percent_index(values, store_id.value_tier)], 'max':values[get_percent_index(values, store_id.mid_tier)+1],'price':store_id.value_tier_price}
                tiers['cut'] = {'min': values[len(values)-1], 'max':values[get_percent_index(values, store_id.value_tier)+1],'price':store_id.cut_tier_price}
            _logger.info("TIERS: %s" % tiers)
            for record in self:
                record.tier = 'none'
                record.tier_price = record.list_price
                try:
                    thc = record.product_template_attribute_value_ids.filtered(lambda r: r.attribute_id.name == "THC").name
                    thc = float(thc.split('%')[0])
                except AttributeError as v:
                    pass
                for key, value in tiers.items():
                    if thc <= value['max'] and thc >= value['min']:
                        record.tier = key
                        record.tier_price = value['price']
                        break


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