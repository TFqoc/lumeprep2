from odoo import models, fields, api
from onfleet import Onfleet

class OnFleet():
    api_key = ''
    api = None
    connected = False
    last_error = ''

    def connect(self, key):
        self.api_key = key
        try:
            self.api = Onfleet(api_key=self.api_key)
            self.connected = True
            self.last_error = ''
        except Exception as e:
            self.connected = False
            self.last_error = f"Error: {e}"
        

_onfleet = OnFleet()

def parse_phone(number):
    if len(number) != 10:
        return number
    return f"{number[:3]}-{number[3:7]}-{number[7:]}"

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
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
                notes += "%s qty.\n%s\n%s\n%s\n" % (line.product_uom_qty, line.product_id.name, line.price_unit,line.lot_id.name)
                total_qty += line.product_uom_qty
            notes += "Total items: %s\n\nSubtotal: $%.2f" % (total_qty, order.amount_untaxed)

            # Sumbit order
            r = _onfleet.api.tasks.create(body={
                "destination": {
                    "address":{
                        "unparsed": "%s, %s, %s" % (self.street,self.zip,'USA'),
                        "apartment": self.street2 # Used for line 2 of street address
                    }
                },
                "recipients": [{"name":self.partner_id.name,"phone":parse_phone(self.partner_id.phone)}],
                "notes": notes
            })
            # Check for errors here
            if len(r['warnings']) > 0:
                pass
        return res