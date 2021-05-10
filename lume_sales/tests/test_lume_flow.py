import logging
from . test_lumesales_base import TestLumeSaleCommon

_logger = logging.getLogger(__name__)


class TestLumeSOPosition(TestLumeSaleCommon):
    def test_so_creation(self):



class TestLumeTaskPosition(TestLumeSaleCommon):
    def test_task_to_build_cart(self): #Upon pressing build cart, the tile should be moved to the Build Cart Stage.
        uid = self.env.ref('base.user_admin').id
        # TODO: This needs to be the id of the task being moved.
        record_ids = [self.env.ref('project.luminarytestcaseclass_project_task_24').id, ]
        # TODO: This needs to be set to be the id of the current row's record.
        active_id = self.env.ref('project.luminarytestcaseclass_project_task_24').project_id.id
        # TODO: This needs to be all models currently loaded in the wizard
        active_ids = [self.env.ref('project.luminarytestcaseclass_project_task_24').project_id.id, ]
        uid = self.env.ref('base.user_admin').id
        self.env['project.task'].browse(record_ids).with_context({
            'active_id': active_id,
            'active_ids': active_ids,
            'active_model': 'project.project',
            'allowed_company_ids': [1],
            'default_project_id': 7,
            'lang': 'en_US',
            'pivot_row_groupby': ['user_id'],
            'tz': 'Europe/Brussels',
            'uid': uid}).with_user(uid).build_cart()

        self.assertTrue(

        )


    



