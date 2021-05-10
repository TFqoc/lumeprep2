import logging
from . test_lumesales_base import TestLumeSaleCommon

_logger = logging.getLogger(__name__)

class TestComputedFields(TestLumeSaleCommon):
    def test_is_banned(self):
        self.assertTrue(
            self.customer_banned.is_banned, 
            "Error in is_banned computed field: Customer was not banned despite having three or more strikes."
        )

    def test_compute_21(self):
        self.assertTrue(
            self.customer_rec.is_over_21,
            "Error in compute_21 computed field: Customer does not register as over age despite being far older."
        )
        
    def test_lume_testing(self):
        self.assertTrue(False, "This should always fail.")

class TestCustomerProfile(TestLumeSaleCommon):
    def test_warn(self):
        self.customer_rec.warn
        self.assertEqual(
            self.customer_rec.warn,  
            1, 
            "Error in Partner Model: Number of warnings does not increase with the current method."
        )
    
    