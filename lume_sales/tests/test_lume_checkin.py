import logging
from . test_lumesales_base import TestLumeSaleCommon
from odoo.tests.common import tagged

_logger = logging.getLogger(__name__)

@tagged('lume')
class TestCheckIn(TestLumeSaleCommon):

@tagged('lume')
class TestBarcodeParse(TestLumeSaleCommon):
    def setUp(self):
        super().setUp()    

    def test_scan_barcode_onchange(self):
        record_ids = []
        # TODO: Check or Find active_id link (external id or otherwise)
        active_id = 7
        # TODO: Check or Find active_ids link (external id or otherwise)
        active_ids = [7, ]
        uid = self.env.ref('base.user_admin').id
        self.env['project.task'].browse(record_ids).with_context({
            'active_id': active_id,
            'active_ids': active_ids,
            'active_model': 'project.project',
            'allowed_company_ids': [1],
            'default_project_id': 7,
            'default_stage_id': 5,
            'lang': 'en_US',
            'pivot_row_groupby': ['user_id'],
            'tz': 'Europe/Brussels',
            'uid': uid}).with_user(uid).onchange({
                'scan_text': '@ANSI 636031080102DL00410263ZW03040017DLDCADDCBJDCDNONEDBA12022021DCSCOUCHDACJACOBDADMICHAELDBD12012020DBB07152001DBC1DAYHAZDAU064 INDAG874 BARBARA STDAISUN PRAIRIEDAJWIDAK535901570  DAQC2004330125505DCFOTA6R2020120113424863DCGUSADDENDDFNDDGNDCK0130600043003565DDAFDDB09012015ZWZWA19252171875', 
                'partner_id': False, 
                'order_type': 'store', 
                'user_id': 2, 
                'project_id': 7, 
                'timesheet_product_id': False, 
                'company_id': 1, 
                'parent_id': False}, 
            'scan_text', {
                'scan_text': '1', 
                'partner_id': '1', 
                'order_type': '', 
                'user_id': '', 
                'project_id': '1', 
                'timesheet_product_id': '', 
                'company_id': '1', 
                'parent_id': '1'})
                
                # TODO: Check or Find active_id link (external id or otherwise)
                active_id = 7
                # TODO: Check or Find active_ids link (external id or otherwise)
                active_ids = [7, ]
                uid = self.env.ref('base.user_admin').id
                record = self.env['project.task'].with_context({
                    'active_id': active_id,
                    'active_ids': active_ids,
                    'active_model': 'project.project',
                    'allowed_company_ids': [1],
                    'default_project_id': 7,
                    'default_stage_id': 5,
                    'lang': 'en_US',
                    'pivot_row_groupby': ['user_id'],
                    'tz': 'Europe/Brussels',
                    'uid': uid}).with_user(uid).create({
                        'scan_text': False, 
                        'partner_id': 45, 
                        'order_type': 'store', 
                        'user_id': self.env.ref('base.user_admin').id, 
                        'project_id': 7, 
                        'timesheet_product_id': False, 
                        'company_id': self.env.ref('base.main_company').id, 
                        'parent_id': False})

                    self.env['ir.model.data'].create({
                        'model': 'project.task',
                        'module': 'project',
                        'name': 'luminarytestcaseclass_project_task_24',
                        'res_id': record.id})
        

        # # TODO: Check or Find active_id link (external id or otherwise)
        # active_id = 8
        # # TODO: Check or Find active_ids link (external id or otherwise)
        # active_ids = [8, ]
        # uid = self.env.ref('base.user_admin').id
        # record = self.env['project.task'].with_context({
        #     'active_id': active_id,
        #     'active_ids': active_ids,
        #     'active_model': 'project.project',
        #     'allowed_company_ids': [1],
        #     'default_project_id': 8,
        #     'default_stage_id': 5,
        #     'lang': 'en_US',
        #     'pivot_row_groupby': ['user_id'],
        #     'tz': 'Europe/Brussels',
        #     'uid': uid}).with_user(uid).create({'scan_text': False, 'partner_id': 46, 'order_type': 'store', 'user_id': self.env.ref('base.user_admin').id, 'project_id': 8, 'timesheet_product_id': False, 'company_id': self.env.ref('base.main_company').id, 'parent_id': False})
        # self.env['ir.model.data'].create({
        #     'model': 'project.task',
        #     'module': 'project',
        #     'name': 'checkinbarcodetest_project_task_37',
        #     'res_id': record.id})

    def test_manditory_fields(self)
    