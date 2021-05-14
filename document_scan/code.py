# -*- encoding: utf-8 -*-
############################################################################################
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
############################################################################################

from osv import osv
from osv import fields

import os
from tools.translate import _
import base64
import StringIO as BaseStringIO

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

try:
    import cPickle as pickle
except ImportError:
    import pickle

import scan
#from tools import profile

class ImageStringIO(BaseStringIO.StringIO):
    def __init__(self, buf=''):
        BaseStringIO.StringIO.__init__(self, buf)
        self.name = ''

class document_scanning_device(osv.osv):
    _name = 'document.scanning.device'

document_scanning_device()

class document_directory(osv.osv):
    _inherit = 'document.directory'

    _columns = {
        'to_process' : fields.selection([('yes', 'Yes'),('no', 'No')], 'To Process'),
        'scanning_device': fields.many2one('document.scanning.device', 'Scanning Device'),
    }

    _defaults = {
        'to_process' : lambda *a: 'no',
    }

document_directory()

class position_storage(osv.osv):
    _name = 'position.storage'
    _columns = {
        'res_model' : fields.char('Model Ref', size=128, required=True),
        'res_id' : fields.integer('ID Ref', required=True),
        'page_num' : fields.integer('Page Number', required=True),
        'checkboxes_position' : fields.binary('Checkboxes position'),
        'checkboxes_value' : fields.binary('Checkboxes value'),
        'checkboxes_context': fields.binary('Checkboxes context'),
    }
    # TODO add (unique?) index on (participation_id, page_num)
    # if unique, alors on doit encore tester qd on imprime plus d'une fois
    #_sql_constraints = [('uniq_participation_page', 'unique(participation_id, page_num)', 'A page for a participation is unique.')]

    def serialize(self, data):
        return pickle.dumps(data, protocol=2)

    def unserialize(self, data):
        return pickle.loads(data)

    def save_checkboxes_position(self, cr, uid, res_model, res_id, data, data_context, context=None):
        """Saves positions for _all_ pages of a participation:
        data is [[lists of 4 floats] for N in range(nbr of pages)] .
        First page is page number 1, so zero-th element of data is discarded (it is an empty list anyway).
        Negative page number not supported."""
        values = {
            'res_model' : res_model,
            'res_id' : res_id,
        }

        for page_num, positions in enumerate(data):
            if page_num == 0:
                continue
            values.update({
                'page_num' : page_num,
                'checkboxes_position' : self.serialize(positions),
                'checkboxes_context' : self.serialize(data_context[page_num]),
            })
            self.create(cr, uid, values, context=context)
        return True

#    def save_checkboxes_context(self, cr, uid, res_model, res_id, data, context=None):
#        values = {
#            'res_model': res_model,
#            'res_id': res_id,
#        }
#        for page_num, chkbox_context in enumerate(data):
#            if page_num == 0:
#                continue
#            values.update({
#                'page_num': page_num,
#                'checkboxes_context': self.serialize(chkbox_context),
#            })
#            self.write(cr, uid, values, context)

    def save_checkboxes_value(self, cr, uid, res_model, res_id, page_num, data, context=None):
        """Saves values for _one_ page."""

        ids = self.search(cr, uid, [('res_model', '=', res_model), ('res_id', '=', res_id), ('page_num', '=', page_num)], context=context)
        values = {
            'checkboxes_value' : self.serialize(data),
        }
        return self.write(cr, uid, ids, values, context=context)


    def load_checkboxes_position(self, cr, uid, res_model, res_id, page_num, context=None):
        """Loads positions for _one_ page."""

        ids = self.search(cr, uid, [('res_model', '=', res_model), ('res_id', '=', res_id), ('page_num', '=', page_num)], context=context)
        if ids:
            obj = self.browse(cr, uid, ids[0])
            data = obj.checkboxes_position
            positions = self.unserialize(data)
        else:
            positions = None

        return positions

    def load_checkboxes_context(self, cr, uid, res_model, res_id, page_num, context=None):
        """Loads context for _one_ page."""
        ids = self.search(cr, uid, [('res_model', '=', res_model), ('res_id', '=', res_id), ('page_num', '=', page_num)], context=context)
        if ids:
            obj = self.browse(cr, uid, ids[0])
            data = obj.checkboxes_context
            chkbox_context = self.unserialize(data)
        else:
            chkbox_context = None

        return chkbox_context

    def load_checkboxes_value(self, cr, uid, res_model, res_id, page_num, context=None):
        """Loads values for _one_ page."""
        ids = self.search(cr, uid, [('res_model', '=', res_model), ('res_id', '=', res_id), ('page_num', '=', page_num)], context=context)
        if ids:
            obj = self.browse(cr, uid, ids[0])
            data = obj.checkboxes_value
            values = self.unserialize(data)
        else:
            values = None

        return values

position_storage()

class document_scanning_action(osv.osv):
    _name = 'document.scanning.action'

    _columns = {
        'name': fields.char('Name', size=64),
        'res_model': fields.char('Model', size=64),
        'function': fields.char('Function', size=64),
        'priority': fields.integer('Priority'),
    }

document_scanning_action()

class document_scanning_device(osv.osv):
    _name = 'document.scanning.device'

    _columns = {
        'name': fields.char('Name', size=64),
        'model': fields.char('Model', size=64),
        # Configuration values
        'auto_resolution': fields.boolean('Auto Resolution'),
        'resolution': fields.float('Resolution', digit=(5,5)),
        'threshold': fields.integer('Threshold', help='Under this level checkbox are considered checked, 0 = black, 255 = white'),
        'deviance_threshold': fields.integer('Deviance Threshold'),
        'deviance_max': fields.integer('Deviance Max'),
        'debug': fields.boolean('Debug'),
    }

    _defaults = {
        'debug': lambda *a: False,
        'auto_resolution': lambda *a: False,
    }

document_scanning_device()

class document_scanning_rename(osv.osv):
    _name = 'document.scanning.rename'

    _columns = {
        'res_model': fields.char('Object', size=128),
        'rename_cond': fields.char('Rename Condition', size=255, required=True),
        'rename_pattern': fields.char('Rename Pattern', size=255),
    }

document_scanning_rename()

def get_image(stream, name):
    image_file = ImageStringIO()
    image_file.write(base64.decodestring(stream))
    image_file.seek(0)
    image_file.name = name
    return image_file

class ir_attachment(osv.osv):
    _inherit = 'ir.attachment'

    def unlink(self, cr, uid, ids, context=None):
        positions_by_model = {}
        positions_to_delete = []
        posstor_proxy = self.pool.get('position.storage')

        for attach in self.browse(cr, uid, ids):
            if attach.datas_fname and attach.datas_fname.startswith('Exam_') and attach.datas_fname.endswith('.pdf'):
                positions_by_model.setdefault(attach.res_model, []).append(attach.res_id)
        for model, model_ids in positions_by_model.iteritems():
            sids = posstor_proxy.search(cr, uid,
                    [('res_model','=',model), ('res_id','in',model_ids)])
            if sids:
                positions_to_delete.extend(sids)
        result = super(ir_attachment, self).unlink(cr, uid, ids, context=context)
        if result:
            result_position = posstor_proxy.unlink(cr, uid, positions_to_delete)
        return result

    #@profile('scannning.gprof')
    def write(self, cr, uid, ids, values, context=None):
        result = super(ir_attachment, self).write(cr, uid, ids, values, context=context)

        scandev = self.pool.get('document.scanning.device')
        scanrename_pool = self.pool.get('document.scanning.rename')
        docdir = self.pool.get('document.directory')

        for obj in self.read(cr, uid, ids, ['id', 'name', 'datas_fname', 'parent_id'], context=context):
            if obj['parent_id']:
                obj_parent = docdir.browse(cr, uid, obj['parent_id'][0], context=context)
                if not (obj_parent and obj_parent.to_process == 'yes' and obj_parent.scanning_device):
                    # no need to process it
                    continue
            else:
                continue

            scanner_obj = obj_parent.scanning_device
#            scanner_config = obj_parent.scanning_device.read(cr, uid, [obj_parent.scanning_device.id, ['resolution','threshold','deviance_threshold','deviance_max', 'debug'])
            scanner = scan.Scanner(
                        out_res = scanner_obj.resolution,
                        checked_threshold = scanner_obj.threshold,
                        deviance_threshold= scanner_obj.deviance_threshold,
                        deviance_max = scanner_obj.deviance_max,
                        debug = scanner_obj.debug,
                        auto_resolution = scanner_obj.auto_resolution,
            )
            ext = os.path.splitext(obj['name'])[-1].lower()[1:]

            if 'datas' not in values:
                objdata = self.read(cr, uid, obj['id'], ['datas'])
                values['datas'] = objdata.get('datas', '')

            image_file = get_image(values['datas'], obj['datas_fname'])
            scanner.set_image_path(image_file, obj['datas_fname'])
            image_file.close()
            try:
                (res_model, res_id, page_num), symbol_location =  scanner.get_qrcode_data()
            except scan.ScannerException, msg:
                # TODO log.warning(msg)
                # could be wrong scan, white sheet, or other kind of error
                print("ScannerException# msg => %s" % (msg))
                continue

            if res_id is None:
                continue

            str_pagenum = '%06d' % (page_num)
            doctype = str_pagenum[0]
            docnum = int(str_pagenum[1:2])
            page_num = int(str_pagenum[3:])

            eval_dict = {
                'res_model': res_model,
                'res_id': res_id,
                'page_num': page_num,
                'docnum': docnum,
                'doctype': doctype,
                'ext': ext,
                'obj_name': obj['name'],
                'obj_id': obj['id'],
                '_': _,
            }
            attach_new_name = obj['name'] # assign the old name as default value
            # search for rename pattern
            rename_name = None
            rename_ids = scanrename_pool.search(cr, uid, [('res_model', '=', res_model)])
            if rename_ids:
                for rename in scanrename_pool.read(cr, uid, rename_ids, context=context):
                    r =  eval(rename['rename_cond'], eval_dict)
                    if r:
                        rename_name = eval(rename['rename_pattern'], eval_dict)
                        break
            if rename_name:
                attach_new_name = rename_name

            if doctype == '2':
                # this document should not be stored in the DMS
                continue

            attach_existing_search = [('res_model','=',res_model),('res_id','=',res_id),('name','=',attach_new_name)]
            attach_existing_name = self.search(cr, uid, attach_existing_search)
            if len(attach_existing_name):
                super(ir_attachment, self).unlink(cr, uid, attach_existing_name)

            cr.execute("UPDATE ir_attachment SET name = %s, res_model = %s, res_id = %s WHERE id = %s",
                        (attach_new_name, res_model, res_id, obj['id']))

            if doctype == '1':
                # this is an annex and should not be checked for checkboxes
                continue

            res_pool = self.pool.get(res_model)
            res_obj = res_pool.browse(cr, uid, res_id, context=context)

            # Search for scanning actions and execute them
            scan_actions_obj = self.pool.get('document.scanning.action')
            scan_actions = scan_actions_obj.search(cr, uid, [('res_model','=',res_model)], order='priority')
            scan_actions_func = [ x['function'] for x in scan_actions_obj.read(cr, uid, scan_actions, ['function']) ]

            if len(scan_actions_func):
                for func in scan_actions_func:
                    f = getattr(res_pool, func)
                    if f:
                        f(cr, uid, res_id, page_num, scanner, context=context)

                if scanner.debug and scanner._debug_image is not None:
                    # score internal debug image in DMS
                    debug_existing_search = [('res_model','=',res_model),('res_id','=',res_id),('name','=','DEBUG_'+attach_new_name)]
                    debug_ids =  self.search(cr, uid, debug_existing_search)
                    if not len(debug_ids):
                        debug_id = super(ir_attachment, self).create(cr, uid, {'name': 'DEBUG_'+attach_new_name, 'datas_fname': 'DEBUG_'+attach_new_name , 'res_model': res_model, 'res_id': res_id})
                        debug_ids = [ debug_id ]

                    f = ImageStringIO()
                    f.name = 'debug.jpg'
                    scanner._debug_image.save(f)
                    f.seek(0)
                    fdata = base64.encodestring(f.read())
                    f.close()
                    del f
                    super(ir_attachment, self).write(cr, uid, debug_ids, {'datas': fdata})

        return result

ir_attachment()

WRITABLE_ONLY_IN_DRAFT = dict(readonly=True, states={'draft': [('readonly', False)]})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
