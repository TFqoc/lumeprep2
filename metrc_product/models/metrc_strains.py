# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MetrcStrains(models.Model):

    _name = 'metrc.strains'
    _description = 'Metrc Strains'
    _inherit = ['mail.thread', 'metrc.meta']
    _metrc_model_name = 'strains'

    def _valid_field_parameter(self, field, name):
        # allow tracking on abstract models; see also 'mail.thread'
        return (
            name in ('metrc_field', 'metrc_rec_name') or super()._valid_field_parameter(field, name)
        )

    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        tracking=True,
        metrc_field='Name',
        metrc_rec_name=True)
    active = fields.Boolean(string='Active', default=True)
    test_status = fields.Selection([
        ('InHouse', 'InHouse'),
        ('None', 'None'),
        ('ThirdParty', 'ThirdParty')], string='Testing Status', tracking=True,
                            metrc_field='TestingStatus')
    thc_level = fields.Float(
        string='THC Level',
        tracking=True,
        digits=(16, 5), metrc_field='ThcLevel')
    cbd_level = fields.Float(
        string='CBD Level',
        tracking=True,
        digits=(16, 5), metrc_field='CbdLevel')
    indica_per = fields.Float(
        string='Indica Percentage',
        tracking=True,
        digits=(16, 2), metrc_field='IndicaPercentage')
    sativa_per = fields.Float(
        string='Sativa Percentage',
        tracking=True,
        digits=(16, 2), metrc_field='SativaPercentage')
    genetics = fields.Char(string='Genetics', compute='_compute_genetics', store=True)
    notes = fields.Html(string='Notes')
    banner_message = fields.Html(compute="compute_banner_message")
    metrc_sync_status = fields.Selection(selection=[
                            ('synced', 'Fully Synced'),
                            ('not_synced', 'Not Synced'),
                            ('partial', 'Partially Synced')
                        ], default="not_synced", compute="compute_banner_message")

    def compute_banner_message(self):
        color_codes = {'synced': '#d4edda', 'not_synced': '#f8d7da', 'partial': '#fff3cd'}
        for strain in self:
            strain.banner_message = ""
            model_datas = strain.get_metrc_model_datas()
            if model_datas:
                if all([(md.metrc_id > 0) and (md.need_sync is False) for md in model_datas]):
                    status = 'synced'
                elif all([(md.metrc_id == 0) for md in model_datas]) or all([(md.metrc_id > 0) and (md.need_sync is True) for md in model_datas]):
                    status = 'not_synced'
                else:
                    status = 'partial'
                strain.metrc_sync_status = status
                license_sync_status = {license.id: False for license in self.get_internal_licenses()}
                for md in model_datas:
                    if md.metrc_id > 0 and md.need_sync is False:
                        license_sync_status[md.metrc_license_id.id] = 'Synced'
                    else:
                        license_sync_status[md.metrc_license_id.id] = 'Not Synced'
                sync_message = "<div style='background-color: {};'>".format(color_codes[status])
                sync_message += "<div style='font-size: 15px;'><b>&nbsp;&nbsp;&nbsp;Metrc sync status for this strain.</b><br/><ul>"
                for license in model_datas.mapped('metrc_license_id'):
                    sync_message += "<li><b>{}</b>: {}</li>".format(license.license_number, license_sync_status[license.id])
                sync_message += "</ul></div></div>"
                strain.banner_message = sync_message

    def _get_api_actions(self):
        actions = {
            'create': 'create',
            'write': 'update',
            'unlink': False,
            'read': 'active'
        }
        return self._metrc_model_name, actions

    @api.depends('indica_per', 'sativa_per')
    def _compute_genetics(self):
        for strain in self:
            strain.genetics = "{:3.2f}% Indica / {:3.2f}% Sativa ".format(strain.indica_per, strain.sativa_per)

    @api.model
    def create(self, vals):
        strain = super(MetrcStrains, self).create(vals)
        if not self.env.context.get('import_mode'):
            for license in self.get_internal_licenses():
                strain._match_with_metrc(license, raise_for_error=False)
        return strain

    def write(self, vals):
        result = super(MetrcStrains, self).write(vals)
        if not self.env.context.get('import_mode'):
            change_in_name = True if vals.get('name') else False
            for license in self.get_internal_licenses():
                for strain in self:
                    model_datas = self.get_metrc_model_datas()
                    if change_in_name and any(model_datas.mapped('is_used')):
                        used_strains = model_datas.filtered(lambda s: s.is_used)
                        raise UserError(_("Strain {} is already marked as used in Metrc license [{}]. Can not have its name changed.".format(strain.name, ','.join(used_strains.mapped('metrc_license_id.license_number')))))
                    strain._match_with_metrc(license, raise_for_error=False)
        return result

    def _match_with_metrc(self, license, update_metrc_meta=True, raise_for_error=True, automatic=True):
        metrc_model_name, actions = self._get_api_actions()
        skip_metrc = self.env['ir.config_parameter'].sudo().get_param('metrc.skip_transactions', default='False')
        metrc_account = self.env.user.ensure_metrc_account()
        if actions.get('read') and str(skip_metrc) == 'False':
            uri = '/{}/{}/{}'.format(metrc_model_name, metrc_account.api_version, actions['read'])
            params = {}
            if self._metrc_license_require and license:
                params = {'licenseNumber': license.license_number}
            records = metrc_account.fetch('GET', uri, params=params)
            for strain in self:
                metrc_fields = self._get_metrc_fields()
                metrc_field_names = {f: False for f in metrc_fields}
                for col_name, col_info in self.fields_get(metrc_fields).items():
                    metrc_field_name = getattr(self._fields.get(col_name), 'metrc_field')
                    metrc_field_names[col_name] = metrc_field_name
                model_data = strain.get_metrc_model_data(license=license)
                if model_data and model_data.metrc_id > 0:
                    records_filtered = [record for record in records if (record['Id'] == model_data.metrc_id)]
                else:
                    records_filtered = [record for record in records if strain['name'] == record['Name']]
                metrc_data = False
                if records_filtered:
                    metrc_data = records_filtered[0]
                if metrc_data:
                    ctx = {
                        'default_metrc_id': metrc_data['Id'],
                        'default_is_used': metrc_data['IsUsed'],
                        'default_metrc_license_id': license.id,
                        'default_metrc_account_id': metrc_account.id,
                        'need_sync': False,
                        'import_mode': True
                    }
                    # creating/updateing the metric model data befoe start processing.
                    strain.with_context(ctx)._track_metrc_model_data()
                    model_data = strain.get_metrc_model_data(license=license)
                    if not all([strain[f] == metrc_data[metrc_field_names[f]] for f in metrc_fields]):
                        strain._do_metrc_update(license, 'write', model_data, raise_for_error=raise_for_error)
                else:
                    model_data = strain.get_metrc_model_data(license=license)
                    strain._do_metrc_update(license, 'create', model_data, raise_for_error=raise_for_error)
                    if update_metrc_meta:
                        strain._update_metrc_id(metrc_account, license=license)

    @api.constrains('indica_per', 'sativa_per')
    def _check_indica_sativa(self):
        for strains in self:
            if (strains.indica_per + strains.sativa_per) != 100 and not self.env.context.get('default_metrc_id'):
                raise UserError(_('Combined Value of IndicaPercentage and SativaPercentage must be 100'))
