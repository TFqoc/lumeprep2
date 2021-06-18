# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _default_metrc_account(self):
        return self.env['metrc.account'].search([], limit=1, order="id asc")

    # API paramaters
    software_api_key = fields.Char(string='Vendor API Key', config_parameter='metrc.VENDOR_API_KEY')
    metrc_api_version = fields.Selection(selection=[('v1', 'v1')], string='API Version',
                                         config_parameter='metrc.METRC_API_VERSION', default='v1')
    metrc_api_region = fields.Selection(selection=[('CA', 'CA'), ('MI', 'MI')], string='API Region',
                                         config_parameter='metrc.METRC_API_REGION', default='CA')
    metrc_account_id = fields.Many2one(comodel_name='metrc.account', string='Service Account',
                                       default=_default_metrc_account, config_parameter='metrc.default_metrc_account_id')
    account_name = fields.Char(related='metrc_account_id.name', readonly=False)
    prod_environment = fields.Boolean(related='metrc_account_id.prod_environment',
                                      readonly=False)
    debug_logging = fields.Boolean(related='metrc_account_id.debug_logging',
                                   readonly=False)
    related_user = fields.Reference(related='metrc_account_id.related_user')

    def action_metrc_account_create_new(self):
        return {
            'view_mode': 'form',
            'view_id': self.env.ref('metrc.view_metrc_account_form_simple').id,
            'res_model': 'metrc.account',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': False,
        }

    def do_import_labtest_types(self):
        self.metrc_account_id.do_import_labtest_types()

    def do_import_licenses(self):
        self.metrc_account_id.do_import_licenses()
