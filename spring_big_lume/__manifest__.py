# -*- coding: utf-8 -*-
{
    'name': "Spring Big Lume",

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
    'depends': ['base','lume_pos'],

    # 'qweb': [
    #     "static/src/xml/lpc_quantity.xml",
    #     "static/src/xml/qty_template.xml",
    #     "static/src/xml/quick_create.xml",
    # ],

    # always loaded
    # 'data': [
    #     'security/ir.model.access.csv',
    #     'wizards/scan_dl.xml',
    #     'wizards/message_wizard.xml',
    #     'wizards/note_wizard.xml',
    #     'views/assets.xml',
    #     'views/sale.xml',
    #     'views/project.xml',
    #     'views/product_catalog.xml',
    #     'views/actions.xml',
    #     'views/partner.xml',
    #     'views/views.xml',
    #     'views/templates.xml',
    #     'data/data.xml',
    #     'data/ir_cron_data.xml',
    # ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}