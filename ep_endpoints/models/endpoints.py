from odoo import models, fields, api
import datetime
import json
import logging

_logger = logging.getLogger(__name__)

# def jsonify_records(records, fields=False):
#     data = []
#     valid_fields = records.fields_get()
#     # Validate fields
#     if fields:
#         for field in fields:
#             if field not in valid_fields.keys():
#                 return "{'error': 'Bad field name'}"
#         if 'id' not in fields:
#             fields.append('id')
#     for r in records:
#         filter_fields = fields or valid_fields
#         record = {}
#         for f in filter_fields:
#             if f in valid_fields:
#                 if valid_fields[f]['type'] in ['many2one','many2many','one2many']:
#                     record[f] = r[f].mapped('id')
#                 elif valid_fields[f]['type'] in ['datetime','date']:
#                     # Handle a false value if date is blank
#                     if r[f]:
#                         record[f] = r[f].isoformat()
#                     else:
#                         record[f] = False
#             else:
#                 record[f] = r[f]
#         data.append(record)
#     return json.dumps(data)


class Product(models.Model):
    _inherit = 'product.product'
    
    @api.model
    def ep_hourly_products(self, fields=None):
        hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
        data = self.env['product.product'].search([('__last_update','>',hour_ago)])
        # return jsonify_records(data, fields)
        return data.read(fields)

    @api.model
    def ep_nightly_products(self, fields=None):
        data = self.env['product.product'].search([('active','=',True)])
        extra_data = self.env['product.product'].search([('active','=',False)])
        lots = self.env['stock.lot'].search([]).product_id
        extra_data = extra_data.filtered(lambda x: x in lots)
        data |= extra_data
        # return jsonify_records(data, fields)
        return data.read(fields)


class Lots(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def stock_lookup(self, **kwargs):
        store = self.env['project.project'].browse(kwargs['store_id'])
        product_id = self.env['project.project']
        pass

class Store(models.Model):
    _inherit = 'project.project'

    # Params: data = json string
    @api.model
    def ecom_order(self, data):
        _logger.info("Self: %s, Data: %s", (self, data))
        # Create task
        # Activate build cart
        # Add so lines
        # Apply promos
        # Confirm SO
        # Return cart total (JSON format?)
        data = json.loads(data)
        # JSON Data format
        # {
        #     "store_id":0,
        #     "customer_id":0,
        #     "fulfillment_type":'',
        #     "order_lines":{
        #         "product_id":0,
        #         "product_uom_qty":0,
        #     }
        # }
        customer = self.env['res.partner'].browse(data['customer_id'])
        task = self.env['project.task'].create({
            'partner_id': customer.id,
            'project_id': data['store_id'],
            'fulfillment_type': data['fulfillment_type'],
            'user_id': False,
            'name': customer.pref_name or customer.name,
        })
        task.build_cart()
        
        line_data = data['order_lines']
        ids = []
        for line in line_data:
            line.update({'order_id': task.sales_order.id})
            ids.append((0,0,line))

        task.sales_order.order_line = ids

        # TODO Apply promos here

        # Confirm sale order to generate demand
        task.sales_order.action_confirm()

        # Return total for ecom's benefit
        return {"order_total":task.sales_order.amount_total}