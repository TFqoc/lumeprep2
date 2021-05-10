from odoo.tests.common import SavepointCase, tagged
from odoo.exceptions import UserError
import datetime
import logging

_logger = logging.getLogger(__name__)

@tagged('lume')
class TestLumeSaleCommon(SavepointCase): 
    
    @classmethod #Creates the base data for the tests to use.
    def setUpClass(cls): 
        super(TestLumeSaleCommon, cls).setUpClass()

        #Here is where each group of users is created as to test permissions. Each group of permissions must be defined using env.res.

        #user_group_associate = cls.env.res('Permissions Group Goes Here')
        #user_group_manager = cls.env.res('Permissions Group Goes Here')
        #user_group_district_manager = cls.env.res('Permissions Group Goes Here')

        _logger.info("Setting up data for Lume Test.")

        Users = cls.env['res.users'].with_context({'no_reset_password': True})

        cls.user_receptionist = Users.create({
            'name': 'Pete Zeria',
            'login': 'pzlume',
            'email': 'p.z@example.com',
            'signature': 'Pete Zeria',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

        cls.user_luminary = Users.create({
            'name': 'Justin Case',
            'login': 'jclume',
            'email': 'j.c@example.com',
            'signature': 'Justin Case',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('project.group_project_user').id])]
        })

        cls.user_picking = Users.create({
            'name': 'Adam Zaple',
            'login': 'azlume',
            'email': 'a.z@example.com',
            'signature': 'Adam Zaple',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('project.group_project_user').id])]
        })

        cls.user_cashier = Users.create({
            'name': 'Robin Banks',
            'login': 'rblume',
            'email': 'r.b@example.com',
            'signature': 'Robin Banks',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('project.group_project_user').id])]
        })

        cls.user_manager = Users.create({
            'name': 'Ella Vader',
            'login': 'evlume',
            'email': 'e.v@example.com',
            'signature': 'Ella Vader',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('project.group_project_user').id])]
        })

        cls.user_district_manager = Users.create({
            'name': 'Adam Sandler',
            'login': 'aslume',
            'email': 'a.s@example.com',
            'signature': 'Adam Sandler',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('project.group_project_user').id])]
        })

        #Creating warehouses as above.
        Warehouses = cls.env['stock.warehouse']

        cls.lumehouse_one = Warehouses.create({
            'name': 'Peterson',
            'code': 'Pete',
            'reception_steps': 'one_step',
            'delivery_steps': 'ship_only',

        })

        cls.lumehouse_two = Warehouses.create({
            'name': 'Escanaba',
            'code': 'ESCA',
            'reception_steps': 'one_step',
            'delivery_steps': 'ship_only',
            
        })

        #Creating Stores as above:

        Stores = cls.env['project.project'].with_context({'mail_create_nolog': True})

        cls.lumestore_one = Stores.create({
            'name': 'Peterson',
            'warehouse_id': Warehouses.search([('name', '=', 'lumehouse_one')], limit=1).id,
            'allow_timesheets': True,
            'allow_timesheet_timer': True,
            'privacy_visibility': 'followers',
            'alias_name': 'project+peterson',
            #'partner_id': cls.partner_1.id,
            'type_ids': [
                (0, 0, {
                    'name': 'Check In',
                    'sequence': 1, #Sets the location of the stage within the project application
                }),
                (0, 0, {
                    'name': 'Build Cart',
                    'sequence': 10,
                }),
                (0, 0, {
                    'name': 'Fulfillment',
                    'sequence': 20,
                }),
                (0, 0, {
                    'name': 'Order Ready',
                    'sequence': 30,
                }),
                (0, 0, {
                    'name': 'Done',
                    'fold': True, #Folds the stage in Kaliban view
                    'is_closed': True, #Makes all tasks within the stage be marked as "Done".
                    'sequence': 500,
                })]
            })
        cls.lumestore_two = Stores.create({
            'name': 'Escanaba',
            'warehouse_id': Warehouses.search([('name', '=', 'lumehouse_two')], limit=1).id,
            'allow_timesheets': True, #Used to keep track of the time a customer spent at each station.
            'allow_timesheet_timer': True, 
            'privacy_visibility': 'followers',
            'alias_name': 'project+escanaba',
            #'partner_id': cls.partner_1.id,
            'type_ids': [
                (0, 0, {
                    'name': 'Check In',
                    'sequence': 1,
                }),
                (0, 0, {
                    'name': 'Build Cart',
                    'sequence': 10,
                }),
                (0, 0, {
                    'name': 'Fulfillment',
                    'sequence': 20,
                }),
                (0, 0, {
                    'name': 'Order Ready',
                    'sequence': 30,
                }),
                (0, 0, {
                    'name': 'Done',
                    'fold': True, #Folds the stage in Kaliban view
                    'is_closed': True,
                    'sequence': 500, 
                })]
            })
        #Creating customers that already exist within the system:

        Customers = cls.env['res.partner'].with_context({'mail_create_nolog': True})

        cls.customer_rec = Customers.create({
            'name': 'Eve A. Love',
            'is_company': False,
            'company_type': 'person',
            'street': '629 Mad Dog Lane',
            'city': 'Detroit',
            'state': 'Michigan',
            'zip': '48201-0001',
            'phone': '555-555-5555',
            'email': 'ev@example.com',
            'date_of_birth': datetime.date(1987, 2, 17),
            'is_medical': False,
            'drivers_license_number': 'C3335473939576',
            'drivers_license_expiration': datetime.date(2021, 12, 31)

        })

        cls.customer_med = Customers.create({
            'name': 'Helen N. Hywater',
            'is_company': False,
            'company_type': 'person',
            'street': '404 Error Place',
            'city': 'Detroit',
            'state': 'Michigan',
            'zip': '48201-0001',
            'phone': '555-555-5555',
            'email': 'hh@example.com',
            'date_of_birth': datetime.date(1999, 5, 14),
            'is_medical': True,
            'medical_id': 'CG-18-089765',
            'medical_expiration': datetime.date(2021, 9, 13),
            'drivers_license_number': 'H1112222333344',
            'drivers_license_expiration': datetime.date(2021, 12, 31)
        })

        cls.customer_banned = Customers.create({
            'name': 'Bennie F. Factor',
            'is_company': False,
            'company_type': 'person',
            'street': '555 Linger Longer Road',
            'city': 'Detroit',
            'state': 'Michigan',
            'zip': '48201-0001',
            'phone': '555-555-5555',
            'email': 'bf@example.com',
            'date_of_birth': datetime.date(1999, 10, 21),
            'is_medical': False,
            'warnings': 3,
            'drivers_license_number': 'B4345545332311',
            'drivers_license_expiration': datetime.date(2021, 12, 31)

        })
        
        #Creating products as above. 

        Products = cls.env['product.template']
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        cls.product_med = Products.create({
            'name': 'Bloodstar 3.5G',
            'type': 'product',
            'available_in_pos': True,
            'is_medical': True,
            'uom_id': cls.uom_unit.id,
            'uom_po_id': cls.uom_unit.id
        })

        cls.product_rec = Products.create({
            'name': 'Jenny Kush 3.5G',
            'type': 'product',
            'available_in_pos': True,
            'is_medical': False,
            'uom_id': cls.uom_unit.id,
            'uom_po_id': cls.uom_unit.id
        })