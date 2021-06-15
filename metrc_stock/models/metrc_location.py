# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MetrcLocationType(models.Model):
    _name = 'metrc.location.type'
    _inherit = 'metrc.meta'
    _metrc_model_name = 'locations'
    _metrc_rec_name = 'name'
    _metrc_license_require = True

    def _valid_field_parameter(self, field, name):
        # allow tracking on abstract models; see also 'mail.thread'
        return (
            name in ('metrc_field', 'metrc_rec_name') or super()._valid_field_parameter(field, name)
        )

    def _get_api_actions(self):
        actions = {
            'read': 'types'
        }
        return self._metrc_model_name, actions
    
    name = fields.Char(string="Location Type Name", metrc_field="Name")
    plants = fields.Boolean(string='For Plants', metrc_field='ForPlants')
    plant_batches = fields.Boolean(string='For Plant Batches', metrc_field="ForPlantBatches")
    harvests = fields.Boolean(string='For Harvests', metrc_field='ForHarvests')
    packages = fields.Boolean(string='For Packages', metrc_field='ForPackages')


class MetrcLocation(models.Model):
    _name = 'metrc.location'
    _inherit = 'metrc.meta'
    _metrc_model_name = 'locations'
    _metrc_rec_name = 'name'
    _metrc_license_require = True

    def _get_api_actions(self):
        actions = {
            'create': 'create',
            'write': 'update',
            'unlink': False,
            'read': 'active'
        }
        return self._metrc_model_name, actions
    
    def _valid_field_parameter(self, field, name):
        return (
            name in ('metrc_field', 'metrc_rec_name') or super()._valid_field_parameter(field, name)
        )
    
    def _get_default_values(self):
        return {
            'facility_license_id': self.env.context.get('default_metrc_license_id')
        }

    name = fields.Char('Location Name', required=True, metrc_field='Name', metrc_rec_name=True)
    location_type_id = fields.Many2one(string='Location Type', comodel_name='metrc.location.type', 
                                       metrc_field='LocationTypeName')
    facility_license_id = fields.Many2one(string='Facility License', comodel_name='metrc.license', 
                                          required=True)
    plants = fields.Boolean(related='location_type_id.plants', readonly=True)
    plant_batches = fields.Boolean(related='location_type_id.plant_batches', readonly=True)
    harvests = fields.Boolean(related='location_type_id.harvests', readonly=True)
    packages = fields.Boolean(related='location_type_id.packages', readonly=True)

    @api.model
    def create(self, vals):
        self = self.with_context(default_metrc_license_id=vals.get('facility_license_id'))
        location = super(MetrcLocation, self).create(vals)
        if not self.env.context.get('import_mode'):
            location._match_with_metrc(location.facility_license_id, raise_for_error=False)
        return location

    def write(self, vals):
        result = super(MetrcLocation, self).write(vals)
        if not self.env.context.get('import_mode'):
            change_in_name = True if vals.get('name') else False
            for location in self:
                model_datas = self.get_metrc_model_datas()
                if change_in_name and any(model_datas.mapped('is_used')):
                    used_location = model_datas.filtered(lambda s: s.is_used)
                    licenses = ','.join(used_location.mapped('metrc_license_id.license_number'))
                    raise UserError(_("Location {} is already marked as used in Metrc license [{}]. "
                                        "Can not have its name changed.".format(location.name, licenses)))
                location._match_with_metrc(location.facility_license_id, raise_for_error=False)
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
            metrc_fields = self._get_metrc_fields()
            metrc_field_names = {f: False for f in metrc_fields}
            metrc_field_details = {}
            for col_name, col_info in self.fields_get(metrc_fields).items():
                metrc_field_name = getattr(self._fields.get(col_name), 'metrc_field')
                metrc_field_names[col_name] = metrc_field_name
                metrc_field_details[col_name] = col_info
            for location in self:
                model_data = location.get_metrc_model_data(license=license)    
                if model_data and model_data.metrc_id > 0:
                    records_filtered = [record for record in records if (record['Id'] == model_data.metrc_id)]
                else:
                    records_filtered = [record for record in records if location['name'] == record['Name']]
                metrc_data = False
                if records_filtered:
                    metrc_data = records_filtered[0]
                if metrc_data:
                    ctx = {
                        'default_metrc_id': metrc_data['Id'],
                        'default_is_used': metrc_data.get('IsUsed', False),
                        'default_metrc_license_id': license.id,
                        'default_metrc_account_id': metrc_account.id,
                        'need_sync': False,
                        'import_mode': True
                    }
                    # creating/updateing the metric model data before start processing.
                    location.with_context(ctx)._track_metrc_model_data()
                    model_data = location.get_metrc_model_data(license=license)
                    mapped_values = {}
                    for col_name, col_data in metrc_field_details.items():
                        mapped_values[col_name] = self.create_mapping_value(metrc_data[metrc_field_names[col_name]], col_data)
                    if not all([location[f] == mapped_values[f] for f in metrc_fields]):
                        location._do_metrc_update(license, 'write', model_data, raise_for_error=raise_for_error)
                else:
                    model_data = location.get_metrc_model_data(license=license)
                    location._do_metrc_update(license, 'create', model_data, raise_for_error=raise_for_error)
                    if update_metrc_meta:
                        location._update_metrc_id(metrc_account, license=license)


