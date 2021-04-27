# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ast import literal_eval

from odoo import api, fields, models, _


class Partner(models.Model):
    _inherit = 'res.partner'

    license_ids = fields.One2many(
        comodel_name='metrc.license', inverse_name='partner_id',
        string='Licenses')
    license_vendor = fields.Boolean(string='License Vendor', compute='_compute_license_count', compute_sudo=True, store=True)
    license_count = fields.Integer(compute='_compute_license_count', compute_sudo=True, string='License Count')
    driver_license_number = fields.Char(string='Driver\'s License Number')

    @api.depends('license_ids')
    def _compute_license_count(self):
        for partner in self:
            partner.license_count = len(partner.license_ids)
            partner.license_vendor = True if partner.license_ids else False

    def action_view_partner_licenses(self):
        self.ensure_one()
        action = self.env.ref('metrc.action_view_all_metrc_license').read()[0]
        action['domain'] = literal_eval(action['domain'])
        action['domain'].append(('partner_id', 'child_of', self.id))
        return action

    def _schedule_todo_activity(self, message='Action Required!'):
        self.ensure_one()
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        model_obj = self.env['ir.model']._get('res.partner')
        self.env['mail.activity'].create({
            'activity_type_id': activity_type.id,
            'res_id': self.id,
            'res_model_id': model_obj.id,
            'user_id': self.env.uid,
            'note': _(message)
        })
