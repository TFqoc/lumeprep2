from odoo import models, fields, api
import datetime
import json

def jsonify_records(records, fields=False):
    data = []
    valid_fields = records.fields_get()
    # Validate fields
    if fields:
        for field in fields:
            if field not in valid_fields.keys():
                return "{'error': 'Bad field name'}"
        if 'id' not in fields:
            fields.append('id')
    for r in records:
        filter_fields = fields or valid_fields
        record = {}
        for f in filter_fields:
            if f in valid_fields and valid_fields[f]['type'] in ['many2one','many2many','one2many']:
                record[f] = r[f].mapped('id')
            else:
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