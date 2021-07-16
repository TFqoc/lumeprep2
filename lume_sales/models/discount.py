# -*- coding: utf-8 -*-

from logging import disable
from odoo import models, fields, api

class Discount(models.Model):
    _name = 'lume.discount'

    color = fields.Integer(string='Color Index', default=7) # Values are from 1-11
    amount = fields.Float(required=True,digits='Product Price')
    discount_type = fields.Selection([('percentage','Percent'),('fixed_amount','Flat Discount')],required=True)
    # line_ids = fields.Many2many('sale.order.line', column1='discount_id',column2='line_id')

    # Override
    def name_get(self):
        res = []
        for record in self:
            name = ""
            if record.discount_type == 'fixed_amount': 
                name = "$%s off" % (record.amount)
            else:
                name="%s%% off" % (record.amount)
            res.append((record.id, name))
        return res