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
            'Name' : 'Pete Zeria'
        })

        cls.user_luminary = Users.create({})

        cls.user_picking = Users.create({})

        cls.user_cashier = Users.create({})

        cls.user_manager = Users.create({})

        cls.user_district_manager = Users.create({})

        #Creating Stores:

        cls.lumestore_one = cls.env['project.project'].with_context({'mail_create_nolog': True}).create({
            'name': 'Peterson',
            'privacy_visibility': 'followers',
            'alias_name': 'project+goats',
            'partner_id': cls.partner_1.id,
            'type_ids': [
                (0, 0, {
                    'name': 'New',
                    'sequence': 1,
                }),
                (0, 0, {
                    'name': 'Won',
                    'sequence': 10,
                })]
            })

