import logging
from . test_lumesales_base import TestLumeSaleCommon

_logger = logging.getLogger(__name__)

class TestCheckIn(TestLumeSaleCommon):

class TestBarcodeParse(TestLumeSaleCommon):
    def setUp(self):
        super().setUp() 
        

        # TODO: Check or Find active_id link (external id or otherwise)
        active_id = 8
        # TODO: Check or Find active_ids link (external id or otherwise)
        active_ids = [8, ]
        uid = self.env.ref('base.user_admin').id
        record = self.env['project.task'].with_context({
            'active_id': active_id,
            'active_ids': active_ids,
            'active_model': 'project.project',
            'allowed_company_ids': [1],
            'default_project_id': 8,
            'default_stage_id': 5,
            'lang': 'en_US',
            'pivot_row_groupby': ['user_id'],
            'tz': 'Europe/Brussels',
            'uid': uid}).with_user(uid).create({'scan_text': False, 'partner_id': 46, 'order_type': 'store', 'user_id': self.env.ref('base.user_admin').id, 'project_id': 8, 'timesheet_product_id': False, 'company_id': self.env.ref('base.main_company').id, 'parent_id': False})
        self.env['ir.model.data'].create({
            'model': 'project.task',
            'module': 'project',
            'name': 'checkinbarcodetest_project_task_37',
            'res_id': record.id})

    def test_manditory_fields(self)
    