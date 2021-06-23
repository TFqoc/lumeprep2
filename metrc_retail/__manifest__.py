# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Metrc Retail Integration',
    'summary': 'Metrc Retail Integration',
    'website': 'https://www.odoo.com',
    'version': '0.1',
    'sequence': 101,
    'author': 'Odoo Inc',
    'maintainer': 'Odoo Inc',
    'license': 'OEEL-1',
    'category': 'Integration Application',
    'description': """
Metrc Integration
===============================
- API Documentation : https://api-ca.metrc.com/Documentation

""",
    'depends': [
        'crm',
        'metrc_stock',
    ],
    'data': [
        # security
        'security/ir.model.access.csv',

        # views
        'views/res_partner_views.xml',
        'views/metrc_customer_types_views.xml',
        'views/metrc_receipt_view.xml',
        'views/patient_id_method_views.xml',
        'views/crm_team_views.xml',
        'views/res_config_settings_views.xml',

        # data
        'data/metrc_retail_cron_data.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'images' : [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
