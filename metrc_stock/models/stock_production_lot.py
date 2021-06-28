# -*- coding: utf-8 -*-

import logging
import math
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, registry,  _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, float_round

_logger = logging.getLogger(__name__)


class StockProductionLot(models.Model):
    _name = 'stock.production.lot'
    _inherit = ['stock.production.lot', 'mail.activity.mixin']
    _labtest_states = [
        ("NotSubmitted", "NotSubmitted"),
        ("SubmittedForTesting", "SubmittedForTesting"),
        ("TestFailed", "TestFailed"),
        ("TestPassed", "TestPassed"),
        ("TestingInProgress", "TestingInProgress"),
        ("AwaitingConfirmation", "AwaitingConfirmation"),
        ("RetestFailed", "RetestFailed"),
        ("RetestPassed", "RetestPassed"),
        ("Remediated", "Remediated"),
        ("SelectedForRandomTesting", "SelectedForRandomTesting"),
        ("NotRequired", "NotRequired"),
    ]
    _copy_exclusions = [
        'x_raw_materials_list',
    ]

    metrc_qty = fields.Float(string='Metrc Quantity', digits='Product Unit of Measure')
    metrc_uom_id = fields.Many2one(comodel_name='uom.uom', compute='_compute_metrc_uom')
    is_metric_product = fields.Boolean(related="product_id.is_metric_product")
    labtest_state = fields.Selection(selection=_labtest_states, default="NotSubmitted")
    testing_state_date = fields.Date()
    metrc_tag = fields.Char(string='Metrc Tag', tracking=True)
    is_legacy_lot = fields.Boolean(tracking=True)
    metrc_id = fields.Integer(string="Metrc ID", tracking=True)
    name_readonly = fields.Boolean(help="Technical field to determine lot name is editable or not.")
    batch_number = fields.Char(string='Production Batch No.')
    is_production_batch = fields.Boolean(string='Production Batch?')
    is_edible = fields.Boolean(related="product_id.metrc_item_cat_id.is_edible")
    is_flower = fields.Boolean(related="product_id.metrc_item_cat_id.is_flower")
    harvest_date = fields.Date(string="Harvest Date")
    expiration_date = fields.Date(String="Exp. Date")
    thc_mg = fields.Float(string="THC(mg)")
    thc_percent = fields.Float(string="THC(%)") 
    metrc_product_name = fields.Char(string="Metrc Product")

    def toggle_name_readonly(self):
        for lot in self:
            lot.name_readonly = not lot.name_readonly

    _sql_constraints = [
        ('metrc_tag_ref_uniq', 'unique (metrc_tag, product_id)', 'The combination of Metrc tag and product must be unique !'),
    ]

    @api.constrains('name', 'metrc_tag')
    def prevent_duplicate_lot(self):
        for lot in self:
            existing_lot = self.sudo().search(['|', ('name', '=', lot.name), ('name', '=', lot.metrc_tag), ('id', '!=', lot.id)])
            if existing_lot:
                raise UserError(_("Lot number {} can not be duplicated.".format(lot.metrc_tag if lot.is_legacy_lot else lot.name)))

    def get_count(self, finished_move_lines):
        self.ensure_one()
        lot_qty = sum(finished_move_lines.filtered(lambda l: l.lot_id == self).mapped('qty_done'))
        each_count = int(math.ceil(lot_qty))
        return min(500, each_count)

    @api.depends('product_id', 'product_uom_id')
    def _compute_metrc_uom(self):
        for lot in self:
            lot.metrc_uom_id =  lot.product_id.metrc_uom_id if lot.product_id.diff_metrc_uom and lot.product_id.metrc_uom_id else lot.product_id.uom_id

    def _is_package_exist_on_metrc(self, label, license=False, raise_for_error=True):
        metrc_account = self.env.user.ensure_metrc_account()
        uri = '/{}/{}/{}'.format('packages', metrc_account.api_version, label)
        params = {'licenseNumber': license} if license else {}
        return metrc_account.fetch('GET', uri, params=params, raise_for_error=raise_for_error)

    def _get_metrc_name(self):
        self.ensure_one()
        return self.metrc_tag if self.is_legacy_lot else self.name

    def get_metrc_package_qty(self):
        wiz = self.env['stock.package.wizard'].create({'lot_id': self.id})
        action = self.env.ref('metrc_stock.action_view_stock_package_wizard').read()[0]
        action.update({
            'views': [(self.env.ref('metrc_stock.wizard_view_stock_package_wizard_form').id, 'form')],
            'res_id': wiz.id
        })
        return action

    def _fetch_metrc_package(self, license=False):
        metrc_account = self.env.user.ensure_metrc_account()
        params = {}
        if license:
            params = {'licenseNumber': license.license_number}
        uri = '/{}/{}/{}'.format('packages', metrc_account.api_version, self._get_metrc_name())
        return metrc_account.fetch('GET', uri, params=params, raise_for_error=False)

    def sync_package(self):
        wiz = self.env['stock.package.wizard'].create({'lot_id': self.id})
        action = self.env.ref('metrc_stock.action_view_stock_package_wizard').read()[0]
        action.update({
            'views': [(self.env.ref('metrc_stock.wizard_view_stock_package_wizard_form').id, 'form')],
            'res_id': wiz.id
        })
        return action

    @api.model
    def _push_packages(self, warehouse, automatic=True):
        metrc_account = self.env.user.ensure_metrc_account()
        license = warehouse.license_id
        reason_note = "Go-Live Adjustments"
        adjust_reason = warehouse.default_adjust_reason_id
        if not metrc_account:
            return False
        if not adjust_reason:
            _logger.error("Default Metrc adjustment reason not configured on warehouse {}".format(warehouse.name))
            return False
        if automatic:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        processed_lots = self.env['stock.production.lot']
        unprocessed_lots = {'uom_differ': [], 'adjust_error': [], 'create_error': []}
        locations = self.env['stock.location'].search([('location_id', 'child_of', warehouse.view_location_id.id), ('usage', '=', 'internal')])
        lots_to_process = self.search([('is_metric_product', '=', True), ('quant_ids.location_id', 'in', locations.ids)])
        lots_to_process = lots_to_process.filtered(lambda l: l.metrc_id == 0)
        _logger.info("metrc push packages cron: started pushing {} packages for license {}".format(len(lots_to_process), license.license_number))
        if lots_to_process:
            lots_to_process.mapped('product_id')._update_metrc_id(metrc_account, license)
        for lot in lots_to_process:
            if lot.product_id.sync_status in ['not_synced', 'partial']:
                model_data = lot.product_id.get_metrc_model_data(license=license)
                if model_data.metrc_id == 0:
                    lot.product_id._update_dependant_objects(license, raise_for_error=False)
                    lot.product_id._match_with_metrc(license, raise_for_error=False)
            resp = lot._fetch_metrc_package()
            if resp:
                if resp['UnitOfMeasureName'] != lot.metrc_uom_id.name:
                    message = "<b>Product unit of measure differs from the unit of measure in metrc.</b><br/>"
                    message += "Odoo UOM | Metrc UOM<br/>"
                    message += "=====================<br/>"
                    message += "{} | {}".format(lot.metrc_uom_id.name, resp['UnitOfMeasureName'])
                    lot._schedule_todo_activity(message=message)
                    unprocessed_lots['uom_differ'].append(lot)

                elif float_compare(lot.product_id.from_metrc_qty(resp['Quantity']), lot.product_qty, precision_rounding=lot.product_uom_id.rounding) == 0:
                    processed_lots |= lot
                else:
                    try:
                        lot._adjust_in_metrc(metrc_account, license, resp['Quantity'], reason=adjust_reason, note=reason_note)
                        processed_lots |= lot
                    except UserError as e:
                        lot._schedule_todo_activity(message=e)
                        unprocessed_lots['adjust_error'].append(lot)
                if automatic:
                    cr.commit()
            else:
                lot_warehouses = lot.get_all_warehouse()
                if lot_warehouses and len(lot_warehouses) > 1:
                    msg = "<p>Lot <b>{}</b> is available in more then one warehouses.<br/>This lot can not be created in METRC.</p><ul>".format(lot._get_metrc_name())
                    for quant in lot.quant_ids.filtered(lambda q: q.location_id.usage == 'internal'):
                        msg += '<li> {}, Quantity:{} {}</li>'.format(quant.location_id.display_name, quant.quantity, quant.product_uom_id.name)
                    msg += "</ul>"
                    unprocessed_lots['create_error'].append(lot)
                    lot._schedule_todo_activity(message=msg)
                    if automatic:
                        cr.commit()
                    continue
                try:
                    lot._create_package_on_metrc(lot._get_metrc_name(), license.license_number, lot.product_id, quantity=lot.product_qty)
                    processed_lots |= lot
                except UserError as e:
                    lot._schedule_todo_activity(message=e)
                    unprocessed_lots['create_error'].append(lot)
                if automatic:
                    cr.commit()
            lot._update_metrc_id()
            if automatic:
                cr.commit()
        _logger.info("metrc push packages cron: finished pushing {} out of {} packages for license {}".format(len(processed_lots), len(lots_to_process), license.license_number))
        msg = "<p><b>Metrc push statistics for the metrc packages in warehouse {} for license {}.</b></p><ul>".format(warehouse.name, warehouse.license_id.license_number)
        if processed_lots:
            processed_lots.write({'name_readonly': True})
            msg += "<li><b>{}</b> of total <b>{}</b> lots are processed successfully.</li>".format(len(processed_lots), len(lots_to_process))
        if any([len(l) > 0 for l in unprocessed_lots.values()]):
            if unprocessed_lots['uom_differ']:
                msg += "<li><b>{}</b> of total <b>{}</b> lots ware not processed due to unit of measure mismatch. Lot numbers are as follows:<br/>{}</li>".format(len(unprocessed_lots['uom_differ']), len(lots_to_process), ','.join([l._get_metrc_name() for l in unprocessed_lots['uom_differ']]))
            if unprocessed_lots['adjust_error']:
                msg += "<li><b>{}</b> of total <b>{}</b> lots ware not processed due to error while package adjustment. Lot numbers are as follows:<br/>{}</li>".format(len(unprocessed_lots['adjust_error']), len(lots_to_process), ','.join([l._get_metrc_name() for l in unprocessed_lots['adjust_error']]))
            if unprocessed_lots['create_error']:
                msg += "<li><b>{}</b> of total <b>{}</b> lots ware not processed due to error while package creation. Lot numbers are as follows:<br/>{}</li>".format(len(unprocessed_lots['create_error']), len(lots_to_process), ','.join([l._get_metrc_name() for l in unprocessed_lots['create_error']]))
            msg += "</ul>"
            msg += "<p><b>NOTE: Please check your activities to do.</b></p>"
        if lots_to_process:
            mail_mail = self.env['mail.mail'].create({
                'notification': True,
                'body_html': msg,
                'subject': 'ODOO -> METRC Package push results.',
                'email_to': self.env.user.email
                })
            mail_mail.send()
        if automatic:
            cr.commit()
            cr.close()
        return True

    def _update_metrc_id(self):
        for lot in self:
            resp = lot._fetch_metrc_package()
            if resp:
                lot.metrc_id = resp['Id']
                lot.metrc_qty = resp['Quantity']
                lot.labtest_state = resp['LabTestingState']
                lot.testing_state_date = resp['LabTestingStateDate']
                lot.is_production_batch = resp['IsProductionBatch']
                lot.batch_number = resp['ProductionBatchNumber']
            else:
                _logger.info(_("Package {} not found on metrc for product {}.".format(lot._get_metrc_name(), lot.product_id.metrc_name)))

    def _schedule_todo_activity(self, message="Action Required!"):
        self.ensure_one()
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        model_obj = self.env['ir.model']._get('stock.production.lot')
        self.env['mail.activity'].create({
            'activity_type_id': activity_type.id,
            'res_id': self.id,
            'res_model_id': model_obj.id,
            'user_id': self.env.uid,
            'note': _(message)
        })

    def get_all_warehouse(self):
        self.ensure_one()
        StockWarehouse = self.env['stock.warehouse']
        warehouse = StockWarehouse
        locations = self.quant_ids.mapped('location_id').filtered(lambda l: l.usage == 'internal')
        for loc in locations:
            warehouse |= loc.get_warehouse()
        return warehouse if warehouse.ids else False

    def create_in_metrc(self):
        for lot in self:
            resp = lot._fetch_metrc_package()
            if not resp:
                if lot.product_qty == 0.0:
                    raise UserError(_("Package with 0.0 quantity can not be created in metrc."))
                warehouse = lot.get_all_warehouse()
                locations = self.quant_ids.mapped('location_id').filtered(lambda l: l.usage == 'internal')
                if not warehouse:
                    raise UserError(_("Not able to find the warehouse where this lot is."))
                if len(warehouse) > 1:
                    msg = "Lot {} is available in more then one warehouses. \nThis lot can not be created in METRC.".format(lot._get_metrc_name())
                    for quant in lot.quant_ids.filtered(lambda q: q.location_id.usage == 'internal'):
                        msg += '\n- {}, Quantity-{} {}'.format(quant.location_id.display_name, quant.quantity, quant.product_uom_id.name)
                    raise UserError(_(msg))
                license = locations and locations.mapped('facility_license_id') or False
                if license:
                    lot._create_package_on_metrc(lot._get_metrc_name(), license.license_number, lot.product_id, quantity=lot.product_qty)
                    lot._update_metrc_id()
                    lot.name_readonly = True
                else:
                    raise UserError(_("Facility license not found. Please check your warehouse configuration."))
            else:
                raise UserError(_("Package {} already exists in metrc.".format(lot._get_metrc_name())))

    def _adjust_in_metrc(self, account, license, package_qty, reason=False, note="", delta=False):
        quantity = self.product_qty - self.product_id.to_metrc_qty(package_qty)
        if not reason:
            location = self.env['stock.location'].search([('facility_license_id', '=', license.id)], limit=1)
            reason = location.default_adjust_reason_id
        if delta:
            quantity = self.product_id.to_metrc_qty(package_qty)
        data = [{
            "Label": self._get_metrc_name(),
            "Quantity": quantity,
            "UnitOfMeasure": self.product_uom_id.name,
            "AdjustmentReason": reason.name,
            "AdjustmentDate": fields.Date.to_string(fields.Date.today()),
            "ReasonNote": note
        }]
        url = '{}/{}/{}'.format('/packages', account.api_version, 'adjust')
        params = {'licenseNumber': license.license_number}
        return account.fetch('POST', url, params=params, data=data)

    def show_reserved_documents(self):
        reserved_objects = ""
        context = dict()
        if self.env.context.get('production'):
            context.update({'production': self.env.context['production']})
        if self.env.context.get('picking'):
            context.update({'picking': self.env.context['picking']})
        for lot in self:
            message = lot.with_context(self.env.context, context).check_reservations()
            if message:
                reserved_objects += message
        if reserved_objects:
            wiz = self.env['lot.split.wizard'].create({
                'reserved_objects': reserved_objects
                })
            return {
                    'name': _('Lot Reservation Details'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'lot.split.wizard',
                    'res_id': wiz.id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': False,
                    'views': [(self.env.ref('metrc.split_lot_reserved_message_form').id, 'form')],
                    'context': {},
                    'domain': [],
                    'target': 'new'
                }
        return False

    @api.model
    def _sync_packages(self):
        ProductProduct = self.env['product.product']
        # ProductTempate = self.env['product.template']
        # MetrcItemCategory = self.env['metrc.product.category']
        StockProductionLot = self.env['stock.production.lot']
        # ProductUom = self.env['uom.uom']
        metrc_account = self.env.user.ensure_metrc_account()
        url = '/{}/{}/{}'.format('packages', metrc_account.api_version, 'active')
        for license in self.env['metrc.license'].search([('base_type', '=', 'Internal')]):
            warehouse = self.env['stock.warehouse'].search([('license_id', '=', license.id)], limit=1)
            if warehouse:
                params = {
                    'licenseNumber': license.license_number,
                    'lastModifiedEnd': datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),
                    'lastModifiedStart': datetime.strftime(datetime.now() - relativedelta(hours=24), '%Y-%m-%d %H:%M:%S'),
                }
                modified_packages = metrc_account.fetch('GET', url, params=params)
                modified_package_labels = [pack['Label'] for pack in modified_packages]
                package_lots = self.search(['|', '&', ('is_legacy_lot', '=', True), ('metrc_tag', 'in', modified_package_labels), ('name', 'in', modified_package_labels)])
                package_lot_dict = {lot._get_metrc_name(): lot.product_qty for lot in package_lots}
                package_lot_id_dict = {lot._get_metrc_name(): lot for lot in package_lots}
                packages_not_processed = []
                for package in modified_packages:
                    product = ProductProduct._get_product(license, package['Item']['ProductName'], package['UnitOfMeasureName'], package['Item']['ProductCategoryName'])
                    if package['Label'] in package_lot_dict.keys():
                        lot = package_lot_id_dict[package['Label']]
                        lot.write({
                            'labtest_state': package['LabTestingState'],
                            'testing_state_date': package['LabTestingStateDate']
                            })
                        if lot.product_id == product:
                            metrc_qty = lot.product_id.from_metrc_qty(package['Quantity'])
                            product = product.with_context(lot_id=lot.id,
                                                                    #location=warehouse.lot_stock_id.id if warehouse.lot_stock_id else  False,
                                                                    warehouse=warehouse.id)
                            if float_compare(metrc_qty, product.virtual_available, precision_rounding=lot.product_uom_id.rounding) != 0:
                                lot._adjust_lot(package['Quantity'], location_id=warehouse.lot_stock_id, warehouse_id=warehouse)
                            else:
                                _logger.info('Nothing to adjust for package %s'%(lot._get_metrc_name()))
                        elif lot.product_id.uom_id.name != package['UnitOfMeasureName'] or lot.product_id.item_cat_id.name != package['Item']['ProductCategoryName']:
                            lot.product_id.with_context({'metrc_license': license.license_number})._do_metrc_force_update()
                    else:
                        if product:
                            new_lot = StockProductionLot.create({
                                'name': package['Label'],
                                'product_id': product.id,
                                'labtest_state': package['LabTestingState'],
                                'testing_state_date': package['LabTestingStateDate']
                                })
                            new_lot._adjust_lot(package['Quantity'], location_id=warehouse.lot_stock_id, warehouse_id=warehouse)
                        else:
                            incoming_transfer_moves = self.env['stock.move.line'].search([('move_id.picking_code', '=', 'incoming'),
                                                                                          ('move_id.state', 'not in', ['done', 'cancel']),
                                                                                          '|', ('lot_name', '=', package['Label']),
                                                                                          '|', '&', ('lot_id', '!=', False),
                                                                                          '&', ('lot_id.is_legacy_lot', '=', True),
                                                                                          ('lot_id.metrc_tag', '=', package['Label']),
                                                                                          ('lot_id.name', '=', package['Label'])])
                            if not incoming_transfer_moves:
                                packages_not_processed.append(package)
                if packages_not_processed:
                    mail_channel = self.env.ref('metrc.channel_metrc_messages')
                    message_body = "<b>[{}]Following packages not processed during package sync.</b><br/>".format(license.license_number)
                    for pack in packages_not_processed:
                        message_body += "<b>{}</b> [{}] [{}]<br/>".format(pack['ProductName'], pack['Label'], pack['Quantity'])
                    mail_channel.message_post(body=_(message_body), message_type="notification", subtype_xmlid="mail.mt_comment")
            else:
                _logger.info('No warehouse found for license %s, skipping package synchronization'%(license.license_number))

    def _adjust_lot(self, quantity, downstream=True, location_id=False, warehouse_id=False):
        if location_id:
            stock_location = location_id
        else:
            # Do adjustment on first internal location found based on user security
            lot_location = self.quant_ids.mapped('location_id').filtered(lambda l: l.usage == 'internal')
            stock_location = lot_location[0] if lot_location else False
        if warehouse_id:
            warehouse = warehouse_id
        else:
            default_warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
            warehouse = stock_location.get_warehouse() or default_warehouse

        if not warehouse or not stock_location:
            raise UserError(_('Missing warehouse and location details for inventory adjustment.'))

        if not warehouse.license_id:
            raise UserError(_("Warehouse {} is not configured with facility license. Please configure one to proceed.". format(warehouse.name)))
        reason = location_id.default_adjust_reason_id
        if not reason:
            raise UserError(_('Default Package adjustment reason not configured on Location {}.'
                                '\n Please configure default adjustment reason on the above Location.'.format(location_id.display_name)))
        company = warehouse.company_id or warehouse.license_id.company_id
        inv_adjst = self.env['stock.inventory'].create({
            'name': 'INV-ADJ: %s (Metrc Package Adjustment) ' % (self.product_id.name, ),
            'location_ids': [(4, stock_location.id)],
            'product_ids': [(4, self.product_id.id)],
            'warehouse_id': warehouse.id,
            'company_id': company.id,
            'reason_id': reason.id,
            'reason_note': 'Lot/Serials inventory adjustment',
            'facility_license_id': warehouse.license_id.id,
            'downstream': downstream,
        })
        inv_adjst.action_start()
        line = inv_adjst.line_ids.filtered(lambda l: l.product_id == self.product_id and l.prod_lot_id.id == self.id)
        if line:
            line.write({
                'product_qty': line.product_id.from_metrc_qty(quantity),
                'do_not_adjust': True,
            })
        else:
            inv_adjst.write({'line_ids': [(0, 0, {
                    'product_id': l.product_id.id,
                    'product_uom_id': l.product_id.uom_id.id,
                    'reason_id': reason.id,
                    'reason_note': inv_adjst.reason_note,
                    'location_id': inv_adjst.location_id.id,
                    'prod_lot_id': l.id,
                    'product_qty': l.product_id.from_metrc_qty(quantity),
                    'do_not_adjust': True,
                }) for l in [self] if quantity >= 0.0]
            })
        try:
            inv_adjst.with_context({'bypass_check': True, 'bypass_adjust': True})._action_done()
            inv_adjst.flush()
        except Exception as ex:
            _logger.error('cannot validate inventory adjustment[%s][ID:%d]' % (inv_adjst.name, inv_adjst.id))
            inv_adjst.action_cancel_draft()
        if inv_adjst.state == 'done':
            msg = _("""<p><span>Adjusted product lot/serial quantity via following inventory adjustment for warehouse <em>%s</em> location <em>%s</em>.</span>
                        <ul><li><a href=# data-oe-model=stock.inventory data-oe-id=%d>%s</a></li></ul></p>""") % (warehouse.name, stock_location.name, inv_adjst.id, inv_adjst.name)
            self.message_post(body=msg, message_type="notification", subtype_xmlid="mail.mt_comment")

    def _create_package_on_metrc(self, lot_name, license, product_id, ingredients=[], quantity=0, raise_for_error=True):
        metrc_account = self.env.user.ensure_metrc_account()
        if metrc_account:
            uri = '/{}/{}/{}'.format('packages', metrc_account.api_version, 'create')
            data = [{
                'Tag': lot_name,
                'Location': "n/a",
                'Item': product_id.metrc_name,
                'Quantity': product_id.to_metrc_qty(quantity),
                'UnitOfMeasure':  product_id.metrc_uom_id.name if product_id.diff_metrc_uom and product_id.metrc_uom_id else product_id.uom_id.name,
                'Ingredients': ingredients,
                'ActualDate': fields.Date.to_string(fields.Date.today()),
                'PatientLicenseNumber': 'n/a'
            }]
            params = {'licenseNumber': license}
            return metrc_account.fetch('POST', uri, params=params, data=data, raise_for_error=raise_for_error)

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        if vals.get('metrc_tag'):
            vals['metrc_tag'] = vals['metrc_tag'].upper()
        # check lot number on metrc
        lot = super(StockProductionLot, self).create(vals)
        license = self.env.context.get('license_number', False)
        if self.env.context.get('check_package_on_metrc') and license:
            result = self._is_package_exist_on_metrc(vals['name'], license)
            if not result:
                raise UserError(_('Lot number %s is not available on the metrc system, for more details you can check the logs in metrc account') % vals['name'])
        return lot

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        if vals.get('metrc_tag'):
            vals['metrc_tag'] = vals['metrc_tag'].upper()
        for lot in self:
            if 'is_legacy_lot' in vals and lot.metrc_id > 0 and lot.metrc_qty > 0.00 and not self.user_has_groups('metrc.group_metrc_admin'):
                raise UserError(_("Lot already synced. You can not change the value of Lagecy Lot field."))
            if lot.metrc_id > 0 and ((lot.is_legacy_lot and 'metrc_tag' in vals) or (not lot.is_legacy_lot and 'name' in vals)) and not self.user_has_groups('metrc.group_metrc_admin'):
                raise UserError(_("Lot already synced. You can not perform modifications."))
        return super(StockProductionLot, self).write(vals)

    def finish_package_in_metrc(self, license):
        params = {'licenseNumber': license}
        metrc_account = self.env.user.ensure_metrc_account()
        data = {
            'Label': self._get_metrc_name(),
            'ActualDate': fields.Date.to_string(fields.Date.today())
        }
        return metrc_account.fetch('POST', '/packages/v1/finish', data=data, params=params)
    
    def unfinish_package_in_metrc(self, license):
        params = {'licenseNumber': license}
        metrc_account = self.env.user.ensure_metrc_account()
        data = {
            'Label': self._get_metrc_name(),
        }
        return metrc_account.fetch('POST', '/packages/v1/unfinish', data=data, params=params)

    def split_lot_quantity(self):
        self.ensure_one()
        if self.metrc_id == 0:
            raise UserError(_("This lot is not synced with metrc.\nOnly metrc synced lot can be spllitted."))
        if float_is_zero(self.product_qty, precision_rounding=self.product_uom_id.rounding) or self.product_qty < 0.00:
            raise ValidationError(_("You can not split package (lot/serial) with zero or negative quantities."))
        location = self.quant_ids.filtered(lambda q: q.location_id.usage == 'internal').mapped('location_id')
        if not location:
            raise UserError(_("Product {} with lot number {} not found on any physical location.\n Can not proceed with splitting.".format(self.product_id.metrc_name, self._get_metrc_name())))
        wiz = self.env['lot.split.wizard'].create({
            'lot_id': self.id,
            'location_id': location[0].id,
            'warehouse_id': location[0].get_warehouse().id
        })
        return {
            'name': _('Batch Split'),
            'type': 'ir.actions.act_window',
            'res_model': 'lot.split.wizard',
            'res_id': wiz.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'views': [(self.env.ref('metrc_stock.split_lot_wizard_form').id, 'form')],
            'context': {'move_ref': self.name, 'custom_qty': True},
            'domain': [],
            'target': 'new'
        }

    def get_reserved_move_lines(self, locations):
        self.ensure_one()
        return self.env['stock.move.line'].search([('lot_id', '=', self.id), ('location_id', 'in', locations.ids), ('state', 'in', ['partially_available', 'assigned'])])

    def check_reservations(self, location=False):
        self.ensure_one()
        quants = self.quant_ids.filtered(lambda q: q.location_id.usage == 'internal')
        locations = quants.mapped('location_id')
        if location:
            locations = self.env['stock.location'].search([('location_id', 'child_of', location.id), ('usage', '=', 'internal')])
        quants = quants.filtered(lambda q: q.location_id in locations)
        msg = ''
        picking = self.env.context.get('picking', False)
        production = self.env.context.get('production', False)
        if any([q.reserved_quantity > 0.0 for q in quants]):
            reserved_objects = []
            for move_line in self.get_reserved_move_lines(locations):
                if move_line.picking_id and (picking and (picking.id != move_line.picking_id.id) or not picking):
                    if not (production and move_line.picking_id.origin == production.name):
                        reserved_objects.append(('stock.picking', move_line.picking_id.id, move_line.picking_id.name))
                elif move_line.move_id.raw_material_production_id and ((production and production.id != move_line.move_id.raw_material_production_id.id) or not production):
                    reserved_objects.append(('mrp.production', move_line.move_id.raw_material_production_id.id, move_line.move_id.raw_material_production_id.name))
                elif move_line.move_id.inventory_id:
                    reserved_objects.append(('stock.inventory', move_line.move_id.inventory_id.id, move_line.move_id.inventory_id.name))
            if reserved_objects:
                msg = "Lot {} is reserved on the following documents. Please process them first.<ul>".format(self._get_metrc_name())
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                for model_name, res_id, name in reserved_objects:
                    msg += '<li><a href="{}/web#id={}&model={}" target="new">{}</a></li>'.format(base_url, res_id, model_name, name)
                msg += "</ul><br/>"
        return msg

    def _update_custom_fields(self, source_lot):
        write_vals = {}
        for field, attrs in self.fields_get().items():
            if (field not in self._copy_exclusions) and attrs.get('manual', False):
                if attrs['type'] == 'many2one':
                    write_vals.update({field: source_lot[field].id})
                elif attrs['type'] in ['one2many', 'many2many']:
                    write_vals.update({field: [(6, 0, source_lot[field].ids)]})
                else:
                    write_vals.update({field: source_lot[field]})
        self.write(write_vals)

    @api.model
    def _cron_do_import_packages(self, metrc_license=False, force_last_sync_date=False,
                                 automatic=True, raise_for_error=False, ignore_last_modfied_filter=False):
        metrc_account = self.env.user.ensure_metrc_account()
        StockProductionLot = self.env['stock.production.lot']
        ProductProduct = self.env['product.product']
        AdjustmentReason = self.env['metrc.package.adjust.reason']
        StockInventory = self.env['stock.inventory']
        existing_lots = StockProductionLot.search([])
        lot_object_dict = {lot._get_metrc_name(): lot for lot in existing_lots}
        licenses = False
        if not metrc_license:
            licenses = self.env['metrc.license'].search([('base_type', '=', 'Internal')])
        elif isinstance(metrc_license, int) or isinstance(metrc_license, (list, tuple)):
            licenses = self.env['metrc.license'].browse(metrc_license)
        elif isinstance(metrc_license, models.BaseModel):
            licenses = metrc_license
        locations = self.env['stock.location'].search([('facility_license_id', 'in', licenses.ids)])
        if automatic:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        # No need to filter licenses based on current users account.
        # Not every inventory user's metrc account will be associated with metrc license.
        # IT Will fix the issue of just being able to validate the outgoing pickings but other users are not.
        # licenses = licenses.filtered(lambda lic: lic.metrc_account_id == self.env.user.metrc_account_id)
        for location in locations:
            warehouse = location.get_warehouse()
            license = location.facility_license_id
            dt_now = datetime.now()
            new_lots = StockProductionLot
            lot_qtys = {}
            all_metrc_packs = {}
            packages_not_processed = []
            if force_last_sync_date and isinstance(force_last_sync_date, datetime):
                last_sync_date = force_last_sync_date
            elif ignore_last_modfied_filter:
                last_sync_date = dt_now - timedelta(minutes=2)
            else:
                last_sync_date = dt_now - timedelta(hours=23, minutes=59, seconds=0)
            while last_sync_date < dt_now:
                new_last_sync_date = last_sync_date + timedelta(hours=23, minutes=59, seconds=0)
                if new_last_sync_date > dt_now:
                    new_last_sync_date = dt_now
                params = {
                    'licenseNumber': license.license_number,
                }
                if not ignore_last_modfied_filter:
                    params.update({
                        'lastModifiedStart': last_sync_date.isoformat(),
                        'lastModifiedEnd': new_last_sync_date.isoformat(),
                    })
                uri = '/{}/{}/{}'.format('packages', metrc_account.api_version, 'active')
                metrc_packages = []
                try:
                    metrc_packages = metrc_account.fetch('GET', uri, params=params)
                except Exception as ex:
                    if automatic:
                        cr.rollback()
                    _logger.error('Error during package import \n%s' % str(ex))
                    last_sync_date = new_last_sync_date
                    if raise_for_error:
                        raise ex
                    else:
                        metrc_account.log_exception()
                if metrc_packages:
                    metrc_package_dict = {pack['Label']: pack for pack in metrc_packages}
                    all_metrc_packs.update(metrc_package_dict)
                while metrc_packages:
                    package = metrc_packages.pop()
                    product = ProductProduct._get_product(license, package['Item']['Name'],
                                                          package['UnitOfMeasureName'],
                                                          package['Item']['ProductCategoryName'])
                    if package['Label'] not in lot_object_dict.keys():
                        if product:
                            package_qty = product.from_metrc_qty(package['Quantity'])
                            lot = StockProductionLot.create({
                                'name': package['Label'],
                                'product_id': product.id,
                                'product_uom_id': product.uom_id.id,
                                'company_id': warehouse.company_id.id,
                                'labtest_state': package['LabTestingState'],
                                'testing_state_date': package['LabTestingStateDate'],
                                'metrc_id': package['Id'],
                                'metrc_qty': package_qty,
                            })
                            new_lots |= lot
                            lot_qtys.update({lot.id: package_qty})
                        else:
                            packages_not_processed.append(package)
                if automatic:
                    cr.commit()
                last_sync_date = new_last_sync_date
            if new_lots:
                reason = location.default_adjust_reason_id
                try:
                    inv_adjst = StockInventory.create({
                        'name': 'INITIAL INVENTORY FROM METRC[%s]' % (license.license_number),
                        'location_ids': [(4, location.id)],
                        'warehouse_id': warehouse.id,
                        'reason_id': reason.id,
                        'facility_license_id': license.id,
                        'start_empty': True,
                        'downstream': True,
                    })
                    inv_adjst._action_start()
                    inv_line_datas = []
                    for new_lot in new_lots:
                        if lot_qtys[new_lot.id] >= 0.0:
                            line_data = (0, 0, {
                                'product_id': new_lot.product_id.id,
                                'product_uom_id': new_lot.product_id.uom_id.id,
                                'location_id': inv_adjst.location_ids[0].id,
                                'prod_lot_id': new_lot.id,
                                'reason_id': reason.id,
                                'product_qty': float_round(lot_qtys[new_lot.id],
                                                           precision_rounding=new_lot.product_id.uom_id.rounding)
                            })
                            inv_line_datas.append(line_data)
                        else:
                            packages_not_processed.append(all_metrc_packs[new_lot._get_metrc_name()])
                    inv_adjst.write({'line_ids': inv_line_datas})
                    inv_adjst.with_context({'bypass_check': True, 'bypass_adjust': True})._action_done()
                    inv_adjst.flush()
                    if automatic:
                        cr.commit()
                except UserError as ue:
                    if automatic:
                        cr.rollback()
                    _logger.error('Error during inventory adjustment for newlu creted lots \n%s' % str(ue))
                    if raise_for_error:
                        raise ue
                    else:
                        metrc_account.log_exception()
                except ValidationError as ve:
                    if automatic:
                        cr.rollback()
                    _logger.error('Error during inventory adjustment for newlu creted lots \n%s' % str(ve))
                    if raise_for_error:
                        raise ve
                    else:
                        metrc_account.log_exception()
            if packages_not_processed:
                mail_channel = self.env.ref('metrc.channel_metrc_messages')
                message_body = '<b>[{}]Following packages not processed during initial package import.</b><br/>'.format(
                        license.license_number)
                for pack in packages_not_processed:
                    message_body += '<b>{}</b> [{}] [{}]<br/>'.format(pack['Item']['Name'], pack['Label'],
                                                                      pack['Quantity'])
                _logger.info(message_body)
                mail_channel.message_post(body=_(message_body), message_type='notification',
                                          subtype_xmlid='mail.mt_comment')
        if automatic:
            cr.commit()
            cr.close()
        return True
