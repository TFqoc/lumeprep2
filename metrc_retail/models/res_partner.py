# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _default_customer_type(self):
        c_types = self.env['metrc.customer.types'].search([])
        return c_types and c_types[0].name or ''

    @api.model
    def _get_customer_types(self):
        return [(type.name, type.name) for type in self.env['metrc.customer.types'].search([])]

    customer_type = fields.Selection(selection='_get_customer_types', default=_default_customer_type)