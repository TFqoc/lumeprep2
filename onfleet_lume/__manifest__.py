# -*- coding: utf-8 -*-
{
    'name': "OnFleet Lume Connector",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,
# 
    'author': "QOC Innovations",
    'website': "http://www.qocinnovations.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['lume_sales'],

    'qweb': [
    ],

    # always loaded
    'data': [
        'views/settings.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    # Not sure if this line is useful or not
    'external_dependencies': {
        'python' : ['pyonfleet'],
    },
}
