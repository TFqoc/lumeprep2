# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "METRC Product",
    'version': '1.0',
    'depends': ['metrc', 'product'],
    'author': 'Odoo Inc',
    'license': 'OEEL-1',
    'mainainer': 'Odoo Inc',
    'category': 'Integration',
    'description': """
METRC Product:
==============
- METRC related product catalog integration.
- METRC Product Syncing.
- METRC Strains.
- METRC Item Categories.
    """,
    # data files always loaded at installation
    'data': [
        # security
        'security/ir.model.access.csv',

        # views
        'views/metrc_views.xml',
        'views/metrc_item_category_view.xml',
        'views/metrc_product_alias_view.xml',
        'views/metrc_strains_view.xml',
        'views/metrc_account_views.xml',
        'views/product_views.xml',
        'views/res_config_settings_views.xml',

        # data
        'data/metrc_cron_data.xml',
    ],
}