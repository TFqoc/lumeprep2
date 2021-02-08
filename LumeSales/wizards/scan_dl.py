from odoo import models, fields

class ScanDL(models.TransientModel):
    _name = "scan_dl"
    _description = "scan_dl"

    #image = fields.Binary("Image", help="Select image here")
    #<field name="image" widget='image' />
    raw_text = fields.Char("Raw Text")

    def confirm_action(self):
        #https://github.com/abbasbeydoun/Python-PDF417-Driver-s-License-decoder/blob/master/decoder.py
        #Test DL data
        """
        {
        "BarcodeFormat": 33554432,
        "BarcodeFormatString": "PDF417",
        "BarcodeFormat_2": 0,
        "BarcodeFormatString_2": "No Barcode Format in group 2",
        "BarcodeText": "@\n\u001e\rANSI 636031080102DL00410270ZW03110017DLDCAD\nDCBB\nDCDNONE\nDBA02092025\nDCSFULLMER\nDACTRISTAN\nDADJAMES\nDBD03022017\nDBB02091996\nDBC1\nDAYBLU\nDAU069 IN\nDAG147 E KLUBERTANZ DR\nDAISUN PRAIRIE\nDAJWI\nDAK535901448  \nDAQF4568109604909\nDCFOTWJH2017030215371750\nDCGUSA\nDDEN\nDDFN\nDDGN\nDCK0130100071337399\nDDAN\nDDB09012015\rZWZWA13846120417\r",
        "BarcodeBytes": "QAoeDUFOU0kgNjM2MDMxMDgwMTAyREwwMDQxMDI3MFpXMDMxMTAwMTdETERDQUQKRENCQgpEQ0ROT05FCkRCQTAyMDkyMDI1CkRDU0ZVTExNRVIKREFDVFJJU1RBTgpEQURKQU1FUwpEQkQwMzAyMjAxNwpEQkIwMjA5MTk5NgpEQkMxCkRBWUJMVQpEQVUwNjkgSU4KREFHMTQ3IEUgS0xVQkVSVEFOWiBEUgpEQUlTVU4gUFJBSVJJRQpEQUpXSQpEQUs1MzU5MDE0NDggIApEQVFGNDU2ODEwOTYwNDkwOQpEQ0ZPVFdKSDIwMTcwMzAyMTUzNzE3NTAKRENHVVNBCkRERU4KRERGTgpEREdOCkRDSzAxMzAxMDAwNzEzMzczOTkKRERBTgpEREIwOTAxMjAxNQ1aV1pXQTEzODQ2MTIwNDE3DQ==",
        "LocalizationResult": {
            "TerminatePhase": 32,
            "BarcodeFormat": 33554432,
            "BarcodeFormatString": "PDF417",
            "BarcodeFormat_2": 0,
            "BarcodeFormatString_2": "No Barcode Format in group 2",
            "Angle": 180,
            "ResultPoints": [
            "92, 21",
            "4, 21",
            "4, 4",
            "92, 4"
            ],
            "ModuleSize": 8,
            "PageNumber": 0,
            "RegionName": "",
            "DocumentName": null,
            "ResultCoordinateType": 1,
            "Confidence": 84
        },
        "Exception": null
        }
        """
        contact_ids = self.env.context.get('active_ids', [])
        contact = self.env['res.partner'].browse(contact_ids)

        dlstring = self.raw_text
        dlstring = dlstring.split('\\n') #the characters \ and n are literally in the string in my test.
        dlstring = dlstring[2:]
        dlstring = [line.strip() for line in dlstring]

        # remove 'ANSI' from first element (It's a fixed header)
        dlstring[0] = dlstring[0][5:]

        metadata = dlstring[0]

        dlstring.remove(metadata)

        IIN = metadata[0:6]  # Issuer Identification Number
        AAMVAV = metadata[6:8]  # AAMVA Version number
        JV = metadata[8:10]  # Jurisdiction Version number
        entries = metadata[10:12]  # Number of entries

        DL = metadata[12:14]

        offset = metadata[14:18]  # offset for this subfile
        subfile_length = metadata[18:22]

        DCA = metadata[27:]  # Jurisdiction specific vehicle class

        for field in dlstring:
            fieldID = field[0:3]
            fieldValue = field[3:]

            if fieldID == 'DCT':
                contact.name = fieldValue
            # if fieldID == 'DCB':
            #     decodedfile.write('Jurisdiction specific restriction codes: ')
            # elif fieldID == 'DCD':
            #     decodedfile.write('Jurisdiction specific endorsement codes: ')
            # elif fieldID == 'DBA':
            #     decodedfile.write('Document Expiration date: ')
            # elif fieldID == 'DCS':
            #     decodedfile.write('Customer Family Name: ')
            # elif fieldID == 'DCT':
            #     decodedfile.write('Customer Given Name: ')
            # elif fieldID == 'DBD':
            #     decodedfile.write('Document Issue Date: ')
            # elif fieldID == 'DBB':
            #     decodedfile.write('Date of Birth: ')
            # elif fieldID == 'DBC':
            #     decodedfile.write('Sex: ')  # 1 for male, 2 for female
            # elif fieldID == 'DAY':
            #     decodedfile.write('Eye Color: ')
            # elif fieldID == 'DAU':
            #     decodedfile.write('Height: ')
            # elif fieldID == 'DAG':
            #     decodedfile.write('Address Line 1: ')
            # elif fieldID == 'DAI':
            #     decodedfile.write('City: ')
            # elif fieldID == 'DAJ':
            #     decodedfile.write('State: ')
            # elif fieldID == 'DAK':
            #     decodedfile.write('Postal Code: ')
            # elif fieldID == 'DAQ':
            #     decodedfile.write('Customer ID Number: ')
            # elif fieldID == 'DCF':
            #     decodedfile.write('Document Discriminator: ')
            # elif fieldID == 'DCG':
            #     decodedfile.write('Country Identification: ')
            # elif fieldID == 'DCK':
            #     decodedfile.write('Inventory control number: ')