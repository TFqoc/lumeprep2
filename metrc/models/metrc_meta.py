# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

from odoo import api, fields, models, registry, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
_pp = pprint.PrettyPrinter(indent=4)


class MetrcMeta(models.AbstractModel):

    _name = 'metrc.meta'
    _description = 'Metrc Sync Meta'
    _metrc_model_name = False
    _metrc_license_require = True

    metrc_create_date = fields.Datetime(string='Metrc Created Date')
    metrc_write_date = fields.Datetime(string='Metrc Last Updated Date')


    def _get_api_actions(self):
        actions = {
            'create': False,
            'write': False,
            'unlink': False,
            'read': False
        }
        return self._metrc_model_name, actions

    def _get_matrc_field_for_create_write(self):
        # TODO : proper method name and could this be add as field attribute?
        """
            Use this method when metric request parameters are different for different action
            for example Items:
                - when we read item from the metrc system , Product category known as 'ProductCategoryName'
                - when we push item to metrc system, Product category known as 'ItemCategory'
                same for strains and other fields
            :return dict: a dict mapping metrc field read params with create/write
             i.e {'ProductCategoryName': ItemCategory}
        """
        return dict()

    @api.model
    def _get_metrc_fields(self, attribute='metrc_field', updated_fields=None):
        """
        Return a structure of metrc fields for the current model.
        @param attribute: field attribure to searhc on record
        :return list: a dict mapping field name to description, containing
                metrc_field
        """
        metrc_fields = []
        for name, field in self._fields.items():
            if getattr(field, attribute, False):
                metrc_fields.append(name)
        return metrc_fields

    def get_metrc_model_datas(self, license=False):
        domain = [('res_id', 'in', self.ids), ('model', '=', self._name)]
        if license:
            domain.append(('metrc_license_id', '=', license.id))
        return self.env['metrc.model.data'].search(domain)

    def get_metrc_model_data(self, license=False):
        self.ensure_one()
        domain = [('res_id', '=', self.id), ('model', '=', self._name)]
        if license:
            domain.append(('metrc_license_id', '=', license.id))
        return self.env['metrc.model.data'].search(domain, limit=1)

    @api.model
    def _track_metrc_model_data(self):
        MetrcModel = self.env['metrc.model.data'].with_context(tracking_disable=True)
        tracked_records = False
        for model_record in self:
            domain = [
                ('model', '=', self._name,),
                ('res_id', '=', model_record.id),
            ]
            if self._context.get('default_metrc_license_id'):
                domain.append(('metrc_license_id', '=', self._context.get('default_metrc_license_id')))
            tracked_records = MetrcModel.search(domain)
            need_sync = self._context.get('need_sync') if 'need_sync' in self._context else self._metrc_license_require
            if not tracked_records:
                for model_record in self:
                    vals = {
                        'name': model_record.name,
                        'model': model_record._name,
                        'res_id': model_record.id,
                        'need_sync': need_sync,
                        'metrc_account_id': self.env.context.get('default_metrc_account_id'),
                        'metrc_license_id': self.env.context.get('default_metrc_license_id'),
                        'metrc_id': self.env.context.get('default_metrc_id', 0),
                        'is_used': self.env.context.get('default_is_used', False),
                    }
                    if self.env.context.get('import_mode') and self.env.context.get('default_metrc_license_id'):
                        vals.update({'need_sync': False})
                        tracked_records = MetrcModel.create(vals)
                    else:
                        tracked_records = MetrcModel
                        for license in self.env['metrc.license'].search([('base_type', '=', 'Internal')]):
                            vals.update({
                                'metrc_license_id': license.id,
                                'metrc_account_id': license.metrc_account_id.id,
                            })
                            tracked_records |= MetrcModel.create(vals)
            else:
                vals = {'need_sync': need_sync}
                for fld in ['metrc_account_id', 'metrc_license_id', 'metrc_id', 'is_used']:
                    ctx_fld = 'default_'+fld
                    if ctx_fld in self._context:
                        vals.update({fld: self._context[ctx_fld]})
                if 'metrc_license_id' in vals:
                    tracked_records = tracked_records.filtered(lambda tr: tr.metrc_license_id.id == vals['metrc_license_id'])
                    if not tracked_records:
                        vals.update({
                            'name': model_record.name,
                            'model': model_record._name,
                            'res_id': model_record.id,
                            'need_sync': need_sync,
                        })
                        MetrcModel.create(vals)
                tracked_records.write(vals)
                tracked_records._compute_record_name()

        return tracked_records

    @api.model
    def create(self, values):
        if self._context.get('metrc_notrack'):
            return super(MetrcMeta, self).create(values)
        metrc_meta = super(MetrcMeta, self).create(values)
        if self._get_metrc_fields():
            metrc_meta._track_metrc_model_data()
        return metrc_meta

    def write(self, values):
        if self._context.get('metrc_notrack'):
            return super(MetrcMeta, self).write(values)
        metrc_fields = self._get_metrc_fields()
        if hasattr(self, '_metrc_toggle_field'):
            metrc_fields.append(self._metrc_toggle_field)
        result = super(MetrcMeta, self).write(values)
        if any([(field in metrc_fields) for field in values.keys()]):
            self._track_metrc_model_data()
        return result

    def unlink(self):
        """
            since there is no direct relationship between metric model data and basic model, we have to
            remove metrc model data when base data is going to remove
        """
        metrc_model_datas_to_remove = self.env['metrc.model.data'].search([('res_id', 'in', self.ids)])
        metrc_model_datas_to_remove.unlink()
        return super(MetrcMeta, self).unlink()

    @api.model
    def create_mapping_value(self, initial_value, col_info, read=False):
        value = False
        if col_info['type'] in ['boolean']:
            value = bool(initial_value)
        elif col_info['type'] in ['integer']:
            value = int(initial_value)
        elif col_info['type'] in ['integer', 'float', 'monetary']:
            value = float(initial_value)
        elif col_info['type'] in ['char', 'text', 'selection', 'date', 'datetime']:
            value = str(initial_value)
        # elif col_info['type'] == 'date':
        #     value = initial_value and datetime.strftime(datetime.combine(datetime.strptime(initial_value, tools.DEFAULT_SERVER_DATE_FORMAT), datetime.min.time()), tools.DEFAULT_SERVER_DATETIME_FORMAT) or False
        # elif col_info['type'] == 'datetime':
        #     value = initial_value and datetime.strftime(datetime.strptime(initial_value, tools.DEFAULT_SERVER_DATE_FORMAT), datetime.min.time()), tools.DEFAULT_SERVER_DATETIME_FORMAT) or False
        elif col_info['type'] == 'many2one':
            if read:
                value = initial_value and initial_value.sudo().name_get()[0][1] or False
            else:
                name_rec_ids = self.env[col_info['relation']].sudo().name_search(initial_value,  operator='=', limit=1)
                if name_rec_ids:
                    value = name_rec_ids[0][0]
        return value

    def _get_default_values(self):
        """
        Call this method to add model specific default values.
        Override this method in your inherited model object.
        """
        return dict()

    @api.model
    def _map_record(self, new_vals, mapped_fields, metrc_vals=True):
        """
        # generate clean dict of final values after parsing from original values
        """
        record_vals = {}
        for col_name, col_info in mapped_fields.items():
            field_name = col_name
            if metrc_vals:
                field_name = getattr(self._fields.get(col_name), 'metrc_field')
            if field_name and new_vals.get(field_name, False):
                initial_value = new_vals[field_name]
                parse_value = self.create_mapping_value(initial_value, col_info)
                record_vals[col_name if metrc_vals else field_name] = parse_value
        return record_vals

    @api.model
    def _map_update_record(self):
        record_vals = {}
        metrc_fields = self._get_metrc_fields()
        for col_name, col_info in self.fields_get(metrc_fields).items():
            metrc_fields_name = getattr(self._fields.get(col_name), 'metrc_field')
            if metrc_fields_name:
                initial_value = self[col_name]
                record_vals[metrc_fields_name] = self.create_mapping_value(initial_value, col_info, read=True) or None
                if col_name == 'name':
                    record_vals[metrc_fields_name] = self.name_get()[0][1]
        # update metrc fields name
        for key, val in self._get_matrc_field_for_create_write().items():
            record_vals[val] = record_vals.pop(key)
        return record_vals

    @api.model
    def get_internal_licenses(self):
        return self.env['metrc.license'].search([('base_type', '=', 'Internal')])

    def _do_metrc_force_update(self):
        license = self.env.context.get('metrc_license', False)
        domain = [('model', '=', self._name), ('res_id', '=', self.id), ('need_sync', '=', True)]
        if license:
            domain.append(('metrc_license_id', '=', license))
        else:
            domain.append(('metrc_license_id', '!=', False))
        model_datas = self.env['metrc.model.data'].search(domain)
        if model_datas:
            for model_data in model_datas:
                self._do_metrc_update(model_data.metrc_license_id, 'write', model_data, raise_for_error=False)
                model_data.write({'need_sync': False})

    def _update_metrc_id(self, account, license):
        metrc_model_name, actions = self._get_api_actions()
        if actions.get('read'):
            uri = '/{}/{}/{}'.format(metrc_model_name, account.api_version, actions['read'])
            params = {}
            if self._metrc_license_require and license:
                params = {'licenseNumber': license.license_number}
            metrc_records = account.fetch('GET', uri, params=params)
            field = 'name'
            if self._name == 'product.product':
                field = 'metrc_name'
            for record in self:
                metrc_record = [r for r in metrc_records if record[field] == r['Name']]
                if metrc_record:
                    model_data = record.get_metrc_model_data(license=license)
                    model_data.write({
                        'metrc_id': metrc_record[0].get('Id', False),
                        'is_used': metrc_record[0].get('IsUsed', False),
                        'metrc_account_id': account.id,
                        'metrc_license_id': license.id,
                        'need_sync': False
                        })

    def _do_metrc_update(self, license, action, model_datas, raise_for_error=True):
        metrc_model_name, actions = self._get_api_actions()
        metrc_account = self.env.user.ensure_metrc_account()
        if actions.get(action):
            records = []
            if action == 'create':
                for meta_record in self:
                    records.append(meta_record._map_update_record())
            elif action == 'write':
                for meta_record in self:
                    record = meta_record._map_update_record()
                    metrc_id = model_datas.filtered(lambda md: md.res_id == meta_record.id and md.metrc_id).metrc_id
                    record.update(Id=metrc_id)
                    records.append(record)
            params = {'licenseNumber': license.license_number}
            uri = '/{}/{}/{}'.format(metrc_model_name, metrc_account.api_version, actions[action])
            metrc_account.fetch('POST', uri, params=params, data=records, raise_for_error=raise_for_error)
        return True

    def do_model_import(self, metrc_account=False):
        """
        Do Implment this method for all metrc.meta childs who needs one time import,
        cron import does no require license so any model that requires license will
        be rejected (skipped) by the cron.
        """
        if self._metrc_license_require or not metrc_account:
            return True
        self._cron_do_model_import(metrc_account, automatic=True, raise_for_error=False)
        return True

    def _cron_do_model_import(self, metrc_account, metrc_notrack=False, license=False, automatic=True, raise_for_error=True):
        """
        Strict cron for one time importing only, it does do sync and anything
        that requries license will be ignored by this object
        """
        if not metrc_account:
            return True
        accounts = metrc_account
        if isinstance(metrc_account, int):
            accounts = self.env['metrc.account'].browse(metrc_account)
        elif isinstance(metrc_account, (list, tuple)):
            accounts = self.env['metrc.account'].browse(metrc_account)
        if automatic:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        MetrcModelData = self.env['metrc.model.data']
        # Get current model and metrc action map
        metrc_model_name, actions = self._get_api_actions()
        # get fielld and search fields
        metrc_fields = self._get_metrc_fields()
        metrc_fields_details = self.fields_get(metrc_fields)
        metrc_search_field = self._get_metrc_fields('metrc_rec_name')
        for account in accounts:
            account = account[0]
            if actions.get('read'):
                uri = '/{}/{}/{}'.format(metrc_model_name, account.api_version, actions['read'])
                params = {}
                if self._metrc_license_require and license:
                    params = {'licenseNumber': license.license_number}
                records = account.fetch('GET', uri, params=params, raise_for_error=raise_for_error)
                # filtering specific product records to be processed.
                if self._name in ['product.product', 'metrc.strains'] and self.env.context.get('specific_name'):
                    records = [record for record in records if self.env.context['specific_name'] == record['Name']]
                _logger.info('queried {} record of {} from {}'.format(len(records), self._name, uri))
                for record in records:
                    try:
                        new_field_vals = self._map_record(record, metrc_fields_details)
                        if record.get("Id"):
                            model_data_domain = [
                                            ('metrc_id', '=', record['Id']),
                                            ('model', '=', self._name),
                                            ('metrc_account_id', '=', account.id),
                                        ]
                            if license:
                                model_data_domain.append(('metrc_license_id', '=', license.id))
                            search_record_ids = MetrcModelData.search(model_data_domain).mapped('res_id')

                            if not search_record_ids:
                                if self._name == 'product.product':
                                    domain = [(msf, '=', new_field_vals[msf]) for msf in metrc_search_field if msf != 'name']
                                else:
                                    domain = [(msf, '=', new_field_vals[msf]) for msf in metrc_search_field]
                                search_records = self.search(domain)
                            else:
                                search_records = self.browse(search_record_ids)
                        else:
                            if self._name == 'product.product':
                                domain = [(msf, '=', new_field_vals[msf]) for msf in metrc_search_field if msf != 'name']
                            else:
                                domain = [(msf, '=', new_field_vals[msf]) for msf in metrc_search_field]
                            search_records = self.search(domain)
                        metrc_ctx = {
                            'metrc_notrack': metrc_notrack,
                            'need_sync': False,
                            'import_mode': True,
                            'default_metrc_account_id': account.id,
                            'default_metrc_id': record.get("Id"),
                            'default_metrc_license_id': license.id if license else False,
                        }
                        print(new_field_vals)
                        if search_records:
                            if self._name == "product.product":
                                search_records.with_context(metrc_ctx)._track_metrc_model_data()
                                if new_field_vals.get('item_cat_id') and self._name == 'product.product':
                                    new_field_vals.update({'metrc_item_cat_id': new_field_vals['item_cat_id']})
                            for search_record in search_records:
                                search_record.with_context(metrc_ctx).write(new_field_vals)
                        else:
                            # if self._name != 'product.product':
                            default_vals = self._get_default_values()
                            if new_field_vals.get('item_cat_id') and self._name == 'product.product':
                                new_field_vals.update({'metrc_item_cat_id': new_field_vals['item_cat_id']})
                            new_field_vals.update(default_vals)
                            self.with_context(metrc_ctx).create(new_field_vals)
                        if automatic:
                            cr.commit()
                    except Exception:
                        if automatic:
                            cr.rollback()
                        account.log_exception(func='_cron_do_model_import')
        if automatic:
            cr.commit()
            cr.close()
        return True
