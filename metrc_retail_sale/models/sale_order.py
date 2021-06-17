# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import timedelta, datetime

from odoo import api, fields, models, registry, _
from odoo.tools.misc import split_every
from odoo.tools import float_compare, float_round, float_is_zero
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import profile

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    metrc_retail_state = fields.Selection(selection=[
                                        ('Draft', 'Draft'),
                                        ('Outgoing', 'Outgoing'),
                                        ('Failed', 'Failed'),
                                        ('Reported', 'Reported'),
                                        ('Except', 'Do not Report'),
                                    ], string='Metrc Retail Status', default='Draft',
                                    index=True, copy=False,
                                    states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    customer_type = fields.Selection(related='partner_id.customer_type')

    patient_license_number = fields.Many2one(comodel_name="metrc.license", string='Patient License',
                                         domain="[('base_type', '=', 'Patient')]",
                                         states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    caregiver_license_number = fields.Char(string='Caregiver License',
                                           states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    ext_patient_id_method = fields.Many2one(comodel_name='patient.id.method', string='External Patient ID Method',
                                        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    @api.depends('order_line', 'order_line.product_id', 'order_line.product_id.is_metric_product', 'warehouse_id', 'team_id')
    def _compute_license_required(self):
        super(SaleOrder, self)._compute_license_required()
        for order in self:
            if order.team_id and order.team_id.metrc_retail_reporting:
                order.license_required = False

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        if order.team_id and not order.facility_license_id:
            order.facility_license_id = order.warehouse_id and order.warehouse_id.license_id or False
        return order

    # @api.multi
    def _cron_flag_retail_sales(self, force_report_date=False, automatic=True, raise_for_error=False):
        if automatic:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        sync_start_date = False
        dt_now = datetime.now()
        if force_report_date and isinstance(force_report_date, datetime):
            sync_start_date = force_report_date
        else:
            sync_start_date = dt_now - timedelta(hours=24)
        orders = self.search([
                        ('state', 'in', ('sale', 'done')),
                        ('team_id.metrc_retail_reporting', '=', True),
                        ('write_date', '>=', fields.Datetime.to_string(sync_start_date)),
                        ('metrc_retail_state', 'not in', ('Except', 'Outgoing')),
                        '|', ('facility_license_id.sell_to_patients', '=', True),
                        ('facility_license_id.sell_to_consumer', '=', True)
                    ])
        for order in orders:
            order_todo = False
            packages_to_report = ''
            try:
                for move in order.order_line.filtered(lambda ol: ol.product_id.is_metric_product).mapped('move_ids'):

                    for move_line in move.move_line_ids.filtered(lambda ml:ml.state == 'done' and \
                                float_compare(ml.qty_done, ml.metrc_reported_qty,precision_rounding=ml.product_uom_id.rounding) > 0):
                        order_todo = True
                        packages_to_report += '<li>Package <strong> %s </strong> for quantity %f %s</li>' % (
                                                move_line.lot_id._get_metrc_name(),
                                                move.product_id.to_metrc_qty(move_line.qty_done),
                                                move.product_id.metrc_uom_id.name
                                                    if move.product_id.diff_metrc_uom and move.product_id.metrc_uom_id
                                                        else move.product_id.uom_id.name,
                                            )
                if order_todo:
                    order.metrc_retail_state = 'Outgoing'
                    msg_body = '''
                    <p><h4>Following retails sale package(s) are scheduled for reporting to Metrc: </h4><ul>%s</ul></p>
                    ''' % (packages_to_report)
                    order.message_post(body=msg_body)
                if automatic:
                    cr.commit()
            except Exception as ex:
                if automatic:
                    cr.rollback()
                _logger.error('Error during flagging retails orders \n%s' % str(ex))
                if raise_for_error:
                    raise ex
        if automatic:
            cr.commit()
            cr.close()
        return True

    def _cron_repot_retail_sales(self, batch_size=100, automatic=True, raise_for_error=False):
        metrc_account = self.env.user.ensure_metrc_account()
        if automatic:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        domain = [
            ('state', 'in', ('sale', 'done')),
            ('team_id.metrc_retail_reporting', '=', True),
            ('metrc_retail_state', '=', ('Except', 'Outgoing')),
            '|', ('facility_license_id.sell_to_patients', '=', True),
            ('facility_license_id.sell_to_consumer', '=', True),
        ]
        orders_by_facility = self.read_group(domain, ['id', 'facility_license_id'], ['facility_license_id'])
        _logger.info('metrc.retail: starting metrc retail sale reporting')
        for facility in orders_by_facility:
            facility_domain = domain + [('facility_license_id', '=', facility['facility_license_id'][0])]
            orders = self.search(facility_domain)
            _logger.info('metrc.retail: processing %d retail order for facility %s' % (
                                        len(orders), facility['facility_license_id'][1]))
            for order_chunk in split_every(batch_size, orders):
                _logger.info('metrc.retail: processing batch of %d retail order for facility %s' % (
                                        len(order_chunk), facility['facility_license_id'][1]))
                order_data = []
                facility_license_id = False
                for order in order_chunk:
                    if (order.customer_type == 'Patient' and not order.patient_license_number) or \
                       (order.customer_type == 'Caregiver' and (not order.patient_license_number or not order.caregiver_license_number)) or \
                       (order.customer_type == 'ExternalPatient' and (not order.patient_license_number or not order.ext_patient_id_method)):
                        error_message = "<p>Customer <b>{}</b> is of <b>{}</b> type.<br/></p>" \
                                        "<p>Make sure Patient/Caregiver License or External ID Method set correctly".format(order.partner_id.name, order.customer_type)
                        if not raise_for_error:
                            order.message_post(body=_(error_message))
                        continue
                    facility_license_id = order.facility_license_id
                    transactions = []
                    for order_line in order.order_line.filtered(lambda ol: ol.product_id.is_metric_product):
                        transactions.extend([{
                                'PackageLabel': ml.lot_id._get_metrc_name(),
                                'Quantity': -(ml.product_id.to_metrc_qty(ml.qty_done)) if (ml.location_id.usage == 'customer' and \
                                              ml.location_dest_id.usage == 'internal') else ml.product_id.to_metrc_qty(ml.qty_done),
                                'UnitOfMeasure': ml.product_id.metrc_uom_id.name 
                                                            if ml.product_id.diff_metrc_uom and ml.product_id.metrc_uom_id 
                                                                    else ml.product_uom_id.name,
                                'TotalAmount': -(ml.qty_done * order_line.price_unit) if (ml.location_id.usage == 'customer' and \
                                              ml.location_dest_id.usage == 'internal') else (ml.qty_done * order_line.price_unit),
                            } for move in order_line.mapped('move_ids')
                                 for ml in move.move_line_ids.filtered(lambda ml:ml.state == 'done' and ml.lot_id and \
                                    float_compare(ml.qty_done, ml.metrc_reported_qty,precision_rounding=ml.product_uom_id.rounding) > 0)
                         ])
                    if transactions:
                        line_vals = {
                            'SalesDateTime': fields.Datetime.from_string(order.date_order).isoformat(),
                            'SalesCustomerType': order.customer_type,
                            'Transactions': transactions,
                        }
                        if order.customer_type != 'Consumer':
                            line_vals.update({
                                'PatientLicenseNumber': order.patient_license_number.license_number,
                            })
                        if order.customer_type == 'Caregiver':
                            line_vals.update({
                                'CaregiverLicenseNumber': order.caregiver_license_number,
                            })
                        if order.customer_type == 'ExternalPatient':
                            line_vals.update({
                                'IdentificationMethod': order.ext_patient_id_method.name,
                            })
                        order_data.append(line_vals)
                if order_data:
                    try:
                        uri = '{}/{}/{}'.format('/sales', metrc_account.api_version, 'receipts')
                        params = {'licenseNumber': facility_license_id.license_number}
                        res = metrc_account.fetch('POST', uri, params=params, data=order_data)
                        for order in order_chunk:
                            order_done = False
                            packages_reported = ''
                            for move in order.order_line.filtered(lambda ol: ol.product_id.is_metric_product).mapped('move_ids'):
                                for move_line in move.move_line_ids.filtered(lambda ml:ml.state == 'done' and ml.lot_id and \
                                        float_compare(ml.qty_done, ml.metrc_reported_qty,precision_rounding=ml.product_uom_id.rounding) > 0):
                                    order_done = True
                                    move_line.write({'metrc_reported_qty': move_line.qty_done})
                                    packages_reported += '<li>Package <strong> %s </strong> for quantity %f %s</li>' % (
                                                move_line.lot_id._get_metrc_name(),
                                                -move.product_id.to_metrc_qty(move_line.qty_done) if (move_line.location_id.usage == 'customer' and \
                                              move_line.location_dest_id.usage == 'internal') else move.product_id.to_metrc_qty(move_line.qty_done),
                                                move.product_id.metrc_uom_id.name 
                                                            if move_line.product_id.diff_metrc_uom and move_line.product_id.metrc_uom_id
                                                                else move_line.product_id.uom_id.name,
                                            )
                            if order_done and packages_reported:
                                order.write({'metrc_retail_state': 'Reported'})
                                msg_body = '''
                                <p><h4>Following retail sale packages were reported Metrc: </h4><ul>%s</ul></p>
                                ''' % (packages_reported)
                                order.message_post(body=msg_body)
                        if automatic:
                            cr.commit()
                        _logger.info('metrc.retail: finished processing batch of %d retail order for facility %s' % (
                                                            len(order_chunk), facility['facility_license_id'][1]))
                    except Exception as ex:
                        if automatic:
                            cr.rollback()
                        _logger.error('metrc.retail: Error during reporting retail orders  to Metrc \n%s' % str(ex))
                        if raise_for_error:
                            raise ex
                        else:
                            metrc_account.log_exception()
        _logger.info('metrc.retail: end of metrc retail sale reporting')
        if automatic:
            cr.commit()
            cr.close()
        return True
