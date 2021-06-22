# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "METRC Sale",
    'version': '1.0',
    'depends': [
        'metrc',
        'metrc_product',
        'sale_stock',
        'metrc_stock',
    ],
    'author': 'Odoo Inc',
    'license': 'OEEL-1',
    'mainainer': 'Odoo Inc',
    'category': 'Integrations',
    'description': """
METRC Base:
===========
- Metrc Sale module contains Sales and delivery related METRC integration functionality.
    """,
    # data files always loaded at installation
    'data': [
        # model views
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
    ],
}