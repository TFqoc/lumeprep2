import logging
from . test_lumesales_base import compare_dictionaries
from . test_lumesales_base import TestLumeSaleCommon
from ..models.barcode_parse import parse_code
from odoo.tests.common import tagged

_logger = logging.getLogger(__name__)

# @tagged('lume')
# class TestLumeSOPosition(TestLumeSaleCommon):
#     def test_so_creation(self):


@tagged('lume') 
class TestRecLumeFlow(TestLumeSaleCommon):
    def test_checkin_onchange(self):
        _logger.warning("Product Rec's Type is %s" % self.product_rec.type)
        Task = self.env['project.task'].with_context({'tracking_disable': True})
        Test_Task = Task.create({
            'name': 'Test',
            'project_id': self.lumestore_one.id,
        })
        _logger.warning(Test_Task.partner_id)
        record_ids = [Test_Task.id]
        active_id = Test_Task.id
        active_ids = [self.lumestore_one.id, Test_Task.id]
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
        # TODO Assert statements.
        self.assertFalse(
            Test_Task.scan_text,
            "Error in Check In Onchange: Scan Text field was %s instead of False." % (Test_Task.scan_text)
        )

        _logger.warning(Test_Task.partner_id)
        _logger.warning(Test_Task.fulfillment_type)
        _logger.warning(Test_Task.order_type)
        _logger.warning(Test_Task.project_id)

        # TODO Verify what is being returned and how the data from the barcode parse is passed on to the check in screen.

        # self.assertEqual(
        #     Test_Task.partner_id.id, #This is not being set correctly.
        #     self.customer_rec.id,
        #     "Error in Check In Onchange: Partner Id was %s instead of %s" % (Test_Task.partner_id, self.customer_rec)
        # )

    def test_scan_text(self):
        Task = self.env['project.task'].with_context({'tracking_disable': True})
        Test_Task = Task.create({
            'name': 'Test',
            'project_id': self.lumestore_one.id,
        })

        Test_Task.scan_text = '@ANSI 636032030102DL00410205ZM03460027DLDCADCBDCDDBA12312021DCSLOVEDCTEVE ADBDDBB02171987DBC2DAYDAUDAG629 MAD DOG LANEDAIDETROITDAJMIDAK482010001  DAQC 333 547 393 957DCFDCGUSADCHDAHDCKDDAN'
        self.assertEqual(
            Test_Task.partner_id.id, #This is not being set correctly.
            self.customer_rec.id,
            "Error in Check In Onchange: Partner Id was %s instead of %s" % (Test_Task.partner_id, self.customer_rec)
        )

    def test_barcode_parse(self): 
        """Checking that the barcode parses correctly."""
        barcode = '@ANSI 636032030102DL00410205ZM03460027DLDCADCBDCDDBA12312021DCSLOVEDCTEVE ADBDDBB02171987DBC2DAYDAUDAG629 MAD DOG LANEDAIDETROITDAJMIDAK482010001  DAQC 333 547 393 957DCFDCGUSADCHDAHDCKDDAN'
        parsed_barcode = parse_code(barcode)
        key_list = ['name', 'street', 'city', 'zip', 'date_of_birth', 'drivers_license_expiration', 'drivers_license_number']

        dictionaries = compare_dictionaries(parsed_barcode, self.customer_rec, key_list)
        _logger.warning(dictionaries)

        self.assertTrue(
            dictionaries[0],
            "List of errors: %s " % (dictionaries[1:])
        )

        self.assertEqual(                  #As the State Field is not yet transfered to an ID, it should be MI.
            parsed_barcode['state_id'],
            'MI',
            "Error in Barcode Parse: the state id was %s instead of MI." % (parsed_barcode['state_id'])
        )
    def test_check_in_button(self):
        record_ids = [self.customer_rec.id]
        uid = self.env.ref('base.user_admin').id
        self.env['res.partner'].browse(record_ids).with_context({
            'allowed_company_ids': [1],
            'check_in_window': True,
            'fulfillment_type': 'store',
            'lang': 'en_US',
            'order_type': 'adult',
            'partner_id': self.customer_rec.id,
            'project_id': self.lumestore_one.id,
            'tz': 'Europe/Brussels',
            'uid': uid}).with_user(uid).check_in()

        
        # TODO: Refine how the test finds this task, as this can fail too easily.
        created_task = self.env['project.task'].search([('partner_id', '=', self.customer_rec.id)])
        #created_task = self.env['project.task'].browse(find_task.id)
        

        _logger.warning(created_task)
        key_list = ['partner_id', 'project_id', 'fulfillment_type', 'order_type', 'user_id', 'name']
        expected_values = {
            'partner_id': self.customer_rec,
            'project_id': self.lumestore_one, 
            'fulfillment_type': 'store',
            'order_type': 'adult',
            'user_id': False,
            'name': self.customer_rec.name
        }

        self.assertTrue(
            self.lumestore_one.tasks,
            "Task was not created upon pressing check in."
        )

        self.assertTrue(
            created_task,
            "Error in Check In: Task was not found (Either the Customer ID was incorrectly ported, or the Task was not created)."
        )
        dictionaries = compare_dictionaries(created_task, expected_values, key_list)
        self.assertTrue(
            dictionaries[0],
            "List of discrepencies between received values and expected values: %s " % (dictionaries[1:])
        )

    def test_task_to_build_cart(self): #Upon pressing build cart, the tile should be moved to the Build Cart Stage.
        _logger.warning("Product Rec's Type is %s" % self.product_rec.type)
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