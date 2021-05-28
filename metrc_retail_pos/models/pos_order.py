# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import pprint
import logging
from datetime import timedelta, datetime

from odoo import api, fields, models, registry, _
from odoo.tools.misc import split_every
from odoo.tools import float_compare, float_round, float_is_zero
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import profile

_logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    metrc_retail_state = fields.Selection(selection=[
                                        ('Draft', 'Draft'),
                                        ('Outgoing', 'Outgoing'),
                                        ('Failed', 'Failed'),
                                        ('Reported', 'Reported'),
                                        ('Except', 'Do not Report'),
                                    ], string='Metrc Retail Status', default='Draft', index=True,
                                    states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    metrc_notes = fields.Html(string='Metrc Retails Notes', copy=False)
    customer_type = fields.Selection(related='partner_id.customer_type')
    patient_license_number = fields.Many2one(comodel_name='metrc.license',
                                         states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                         domain=[('base_type', '=', 'Patient')])
    caregiver_license_number = fields.Char(string='Caregiver License',
                                           states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    ext_patient_id_method = fields.Many2one(comodel_name='patient.id.method', string='External Patient ID Method',
                                        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    # @api.multi
    def _cron_flag_retail_pos(self, session_ids=[], force_report_date=False, automatic=True, raise_for_error=False):
        if automatic:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        sync_start_date = False
        dt_now = datetime.now()
        if force_report_date and isinstance(force_report_date, datetime):
            sync_start_date = force_report_date
        else:
            sync_start_date = dt_now - timedelta(hours=24)
        domain = [
            ('state', 'not in', ('draft', 'cancel')),
            ('write_date', '>=', fields.Datetime.to_string(sync_start_date)),
            ('metrc_retail_state', 'not in', ('Except', 'Outgoing', 'Reported')),
            ('picking_ids', '!=', []),
        ]
        if session_ids:
            domain.append(('session_id', 'in', session_ids))
        else:
            domain.append(('session_id.state', '=', 'closed'))
        orders = self.search(domain)
        _logger.info("metrc_retail: Total %d pos orders are filtered to be flagged for metrc reporting. It is possible that all of them would not be marked." % (len(orders)))
        for order in orders:
            move_line_ids = order.picking_ids.mapped('move_line_ids').filtered(lambda ml: ml.product_id.is_metric_product \
                                and ml.state == 'done' and ml.lot_id and \
                                float_compare(ml.qty_done, ml.metrc_reported_qty,precision_rounding=ml.product_uom_id.rounding) > 0)
            order_todo = False
            packages_to_report = ''
            line_prod_dict = {product: order.lines.filtered(lambda l: l.product_id == product) for product in order.lines.mapped('product_id')}
            for line_prod, order_lines in line_prod_dict.items():
                for line_lot in list(set(order_lines.mapped('pack_lot_ids').mapped('lot_name'))):
                    pack_move_line_ids = move_line_ids.filtered(lambda ml: (ml.lot_id._get_metrc_name() == line_lot) or \
                            (ml.lot_id.name == line_lot))
                    if pack_move_line_ids:
                        order_todo = True
                        move_line = pack_move_line_ids[0]
                        qty_done = move_line.qty_done
                        if len(pack_move_line_ids) > 1:
                            qty_done = sum(pack_move_line_ids.mapped('qty_done'))
                        packages_to_report += '<li>Package <strong> %s </strong> with quantity %f %s</li>' % (
                                                move_line.lot_id._get_metrc_name(),
                                                move_line.product_id.to_metrc_qty(qty_done),
                                                move_line.product_id.metrc_uom_id.name
                                                    if move_line.product_id.diff_metrc_uom and move_line.product_id.metrc_uom_id
                                                        else move_line.product_id.uom_id.name,
                                            )
            try:
                if order_todo:
                    order.write({
                        'metrc_retail_state': 'Outgoing',
                        'metrc_notes': '''%s<hr>
                                    <p><h4>Following packages are <mark> scheduled </mark> for retails reporting to Metrc: </h4>
                                    <ul>%s</ul>
                                    ''' % (order.metrc_notes or '', packages_to_report)
                    })
                if automatic:
                    cr.commit()
            except Exception as ex:
                if automatic:
                    cr.rollback()
                _logger.error('Error during flagging retails orders \n%s' % str(ex))
                if raise_for_error:
                    raise ex
        _logger.info("metrc_retail: Finished execution of the cron to flag pos orders to be reported to metrc.")
        if automatic:
            cr.commit()
            cr.close()
        return True

    def _cron_report_retail_pos(self, session_ids=[], batch_size=100, automatic=True, raise_for_error=False):
        metrc_account = self.env.user.ensure_metrc_account()
        if automatic:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        domain = [
            ('state', 'not in', ('draft', 'cancel')),
            ('metrc_retail_state', 'in', ('Except', 'Outgoing')),
            ('picking_ids', '!=', []),
        ]
        if session_ids:
            domain.append(('session_id', 'in', session_ids))
        else:
            domain.append(('session_id.state', '=', 'closed'))
        _logger.info('metrc.retail: starting metrc retail pos reporting')
        pos_orders = self.sudo().search(domain)
        picking_types = pos_orders.mapped('picking_type_id')
        for picking_type in picking_types:
            if not picking_type.warehouse_id and not picking_type.warehouse_id.license_id:
                _logger.warning('metrc.retail: skipping metrc retail pos reporting for '
                                'operation type "%s"  due to missing warehouse or license '
                                'on related operation type warehouse ' % (picking_type.name))
                continue
            facility_license_id = picking_type.warehouse_id.license_id
            picking_type_orders = pos_orders.filtered(lambda po: po.picking_type_id == picking_type)
            _logger.info('metrc.retail: processing %d retail pos orders for facility %s' % (
                                        len(picking_type_orders), facility_license_id.name))
            for order_chunk in split_every(batch_size, picking_type_orders):
                _logger.info('metrc.retail: processing batch of %d retail order for facility %s' % (
                                        len(order_chunk), facility_license_id.name))
                order_data = []
                for order in order_chunk:
                    move_line_ids = order.picking_ids.mapped('move_line_ids').filtered(lambda ml: ml.product_id.is_metric_product \
                                    and ml.state == 'done' and ml.lot_id and \
                                    float_compare(ml.qty_done, ml.metrc_reported_qty,precision_rounding=ml.product_uom_id.rounding) > 0)
                    transactions = []
                    line_prod_dict = {product: order.lines.filtered(lambda l: l.product_id == product) for product in order.lines.mapped('product_id')}
                    for line_prod, order_lines in line_prod_dict.items():
                        for line_lot in list(set(order_lines.mapped('pack_lot_ids').mapped('lot_name'))):
                            lot_move_line_ids = move_line_ids.filtered(lambda ml: (ml.lot_id._get_metrc_name() == line_lot) or \
                                (ml.lot_id.name == line_lot))
                            if lot_move_line_ids:
                                transactions.extend([{
                                    'PackageLabel': move_line.lot_id._get_metrc_name(),
                                    'Quantity': move_line.product_id.to_metrc_qty(move_line.qty_done),
                                    'UnitOfMeasure': move_line.product_id.metrc_uom_id.name
                                                             if move_line.product_id.diff_metrc_uom and move_line.product_id.metrc_uom_id 
                                                                     else move_line.product_uom_id.name,
                                    'TotalAmount': move_line.qty_done * order_lines[0].price_unit,
                                } for move_line in lot_move_line_ids])
                    if transactions:
                        receipt_data = {
                            'SalesDateTime': fields.Datetime.from_string(order.date_order).isoformat(),
                            'SalesCustomerType': order.customer_type or 'Patient',
                            'Transactions': transactions,
                        }
                        if order.customer_type != 'Consumer':
                            receipt_data.update({
                                'PatientLicenseNumber': order.patient_license_number.license_number,
                            })
                        if order.customer_type == 'Caregiver':
                            receipt_data.update({
                                'CaregiverLicenseNumber': order.caregiver_license_number,
                            })
                        if order.customer_type == 'ExternalPatient':
                            receipt_data.update({
                                'IdentificationMethod': order.ext_patient_id_method.name,
                            })
                        order_data.append(receipt_data)
                if order_data:
                    try:
                        uri = '{}/{}/{}'.format('/sales', metrc_account.api_version, 'receipts')
                        params = {'licenseNumber': facility_license_id.license_number}
                        res = metrc_account.fetch('POST', uri, params=params, data=order_data)
                        _logger.info('metrc.retail: processing batch reported pos order for facility %s' % (
                                                facility_license_id.name))
                        for order in order_chunk:
                            move_line_ids = order.picking_ids.mapped('move_line_ids').filtered(lambda ml: ml.product_id.is_metric_product \
                                    and ml.state == 'done' and ml.lot_id and \
                                    float_compare(ml.qty_done, ml.metrc_reported_qty,precision_rounding=ml.product_uom_id.rounding) > 0)
                            order_done = False
                            packages_reported = ''
                            line_prod_dict = {product: order.lines.filtered(lambda l: l.product_id == product) for product in order.lines.mapped('product_id')}
                            for line_prod, order_lines in line_prod_dict.items():
                                for line_lot in list(set(order_lines.mapped('pack_lot_ids').mapped('lot_name'))):
                                    lot_move_line_ids = move_line_ids.filtered(lambda ml: (ml.lot_id._get_metrc_name() == line_lot) or \
                                            (ml.lot_id.name == line_lot))
                                    if lot_move_line_ids:
                                        order_done = True
                                        move_line = lot_move_line_ids[0]
                                        qty_done = move_line.qty_done
                                        if len(lot_move_line_ids) > 1:
                                            for line in lot_move_line_ids:
                                                line.write({'metrc_reported_qty': line.qty_done})
                                            qty_done = sum(lot_move_line_ids.mapped('qty_done'))
                                        packages_reported += '<li>Package <strong> %s </strong> with quantity %f %s</li>' % (
                                                move_line.lot_id._get_metrc_name(),
                                                move_line.product_id.to_metrc_qty(qty_done),
                                                move_line.product_id.metrc_uom_id.name
                                                    if move_line.product_id.diff_metrc_uom and move_line.product_id.metrc_uom_id
                                                        else move_line.product_id.uom_id.name,
                                            )

                            if order_done and packages_reported:
                                order.write({
                                    'metrc_retail_state': 'Reported',
                                    'metrc_notes': '''%s<hr>
                                                    <p><h4>Following pos retails sales packages were <mark> reported </mark> to Metrc: </h4>
                                                    <ul>%s</ul>
                                                    ''' % (order.metrc_notes or '', packages_reported)
                                })
                        if automatic:
                            cr.commit()
                        _logger.info('metrc.retail: finished processing batch of %d retail pos order for facility %s' % (
                                                            len(order_chunk), facility_license_id.name))
                    except Exception as ex:
                        if automatic:
                            cr.rollback()
                        _logger.error('metrc.retail: Error during reporting retail pos orders  to Metrc \n%s' % str(ex))
                        if raise_for_error:
                            raise ex
                        else:
                            metrc_account.log_exception()
        _logger.info('metrc.retail: end of metrc retail pos reporting')
        if automatic:
            cr.commit()
            cr.close()
        return True


# class PosOrderLine(models.Model):
#     _inherit = 'pos.order.line'

#     metrc_reported_qty = fields.Float(string='Quantity reported to Metrc', default=0.0,
#                                         digits=dp.get_precision('Product Unit of Measure'))
