# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    import_package_adjust_reasons = fields.Boolean(related='metrc_account_id.import_package_adjust_reasons',
                                                   readonly=False)
    import_packages = fields.Boolean(related='metrc_account_id.import_packages',
                                     readonly=False)
    import_transfer_types = fields.Boolean(related='metrc_account_id.import_transfer_types', readonly=False)

    def do_import_package_adjust_reasons(self):
        self.metrc_account_id.do_import_package_adjust_reasons()

    def do_import_transfer_types(self):
        self.metrc_account_id.do_import_transfer_types()