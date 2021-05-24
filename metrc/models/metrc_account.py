# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MetrcAccount(models.Model):
    _inherit = ['metrc.account']

    import_licenses = fields.Boolean(string='Import Licenses', help='Import license for each facilities')
    import_labtest_types = fields.Boolean(string='Import Labtest Types', help='Import Labtest Types from Metrc')

    def do_import_labtest_types(self):
        self.ensure_one()
        self.env['metrc.labtest.type'].do_model_import(self)

    def do_import_licenses(self):
        # importing all available licenses based on facilities from metrc
        MetrcLicense = self.env['metrc.license']
        url = '{}/{}'.format('/facilities', self.api_version)
        facilities = self.fetch('GET', url)
        existing_license_ids = MetrcLicense.search([])
        for facility in facilities:
            if facility['License']['Number'] not in existing_license_ids.mapped('license_number'):
                license_data = facility['License']
                MetrcLicense.create({
                    'license_number': license_data['Number'],
                    'base_type': 'Internal',
                    'metrc_type': 'metrc',
                    'usage_type': False,
                    'metrc_account_id': self.id,
                    # 'company_id': self.env.user.company_id and self.env.user.company_id.id or False,
                    'issue_date': license_data['StartDate'],
                    'expire_date': license_data['EndDate'],
                    'sell_to_patients': facility['FacilityType']['CanSellToPatients'],
                })