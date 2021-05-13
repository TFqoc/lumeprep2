import logging
from . test_lumesales_base import TestLumeSaleCommon
from odoo.tests.common import tagged

_logger = logging.getLogger(__name__)

@tagged('lume')
class TestComputedFields(TestLumeSaleCommon):
    def test_is_banned(self):
        self.assertTrue(
            self.customer_banned.is_banned, 
            "Error in is_banned computed field: Customer was not banned despite having three or more strikes."
        )
        _logger.info("Test Is Banned Status: Complete.")

    def test_compute_21(self):
        self.assertTrue(
            self.customer_rec.is_over_21,
            "Error in compute_21 computed field: Customer does not register as over age despite being far older."
        )
        _logger.info("Test Compute Twenty-One Status: Complete.")

    # def test_lume_testing(self):
    #     self.assertTrue(False, "This should always fail.")
    #     _logger.info("Lume Tests are Running.")

@tagged('lume')
class TestCustomerProfile(TestLumeSaleCommon):
    def test_warn(self):
        #Class is set up with the data before the test.

        record_ids = [self.customer_rec.id] #Id of the record being manipulated.
        uid = self.env.ref('base.user_admin').id #Id of the user doing the action.
        self.env['res.partner'].browse(record_ids).with_context({
            'allowed_company_ids': [1],
            'lang': 'en_US',
            'tz': 'Europe/Brussels',
            'uid': uid}).with_user(uid).warn()

        #The result is tested. If the result is what is expected, the test passes. If the result is unexpected, the test fails.
        self.assertEqual(
            self.customer_rec.warnings,  
            1, 
            "Error in Partner Model: Number of warnings does not increase with the current method."
        )
        _logger.info("Test Warn Status: Complete.") 

    def test_warn_test(self):
        self.assertEqual(
            self.customer_rec.warnings,  
            1, 
            "Error in Partner Model: Number of warnings does not increase with the current method."
    
    