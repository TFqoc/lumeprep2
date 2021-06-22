# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    import_category = fields.Boolean(related='metrc_account_id.import_category',
                                     readonly=False)

    def do_import_category(self):
        self.metrc_account_id.do_import_category()