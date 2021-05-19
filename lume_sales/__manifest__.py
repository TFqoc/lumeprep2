# -*- coding: utf-8 -*-
{
    'name': "Lume Sales",

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
    'version': '0.33',

    # any module necessary for this one to work correctly
    'depends': ['base','contacts','project','stock','timesheet_grid','sale_management','sale_stock','barcodes'],

    'qweb': [
        "static/src/xml/lpc_quantity.xml"
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'wizards/scan_dl.xml',
        'wizards/message_wizard.xml',
        'views/assets.xml',
        'views/sale.xml',
        'views/project.xml',
        'views/product_catalog.xml',
        'views/actions.xml',
        'views/partner.xml',
        'views/views.xml',
        'views/templates.xml',
        'data/data.xml',
        'data/ir_cron_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'external_dependencies': {
        'bin': ['cmake'],
        'python': ['face_recognition'],
    },
}
