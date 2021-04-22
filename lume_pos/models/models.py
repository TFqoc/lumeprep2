# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
import datetime as date
import logging
_logger = logging.getLogger(__name__)

class pos_test(models.Model):
    _inherit = 'sale.order'

    pos_update = fields.Boolean(help='Technical field to trigger an update on the pos system for this record')
    no_pos_update = fields.Boolean(help='Technical field to stop the pos_update field triggering')

    @api.model
    def get_orders(self, ids, session_id, user_id):
        config_id = self.env['pos.session'].browse(session_id).config_id
        # This filters includes anyone explicitly listed on the project, as we as anyone who has permission to see it (administrator rights on project app)
        orders = self.env['sale.order'].search([('id','not in', ids),('state','in',['sale']),('task.project_id.allowed_user_ids','=',user_id)])
        data = {}
        new_orders = {"unpaid_orders":self.jsonify_orders(orders, session_id)}

        data['new_orders'] = new_orders
        orders = self.env['sale.order'].search([('id','in', ids)])
        old_orders = []
        for order in orders:
            if order.state != 'sale':
                old_orders.append(order.id)

        data['old_orders'] = old_orders

        orders = orders.filtered(lambda x: x.pos_update == True)
        for order in orders:
            order.pos_update = False
        data['update_orders'] = {"unpaid_orders":self.jsonify_orders(orders, session_id)}
        return json.dumps(data, default=str)

    @api.model
    def remove_item(self, order_id, product_id):
        order = self.browse(order_id)
        order.no_pos_update = True
        for line in order.order_line:
            if line.product_id.id == product_id:
                line.unlink()
                break
        order.no_pos_update = False
    
    @api.model
    def add_item(self, order_id, product_id, quantity):
        vals = {
            # 'name':'description',
            'order_id':order_id,
            'product_uom_qty':quantity,
            'product_id': product_id,
        }
        order = self.browse(order_id)
        order.no_pos_update = True
        order.order_line = [(0,0,vals)]
        # TODO Do stuff to add to delivery
        order.no_pos_update = False

    @api.model
    def update_item_quantity(self, order_id, product_id, quantity):
        order = self.browse(order_id)
        order.no_pos_update = True
        for line in order.order_line:
            if line.product_id.id == product_id:
                line.product_uom_qty = quantity
                break
        order.no_pos_update = False

    @api.model
    def finalize(self, order_id):
        self.browse(order_id).state = 'done'

    @api.model
    def jsonify_orders(self, orders, session_id):
        list_data = []
        for order in orders:
            json_data = {
                'sale_order_id':order.id,
                'pos_session_id':session_id,
                'name':order.id,
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

    @api.onchange('partner_id','order_line','payment_term_id')
    def _on_change(self):
        if not self.no_pos_update and self.state == 'sale':
            self.pos_update = True

class SaleLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id','product_uom_qty')
    def _on_change(self):
        self.order_id._on_change()
