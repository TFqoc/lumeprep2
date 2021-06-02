# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "METRC Stock",
    'version': '1.0',
    'depends': [
        'stock',
        'fleet',
        'metrc_product',
        'metrc_mrp',
    ],
    'author': 'Odoo Inc',
    'license': 'OEEL-1',
    'mainainer': 'Odoo Inc',
    'category': 'Integration',
    'description': """
METRC Stock
===========
- Inventory related metrc integration.
- Metrc Packages.
- Package Adjustments.
    """,
    # data files always loaded at installation
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Model Views
        'views/transfer_type_views.xml',
        'views/metrc_transfer_view.xml',
        'views/metrc_location_views.xml',
        'views/package_adjust_reason_views.xml',
        'views/stock_move_views.xml',
        # 'views/stock_quant_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_views.xml',
        'views/stock_location_views.xml',
        'views/metrc_account_views.xml',
        'views/res_config_settings_views.xml',

        # Wizard Views
        'wizard/split_lot_wizard_views.xml',
        'wizard/merge_lot_wizard_views.xml',
        'wizard/stock_change_product_qty_views.xml',
        'wizard/stock_package_wizard_views.xml',
        'wizard/stock_transfer_wizard_views.xml',
        'wizard/warehouse_package_adjustment_views.xml',
        'wizard/metrc_package_adjustment_views.xml',
        'wizard/metrc_push_data.xml',
        'wizard/package_item_change.xml',
        'wizard/receive_metrc_transfer_wizard_views.xml',

        # data
        'data/metrc_cron_data.xml',
        'data/action_data.xml',
    ],
}