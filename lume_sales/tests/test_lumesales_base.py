from odoo.tests.common import SavepointCase, tagged
from odoo.exceptions import UserError
from datetime import datetime
from datetime import timedelta
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
            'warehouse_id': cls.lumehouse_one.id,
            'allow_timesheets': True,
            'allow_timesheet_timer': True,
            'privacy_visibility': 'followers',
            'alias_name': 'project+peterson',
            'blink_threshold': 5,
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
                    'name': 'Out for Delivery',
                    'sequence': 40,
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
            'warehouse_id': cls.lumehouse_two.id,
            'allow_timesheets': True, #Used to keep track of the time a customer spent at each station.
            'allow_timesheet_timer': True, 
            'privacy_visibility': 'followers',
            'alias_name': 'project+escanaba',
            'blink_threshold': 5,
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
                    'name': 'Out for Delivery',
                    'sequence': 40,
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
        state = cls.env['res.country.state'].search([("code","=", "MI")], limit=1)

        cls.customer_rec = Customers.create({
            'name': 'Eve A Love',
            'is_company': False,
            'company_type': 'person',
            'street': '629 Mad Dog Lane',
            'city': 'Detroit',
            'state_id': state.id,
            'country_id': state.country_id.id,
            'zip': '48201-0001',
            'phone': '555-555-5555',
            'email': 'ev@example.com',
            'date_of_birth': datetime.now() - timedelta(days = 365*23),
            'drivers_license_number': 'C333547393957',
            'drivers_license_expiration': datetime.now() + timedelta(days = 365*1)

        })

        cls.customer_med = Customers.create({
            'name': 'Helen N Hywater',
            'is_company': False,
            'company_type': 'person',
            'street': '404 Error Place',
            'city': 'Detroit',
            'state_id': state.id,
            'country_id': state.country_id.id,
            'zip': '48201-0001',
            'phone': '555-555-5555',
            'email': 'hh@example.com',
            'date_of_birth': datetime.now() - timedelta(days = 365*24),
            'medical_id': 'CG-18-089765',
            'medical_expiration': datetime.now() + timedelta(days = 365*2),
            'drivers_license_number': 'H111222233334',
            'drivers_license_expiration': datetime.now() + timedelta(days = 365*2)
        })

        cls.customer_banned = Customers.create({
            'name': 'Bennie F Factor',
            'is_company': False,
            'company_type': 'person',
            'street': '555 Linger Longer Road',
            'city': 'Detroit',
            'state_id': state.id,
            'country_id': state.country_id.id,
            'zip': '48201-0001',
            'phone': '555-555-5555',
            'email': 'bf@example.com',
            'date_of_birth': datetime.now() - timedelta(days = 365*24),
            'warnings': 3,
            'drivers_license_number': 'B434554533231',
            'drivers_license_expiration': datetime.now() + timedelta(days = 365*3)

        })

        cls.customer_care = Customers.create({
            'name': 'Dexter Michael Davenport',
            'is_company': False,
            'company_type': 'person',
            'street': '404 Frying Pan Road',
            'city': 'Detroit',
            'state_id': state.id,
            'country_id': state.country_id.id,
            'zip': '48201-0001',
            'phone': '555-555-5555',
            'email': 'jt@example.com',
            'date_of_birth': datetime.now() - timedelta(days = 365*25),
            'medical_id': 'CG-21-089765',
            'medical_expiration': datetime.now() + timedelta(days = 365*2),
            'is_caregiver': True,
            'caregiver_license': 'Caregiver',
            'drivers_license_number': 'B434555533231',
            'drivers_license_expiration': datetime.now() + timedelta(days = 365*4)
        })

        state = cls.env['res.country.state'].search([("code","=", "WI")], limit=1)
        cls.customer_pat = Customers.create({
            'name': 'Justin Nick Thyme',
            'is_company': False,
            'company_type': 'person',
            'street': '404 Electric Avenue',
            'city': 'Madison',
            'state_id': state.id,
            'country_id': state.country_id.id,
            'zip': '53590-0001',
            'phone': '555-555-5555',
            'email': 'jt@example.com',
            'date_of_birth': datetime.now() - timedelta(days = 365*26),
            'medical_id': 'CG-19-089765',
            'medical_expiration': datetime.now() + timedelta(days = 365*3),
            'caregiver_id': cls.customer_care.id,
            'drivers_license_number': 'F672554568631',
            'drivers_license_expiration': datetime.now() + timedelta(days = 365*5)
        })
        
        #Creating products as above. 

        Products = cls.env['product.template']
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        cls.product_med = Products.create({
            'name': 'Bloodstar 3.5G',
            'type': 'product',
            'available_in_pos': True,
            'thc_type': 'medical',
            'uom_id': cls.uom_unit.id,
            'uom_po_id': cls.uom_unit.id
        })

        cls.product_rec = Products.create({
            'name': 'Jenny Kush 3.5G',
            'type': 'product',
            'available_in_pos': True,
            'thc_type': 'adult',
            'uom_id': cls.uom_unit.id,
            'uom_po_id': cls.uom_unit.id
        })

        # Quantity = cls.env['stock.quant'].with_context(inventory_mode=True)

        # med_quantity_pete = Quantity.create({
        #     'product_id': cls.product_med.id,
        #     'inventory_quantity': 50.0,
        #     'location_id': cls.lumehouse_one.lot_stock_id.id,
        # })

        # rec_quantity_pete = Quantity.create({
        #     'product_id': cls.product_rec.id,
        #     'inventory_quantity': 50.0,
        #     'location_id': cls.lumehouse_one.lot_stock_id.id,
        # })

        # med_quantity_esca = Quantity.create({
        #     'product_id': cls.product_med.id,
        #     'inventory_quantity': 50.0,
        #     'location_id': cls.lumehouse_two.lot_stock_id.id,
        # })

        # rec_quantity_esca = Quantity.create({
        #     'product_id': cls.product_rec.id,
        #     'inventory_quantity': 50.0,
        #     'location_id': cls.lumehouse_two.lot_stock_id.id,
        # })

        # _logger.warning("Product Rec's Type is %s" % cls.product_rec.type)

        
def compare_dictionaries(dictionary_1, dictionary_2, list_of_keys):
    error_list = [True]
    if list_of_keys != False:
        x = list_of_keys
    else:
        x = dictionary_1
    for key in x:
        if not (key in dictionary_1): #Catches a key not shared between two dictionaries.
            if error_list[0]:
                error_list[0] = False
                error_list.append("%s key was not found in %s." % (key, dictionary_1))
            else:
                error_list.append("%s key was not found in %s." % (key, dictionary_1))
        if not (key in dictionary_2): #Catches a key not shared between two dictionaries.
            if error_list[0]:
                error_list[0] = False
                error_list.append("%s key was not found in %s." % (key, dictionary_2))
            else:
                error_list.append("%s key was not found in %s." % (key, dictionary_2))
        if dictionary_1[key] != dictionary_2[key] and type(dictionary_2[key]) != bool: #Catches if the values are not the same.
            if error_list[0]:
                error_list[0] = False
                error_list.append("%s key held two different values: %s and %s." % (key, dictionary_1[key], dictionary_2[key]))
            else:
                error_list.append("%s key held two different values: %s and %s." % (key, dictionary_1[key], dictionary_2[key]))
        if dictionary_1[key] != dictionary_2[key] and type(dictionary_2[key]) == bool:
            if bool(dictionary_1[key]) != bool(dictionary_2[key]):
                if error_list[0]:
                    error_list[0] = False
                    error_list.append("%s key held two different values: %s and %s." % (key, dictionary_1[key], dictionary_2[key]))
                else:
                    error_list.append("%s key held two different values: %s and %s." % (key, dictionary_1[key], dictionary_2[key]))

    return error_list

