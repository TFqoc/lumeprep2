from odoo import models, fields, api
import datetime
import logging

_logger = logging.getLogger(__name__)

class Tasks(models.Model):
    _name = 'project.task'
    _inherit = ['project.task','barcodes.barcode_events_mixin']
    _description = 'project.task'

    name = fields.Char(required=False)
    sales_order = fields.Many2one(comodel_name="sale.order", readonly=True)
    dummy_field = fields.Char(compute='_compute_dummy_field',store=False)
    scan_text = fields.Char()
    # stage_id = fields.Many2one(readonly=True)
    # show_customer_form = fields.Boolean(compute='_compute_show_customer_form')

    order_type = fields.Selection(selection=[('store','In Store'),('delivery','Delivery'),('online','Website')], default='store')

    def on_barcode_scanned(self, barcode):
        _logger.info("BARCODE SCANNED")
        if self.partner_id:
            self.show_customer_form = True
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'res.partner',
                'target': 'new', #for popup style window
                'res_id': self.partner_id.id
            }
        # raise NotImplementedError("In order to use barcodes.barcode_events_mixin, method on_barcode_scanned must be implemented")

    @api.onchange('scan_text')
    def auto_fill(self):
        text = self.scan_text
        if not text:
            return
        else:
            self.scan_text = False
        data = self.parse_barcode(text)[1]

        customer_id = ""
        record_exists = self.env['res.partner'].search([['drivers_license_number','=',data['drivers_license_number']]])
        if len(record_exists) > 0:
            customer_id = record_exists[0].id

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

        # self.name = "Customer Order #" + str(self.project_id.task_number)
        # self.project_id.task_number += 1
        self.partner_id = customer_id

        # Open the customer profile in windowed popup
        return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'res.partner',
                'target': 'new', #for popup style window
                'res_id': customer_id,
            }

    # @api.depends('partner_id')
    # def _compute_show_customer_form(self):
    #     if self.partner_id:
    #         self.show_customer_form = True
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'res.partner',
    #             'target': 'new', #for popup style window
    #             'res_id': self.partner_id.id
    #         }
    #     else:
    #         self.show_customer_form = False

    @api.model
    def create(self, vals):
        _logger.info("CREATE NEW TASK")
        project = self.env['project.project'].browse(vals['project_id'])
        vals['name'] = "Customer Order #" + str(project.task_number)
        project.task_number += 1
        res = super(Tasks, self).create(vals)
        res.action_timer_start()
        return res

    def get_message_count(self, id): #called from js widget for display purposes
        return self.browse(id).message_unread_counter
    
    def _compute_dummy_field(self):
        # Mail module > models > mail_channel.py Line 743
                # active_id = self.env.context.get('active_ids', []) #gets id of task
        # self.env['mail.channel'].search([''])   #channel_seen(None)
        message_id = self.message_ids[0].id
        for channel in self.message_channel_ids:
            channel.channel_seen(message_id) #should be the id of the message to be marked as seen.

        self.dummy_field = 'dummy'

    def build_cart(self):
        self.sales_order = self.env['sale.order'].create({
            'partner_id':self.partner_id.id,
            'task':self.id,
            'date_order': fields.datetime.now(),
            # 'picking_policy':'direct',
            # 'pricelist_id':'idk',
            # 'warehouse_id':'',
        })
        self.next_stage()
        # Open up the sale order we just created
        return {
            "type":"ir.actions.act_window",
            "res_model":"sale.order",
            "res_id":self.sales_order.id,
            "views":[[False, "form"]],
        }

    def next_stage(self):
        if self.stage_id.name == 'Done':
            return

        get_next = False
        for stage in self.project_id.type_ids:
            if get_next:
                self.stage_id = stage
                break
            elif stage == self.stage_id:
                get_next = True


    # Mail module > models > mail_channel.py Line 758

    @api.model
    def delete_recent(self):
        target_record = self.env['project.task'].search([], order='id desc')[0]
        # target_record = self.env['project.task'].browse(ids)[0]
        target_record.unlink()

    @api.onchange('stage_id')
    def change_stage(self):
        new_stage = self.stage_id.name
        old_stage = self._origin.stage_id.name
        self._origin.stage_id = self.stage_id
        _logger.info("Timer Vals: %s %s",self.user_timer_id.timer_start,self.display_timesheet_timer)
        if self.user_timer_id.timer_start or self.display_timesheet_timer:
            _logger.info("STOPPING TIMER")
            self._origin.action_timer_auto_stop(old_stage+" > "+new_stage)
        if not self.stage_id.is_closed:
            self._origin.action_timer_start()
        
        return {
    'warning': {'title': "Info", 'message': old_stage+" > "+new_stage, 'type': 'notification'},
}

        # if new_stage is 'Check In':
        #     pass
        # elif new_stage is 'Build Cart':
        #     if old_stage is 'Check In':
        #         self.action_timer_start()
        #         pass
        #     pass
        # elif new_stage is 'Fulfilment':
        #     if old_stage is 'Build Cart':
        #         self.action_timer_auto_stop()
        #     pass
        # elif new_stage is 'Check Out':
        #     pass
        # elif new_stage is 'Done':
        #     self.action_timer_auto_stop()
        #     pass
    
    def save_timesheet(self, minutes, desc=None):
        values = {
            'task_id': self.id,
            'project_id': self.project_id.id,
            'date': fields.Date.context_today(self),
            'name': desc or "",
            'user_id': self.env.uid,
            'unit_amount': minutes,
        }
        self.user_timer_id.unlink()
        return self.env['account.analytic.line'].create(values)

    def action_timer_auto_stop(self, desc=None):
        # timer was either running or paused
        _logger.info("ACTION TIMER AUTO STOP: "+str(desc))
        _logger.info("VALS: %s %s",self.user_timer_id.timer_start, self.display_timesheet_timer)
        if self.user_timer_id.timer_start and self.display_timesheet_timer:
            minutes_spent = self.user_timer_id._get_minutes_spent()
            minimum_duration = int(self.env['ir.config_parameter'].sudo().get_param('hr_timesheet.timesheet_min_duration', 0))
            rounding = int(self.env['ir.config_parameter'].sudo().get_param('hr_timesheet.timesheet_rounding', 0))
            minutes_spent = self._timer_rounding(minutes_spent, minimum_duration, rounding)
            self.save_timesheet(minutes_spent * 60 / 3600, desc)
            #return self._action_open_new_timesheet(minutes_spent * 60 / 3600)
        #return False

    def parse_barcode(self, code):
        # @\n\u001e\rANSI 636031080102DL00410270ZW03110017DLDCAD\nDCBB\nDCDNONE\nDBA02092025\nDCSFULLMER\nDACTRISTAN\nDADJAMES\nDBD03022017\nDBB02091996\nDBC1\nDAYBLU\nDAU069 IN\nDAG147 E KLUBERTANZ DR\nDAISUN PRAIRIE\nDAJWI\nDAK535901448  \nDAQF4568109604909\nDCFOTWJH2017030215371750\nDCGUSA\nDDEN\nDDFN\nDDGN\nDCK0130100071337399\nDDAN\nDDB09012015\rZWZWA13846120417\r
        dlstring = code
        # dlstring = dlstring.split('0010') #Used for when the code is scanned from an apple device or from a linux device.
        if dlstring.__contains__('\n'): 
             dlstring = dlstring.split('\n') #the characters \ and n are literally in the string in my test.
        elif dlstring.__contains__('0010'):
             dlstring = dlstring.split('0010') #Used for when the code is scanned from an apple device or from a linux device.
        else: 
            _logger.debug("Barcode failed to parse." + str(dlstring))
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

class project_inherit(models.Model):
    _inherit = 'project.project'

    task_number = fields.Integer(default=0)# Used to generate a task name
    # store = fields.Many2one(comodel_name='lume.store')