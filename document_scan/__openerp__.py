# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name' : 'Document Scanning',
    'version' : '0.2',
    'author' : 'Tiny SPRL - AJM Technologies S.A',
    'website' : 'http://www.openerp.com',
    'description' : """This module add document scan post-processing to documents""",
    'depends' : [
        'document',
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
    'init_xml' : [ ],
    'demo_xml' : [
    ],
    'update_xml' : [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'view.xml',
    ],
    'active' : False,
    'installable' : True,
    'certificate': '0083858971589',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
