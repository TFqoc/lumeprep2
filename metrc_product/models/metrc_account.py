# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MetrcAccount(models.Model):
    _inherit = 'metrc.account'

    def do_import_category(self):
        self.ensure_one()
        self.env['metrc.product.category'].do_model_import(self)