# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def do_import_package_adjust_reasons(self):
        self.metrc_account_id.do_import_package_adjust_reasons()

    def do_import_transfer_types(self):
        self.metrc_account_id.do_import_transfer_types()
    
    def do_import_metrc_locations(self):
        self.metrc_account_id.do_import_metrc_locations()