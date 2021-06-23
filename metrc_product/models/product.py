# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import traceback

from odoo import api, models, fields, registry, _
from odoo.tools import float_round, float_is_zero
from odoo.tools.misc import split_every
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _valid_field_parameter(self, field, name):
        # allow tracking on abstract models; see also 'mail.thread'
        return (
            name in ('metrc_field', 'metrc_rec_name') or super()._valid_field_parameter(field, name)
        )

    name = fields.Char(
        metrc_field='Name')
    is_metric_product = fields.Boolean(string="METRC Product?", compute="compute_is_metric_product", store=True)
    metrc_item_cat_id = fields.Many2one(
        'metrc.product.category',
        string='Metrc Item Category',
        tracking=True)
    uom_id = fields.Many2one(metrc_field='UnitOfMeasureName', metrc_rec_name=True)
    uom_po_id = fields.Many2one(metrc_field='UnitOfMeasureName')
    banner_message = fields.Html(compute="compute_banner_message")
    req_metrc_fields = fields.Char(compute="compute_banner_message")
    metrc_sync_status = fields.Selection(selection=[
                            ('synced', 'Fully Synced'),
                            ('not_synced', 'Not Synced'),
                            ('partial', 'Partially Synced')
                        ], default="not_synced", compute="compute_banner_message")
    diff_metrc_uom = fields.Boolean(related='metrc_item_cat_id.diff_metrc_uom', store=True, string='Requires Different Metrc UoM')
    metrc_uom_id = fields.Many2one(comodel_name='uom.uom', string='Metrc Unit Of Measure', tracking=True)

    # @api.constrains('diff_metrc_uom', 'metrc_uom_id')
    # def _check_metrc_uom_id(self):
    #     for pt in self:
    #         if pt.diff_metrc_uom and not pt.metrc_uom_id:
    #             raise ValidationError(_('Product Metrc category "%s" required different Unit Of Measure.\n\
    #                                     Please configure Metrc Unit of Measure')%(pt.metrc_item_cat_id.name))

    def compute_banner_message(self):
        cat_product_fields = {
            'cbdpercent': ['unit_cbd_percent'],
            'cbdcontent': ['unit_cbd_content', 'unit_cbd_content_uom'],
            'thcpercent': ['unit_thc_percent'],
            'thccontent': ['unit_thc_content', 'unit_thc_content_uom'],
            'servingsize': ['serving_size'],
            'supplydurationdays': ['supply_duration_days'],
            'ingredients': ['ingredients'],
            'strain': ['strain_id'],
            'unitweight': ['metrc_weight', 'unit_weight_uom'],
            'unitvolume': ['metrc_volume', 'unit_volume_uom']
        }
        cat_fields = cat_product_fields.keys()
        cat_model_fields = {field_name: False for field_name in cat_fields}
        for col_name, col_info in self.env['metrc.product.category'].fields_get(cat_fields).items():
            cat_model_fields[col_name] = col_info['string'][8:]
        color_codes = {'synced': '#d4edda', 'not_synced': '#f8d7da', 'partial': '#fff3cd'}
        for product in self:
            banner_message = ""
            if product.metrc_item_cat_id:
                if product.metrc_item_cat_id.diff_metrc_uom:
                    cat_product_fields.update({
                        'diff_metrc_uom': [product.metrc_item_cat_id.coeff_field_id.name]
                        })
                    if product.metrc_item_cat_id.coeff_related_fields_ids:
                        cat_product_fields['diff_metrc_uom'] += product.metrc_item_cat_id.coeff_related_fields_ids.mapped('name')
                    cat_fields = cat_product_fields.keys()
                pv_status = product.product_variant_ids.mapped('sync_status')
                if all([s == 'synced' for s in pv_status]):
                    status = 'synced'
                elif all([s == 'not_synced' for s in pv_status]):
                    status = 'not_synced'
                else:
                    status = 'partial'
                product.metrc_sync_status = status
                banner_message += "<div style='background-color: {};'>".format(color_codes[status])
                sync_message = "<div style='font-size: 15px;'><b>&nbsp;&nbsp;&nbsp;Metrc sync status for variant(s) of this product template.</b><br/><ul>"
                for pv in product.product_variant_ids:
                    sync_message += pv.sync_message
                sync_message += "</ul></div>"
                banner_message += sync_message
                product.req_metrc_fields = ''
                if any([product.metrc_item_cat_id[f] for f in cat_fields]):
                    fields_required = []
                    for field_name in cat_fields:
                        if product.metrc_item_cat_id[field_name]:
                            fields_required.append(field_name)
                    varians_set = []
                    variants_dict = {pv: [] for pv in product.product_variant_ids}
                    variant_field_names = {}
                    for pv in product.product_variant_ids:
                        fields_not_set = []
                        for required_field in fields_required:
                            for col_name, col_info in pv.fields_get(cat_product_fields[required_field]).items():
                                if not pv.has_value(col_name, col_info):
                                    fields_not_set.append(col_name)
                                    variant_field_names.update({col_name: col_info['string']})
                        if fields_not_set:
                            varians_set.append(False)
                            variants_dict[pv] = fields_not_set
                        else:
                            varians_set.append(True)
                    req_metrc_fields = []
                    for req_field in fields_required:
                        for prod_field in cat_product_fields[req_field]:
                            req_metrc_fields.append(prod_field)
                    product.req_metrc_fields = req_metrc_fields and ','.join(req_metrc_fields) or ''
                    if not all(varians_set):
                        fields_msg = "<div style='font-size: 15px;'><b>&nbsp;&nbsp;&nbsp;In order to sync this item to METRC please configre the following fields on corrosponding product variant(s).</b><br/><ul>"
                        for pv, fields_unset in variants_dict.items():
                            if fields_unset:
                                fields_msg += "<li><b>{}</b>: {}</li>".format(pv.metrc_name, ','.join([variant_field_names[f] for f in fields_unset]))
                        fields_msg += "</ul></div></div>"
                        banner_message += fields_msg
            else:
                product.metrc_sync_status = 'not_synced'
                product.req_metrc_fields = ''
            product.banner_message = banner_message

    def configre_metrc_fields(self):
        self.ensure_one()
        act_window = self.env.ref('metrc_product.action_open_product_metrc_properties').read()[0]
        act_window['context'] = {field: True for field in self.req_metrc_fields.split(',')}
        act_window['domain'] = [('id', 'in', self.product_variant_ids.ids)]
        return act_window

    @api.onchange('is_metric_product')
    def onchange_is_metric_product(self):
        if self.is_metric_product:
            self.tracking = 'lot'
            self.type = 'product'

    @api.depends('metrc_item_cat_id')
    def compute_is_metric_product(self):
        for product in self:
            product.is_metric_product = True if product.metrc_item_cat_id else False

    def sync_with_metrc(self):
        self.ensure_one()
        metrc_errors = ""
        for product in self.product_variant_ids.filtered(lambda p: p.sync_status in ['not_synced', 'partial']):
            model_datas = product.get_metrc_model_datas()
            for model_data in model_datas:
                product._update_dependant_objects(license=model_data.metrc_license_id, raise_for_error=False)
                error = product._match_with_metrc(license=model_data.metrc_license_id, raise_for_error=False)
                if error:
                    error = error.replace("odoo.exceptions.UserError:", "")
                    error = error.replace('\\n\\n', '\n')
                    error = error.replace('\\r\\n', ' ')
                    metrc_errors += '\n{}:\n'.format(product.metrc_name) + error
        if metrc_errors:
            raise UserError(_(metrc_errors))

    @api.model
    def create(self, vals):
        product = super(ProductTemplate, self).create(vals)
        if product.is_metric_product:
            product.product_variant_ids.with_context({'need_sync': False})._track_metrc_model_data()
        return product

    def unlink(self):
        for product in self.mapped('product_variant_ids'):
            if product.is_metric_product:
                model_datas = product.get_metrc_model_datas()
                model_datas.unlink()
        return super(ProductTemplate, self).unlink()

    def write(self, vals):
        if self.banner_message:
            self = self.with_context(from_product_tmpl=True)
        res = super(ProductTemplate, self).write(vals)
        update_trigger_fields = ['name', 'metrc_item_cat_id', 'attribute_line_ids', 'default_code']
        if self.metrc_item_cat_id and self.metrc_item_cat_id.diff_metrc_uom:
            update_trigger_fields.append('metrc_uom_id')
        else:
            update_trigger_fields += ['uom_id', 'uom_po_id']
        if vals.get('uom_id') and vals['uom_id'] == self.uom_id.id:
            vals.pop('uom_id')
        if any([f in vals.keys() for f in update_trigger_fields]) and \
                self.metrc_item_cat_id and not self.uom_id == self.metrc_uom_id:
            multi_value_attribute_lines = self.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1)
            if multi_value_attribute_lines and (len(multi_value_attribute_lines) == 1) and vals.get('attribute_line_ids'):
                # do not update metrc if there is only one attribute line is creating variant on product template.
                # in this case only new products get created. name not going to be changed.
                return res
            for pv in self.mapped('product_variant_ids'):
                model_datas = pv.get_metrc_model_datas()
                if any([md.is_used for md in model_datas]):
                    used_licenses = ','.join([md.metrc_license_id.license_number for md in model_datas if md.is_used])
                    raise UserError(_("Product {} is already used in metrc for license(s) [{}]. You can not update its name/uom/category.".format(pv.metrc_name, used_licenses)))
            self.product_variant_ids._track_metrc_model_data()
        return res


class ProductProduct(models.Model):
    _name = 'product.product'
    _description = "Product"
    _inherits = {'product.template': 'product_tmpl_id'}
    _inherit = ['product.product', 'metrc.meta', 'mail.thread', 'mail.activity.mixin']
    _order = 'default_code, name, id'

    # METRC Properties
    _metrc_model_name = 'items'
    _metrc_license_require = True
    _metrc_toggle_field = 'is_metric_product'

    def _valid_field_parameter(self, field, name):
        # allow tracking on abstract models; see also 'mail.thread'
        return (
            name in ('metrc_field', 'metrc_rec_name') or super()._valid_field_parameter(field, name)
        )

    def _get_api_actions(self):
        return self._metrc_model_name, {
            'create': 'create',
            'write': 'update',
            'read': 'active',
        }

    def _get_matrc_field_for_create_write(self):
        return {
            'StrainName': 'Strain',
            'ProductCategoryName': 'ItemCategory',
            'UnitCbdContentUnitOfMeasureName': 'UnitCbdContentUnitOfMeasure',
            'UnitThcContentUnitOfMeasureName': 'UnitThcContentUnitOfMeasure',
            'UnitVolumeUnitOfMeasureName': 'UnitVolumeUnitOfMeasure',
            'UnitWeightUnitOfMeasureName': 'UnitWeightUnitOfMeasure',
            'UnitOfMeasureName': 'UnitOfMeasure'
        }

    metrc_name = fields.Char(compute="_compute_metrc_name", store=True, metrc_field='Name', metrc_rec_name=True)
    strain_id = fields.Many2one(
        'metrc.strains',
        string='Strain',
        tracking=True,
        metrc_field='StrainName', metrc_rec_name=True)
    item_cat_id = fields.Many2one(
        related="product_tmpl_id.metrc_item_cat_id",
        string='Metric Item Category',
        tracking=True,
        metrc_field='ProductCategoryName', metrc_rec_name=True)
    item_brand = fields.Char(
        string='Item Brand',
        metrc_field='ItemBrand')
    administration_method = fields.Char(
        string='Administration Method',
        metrc_field='AdministrationMethod')
    unit_cbd_percent = fields.Float(
        string='Unit Cbd Percent',
        metrc_field='UnitCbdPercent')
    unit_cbd_content = fields.Float(
        string='Unit Cbd Content',
        metrc_field='UnitCbdContent')
    unit_cbd_content_uom = fields.Many2one(
        'uom.uom',
        string='Unit Cbd Content Unit Of Measure',
        metrc_field='UnitCbdContentUnitOfMeasureName')
    unit_thc_percent = fields.Float(
        string='Unit Thc Percent',
        metrc_field='UnitThcPercent')
    unit_thc_content = fields.Float(
        string='Unit Thc Content',
        metrc_field='UnitThcContent')
    unit_thc_content_uom = fields.Many2one(
        'uom.uom',
        string='Unit Thc Content Unit Of Measure',
        metrc_field='UnitThcContentUnitOfMeasureName')
    metrc_volume = fields.Float(metrc_field='UnitVolume')
    unit_volume_uom = fields.Many2one(
        'uom.uom',
        domain=[('category_id.name', '=', 'Volume')],
        string='Unit Volume Unit Of Measure',
        metrc_field='UnitVolumeUnitOfMeasureName')
    metrc_weight = fields.Float(metrc_field='UnitWeight')
    unit_weight_uom = fields.Many2one(
        'uom.uom',
        domain=[('category_id.name', '=', 'Weight')],
        string='Unit Weight Unit Of Measure',
        metrc_field='UnitWeightUnitOfMeasureName')
    serving_size = fields.Float(
        string='Serving Size',
        metrc_field='ServingSize')
    supply_duration_days = fields.Integer(
        string='Supply Duration Days',
        metrc_field='SupplyDurationDays')
    ingredients = fields.Char(metrc_field='Ingredients')
    approval_status = fields.Char(metrc_field='ApprovalStatus', default="Approved")

    # Related field
    require_strain = fields.Boolean(related='item_cat_id.strain')
    require_itembrand = fields.Boolean(related='item_cat_id.item_brand')
    require_administrationmethod = fields.Boolean(related='item_cat_id.administration_method')
    require_cbdpercent = fields.Boolean(related='item_cat_id.cbdpercent')
    require_cbdcontent = fields.Boolean(related='item_cat_id.cbdcontent')
    require_thcpercent = fields.Boolean(related='item_cat_id.thcpercent')
    require_thccontent = fields.Boolean(related='item_cat_id.thccontent')
    require_unitvolume = fields.Boolean(related='item_cat_id.unitvolume')
    require_unitweight = fields.Boolean(related='item_cat_id.unitweight')
    require_servingsize = fields.Boolean(related='item_cat_id.servingsize')
    require_supplydurationdays = fields.Boolean(related='item_cat_id.supplydurationdays')
    require_ingredients = fields.Boolean(related='item_cat_id.ingredients')
    sync_status = fields.Selection(selection=[
                        ('synced', 'Fully Synced'),
                        ('not_synced', 'Not Synced'),
                        ('partial', 'Partially Synced')
                    ], default="not_synced", compute="compute_sync_status", string="METRC Sync Status")
    sync_message = fields.Html(compute="compute_sync_status")

    def to_metrc_qty(self, quantity, raise_for_error=True):
        # precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        if self.diff_metrc_uom and self.metrc_uom_id:
            coeff = 1 if (self.metrc_uom_id == self.uom_id) else self[self.metrc_item_cat_id.coeff_field_id.name]
            quantity = quantity * coeff
            return float_round(quantity, precision_rounding=self.uom_id.rounding)
        return float_round(quantity, precision_rounding=self.uom_id.rounding)

    def from_metrc_qty(self, quantity, raise_for_error=True):
        # precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        if self.diff_metrc_uom and self.metrc_uom_id:
            if float_is_zero(self[self.metrc_item_cat_id.coeff_field_id.name], precision_digits=self.uom_id.rounding):
                msg = 'Product "%s" Metrc UoM "%s" coefficient field "%s" \
                            value can not be zero.' % (self.metrc_name, self.metrc_uom_id.name, self.metrc_item_cat_id.coeff_field_id.name)
                if raise_for_error:
                    raise ValidationError(msg)
                _logger.warning(msg)
            else:
                quantity = quantity / self[self.metrc_item_cat_id.coeff_field_id.name]
        return float_round(quantity, precision_rounding=self.uom_id.rounding)

    def compute_sync_status(self):
        sync_status = {'synced': 'Fully Synced', 'not_synced': 'Not Synced', 'partial': 'Partially Synced'}
        for product in self:
            sync_message = ""
            model_datas = product.get_metrc_model_datas()
            status = 'not_synced'
            if model_datas:
                if all([(md.metrc_id > 0) and (md.need_sync is False) for md in model_datas]):
                    status = 'synced'
                elif all([(md.metrc_id == 0) for md in model_datas]) or all([(md.metrc_id > 0) and (md.need_sync is True) for md in model_datas]):
                    status = 'not_synced'
                else:
                    status = 'partial'
                sync_msg = '{} [Sync pending for {}]'.format(sync_status[status], ','.join(model_datas.filtered(lambda md: md.metrc_id == 0).mapped('metrc_license_id.license_number'))) if (status == 'partial') else sync_status[status]
                sync_message = "<li><b>{}</b>: {}</li>".format(product.metrc_name, sync_msg)
            product.sync_status = status
            product.sync_message = sync_message

    @api.onchange('metrc_item_cat_id')
    def onchange_metrc_item_category(self):
        if self.metrc_item_cat_id:
            self.item_cat_id = self.metrc_item_cat_id

    @api.depends('product_tmpl_id.name', 'name', 'product_template_attribute_value_ids', 'default_code')
    def _compute_metrc_name(self):
        for product in self:
            product.metrc_name = product.name_get()[0][1]

    @api.onchange('is_metric_product')
    def product_onchange_is_metric_product(self):
        if self.is_metric_product:
            self.tracking = 'lot'
            self.type = 'product'

    @api.model
    def create(self, vals):
        context = dict(self._context)
        if vals.get('is_metric_product'):
            context.update({'metrc_notrack': not vals.get('is_metric_product')})
        if vals.get('metrc_item_cat_id'):
            vals.update({'item_cat_id': vals['metrc_item_cat_id'], 'is_metric_product': True})
        return super(ProductProduct, self.with_context(context)).create(vals)

    def write(self, vals):
        context = dict(self._context)
        if vals.get('metrc_item_cat_id'):
            vals.update({'is_metric_product': True})
        if vals.get('is_metric_product'):
            context.update({'metrc_notrack': not vals.get('is_metric_product')})
        result = super(ProductProduct,  self.with_context(context)).write(vals)
        metrc_fields = self._get_metrc_fields()
        metrc_fields = list(set(metrc_fields) - set(['metrc_item_cat_id', 'metrc_uom_id', 'uom_id', 'uom_po_id']))
        metrc_fields += ['default_code', 'product_template_attribute_value_ids', 'is_metric_product']
        for product in self:
            if product.metrc_item_cat_id and not self.env.context.get('import_mode') and \
               any([field in vals.keys() for field in metrc_fields]):
                model_datas = product.get_metrc_model_datas()
                if any(model_datas.mapped('is_used')) and any([(True if vals.get(f) else False) for f in ['default_code', 'product_template_attribute_value_ids']]):
                    used_items = model_datas.filtered(lambda m: m.is_used)
                    raise UserError(_("Product variant {} is already marked as used in metrc license [{}]. Can not have its name changed.".format(product.metrc_name, ','.join(used_items.mapped('metrc_license_id.license_number')))))
        return result

    def _get_default_values(self):
        res = super(ProductProduct, self)._get_default_values()
        res.update({
            'tracking': 'lot',
            'type': 'product',
            'is_metric_product': True,
            'standard_price': 0.01
            })
        return res

    def has_value(self, col_name, col_info):
        # Helper method to determine the field has set on the current product or not.
        value = False
        if col_info['type'] in ['float', 'monetary']:
            if self[col_name] != 0.00:
                value = True
        elif col_info['type'] in ['integer']:
            if self[col_name] != 0:
                value = True
        elif col_info['type'] in ['char']:
            if self[col_name] != '':
                value = True
        elif col_info['type'] == 'many2one':
            if self[col_name] != False and self[col_name].id:
                value = True
        else:
            value = False
        return value

    def sync_with_metrc(self):
        for product in self.filtered(lambda p: p.sync_status in ['not_synced', 'partial']):
            model_datas = product.get_metrc_model_datas()
            for model_data in model_datas:
                product._update_dependant_objects(license=model_data.metrc_license_id)
                product._match_with_metrc(license=model_data.metrc_license_id)

    @api.model
    def _map_update_record(self):
        record_vals = super(ProductProduct, self)._map_update_record()
        if self.diff_metrc_uom:
            record_vals.update({'UnitOfMeasure': self.metrc_uom_id.name})
            if self.metrc_item_cat_id.coeff_related_fields_ids:
                for col_name, col_info in self.fields_get(self.metrc_item_cat_id.coeff_related_fields_ids.mapped('name')).items():
                    metrc_fields_name = getattr(self._fields.get(col_name), 'metrc_field')
                    if metrc_fields_name:
                        initial_value = self[col_name]
                        record_vals[metrc_fields_name] = self.create_mapping_value(initial_value, col_info, read=True) or None
        return record_vals

    def _match_with_metrc(self, license, update_metrc_meta=True, raise_for_error=True, automatic=True):
        metrc_model_name, actions = self._get_api_actions()
        skip_metrc = self.env['ir.config_parameter'].sudo().get_param('metrc.skip_transactions', default='False')
        metrc_account = self.env.user.ensure_metrc_account()
        if automatic:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        if actions.get('read') and str(skip_metrc) == 'False':
            errors = ""
            uri = '/{}/{}/{}'.format(metrc_model_name, metrc_account.api_version, actions['read'])
            params = {}
            if self._metrc_license_require and license:
                params = {'licenseNumber': license.license_number}
            records = metrc_account.fetch('GET', uri, params=params)
            for product in self:
                metrc_fields = self._get_metrc_fields()
                metrc_fields_details = self.fields_get(metrc_fields)
                metrc_fields_details.pop('name')
                metrc_field_names = {f: False for f in metrc_fields}
                for col_name, col_info in self.fields_get(metrc_fields).items():
                    metrc_field_name = getattr(product._fields.get(col_name), 'metrc_field')
                    metrc_field_names[col_name] = metrc_field_name
                model_data = product.get_metrc_model_data(license=license)
                if model_data and model_data.metrc_id > 0:
                    records_filtered = [record for record in records if (record['Id'] == model_data.metrc_id)]
                else:
                    records_filtered = [record for record in records if (product['metrc_name'] == record['Name'])]
                metrc_data = False
                if records_filtered:
                    metrc_data = records_filtered[0]
                if metrc_data:
                    ctx = {
                        'default_metrc_id': metrc_data['Id'],
                        'default_metrc_license_id': license.id,
                        'default_metrc_account_id': metrc_account.id,
                        'need_sync': False,
                        'import_mode': True,
                        'default_is_used': metrc_data['IsUsed']
                    }
                    # creating/updating the metric model data before start processing.
                    product.with_context(ctx)._track_metrc_model_data()
                    model_data = product.get_metrc_model_data(license=license)
                    new_field_vals = product._map_record(metrc_data, metrc_fields_details)
                    product_data = product.read(new_field_vals.keys())[0]
                    for col, val in product_data.items():
                        if isinstance(val, tuple):
                            product_data[col] = val[0]
                    if not all([product_data[f] == new_field_vals[f] for f in new_field_vals.keys()]):
                        try:
                            product._do_metrc_update(license, 'write', model_data)
                            if automatic:
                                cr.commit()
                        except UserError as e:
                            exinfo = traceback.format_exception_only(e.__class__, e)
                            _logger.error(e)
                            if not raise_for_error:
                                errors += exinfo[0]
                                if automatic:
                                    cr.rollback()
                            else:
                                raise e
                else:
                    model_data = product.get_metrc_model_data(license=license)
                    try:
                        product._do_metrc_update(license, 'create', model_data)
                        if automatic:
                            cr.commit()
                    except UserError as e:
                        exinfo = traceback.format_exception_only(e.__class__, e)
                        _logger.error(e)
                        if not raise_for_error:
                            errors += exinfo[0]
                            if automatic:
                                cr.rollback()
                        else:
                            raise e
                    if update_metrc_meta:
                        product._update_metrc_id(metrc_account, license=license)
                    if automatic:
                        cr.commit()
            if automatic:
                cr.commit()
                cr.close()
            return errors

    def _cron_go_live_push_products(self, license, all_products=False, batch_size=100, automatic=True, raise_for_error=False):
        metrc_account = self.env.user.ensure_metrc_account()
        if automatic:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        products = self.env['product.product'].search([('is_metric_product', '=', True)])
        if not all_products:
            products = products.filtered(lambda p: p.sync_status in ['not_synced', 'partial'])
        _logger.info('metrc: starting go-live push products to metrc')
        for batch in split_every(batch_size, products):
            _logger.info('metrc: pushing batch of %d products to facility %s' % (
                                        len(batch), license.name))
            product_batch = self.env['product.product']
            for p in batch:
                metrc_model_data = p.get_metrc_model_data(license=license)
                if metrc_model_data and metrc_model_data.metrc_id > 0:
                    continue
                if not metrc_model_data:
                    p.with_context({'default_metrc_license_id': license.id, 'import_mode': True})._track_metrc_model_data()
                product_batch |= p
            if automatic:
                cr.commit()
            try:
                product_batch._update_dependant_objects(license=license, update_metrc_meta=False, raise_for_error=False)
                product_batch._match_with_metrc(license=license, raise_for_error=False, update_metrc_meta=False, automatic=False)
                if automatic:
                    cr.commit()
            except Exception as ex:
                if automatic:
                    cr.rollback()
                _logger.error("Error during pushing products to METRC.")
                _logger.error(ex)
                if raise_for_error:
                    raise ex
                else:
                    metrc_account.log_exception()
            _logger.info('metrc: finished pushing batch of %d products to facility %s' % (
                                                len(batch), license.name))
        try:
            products._update_metrc_id(metrc_account, license)
        except Exception as ex:
            if automatic:
                cr.rollback()
            _logger.error("Error during linking products meta data from METRC.")
            _logger.error(ex)
            if raise_for_error:
                raise ex
            else:
                metrc_account.log_exception()
        _logger.info('metrc: end of go-live push products to metrc')
        if automatic:
            cr.commit()
            cr.close()
        return True

    def _update_dependant_objects(self, license, update_metrc_meta=True, raise_for_error=True):
        metrc_account = self.env.user.ensure_metrc_account()
        strains_to_match = self.env['metrc.strains']
        for product in self:
            if product.item_cat_id.strain and product.strain_id:
                model_data = product.strain_id.get_metrc_model_data(license=license)
                if model_data.metrc_id == 0:
                    strains_to_match |= product.strain_id
        if strains_to_match and strains_to_match.ids:
            strains_to_match._match_with_metrc(license=license, raise_for_error=raise_for_error, update_metrc_meta=update_metrc_meta)
            if not update_metrc_meta:
                strains_to_match._update_metrc_id(metrc_account, license)

    @api.model
    def _get_product(self, license, name, uom, categ):
        product = False
        model_datas = self.env['metrc.model.data'].search([('model', '=', 'product.product'), ('metrc_license_id', '=', license.id)])
        if model_datas:
            products = self.browse(model_datas.mapped('res_id')).filtered(lambda p: p.name == name and p.uom_id.name == uom and p.item_cat_id.name == categ)
            product = products[0] if products else False
        return product
