# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime

from odoo import api, fields, models, _

class MetrcAccount(models.Model):
    _inherit = 'metrc.account'

    import_package_adjust_reasons = fields.Boolean(string='Import Package Adjust Reasons')
    import_packages = fields.Boolean(string='Import Packages', help='Import active packages from Metrc.')
    import_transfer_types = fields.Boolean(string='Import Transfer Types', help='Import Transfer Types from metrc.')

    def do_import_transfer_types(self):
        self.ensure_one()
        MetrcTransferType = self.env['metrc.transfer.type']
        licenses = self.env['metrc.license'].search([('base_type', '=', 'Internal'), ('metrc_account_id', '=', self.id)])
        for license in licenses:
            MetrcTransferType._cron_do_model_import(self, metrc_notrack=False, license=license)

    def do_import_package_adjust_reasons(self):
        licenses = self.env['metrc.license'].search([('base_type', '=', 'Internal')])
        PackageAdjustReason = self.env['metrc.package.adjust.reason']
        existing_reasons = PackageAdjustReason.search([])
        for license in licenses:
            url = '{}/{}/{}'.format('/packages', self.api_version, 'adjust/reasons')
            params = {
                'licenseNumber': license.license_number
            }
            resp = self.fetch('GET', url, params=params)
            license_reasons = existing_reasons.filtered(lambda r: r.license_id == license)
            for reason in resp:
                if reason['Name'] not in license_reasons.mapped('name'):
                    PackageAdjustReason.create({
                        'name': reason['Name'],
                        'note_required': reason['RequiresNote'],
                        'license_id': license.id
                        })

    def do_import_packages(self):
        self.env['stock.production.lot']._cron_do_import_packages(force_last_sync_date=datetime.datetime.utcnow()-datetime.timedelta(days=30))