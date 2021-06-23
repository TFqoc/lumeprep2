# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class MetrcProductCategory(models.Model):

    _name = 'metrc.product.category'
    _description = 'Metrc Product Category'
    _inherit = ['mail.thread', 'metrc.meta']
    _metrc_model_name = 'items'
    _metrc_license_require = False

    def _valid_field_parameter(self, field, name):
        # allow tracking on abstract models; see also 'mail.thread'
        return (
            name in ('metrc_field', 'metrc_rec_name') or super()._valid_field_parameter(field, name)
        )

    def _get_api_actions(self):
        return self._metrc_model_name, {
            'read': 'categories'
        }

    name = fields.Char(
        string='Name', index=True, required=True,
        tracking=True, metrc_field='Name',
        metrc_rec_name=True)
    active = fields.Boolean(string='Active', default=True)
    category_type = fields.Char(
        string='Type', required=True,
        index=True, tracking=True,
        metrc_field='ProductCategoryType')
    quantity_type = fields.Char(
        string='Quantity Type', required=True,
        tracking=True, metrc_field='QuantityType')
    testing_state = fields.Char(
        string='Default Lab Testing State', required=True,
        tracking=True, metrc_field='DefaultLabTestingState', default="0")
    approval = fields.Boolean(string='Requires Approval', metrc_field='RequiresApproval')
    strain = fields.Boolean(string='Requires Strain', metrc_field='RequiresStrain')
    item_brand = fields.Boolean(string='Requires Item Brand', metrc_field='RequiresItemBrand')
    administration_method = fields.Boolean(
        string='Requires Administration Method',
        metrc_field='RequiresAdministrationMethod')
    cbdpercent = fields.Boolean(
        string='Requires Unit Cbd Percent',
        metrc_field='RequiresUnitCbdPercent')
    cbdcontent = fields.Boolean(
        string='Requires Unit Cbd Content',
        metrc_field='RequiresUnitCbdContent')
    thcpercent = fields.Boolean(
        string='Requires Unit Thc Percent',
        metrc_field='RequiresUnitThcPercent')
    thccontent = fields.Boolean(
        string='Requires Unit Thc Content',
        metrc_field='RequiresUnitThcContent')
    unitvolume = fields.Boolean(
        string='Requires Unit Volume',
        metrc_field='RequiresUnitVolume')
    unitweight = fields.Boolean(
        string='Requires Unit Weight',
        metrc_field='RequiresUnitWeight')
    servingsize = fields.Boolean(
        string='Requires Serving Size',
        metrc_field='RequiresServingSize')
    supplydurationdays = fields.Boolean(
        string='Requires Supply Duration Days',
        metrc_field='RequiresSupplyDurationDays')
    qty_uom_name = fields.Char(
        string='Quantity Unit Of Measure Name',
        metrc_field='UnitQuantityUnitOfMeasureName')
    qty_multiplier = fields.Char(
        string='Quantity Multiplier',
        metrc_field='UnitQuantityMultiplier')
    ingredients = fields.Boolean(
        string='Requires Ingredients',
        metrc_field='RequiresIngredients')
    productphoto = fields.Boolean(
        string='Requires ProductPhoto',
        metrc_field='RequiresProductPhoto')
    cancontainseeds = fields.Boolean(
        string='Can ContainSeeds',
        metrc_field='CanContainSeeds')
    canberemediated = fields.Boolean(
        string='Can Be Remediated',
        metrc_field='CanBeRemediated')
    diff_metrc_uom = fields.Boolean(string='Requires Different Metrc UoM')
    coeff_field_id = fields.Many2one(comodel_name='ir.model.fields', string='UoM Coefficient Field',
            domain=[('ttype', '=', 'float'), ('model_id.model', '=', 'product.product')],
            help='Coefficient to convert Metrc Unit of Measure to product Unit of Measure\n'
            ' * Unit of Measure = Product Unit of Measure * UoM Coefficient Field Value')
    coeff_related_fields_ids = fields.Many2many(comodel_name='ir.model.fields',
            relation='metrc_categ_field_rel', string='Coefficient Related Metrc Fields',
            domain=[('metrc_field', '!=', False), ('model_id.model', '=', 'product.product')],
            help='Force update the field values when creating/updating product in Metrc.')