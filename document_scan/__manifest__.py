# -*- encoding: utf-8 -*-


{
    'name' : "Document Scanning",
    'version' : '0.0',
    'author' : 'Tiny SPRL - AJM Technologies S.A',
    'website': "http://www.qocinnovations.com",
    'description' : """This module add document scan post-processing to documents""",
    'depends': ['document'],

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/view.xml',
    ],

    'external_dependencies': {
        'python': [
            # python-zbar
            'zbar',
            # python-imaging
            'Image',
            'ImageDraw',
            'ImageStat',
        ],
    },

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'active': False,
    'installable': True,
    'certificate': '0083858971589',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
