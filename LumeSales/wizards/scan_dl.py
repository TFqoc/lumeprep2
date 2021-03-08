from odoo import models, fields, api
import datetime

class ScanDL(models.TransientModel):
    _name = "scan_dl"
    _description = "scan_dl"

    #image = fields.Binary("Image", help="Select image here")
    #<field name="image" widget='image' />
    raw_text = fields.Char("Raw Text")

    @api.model
    def create(self, vals_list):
        # Delete the duplicate task that was created just before this menu popped up
        self.env['project.task'].delete_recent()
        self.raw_text = "Created"
        return super(ScanDL, self).create(vals_list)

    def confirm_action(self):
        #https://github.com/abbasbeydoun/Python-PDF417-Driver-s-License-decoder/blob/master/decoder.py
        #Test DL data
        x="""
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
        # @\n\u001e\rANSI 636031080102DL00410270ZW03110017DLDCAD\nDCBB\nDCDNONE\nDBA02092025\nDCSFULLMER\nDACTRISTAN\nDADJAMES\nDBD03022017\nDBB02091996\nDBC1\nDAYBLU\nDAU069 IN\nDAG147 E KLUBERTANZ DR\nDAISUN PRAIRIE\nDAJWI\nDAK535901448  \nDAQF4568109604909\nDCFOTWJH2017030215371750\nDCGUSA\nDDEN\nDDFN\nDDGN\nDCK0130100071337399\nDDAN\nDDB09012015\rZWZWA13846120417\r
        ids = self.env.context.get('active_ids', [])
        target_record = self.env['project.task'].browse(ids)[0]

        meta, data = self.parse_barcode(self.raw_text)
        
        customer_id = ""
        record_exists = self.env['res.partner'].search([['drivers_license_number','=',data['drivers_license_number']]])
        if len(record_exists) > 0:
            customer_id = record_exists[0].id

            # message_id = self.env['message.wizard'].create({'message': ("Selecting Customer " + record_exists[0].name + str(customer_id))})
            # return {
            #     'name': ('Customer'),
            #     'type': 'ir.actions.act_window',
            #     'view_mode': 'form',
            #     'res_model': 'message.wizard',
            #     # pass the id
            #     'res_id': message_id.id,
            #     'target': 'new'
            # }
        else: #create new customer, then create task
            new_customer = self.env['res.partner'].create({
                'name': data['name'],
                'street': data['street'],
                'city': data['city'],
                'state_id': data['state_id'].id,
                'zip': data['zip'],
                'date_of_birth': data['date_of_birth'],
                'drivers_license_expiration': data['drivers_license_expiration'],
                'drivers_license_number': data['drivers_license_number']
            })
            customer_id = new_customer.id

        target_record.name = "Customer Order #" + str(target_record.project_id.task_number)
        target_record.project_id.task_number += 1
        target_record.partner_id = customer_id
        #target_record.unlink()

        # Open the customer profile in windowed popup
        return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'res.partner',
                'target': 'new', #for popup style window
                'res_id': customer_id,
            } 

    def parse_barcode(self, code):
        dlstring = code
        dlstring = dlstring.split('\\n') #the characters \ and n are literally in the string in my test.
        dlstring = dlstring[2:]
        dlstring = [line.strip() for line in dlstring]

        # remove 'ANSI' from first element (It's a fixed header)
        dlstring[0] = dlstring[0][5:]

        metadata = dlstring[0]

        dlstring.remove(metadata)

        meta = {}
        meta['IIN'] = metadata[0:6] # Issuer Identification Number
        meta['AAMVAV'] = metadata[6:8] # AAMVA Version Number
        meta['JV'] = metadata[8:10] # Jurisdiction Version Number
        meta['entries'] = metadata[10:12] # Number of Entries
        meta['DL'] = metadata[12:14]
        meta['offset'] = metadata[14:18] # offset for this subfile
        meta['subfile_length'] = metadata[18:22]
        meta['DCA'] = metadata[27:] # Jurisdiction specific vehicle class

        data = {}
        fname = ""
        lname = ""
        for field in dlstring:
            fieldID = field[0:3]
            fieldValue = field[3:]

            if fieldID == 'DAC': #first name
                fname = fieldValue.capitalize()
                #raise Warning("Name is: " + fieldValue)
            elif fieldID == 'DCS': #last name
                lname = fieldValue.capitalize()
            elif fieldID == 'DAD': #middle name
                #contact.name = fname + " " + fieldValue.capitalize() + " " + lname
                data['name'] = fname + " " + fieldValue.capitalize() + " " + lname
            elif fieldID == 'DAG': #Address line 1
                words = fieldValue.split(' ')
                street = ""
                for w in words:
                    street = " ".join([street,w.capitalize()])
                #contact.street = street
                data['street'] = street
            elif fieldID == 'DAI': # City name
                words = fieldValue.split(' ')
                city = ""
                for w in words:
                    city = " ".join([city,w.capitalize()])
                #contact.city = city
                data['city'] = city
            elif fieldID == 'DAJ': # Need to figure out state ID
                #contact.state_id = self.env['res.country.state'].search(["&",["code","=",fieldValue],"|",["country_id.name","=","United States"],["country_id.name","=","Canada"]])
                data['state_id'] = self.env['res.country.state'].search(["&",["code","=",fieldValue],"|",["country_id.name","=","United States"],["country_id.name","=","Canada"]])
            elif fieldID == 'DAK': #ZIP code
                #contact.zip = fieldValue[:5] + '-' + fieldValue[5:]
                data['zip'] = fieldValue[:5] + '-' + fieldValue[5:]
            elif fieldID == 'DBB': #date of birth in numbers
                month = int(fieldValue[:2])
                day = int(fieldValue[2:4])
                year = int(fieldValue[4:])
                #contact.date_of_birth = datetime.date(year, month, day)
                data['date_of_birth'] = datetime.date(year, month, day)
            elif fieldID == 'DBA': #DL expiration Date
                month = int(fieldValue[:2])
                day = int(fieldValue[2:4])
                year = int(fieldValue[4:])
                #contact.drivers_license_expiration = datetime.date(year, month, day)
                data['drivers_license_expiration'] = datetime.date(year,month,day)
            elif fieldID == 'DAQ': # DL number
                #contact.drivers_license_number = fieldValue
                data['drivers_license_number'] = fieldValue
        return meta, data
