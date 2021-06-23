# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Metrc Integration',
    'summary': 'Metrc Integration Module',
    'website': 'https://www.odoo.com',
    'version': '1.1',
    'sequence': 100,
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
        'metrc_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ir_model_views.xml',

        'views/metrc_views.xml',
        'views/metrc_license_view.xml',
        'views/metrc_license_issuer_views.xml',
        'views/metrc_model_data_view.xml',
        'views/labtest_views.xml',
        'views/res_partner_view.xml',
        'views/res_config_settings_views.xml',
        'report/flower_package_lables.xml',

        # data
        'data/metrc_cron_data.xml',
        'data/metrc_uom_data.xml',
        'data/mail_channel_data.xml',

    ],
    'demo': [
        'demo/metrc_demo.xml',
    ],
    'qweb': [
    ],
    'images' : [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
