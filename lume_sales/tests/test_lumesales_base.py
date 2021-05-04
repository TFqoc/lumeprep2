from odoo.tests.common import SavepointCase
from odoo.exceptions import UserError

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
            'Name': 'Pete Zeria',
            'login': 'pzlume',
            'email': 'p.z@example.com',
            'signature': 'Pete Zeria',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_public').id])]
        })

        cls.user_luminary = Users.create({
            'Name': 'Justin Case',
            'login': 'jclume',
            'email': 'j.c@example.com',
            'signature': 'Justin Case',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_public').id])]
        })

        cls.user_picking = Users.create({
            'Name': 'Adam Zaple',
            'login': 'azlume',
            'email': 'a.z@example.com',
            'signature': 'Adam Zaple',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_public').id])]
        })

        cls.user_cashier = Users.create({
            'Name': 'Robin Banks',
            'login': 'rblume',
            'email': 'r.b@example.com',
            'signature': 'Robin Banks',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_public').id])]
        })

        cls.user_manager = Users.create({
            'Name': 'Ella Vader',
            'login': 'evlume',
            'email': 'e.v@example.com',
            'signature': 'Ella Vader',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_public').id])]
        })

        cls.user_district_manager = Users.create({
            'Name': 'Adam Sandler',
            'login': 'aslume',
            'email': 'a.s@example.com',
            'signature': 'Adam Sandler',
            'notification_type': 'email',
            'groups_id': [(6, 0, [cls.env.ref('base.group_public').id])]
        })

        #Creating Stores:

        cls.lumestore_one = cls.env['project.project'].with_context({'mail_create_nolog': True}).create({
            'name': 'Peterson',
            'privacy_visibility': 'followers',
            'alias_name': 'project+peterson',
            'partner_id': cls.partner_1.id,
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
        cls.lumestore_two = cls.env['project.project'].with_context({'mail_create_nolog': True}).create({
            'name': 'Escanaba',
            'privacy_visibility': 'followers',
            'alias_name': 'project+escanaba',
            'partner_id': cls.partner_1.id,
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

