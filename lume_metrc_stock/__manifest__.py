# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Lume: Inventory Customizations",
    'version': '14.0.1',
    'depends': ['metrc_stock', 'lume_sales'],
    'author': 'Odoo Inc',
    'license': 'OEEL-1',
    'mainainer': 'Odoo Inc',
    'category': 'Customizations',
    'description': """
Lume: Inventory Customizations
==============================
1. Add metrtc receipts menu from Metrc app to Inventory app under Operations menu.
2. New Internal Transfers Menu
3. Ready to do Inventory adjustment screen.
4. Store to Store transfers.
5. Menu renaming and re-arranging under Operations menu.
3. Tier on metrc transfer. Flowing it to packages received.
    """,
    # data files always loaded at installation
    'data': [
        'views/stock_views.xml',
        'views/metrc_transfer_views.xml',
    ],
}