# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "METRC Base",
    'version': '1.0',
    'depends': ['base', 'contacts', 'uom'],
    'author': 'Odoo Inc',
    'license': 'OEEL-1',
    'mainainer': 'Odoo Inc',
    'category': 'Integrations',
    'description': """
METRC Base:
===========
- Base module containing metrc account, license and user related functionality.
- Serves as a base for all other METRC features.
    """,
    # data files always loaded at installation
    'data': [
        # security
        'security/metrc_security.xml',
        'security/ir.model.access.csv',

        # model views
        'views/metrc_menus.xml',
        'views/res_users_views.xml',
        'views/metrc_account_views.xml',
        'views/ir_cron_views.xml',
        'views/product_uom_views.xml',

        # data
        'data/metrc_cron_data.xml',
    ],
}