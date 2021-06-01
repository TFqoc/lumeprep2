# -*- coding: utf-8 -*-
{
    'name': "Metrc Retail POS",

    'summary': """Metrc Retail POS Integration""",

    'description': """
        Metrc Retail POS Integration
        ===============================
        - API Documentation : https://api-ca.metrc.com/Documentation
        - Reporting of POS orders to metrc as sales receipts.
        """,

    'author': 'Odoo',
    'website': 'https://www.odoo.com/',
    'sequence': 102,

    'category': 'Integration Application',
    'version': '0.1',
    'license': 'OEEL-1',

    # any module necessary for this one to work correctly
    'depends': [
        'metrc_retail',
        'metrc_stock',
        'point_of_sale'
    ],

    # always loaded
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # views
        'views/patient_id_method_views.xml',
        'views/pos_order_view.xml',
        'views/pos_session_view.xml',
        'views/pos_assets_common.xml',

        # Data
        'data/metrc_retail_pos_cron_data.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [
        'static/src/xml/Screens/ClientListScreen/ClientDetailsEdit.xml',
        'static/src/xml/Screens/PatientLicenseScreen/PatientLicenseScreen.xml',
        'static/src/xml/popups/LicensePopup.xml',
    ],
    'demo': [],
    'application': True,
}
