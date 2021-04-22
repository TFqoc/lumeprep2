# -*- coding: utf-8 -*-
{
    'name': "Lume Pos",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "QOC Innovations",
    'website': "http://www.qocinnovations.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','point_of_sale','sale','lume_sales'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/assets.xml',
        'views/views.xml',
        'views/point_of_sale.xml',
        'views/templates.xml',
    ],
    # 'assets': {
    #     'web.assets_common': [ # This doesn't load the js file
    #         ('prepend', 'pos_test/static/js/button.js'),
    #     ],
    # },
    'qweb':[
        # 'static/xml/button.xml',
        'static/xml/update_orders.xml',
        'static/xml/ReceiptScreen.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
