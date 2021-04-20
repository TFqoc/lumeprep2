# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
import datetime as date
import logging
_logger = logging.getLogger(__name__)

class pos_test(models.Model):
    _inherit = 'sale.order'

    @api.model
    def get_all(self):
        return self.env['sale.order'].search([])

    @api.model
    def get_orders(self, ids, session_id):
        config_id = self.env['pos.session'].browse(session_id).config_id
        # Use config_id to filter sale orders to just the ones that apply to this store
        orders = self.env['sale.order'].search([('id','not in', ids),('state','in',['sale'])])#more states could be added
        data = {}
        new_orders = {"unpaid_orders":self.jsonify_orders(orders, session_id)}

        data['new_orders'] = new_orders
        orders = self.env['sale.order'].search([('id','in', ids)])
        old_orders = []
        for order in orders:
            if order.state != 'sale':
                old_orders.append(order.id)

        data['old_orders'] = old_orders

        orders = orders.filtered(lambda x: (date.datetime.now() - x.write_date).total_seconds() < 10)
        data['update_orders'] = self.jsonify_orders(orders, session_id)
        return json.dumps(data, default=str)

    @api.model
    def remove_item(self, order_id, product_id):
        for line in self.browse(order_id).order_line:
            if line.product_id.id == product_id:
                line.unlink()
                break
    
    @api.model
    def add_item(self, order_id, product_id, quantity):
        vals = {
            # 'name':'description',
            'order_id':order_id,
            'product_uom_qty':quantity,
            'product_id': product_id,
        }
        self.browse(order_id).order_line = [(0,0,vals)]
        # TODO Do stuff to add to delivery

    @api.model
    def update_item_quantity(self, order_id, product_id, quantity):
        for line in self.browse(order_id).order_line:
            if line.product_id.id == product_id:
                line.product_uom_qty = quantity
                break

    @api.model
    def jsonify_orders(self, orders, session_id):
        list_data = []
        for order in orders:
            json_data = {
                'sale_order_id':order.id,
                'pos_session_id':session_id,
                'uid':order.name,
                'creation_date':order.create_date,
                'user_id':self.env.user.id,
                'fiscal_position_id':False, #optional
                'pricelist_id':order.pricelist_id.id, #optional
                'partner_id':order.partner_id.id,
                'lines':[], #orderline data generated below 
                'statement_ids':[], # leave blank
                'state':'ongoing',
                'amount_return':0, # leave at 0
                'account_move':0, # leaving at 0 for now
                'id':0, #backend id? leaving at 0 for now
                'is_session_closed':False,
            }
            for line in order.order_line:
                line_product_json = {
                    'qty':line.product_uom_qty,
                    'price_unit':line.price_unit,
                    'discount':0,
                    'product_id':line.product_id.id,
                    'description':line.name,
                    'price_extra':line.product_id.price_extra or 0,
                    'pack_lot_ids':[], #models.js line 1652
                }
                json_data['lines'].append([0,0,line_product_json])
            list_data.append(json_data)
        return list_data
