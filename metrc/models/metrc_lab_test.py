# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class MetrcLabTestType(models.Model):
    _name = 'metrc.labtest.type'
    _description = 'Metrc Labtest Type'
    _inherit = ['metrc.meta']
    _metrc_model_name = 'labtests'
    _metrc_license_require = False

    def _valid_field_parameter(self, field, name):
        # allow tracking on abstract models; see also 'mail.thread'
        return (
            name in ('metrc_field', 'metrc_rec_name') or super()._valid_field_parameter(field, name)
        )

    def _get_api_actions(self):
        return self._metrc_model_name, {
            'read': 'types'
        }

    name = fields.Char(string='Name', metrc_field='Name', metrc_rec_name=True,  index=True)
    result_required = fields.Boolean(string='Test Result Required?', metrc_field='RequiresTestResult')
    pass_always = fields.Boolean(string='Always Pass', metrc_field='AlwaysPasses')
    depedency = fields.Char(string='Dependency Mode', metrc_field='DependencyMode')


class MetrcLabTest(models.Model):
    _name = 'metrc.labtest'
    _description = 'Metrc Labtest'

    def _valid_field_parameter(self, field, name):
        # allow tracking on abstract models; see also 'mail.thread'
        return (
            name in ('metrc_field', 'metrc_rec_name') or super()._valid_field_parameter(field, name)
        )

    name = fields.Char('Label', required=True)
    result_date = fields.Date(string='Result Date')
    result_ids = fields.One2many(comodel_name='metrc.labtest.result',
                                    inverse_name='test_id', string='Results')
    metrc_license_id = fields.Many2one(comodel_name='metrc.license', required=True)

    def create_on_metrc(self):
        self.ensure_one()
        metrc_account = self.env.user.metrc_account_id
        if not metrc_account:
            raise UserError(_('No metrc API account configured on this user {}. '
                                'Cannot perform this operation.'.format(self.env.user.name)))
        url = '/{}/{}/{}'.format('labtests', metrc_account.api_version, 'record')
        params = {'licenseNumber': self.metrc_license_id.license_number}
        data = {
            'Label': self.name,
            'ResultDate': self.result_date,
            'Results': [{
                'LabTestTypeName': result.test_type_id.name,
                'Quantity': result.quantity,
                'Passed': result.passed,
                'Notes': result.note
            } for result in self.result_ids]
        }
        metrc_account.fetch('POST', url, params=params, data=data)


class MetrcLabTestResult(models.Model):
    _name = 'metrc.labtest.result'
    _description = 'Labtest Results'

    test_id = fields.Many2one(comodel_name='metrc.labtest', 
                                string='Labtest Reference')
    test_type_id = fields.Many2one(comodel_name='metrc.labtest.type',
                                string='Test Type', required=True)
    metrc_license_id = fields.Many2one(comodel_name='metrc.license',
                                string='Associated License', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    passed = fields.Boolean(string='Passed', required=True)
    note = fields.Text(string='Notes')
