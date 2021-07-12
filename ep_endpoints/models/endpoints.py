from odoo import models, fields, api
import datetime
import json

def jsonify_records(records, fields=False):
    data = []
    # Validate fields
    if fields:
        try:
            for field in fields:
                records[field]
        except:
            return "{'error': 'Bad field name'}"
        if 'id' not in fields:
            fields.append('id')
    for r in records:
        filter_fields = fields or records.fields_get()
        record = {}
        for f in filter_fields:
            record[f] = r[f]
        data.append(record)
    return json.dumps(data)


class Product(models.Model):
    _inherit = 'product.product'
    
    @api.model
    def ep_hourly_products(self, fields=False):
        hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
        data = self.env['product.product'].search([('__last_update','>',hour_ago)])
        return jsonify_records(data, fields)

    @api.model
    def ep_nightly_products(self, fields=False):
        data = self.env['product.product'].search([('active','=',True)])
        extra_data = self.env['product.product'].search([('active','=',False)])
        lots = self.env['stock.lot'].search([]).product_id
        extra_data = extra_data.filtered(lambda x: x in lots)
        data |= extra_data
        return jsonify_records(data, fields)


class Lots(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def stock_lookup(self, **kwargs):
        store = self.env['project.project'].browse(kwargs['store_id'])
        product_id = self.env['project.project']
        pass