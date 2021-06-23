# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "METRC MRP",
    'version': '1.0',
    'depends': [
        'mrp',
    ],
    'author': 'Odoo Inc',
    'license': 'OEEL-1',
    'mainainer': 'Odoo Inc',
    'category': 'Integration',
    'description': """
METRC MRP
=========
- METRC manufacturing related features.
- Batch Splits.
- Cannbis MO/WO.
    """,
    # data files always loaded at installation
    'data': [
        # views
        'views/stock_warehouse_views.xml',
        'views/mrp_production_views.xml',

        # data
        'data/metrc_actions.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}