from odoo import models, fields, api
from onfleet import Onfleet
from onfleet import RateLimitError
import json
import logging

_logger = logging.getLogger(__name__)

class OnFleet():
    api_key = ''
    api = None
    connected = False
    last_error = ''

    def connect(self, key):
        self.api_key = key
        try:
            self.api = Onfleet(api_key=self.api_key)
            auth_test = self.api.auth_test()
            if auth_test.get('message', '').startswith("Hello"):
                self.connected = True
                self.last_error = ''
            else:
                self.connected = False
                self.last_error = "Code: %s\nMessage: %s" % (auth_test.get('code', ''), auth_test.get('message',''))
                _logger.error(self.last_error)
        except RateLimitError as e:
            self.connected = False
            self.last_error = f"Error: {e}"
            _logger.error("""Rate Limit Error: To many requests are being made to OnFleet. This means that Odoo + Treez are making more than 20 requests per second.\n
                Please slow down calls to OnFleet\n
                Status: %s\n
                Message: %s\n
                Request: %s\n
                """ % (e.message, e.status, e.request))
        except Exception as e:
            self.connected = False
            self.last_error = f"Error: {e}"
            _logger.warning("Failed to connect to onfleet: %s" % (self.last_error))
        

_onfleet = OnFleet()

def parse_phone(number):
    if len(number) != 10:
        return number
    return f"{number[:3]}-{number[3:7]}-{number[7:]}"

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    onfleet_task_id = fields.Char()
    onfleet_pending_request = fields.Char()
    onfleet_has_pending_request = fields.Char()
    
    def check_onfleet_connection(self):
        if not _onfleet.connected:
            # Get setting info here
            ICPSudo = self.env['ir.config_parameter'].sudo()
            key = ICPSudo.get_param('onfleet_lume.onfleet_api_key')
            _onfleet.connect(key)
            # May need to wait here a bit to ensure time to connect
            return _onfleet.connected
        else:
            return True

    # Override
    def on_fulfillment(self):
        res = super().on_fulfillment()
        for order in self:
            # Create notes for order lines
            notes = ""
            total_qty = 0
            for line in order.order_line:
                notes += "%s qty.\n%s\nUnit Price: $%.2f\n%s\n" % (line.product_uom_qty, line.product_id.name, line.price_unit,line.lot_id.name)
                total_qty += line.product_uom_qty
            notes += "Total items: %.0f\n\nSubtotal: $%.2f" % (total_qty, order.amount_untaxed)

            b = {
                "destination": {
                    "address":{
                        "unparsed": "%s, %s, %s" % (self.street,self.zip,'USA'),
                        "apartment": self.street2 or ''# Used for line 2 of street address
                    }
                },
                "recipients": [{"name":self.partner_id.name,"phone":parse_phone(self.partner_id.phone)}],
                "notes": notes
            }
            # Sumbit order
            if order.check_onfleet_connection():
                _logger.info(f"OnFleet Create Task Request: {b}")
                r = _onfleet.api.tasks.create(body=b)
                _logger.info(f"Response: {r}")
                # Check for errors here
                if len(r['destination'].get('warnings',[])) > 0:
                    pass
                order.onfleet_task_id = r.get('shortID\d', False)
            else:
                # Do something with failed connection
                _logger.info("Connection to OnFleet Failed")
                self.onfleet_pending_request = json.dumps(b)
                self.onfleet_has_pending_request = True
                pass
        return res

    def retry_request(self):
        self.ensure_one()
        if self.onfleet_has_pending_request and self.onfleet_pending_request:
            b = json.loads(self.onfleet_pending_request)
            if self.check_onfleet_connection():
                _logger.info(f"OnFleet Create Task Retry Request: {b}")
                r = _onfleet.api.tasks.create(body=b)
                _logger.info(f"Response: {r}")
                # Check for errors here
                if len(r['destination'].get('warnings',[])) > 0:
                    pass
                self.onfleet_task_id = r.get('shortID\d', False)
                self.onfleet_has_pending_request = False
                self.onfleet_pending_request = ""