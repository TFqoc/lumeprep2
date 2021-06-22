# -*- coding: utf-8 -*-

from odoo import fields, models


class MetrcLabTestType(models.Model):
    _name = 'metrc.labtest.type'
    _description = 'Metrc Lab Test Type'
    _inherit = ['metrc.meta']
    _metrc_model_name = 'labtests'
    _metrc_license_require = False

    def _get_api_actions(self):
        return self._metrc_model_name, {
            'read': 'types'
        }

    name = fields.Char(metrc_field="Name", metrc_rec_name=True,  index=True)
    result_required = fields.Boolean(string="Test Result Required?", metrc_field="RequiresTestResult")
    pass_always = fields.Boolean(string="Always Pass", metrc_field="AlwaysPasses")
    depedency = fields.Char(string="Dependency Mode", metrc_field="DependencyMode")


class MetrcLabTest(models.Model):
    _name = 'metrc.labtest'
    _description = 'Metrc Lab Test'

    name = fields.Char('Label', required=True)
    result_date = fields.Date()
    result_ids = fields.One2many('metrc.labtest.result', 'test_id', string="Results")
    license_id = fields.Many2one('metrc.license', required=True)

    def create_on_metrc(self):
        self.ensure_one()
        metrc_account = self.env.user.ensure_metrc_account()
        url = '/{}/{}/{}'.format('labtests', metrc_account.api_version, 'record')
        params = {'licenseNumber': self.license_id.license_number}
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
    _description = 'Lab Test Results'

    test_id = fields.Many2one('metrc.labtest', string="Labtest Reference")
    test_type_id = fields.Many2one('metrc.labtest.type', string="Test Type", required=True)
    license_id = fields.Many2one('metrc.license', string="Associated License", required=True)
    quantity = fields.Float(required=True)
    passed = fields.Boolean(required=True)
    note = fields.Text()
