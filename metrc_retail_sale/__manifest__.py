# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "METRC Retail Sales Order Reporting",
    'version': '1.0',
    'depends': [
        'metrc_retail',
        'sale',
    ],
    'author': 'Odoo Inc',
    'license': 'OEEL-1',
    'mainainer': 'Odoo Inc',
    'category': 'Integration',
    'description': """
METRC Retail Sales Order Reporting
==================================
    """,
    # data files always loaded at installation
    'data': [
        # views
        'views/sale_order_views.xml',

        #data
        'data/metrc_retail_cron_data.xml',
    ],
    'application': True,
}