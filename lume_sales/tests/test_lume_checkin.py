import logging
from . test_lumesales_base import TestLumeSaleCommon
from odoo.tests.common import tagged
from ..models.barcode_parse import parse_code
from . test_lumesales_base import compare_dictionaries

_logger = logging.getLogger(__name__)

@tagged('lume')
class TestCheckIn(TestLumeSaleCommon):
    def test_rec_checkin(self):
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

        key_list = ['partner_id', 'project_id', 'fulfillment_type', 'order_type', 'user_id', 'name']
        expected_values = {
            'partner_id': self.customer_rec,
            'project_id': self.lumestore_one, 
            'fulfillment_type': 'store',
            'order_type': False,
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

    def test_med_checkin(self):
        record_ids = [self.customer_med.id]
        uid = self.env.ref('base.user_admin').id
        self.env['res.partner'].browse(record_ids).with_context({
            'allowed_company_ids': [1],
            'check_in_window': True,
            'fulfillment_type': 'store',
            'lang': 'en_US',
            'order_type': 'adult',
            'partner_id': self.customer_med.id,
            'project_id': self.lumestore_one.id,
            'tz': 'Europe/Brussels',
            'uid': uid}).with_user(uid).check_in()

        # TODO: Refine how the test finds this task, as this can fail too easily.
        created_task = self.env['project.task'].search([('partner_id', '=', self.customer_med.id.id)])

        key_list = ['partner_id', 'project_id', 'fulfillment_type', 'order_type', 'user_id', 'name']
        expected_values = {
            'partner_id': self.customer_med.id,
            'project_id': self.lumestore_one, 
            'fulfillment_type': 'store',
            'order_type': False,
            'user_id': False,
            'name': self.customer_med.id.name
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

    # def test_med_under_21_checkin(self):
    #     self.assertTrue(False, "Do this test.")

    # def test_expired_dl(self):
    #     self.assertTrue(False, "Do this test.")

    # def test_expired_med_id(self):
    #     self.assertTrue(False, "Do this test.")

    # def test_banned_checkin(self):
    #     self.assertTrue(False, "Do this test.")

    # def test_under_eighteen_checkin(self):
    #     self.assertTrue(False, "Do this test.")

    # def test_under_21_checkin(self):
    #     self.assertTrue(False, "Do this test.")

    

@tagged('lume')
class TestBarcodeParse(TestLumeSaleCommon):
    def test_mi_barcode_parse(self):
        """Checking that the barcode parses correctly."""
        barcode = '@ANSI 636032030102DL00410205ZM03460027DLDCADCBDCDDBA12312021DCSLOVEDCTEVE ADBDDBB02171987DBC2DAYDAUDAG629 MAD DOG LANEDAIDETROITDAJMIDAK482010001  DAQC 333 547 393 957DCFDCGUSADCHDAHDCKDDAN'
        parsed_barcode = parse_code(barcode)
        key_list = ['name', 'street', 'city', 'zip', 'date_of_birth', 'drivers_license_expiration', 'drivers_license_number']

        dictionaries = compare_dictionaries(parsed_barcode, self.customer_rec, key_list)


        self.assertTrue(
            dictionaries[0],
            "List of errors: %s " % (dictionaries[1:])
        )

        self.assertEqual(                  #As the State Field is not yet transfered to an ID, it should be MI.
            parsed_barcode['state_id'],
            'MI',
            "Error in Barcode Parse: the state id was %s instead of MI." % (parsed_barcode['state_id'])
        )

    def test_wi_barcode_parse(self):
        barcode = '@ANSI 636031080102DL0041W03070017DLDCADDCBNONEDCDNONEDBA12312021DCSTHYMEDACJUSTINDADNICKDBD05052001DBB10211999DBC1DAYHAZDAU072 INDAG404 ELECTRIC AVENUEDAIMADISONDAJWIDAK535900001DAQF672554568631DCFNDCGUSADDENDDFNDDGNDCKNDDAFDDB06182021ZWZWA13255171875'
        parsed_barcode = parse_code(barcode)
        key_list = ['name', 'street', 'city', 'zip', 'date_of_birth', 'drivers_license_expiration', 'drivers_license_number']

        dictionaries = compare_dictionaries(parsed_barcode, self.customer_pat, key_list)

        self.assertTrue(
            dictionaries[0],
            "List of errors: %s " % (dictionaries[1:])
        )

        self.assertEqual(                  #As the State Field is not yet transfered to an ID, it should be MI.
            parsed_barcode['state_id'],
            'WI',
            "Error in Barcode Parse: the state id was %s instead of WI." % (parsed_barcode['state_id'])
        )