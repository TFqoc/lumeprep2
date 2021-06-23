# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class IrModel(models.Model):
    _inherit = 'ir.model'
    _do_metrc_sync = False

    do_metrc_sync = fields.Boolean(
        string="Do Metrc Sync", default=False, index=True,
        help="Whether this model record will be synchromized with Metrc.",
    )

    def _reflect_model_params(self, model):
        vals = super(IrModel, self)._reflect_model_params(model)
        vals['do_metrc_sync'] = issubclass(type(model), self.pool['ir.model'])
        return vals

    @api.model
    def _instanciate(self, model_data):
        model_class = super(IrModel, self)._instanciate(model_data)
        if not model_class._custom and model_class.get('do_metrc_sync'):
            model_class._do_metrc_sync = model_data.get('do_metrc_sync')
        return model_class


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    metrc_field = fields.Char(
        string="Metrc Field", default=False,  index=True,
        help="When imported/synchromized what metrc field will be mapped on this table.",
    )
    metrc_rec_name = fields.Boolean(
        string="Metrc Search Field", default=False, index=True,
        help="When imported/synchromized to avoid duplicate use this field for search for record and create instead.",
    )

    def _reflect_field_params(self, field, model_id):
        vals = super(IrModelFields, self)._reflect_field_params(field, model_id)
        vals['metrc_rec_name'] = getattr(field, 'metrc_rec_name', None)
        vals['metrc_field'] = getattr(field, 'metrc_field', None)
        return vals

    def _instanciate_attrs(self, field_data):
        attrs = super(IrModelFields, self)._instanciate_attrs(field_data)
        if attrs:
            attrs['metrc_field'] = field_data['metrc_field'] if field_data.get('metrc_field') else False
            attrs['metrc_rec_name'] = bool(field_data['metrc_rec_name']) if field_data.get('metrc_rec_name') else False
        return attrs
