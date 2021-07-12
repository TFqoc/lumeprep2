from odoo import models, fields, api
import datetime

class Product(models.Model):
    _inherit = 'product.product'
    
    @api.model
    def ep_hourly_products(self, fields=False):
        hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
        data = self.env['product.product'].search([('__last_update','>',hour_ago)])
        if fields:
            l = []
            try:
                for field in fields:
                    l.append(data[field])
                return l
            except:
                return "{'error': 'Bad field name'}"
        return data

    @api.model
    def ep_nightly_products(self):
        data = self.env['product.product'].search([('active','=',True)])
        extra_data = self.env['product.product'].search([('active','=',False)])
        lots = self.env['stock.lot'].search([]).product_id
        extra_data = extra_data.filtered(lambda x: x in lots)
        data |= extra_data
        return data


class Lots(models.Model):
    _inherit = 'stock.lot'

    @api.model
    def stock_lookup(self, **kwargs):
        store = self.env['project.project'].browse(kwargs['store_id'])
        product_id = self.env['project.project']
        pass