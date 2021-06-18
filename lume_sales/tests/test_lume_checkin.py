import logging
from . test_lumesales_base import TestLumeSaleCommon
from odoo.tests.common import tagged
from ..models.barcode_parse import parse_code
from . test_lumesales_base import compare_dictionaries

_logger = logging.getLogger(__name__)

@tagged('lume')
class TestCheckIn(TestLumeSaleCommon):
    def shut_up_pylance(self):
        pass

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
        barcode = '@ANSI 636031080102DL0041W03070017DLDCADDCBNONEDCDNONEDBA12312021DCSTHYMEDACJUSTINDADNICKDBD05052001DBB10211999DBC1DAYHAZDAU072 INDAG 404 ELECTRIC AVENUEDAI MADISONDAJWIDAK535900001DAQF672554568631DCFNDCGUSADDENDDFNDDGNDCKNDDAFDDB06182021ZWZWA13255171875'
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