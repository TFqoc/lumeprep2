# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "METRC Intercompany Sale-Purchase",
    'version': '1.0',
    'depends': [
        'metrc_sale',
        'metrc_purchase',
        'sale_purchase_inter_company_rules',
    ],
    'author': 'Odoo Inc',
    'license': 'OEEL-1',
    'mainainer': 'Odoo Inc',
    'category': 'Integration',
    'description': """
METRC Intercompany Sale-Purchase
================================
- Automatically assign partner license based on the pickking type on both sale on purchase orders 
  when it is created based on inter company rules.
    """,
    # data files always loaded at installation
    'data': [
    ],
    'installable': True,
    'auto_install': True,
}