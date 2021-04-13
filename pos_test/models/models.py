# -*- coding: utf-8 -*-

from odoo import models, fields, api


class pos_test(models.Model):
    _inherit = 'sale.order'

    @api.model
    def get_all(self):
        return self.env['sale.order'].search([])
