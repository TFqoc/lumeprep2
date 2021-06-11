from odoo import models, fields, api
import requests
import json
import logging

logger = logging.getLogger(__name__)


apiKey = "3QhFhyh3Qj5t49RYrcqDn6WGItlFeQY41gBuAE8q"
authToken = "5a0d9d3e595c323c82c412649a7ca2b3"
url = "https://staging.springbig.technology"

global_headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'AUTH-TOKEN': authToken, 'x-api-key': apiKey}

class Customer(models.Model):
    _inherit = "res.partner"
    
    spring_big_registered = fields.Boolean(readonly=True)

    def check_in(self):
        res = super(Customer, self).check_in()
        logger.info("SB: Checking if customer exists")
        if not self.spring_big_registered:
            # Check if customer exists
            data = {"phone_number": self.phone}
            response = requests.get(url + '/api/pos/v1/members',
                            params=data,
                            headers=global_headers)
            if response.status_code != 200:
                #if not, then create customer
                logger.info("SB: Creating customer")
                name = self.name.split(' ')
                creation_data = {
                    "pos_user": str(self.id),
                    "pos_type": "lume-odoo",
                    "phone_number": self.phone,
                    "first_name": name[0],
                    "last_name": name[1:],
                    "email": self.email,
                    "address1": self.street,
                    "address2": self.street2,
                    "city": self.city,
                    "zip": self.zip,
                    "birthday": self.date_of_birth.strftime("%Y-%m-%d"),
                    "medical_card_expiration": self.medical_expiration.strftime("%Y-%m-%d") if self.medical_expiration else '',
                    # "interest_list": "baseball, also-dope-store",
                    # "location_list": "dope-dope-store, also-dope-store",
                    # "discount_list": "senior, veteran, human",
                    "gender": "other",
                    # "purpose": "recreational",
                    "url_encoded": "true",
                    "allowed_email": "true"
                }
                # TODO What if the request fails?
                result = requests.post(url + '/api/pos/v1/members',
                            json=creation_data,
                            headers=global_headers)
                logger.info("SB: Result of creation: %s" % result.json())
            self.spring_big_registered = True
        return res

class Sale(models.Model):
    _inherit = 'sale.order'

    @api.model
    def finalize(self, order_id, data):
        res = super(Sale, self).finalize(order_id, data)
        # Report visit to spring big
        data = {
            "pos_id": self.id,
            "pos_user": str(self.partner_id.id),
            "pos_type": "lume-odoo",
            "transaction_date": fields.Datetime.now().isoformat(),
            "transaction_total": self.amount_total,
            "order_source": 2, #What is this
            "send_notification": False,
            "location": self.task.project_id.name,
            "url_encoded": True,
            "visit_detail_attributes": [],
        }
        for line in self.order_line:
            line_data = {
                "sku": line.product_id.default_code,
                "price": line.price_unit,
                "quantity": line.product_uom_qty,
                "category": "None",
                "brand": line.product_id.brand,
                "name": line.product_id.name,
                "discount": 0,#TBD as far as where this value will come from
            }
            data['visit_detail_attributes'].append(line_data)
        
        response = requests.post(url + '/api/pos/v1/visits',
                            json=data,
                            headers=global_headers)
        # TODO What happens if the request fails for any reason?
        logger.info("SB Create Visit Request: %s" % data)
        logger.info("SB Create Visit Response: %s" % response.json())
        
        return res