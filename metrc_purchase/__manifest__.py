# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "METRC Purchase",
    'version': '1.0',
    'depends': [
        'metrc',
        'metrc_product',
        'purchase_stock',
        'metrc_stock',
    ],
    'author': 'Odoo Inc',
    'license': 'OEEL-1',
    'mainainer': 'Odoo Inc',
    'category': 'Integrations',
    'description': """
METRC Base:
===========
- METRC Purchase module contains Purchase related integration functionality.
    """,
    # data files always loaded at installation
    'data': [
        # model views
        'views/purchase_views.xml',
        'views/res_partner_views.xml',
    ],
}