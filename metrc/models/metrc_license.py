# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MetrcLicense(models.Model):

    _name = 'metrc.license'
    _description = 'Metrc License'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _valid_field_parameter(self, field, name):
        # allow tracking on abstract models; see also 'mail.thread'
        return (
            name in ('metrc_field', 'metrc_rec_name') or super()._valid_field_parameter(field, name)
        )

    name = fields.Char(string='License', store=True, index=True, compute='_compute_license_name')
    license_number = fields.Char(string='License Number', required=True, index=True, tracking=True)
    base_type = fields.Selection(selection=[
                        ('Internal', 'Facility'),
                        ('External', 'Customer/Vendor'),
                        ('Patient', 'Patient'),
                    ], required=True, string='Type', index=True,
                    default='External', tracking=True)
    metrc_type = fields.Selection(selection=[
                        ('metrc', 'Metrc Enabled'),
                        ('non_metrc', 'Non-Metrc Enabled')
                    ], string='Metrc Type', default='metrc',
                    tracking=True)
    usage_type = fields.Selection(selection=[
                        ('Adult-Use', 'Adult-Use'),
                        ('Medical', 'Medical'),
                        ('Both', 'Both'),
                    ], string='Usage Type',
                    tracking=True)
    permit_type = fields.Selection(selection=[
                        ('Cultivation', 'Cultivation'),
                        ('Distributor', 'Distributor'),
                        ('Harvest Processing', 'Harvest Processing'),
                        ('Manufacturing', 'Manufacturing'),
                        ('Nursery', 'Nursery'),
                        ('Retail Non-Storefront', 'Retail Non-Storefront'),
                        ('Retail', 'Retail'),
                        ('Transportation', 'Transportation'),
                        ('Microbusiness', 'Microbusiness')
                    ], string='Permit Types')
    active = fields.Boolean(string='Active', default=True)
    issue_date = fields.Date(
                    string="Issue Date", required=False,
                    tracking=True)
    expire_date = fields.Date(
                    string="Expiration Date", required=False,
                    tracking=True)
    partner_id = fields.Many2one(
                    comodel_name='res.partner', string='Contact',
                    required=False, index=1, tracking=True, compute="_compute_partner_id", store=True, readonly=False,
                    ondelete='restrict')
    issuer_id = fields.Many2one(
                    comodel_name='metrc.license.issuer', string='Issued By',
                    tracking=True,
                    ondelete='restrict')
    company_id = fields.Many2one(comodel_name='res.company', string="Company", tracking=True)
    metrc_account_id = fields.Many2one(comodel_name='metrc.account', string='Service Account')
    old_id = fields.Integer(string='Old ID')
    notes = fields.Html(string='Notes')

    image = fields.Image("Logo", attachment=True,
                    max_width=1024, max_height=1024,
                    help="This field holds the image used as logo for the brand, limited to 1024x1024px.")
    image_medium = fields.Image("Medium-sized image", attachment=True,
                    max_width=128, max_height=128,
                    help="Medium-sized logo of the brand. It is automatically "
                         "resized as a 128x128px image, with aspect ratio preserved. "
                         "Use this field in form views or some kanban views.")
    image_small = fields.Image("Small-sized image", attachment=True,
                    max_width=64, max_height=64,
                    help="Small-sized logo of the brand. It is automatically "
                    "resized as a 64x64px image, with aspect ratio preserved. "
                    "Use this field anywhere a small image is required.")
    flower_available = fields.Float("Available Flower")
    thc_available = fields.Float("Available THC")
    purchase_amount = fields.Float("Purchase Amount Days")
    facility_license_id = fields.Many2one(comodel_name='metrc.license', string="Facliilty License",
                                          domain=[('base_type', '=', 'Internal'), ('sell_to_patients', '=', True)],
                                          ondelete='set null')
    sell_to_patients = fields.Boolean(help='Field to determine whether this facility can sell to patients or not.'
                                           '\nAllowd to check patient quota or not.')
    

    _sql_constraints = [
        ('uniq_license_by_customer', 'unique (license_number, base_type, partner_id)', 'Customer/Company can not have duplicate license number!'),
    ]

    def refresh_allotments(self):
        metrc_account = self.env.user.ensure_metrc_account()
        uri = '/patients/v1/status/{}'.format(self.license_number)
        params = {
            'licenseNumber': self.facility_license_id.license_number,
        }
        patient_data = metrc_account.fetch('GET', uri, params=params)
        if patient_data:
            self.update({
                'flower_available': patient_data['FlowerOuncesAvailable'],
                'thc_available': patient_data['ThcOuncesAvailable'],
                'purchase_amount': patient_data['PurchaseAmountDays'],
            })

    def toggle_active(self):
        super(MetrcLicense, self).toggle_active()
        ModelData = self.env['metrc.model.data']
        for license in self:
            domain = [('metrc_license_id', '=', license.id)]
            if license.active:
                domain += [('active', '=', False)]
            model_datas = ModelData.search(domain)
            model_datas.write({'active': license.active})
            if license.base_type == 'Internal' and license.active and not model_datas:
                license.create_license_model_datas()

    @api.depends('company_id')
    def _compute_partner_id(self):
        if self.company_id:
            self.partner_id = self.company_id.partner_id

    @api.depends('license_number', 'partner_id', 'company_id', 'base_type')
    def _compute_license_name(self):
        for res in self:
            res.name = " - ".join(n for n in [res.license_number, res.company_id.name if (res.base_type == 'Internal') else res.partner_id.name] if n)

    def create_license_model_datas(self):
        metrc_account_id = self.env.user.ensure_metrc_account()
        products = self.env['product.product'].search([('is_metric_product', '=', True), ('metrc_item_cat_id', '!=', False)])
        products.with_context({
                'default_metrc_account_id': metrc_account_id.id,
                'default_metrc_license_id': self.id,
                'import_mode': True})._track_metrc_model_data()
        strains = self.env['metrc.strains'].search([])
        strains.with_context({'default_metrc_account_id': metrc_account_id.id, 'default_metrc_license_id': self.id})._track_metrc_model_data()

    def _schedule_todo_activity(self, message="Action Required!"):
        self.ensure_one()
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        model_obj = self.env['ir.model']._get('metrc.license')
        self.env['mail.activity'].create({
            'activity_type_id': activity_type.id,
            'res_id': self.id,
            'res_model_id': model_obj.id,
            'user_id': self.env.uid,
            'note': _(message)
        })

    @api.model
    def create(self, vals):
        license = super(MetrcLicense, self).create(vals)
        if license.base_type == 'Internal':
            license.create_license_model_datas()
        return license

    def write(self, vals):
        if vals.get('base_type'):
            raise UserError(_("You can not change a base type of the license. \nTry deleting and recreating again with desired base type."))
        return super(MetrcLicense, self).write(vals)

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args.append(('expire_date', '>=', fields.Date.today()))
        return super(MetrcLicense, self)._name_search(name=name, args=args, limit=limit, name_get_uid=name_get_uid)

    def unlink(self):
        if not self.env.context.get('force_unlink'):
            raise UserError(_('You should not delete or change facility license details, '
                              'If you planning to discontinue the facility license anymore,'
                              ' consider archiving the license or set it expired by adding'
                              ' license expiration date in past.'))
        return super(MetrcLicense, self).unlink()

class MetrcLicenseIssuer(models.Model):

    _name = 'metrc.license.issuer'
    _description = 'Metrc License Issuer'

    name = fields.Char(string="Issuer Name")

    _sql_constraints = [
        ('issuer_name_uniq', 'unique (name)', 'Metrc license issuer with this name already exists!'),
    ]
