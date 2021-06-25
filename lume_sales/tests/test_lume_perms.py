import logging
from . test_lumesales_base import TestLumeSaleCommon
from odoo.tests.common import tagged

_logger = logging.getLogger(__name__)

@tagged('lume') 
class TestLumePerms(TestLumeSaleCommon):
    def setUp(self):
        super().setUp()