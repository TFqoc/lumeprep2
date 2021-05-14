import logging
from . test_lumesales_base import TestLumeSaleCommon
from odoo.tests.common import tagged

_logger = logging.getLogger(__name__)

# @tagged('lume')
# class TestLumeSOPosition(TestLumeSaleCommon):
#     def test_so_creation(self):


@tagged('lume')
class TestLumeTaskPosition(TestLumeSaleCommon):
    def test_task_to_build_cart(self): #Upon pressing build cart, the tile should be moved to the Build Cart Stage.
        Task = self.env['project.task'].with_context({'tracking_disable': True})
        uid = self.env.ref('base.user_admin').id
        Test_Task = Task.create({
            'name': 'Test',
            'user_id': uid, #Change to person assigned to that task.
            'project_id': self.lumestore_one.id,
            'partner_id': self.customer_rec.id,
            'stage_id': self.env.ref('lume_sales.lume_stage_1').id
        })
        record_ids = [Test_Task.id]
        active_id = [Test_Task.id]
        active_ids = [Test_Task.id, self.lumestore_one.id]

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

        #Test Task Position.

        self.assertEqual(
            Test_Task.stage_id.sequence,
            10, 
            "Error in build_cart: Task did not move to the appropriate stage."
        )

        #Validating Sale_Order
        # TODO: Assert that the Order Type is carried over to the Sale Order.

        self.assertTrue(
            Test_Task.sales_order,
            "Error in build_cart: Sale Order was not created."
        )

        self.assertEqual(
            Test_Task.sales_order.task.id,
            Test_Task.id,
            "Error in build_cart: Task was not tied to Sale Order."
        )

        self.assertEqual(
            Test_Task.sales_order.warehouse_id.id,
            self.lumestore_one.warehouse_id.id,
            "Error in build_cart: Sale Order did not have the correct warehouse."
        )

        self.assertEqual(
            Test_Task.sales_order.partner_id.id,
            self.customer_rec.id,
            "Error in build_cart: Sale Order did not have the correct customer."
        )

        self.assertEqual(
            Test_Task.sales_order.user_id.id,
            uid,
            "Error in build_cart: Sale Order did not have the correct user id."
        )

        # TODO Assert that the view has changed to be that of the Sale Order as well as the Sale Order is already in edit mode.

        _logger.warning("Test Build Cart Status: Complete.")
        # TODO: Remove.


    



