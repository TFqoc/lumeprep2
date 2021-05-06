import logging
from . test_lumesales_base import TestLumeSaleCommon

_logger = logging.getLogger(__name__)

class TestLumePerms(TestLumeSaleCommon):
    def setUp(self):
        super().setUp()