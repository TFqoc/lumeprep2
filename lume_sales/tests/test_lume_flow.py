import logging
from . test_lumesales_base import TestLumeSaleCommon
from odoo.tests.common import tagged

_logger = logging.getLogger(__name__)

# @tagged('lume')
# class TestLumeSOPosition(TestLumeSaleCommon):
#     def test_so_creation(self):


@tagged('lume')
class TestRecLumeFlow(TestLumeSaleCommon):
    def test_checkin_onchange(self):
        Task = self.env['project.task'].with_context({'tracking_disable': True})
        Test_Task = Task.create({
            'name': 'Test',
            'project_id': self.lumestore_one.id,
        })
        record_ids = [Test_Task.id]
        active_id = self.lumestore_one.id
        active_ids = [self.lumestore_one.id]
        uid = self.env.ref('base.user_admin').id
        self.env['project.task'].browse(record_ids).with_context({
            'active_id': active_id,
            'active_ids': active_ids,
            'active_model': 'project.project',
            'allowed_company_ids': [1],
            'default_project_id': 5,
            'default_stage_id': self.env.ref('lume_sales.lume_stage_0'),
            'lang': 'en_US',
            'pivot_row_groupby': ['user_id'],
            'tz': 'Europe/Brussels',
            'uid': uid}).with_user(uid).onchange({
                'scan_text': '@ANSI 636032030102DL00410205ZM03460027DLDCADCBDCDDBA12312021DCSLOVEDCTEVE ADBDDBB02171987DBC2DAYDAUDAG629 MAD DOG LANEDAIDETROITDAJMIDAK482010001  DAQC 333 547 393 957DCFDCGUSADCHDAHDCKDDAN', 
                'partner_id': False, 
                'fulfillment_type': 'store', 
                'order_type': 'adult', 
                'project_id': self.lumestore_one.id, 
                #'timesheet_product_id': False, 
                'company_id': 1, 
                'parent_id': False}, 
                'scan_text', {
                    'scan_text': '1', 
                    'partner_id': '1', 
                    'fulfillment_type': '', 
                    'order_type': '', 
                    'project_id': '1', 
                    'timesheet_product_id': '', 
                    'company_id': '1', 
                    'parent_id': '1'})
        _logger.warning(Test_Task.scan_text)
        # TODO Assert statements.
        self.assertEqual(
            Test_Task.partner_id.id,
            self.customer_rec.id,
            "Error in Check In Onchange: Partner Id was %s instead of %s" % (Test_Task.partner_id.id, self. customer_rec.id)
        )

    def test_task_to_build_cart(self): #Upon pressing build cart, the tile should be moved to the Build Cart Stage.
        Task = self.env['project.task'].with_context({'tracking_disable': True})
        uid = self.env.ref('base.user_admin').id
        Test_Task = Task.create({
            'name': 'Test',
            'user_id': uid, #Change to person assigned to that task.
            'project_id': self.lumestore_one.id,
            'partner_id': self.customer_rec.id,
            'stage_id': self.env.ref('lume_sales.lume_stage_0').id
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

        #Validate Task Position.

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
    # def test_barcode_parse(self): 
    #     """Checking that the barcode parses correctly."""
    #     pass #TODO: Paste runbot code.
    # def test_add_button(self):
    #     pass #TODO: Paste runbot code.
    # def test_check_in_button(self):
        
    #     pass #TODO: Paste runbot code.


    



