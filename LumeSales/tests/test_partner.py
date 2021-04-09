from odoo.tests.common import TransactionCase #Gives the file the transaction base framework.
from odoo import models, fields, api
import datetime
import logging


_logger = logging.getLogger(__name__)

# class Partner(models.Model):
#     _inherit = 'res.partner'

#     is_medical = fields.Boolean()
#     medical_id = fields.Char()
#     medical_expiration = fields.Date()
#     date_of_birth = fields.Date()
#     is_over_21 = fields.Boolean(compute='_compute_21')
#     drivers_license_number = fields.Char()
#     drivers_license_expiration = fields.Date()

#     last_visit = fields.Datetime()

#     warnings = fields.Integer()
#     is_banned = fields.Boolean(compute='_compute_banned', default=False)

#     @api.depends('date_of_birth')#will be accurate when dob is entered, but not if they later become 21
#     def _compute_21(self):
#         for record in self:
#             if record.date_of_birth is False:# In case dob is not set yet
#                 record.is_over_21 = False
#             else:
#                 difference_in_years = (datetime.date.today() - record['date_of_birth']).days / 365.25
#                 record['is_over_21'] = difference_in_years >= 21


#     @api.depends('warnings')
#     def _compute_banned(self):
#         for record in self:
#             record.is_banned = self.warnings >= 3
    
#     def warn(self):
#         self.warnings += 1

#     def verify_address(self):
#         pass


#Jacob's Note: In order to run the tests I would need to figure out a way to bypass the framework,
# and the time it would take to learn how to bypass it would be better spent learning how to use it.
class Test_Partner(TransactionCase):

    # The below method would be used to imput the data into the system.

    @classmethod 
    def setUpClass :

    # Below would take the data used from above, and input it through the run 

    def test_compute_banned(self):
        self.Partner._compute_banned
        self.Partner.assertTrue(self.record.is_banned == True, 'Customer should be banned.')
