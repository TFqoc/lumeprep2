# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class MetrcModelData(models.Model):
    """
    Holds external identifier keys for records in the database.
    """
    _name = 'metrc.model.data'
    _description = 'Metrc Sync Model Data'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Record Name', required=True,
        compute='_compute_record_name', readonly=True, store=True)
    reference = fields.Char(
        string='Reference', compute='_compute_reference',
        readonly=True, store=False)
    model = fields.Char(string='Model', required=True)
    res_id = fields.Integer(string='Record ID', help="ID of the target record in the database")
    need_sync = fields.Boolean(string='Require Sync', default=False)
    date_update = fields.Datetime(string='Update Date', default=fields.Datetime.now)
    date_init = fields.Datetime(string='Init Date', default=fields.Datetime.now)
    metrc_account_id = fields.Many2one(comodel_name='metrc.account', string='Metrc Account')
    metrc_license_id = fields.Many2one(comodel_name='metrc.license', string='Metrc License')
    metrc_id = fields.Integer(string='Metrc Id', help='Metrc resouece id used to identify record in the Metrc')
    raw_data = fields.Text(string="Raw Request Response")
    is_used = fields.Boolean()
    active = fields.Boolean(default=True, help="Set active to false to stop interaction with metrc for this record and license.")

    @api.depends('model', 'res_id')
    def _compute_record_name(self):
        for data in self:
            if data.model and data.res_id:
                data.name = self.env[data.model].browse(data.res_id).name_get()[0][1]

    @api.depends('model', 'res_id')
    def _compute_reference(self):
        for res in self:
            res.reference = "%s,%s" % (res.model, res.res_id)

    def _auto_init(self):
        res = super(MetrcModelData, self)._auto_init()
        tools.create_index(self._cr, 'metrc_model_data_model_res_id_index',
                           self._table, ['model', 'res_id'])
        return res
