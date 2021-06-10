# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    manifest_number = fields.Char(string='Manifest Number', copy=False)
    manifest_last_modified = fields.Date(copy=False)
    metrc_delivery_id = fields.Char(copy=False)

    not_metrc_enabled = fields.Boolean(string='Non Metrc licensed transfer', copy=False)

    transporter_license_id = fields.Many2one('metrc.license', string='Transporter License',
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    partner_license_id = fields.Many2one('metrc.license', string='Partner License',
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                tracking=True)
    facility_license_id = fields.Many2one(comodel_name='metrc.license', compute='_compute_facility_license',
                                string='Facility License',
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    arrival_date = fields.Datetime(string='Estimated Arrival Date',copy=False)
    processed_date = fields.Datetime(string='Transfer Metrc Received Date',
                                help='Transfer received date from Metrc, this will be used for '\
                                        'searching transfer based on manifest number.')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', copy=False,
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    driver_id = fields.Many2one('res.partner', copy=False,
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    driver_license_number = fields.Char(string='Driver\'s License Number',
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    route = fields.Text(string='Planned Route', copy=False)
    has_layover = fields.Boolean(string='Is Layover?', copy=False,
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    transfer_type_id = fields.Many2one('metrc.transfer.type', string='Metrc Transfer Type',
                                copy=False,
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    external_transfer = fields.Boolean(string='External Incoming Transfer', copy=False,
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                tracking=True)
    transfer_template_created = fields.Boolean(string='Outgoing Transfer Template', copy=False,
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                help='Flag to determine that the transfer template \
                                                is created or not for the picking.',
                                tracking=True)
    require_metrc_validation = fields.Boolean(string='Require Metrc Validation',
                                compute='_compute_metrc_validation',
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    moving_metrc_product = fields.Boolean(string='Processing Metrc Product',
                                compute='_compute_metrc_validation',
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    no_metrc = fields.Boolean(string='Do not report to Metrc',
                                states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                tracking=True, default=False)
    to_consolidate = fields.Boolean(compute='_check_consolidation', help='Technical field to determine that'
                                                        ' picking contains moves which can be consolidated.')
    metrc_transfer_count = fields.Integer(compute="_compute_metrc_transfer_count")

    def _compute_facility_license(self):
        for pick in self:
            if pick.picking_type_code in ['incoming', 'outgoing']:
                pick.facility_license_id = pick.picking_type_id.warehouse_id.license_id
            elif pick._is_in():
                pick.facility_license_id = pick.location_dest_id.get_warehouse() and pick.location_dest_id.get_warehouse().license_id
            elif pick._is_out():
                pick.facility_license_id = pick.location_id.get_warehouse() and pick.location_id.get_warehouse().license_id
            else:
                pick.facility_license_id = False

    def _check_consolidation(self):
        for picking in self:
            picking.to_consolidate = True if (picking.moving_metrc_product and
                                              (picking.state in ['assigned', 'confirmed']) and
                                              (picking.picking_type_code != 'incoming') and
                                              self.env.user.has_group('stock.group_stock_user') and
                                              self.env.user.has_group('metrc.group_metrc_user')) else False

    def _get_metrc_moves_todo(self):
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        move_lines_todo  = self.move_line_ids.filtered(lambda ml: ml.state not in ('done', 'cancel')
                                            and ml.product_id.is_metric_product
                                            and not ml.move_id._is_dropshipped()
                                            and not ml.move_id._is_dropshipped_returned())
                                            #and not float_is_zero(ml.qty_done, precision_digits=precision_digits))
        return move_lines_todo
    
    def _compute_metrc_transfer_count(self):
        MetrcTransfer = self.env['metrc.transfer']
        for picking in self:
            picking.metrc_transfer_count = MetrcTransfer.search_count([
                ('move_line_id', 'in', picking.move_line_ids.ids)
            ])

    def _is_in(self):
        '''
        Function to determine the products are coming in or not.
        Rgardless of the picking type code on the Operation type.
        Returns : Bool (True if the picking type code is incoming or
                        source location is a vendor location or transit location)
        '''
        return True if ((self.picking_type_code == 'incoming') or (self.location_id.usage in ['supplier', 'transit', 'inventory'])) else False

    def _is_out(self):
        '''
        Function to determine the products are going out or not.
        Rgardless of the picking type code on the Operation type.
        Returns : Bool (True if the picking type code is outgoing or
                        destination location is a customer location or transit location)
        '''
        return True if ((self.picking_type_code == 'outgoing') or (self.location_dest_id.usage in ['customer', 'transit', 'inventory'])) else False

    def _get_picking_type(self):
        if self._is_in():
            return 'incoming'
        elif self._is_out():
            return 'outgoing'
        else:
            return 'internal'

    def _split_create_backorder(self, backorder_moves=[]):
        '''
        Split lines  that needs
        '''
        backorders = self.env['stock.picking']
        StockMove = self.env['stock.move']
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        moves_to_backorder = self.move_lines

        move_lines_todo = self._get_metrc_moves_todo()
        moves_to_split = move_lines_todo.mapped('move_id')
        moves_to_backorder -= moves_to_split
        if moves_to_backorder or moves_to_split:
            for move in moves_to_split:
                # To know whether we need to create a backorder or not, round to the general product's
                qty_split = move.product_uom._compute_quantity(
                                            move.product_uom_qty - move.quantity_done, move.product_id.uom_id,
                                            rounding_method='HALF-UP')
                if not float_is_zero(qty_split, precision_digits=precision_digits):
                    new_move = move._split(qty_split)
                    moves_to_backorder += StockMove.browse(new_move)
            if moves_to_backorder and moves_to_backorder != self.move_lines:
                backorder_picking = self.copy({
                    'name': '/',
                    'move_lines': [],
                    'move_line_ids': [],
                    'backorder_id': self.id
                })
                self.message_post(body=_('The backorder <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> \
                        has been created.') % (backorder_picking.id, backorder_picking.name))
                moves_to_backorder.write({'picking_id': backorder_picking.id})
                moves_to_backorder.mapped('move_line_ids').write({'picking_id': backorder_picking.id})
                backorder_picking.action_assign()
                backorders |= backorder_picking
            return backorders
        else:
            return False

    @api.depends('move_lines', 'move_line_ids', 'move_line_ids.qty_done', 'move_line_ids.product_uom_qty')
    def _compute_metrc_validation(self):
        for pick in self:
            pick.require_metrc_validation = not pick.no_metrc and (pick._is_in() or pick._is_out()) and any(pick.move_lines
                                                .filtered(lambda ml: ml.state not in ('done', 'cancel'))
                                                    .mapped('product_id.is_metric_product')) and (pick.facility_license_id.metrc_type == 'metrc')

            pick.moving_metrc_product = True if pick._get_metrc_moves_todo() else False

    def _prepare_transfer_lot_message(self, move_lines_todo):
        message = ''.join(['<li>Product <strong>{}</strong>, package \
                            <strong>{}</strong> with processed quantities <em> {} {}</em>.</li>'\
                                .format(move.product_id.display_name,
                                        move.lot_id._get_metrc_name() if move.lot_id else move.lot_name,
                                        move.product_uom_qty,
                                        move.product_uom_id.name)
                                   for move in move_lines_todo])
        return message

    def _check_move_consume(self, move_lines_todo):
        invalid_lots = []
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for move_line in move_lines_todo:
            if not float_is_zero(move_line.lot_id.product_qty, precision_digits=precision_digits) and \
                float_compare(move_line.lot_id.product_qty, move_line.qty_done, precision_rounding=move_line.product_uom_id.rounding) != 0:
                invalid_lots.append(move_line.lot_id)
        if invalid_lots:
            msg = 'Can not consume partial quantities for Metrc enabled product packages. \
                    Review the package and processed quantities, below are packages and processed quantity details. \n'
            for lot in invalid_lots:
                msg += '\n- Product {}, package {} processed quantity is {} {} and \
                                    available quantity is {} {}.'.format(
                                                lot.product_id.name, lot._get_metrc_name(),
                                                move_line.qty_done, move_line.product_id.uom_id.name,
                                                move_line.lot_id.product_qty, move_line.product_id.uom_id.name)
            msg += '\n\n if you want to process partial packages quantity then spit the package to required quantity or\
                             removed detailed operation lines to skip and create backorder.'
            raise ValidationError(_(msg))
        return True

    def _create_transfer_template(self):
        metrc_account = self.env.user.ensure_metrc_account()
        move_lines_todo = self._get_metrc_moves_todo()
        facility_license_id = self.facility_license_id
        # self._check_move_consume(move_lines_todo)
        uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version, 'templates')
        now_dt = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now())).isoformat()
        scheduled_date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.scheduled_date)).isoformat() if self.scheduled_date else now_dt
        arrival_date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.arrival_date)).isoformat() if self.arrival_date else scheduled_date
        data = [{
            'Name': '%s:%s' % (self.group_id.sale_id.name, self.name) if (self.group_id and self.group_id.sale_id) else self.name,
            'TransporterFacilityLicenseNumber': self.transporter_license_id.license_number if self.transporter_license_id else '',
            'DriverOccupationalLicenseNumber': '50',
            'DriverName': self.driver_id and self.driver_id.name or '',
            'DriverLicenseNumber': self.driver_license_number or '',
            'PhoneNumberForQuestions': self.driver_id.phone if self.driver_id else '',
            'VehicleMake': self.vehicle_id and self.vehicle_id.model_id.name or '',
            'VehicleModel': self.vehicle_id and self.vehicle_id.model_id.brand_id.name or '',
            'VehicleLicensePlateNumber': self.vehicle_id and self.vehicle_id.license_plate or '',
            'Destinations': [{
                'RecipientLicenseNumber': self.partner_license_id.license_number,
                'TransferTypeName': self.transfer_type_id and self.transfer_type_id.name or 'Wholesale Manifest',
                'PlannedRoute': self.route,
                'EstimatedDepartureDateTime': scheduled_date,
                'EstimatedArrivalDateTime': arrival_date,
                'Transporters': [{
                    'TransporterFacilityLicenseNumber': self.transporter_license_id.license_number if self.transporter_license_id else '',
                    'DriverOccupationalLicenseNumber': '50',
                    'DriverName': self.driver_id and self.driver_id.name or '',
                    'DriverLicenseNumber': self.driver_license_number or '',
                    'PhoneNumberForQuestions': self.driver_id.phone if self.driver_id else '',
                    'VehicleMake': self.vehicle_id and self.vehicle_id.model_id.name or '',
                    'VehicleModel': self.vehicle_id and self.vehicle_id.model_id.brand_id.name or '',
                    'VehicleLicensePlateNumber': self.vehicle_id and self.vehicle_id.license_plate or '',
                    'IsLayover': self.has_layover,
                    'EstimatedDepartureDateTime': scheduled_date,
                    'EstimatedArrivalDateTime': arrival_date,
                }],
                'Packages': [{
                    'PackageLabel': move_line.lot_id._get_metrc_name(),
                    'WholesalePrice': move_line.move_id.sale_line_id.price_unit if move_line.move_id and move_line.move_id.sale_line_id else move_line.product_id.list_price
                } for move_line in move_lines_todo]
            }]
        }]
        params = {'licenseNumber': facility_license_id.license_number}
        metrc_ret = metrc_account.fetch('POST', uri, params=params, data=data, raise_for_error=False)

        if metrc_ret:
            uncertified_msg = 'Recipient License Number not specified.'
            if type(metrc_ret) == list and metrc_ret[0].get('message') == uncertified_msg:
                message = '''<p>
    <p>Customer <em>%s</em> license <em>%s</em> is either not Metrc enabled or Invalid license.</p>
    <p>You must create an external outgoing transfer for the customer in Metrc manually.</p>
    <p> Package Details: </p>
    <ul>
    %s
    </ul>
    <p>Facility License : <em>%s</em></p>
                </p>''' % (self.partner_id.display_name, self.partner_license_id.license_number,
                        self._prepare_transfer_lot_message(move_lines_todo),
                        facility_license_id.license_number)
                wiz = self.env['stock.transfer.wizard'].create({
                                                'picking_id': self.id,
                                                'message': message,
                                            })
                action = self.env.ref('metrc_stock.action_view_stock_transfer_wizard').read()[0]
                action.update({
                    'views': [(self.env.ref('metrc.wizard_view_stock_transfer_template_common_form').id, 'form')],
                    'res_id': wiz.id
                })
                self.not_metrc_enabled = True
                return action
            else:
                # TODO: add better error handling here, this is quick code and should work.
                message = 'Metrc Error (facility license used : {})'.format(facility_license_id.license_number)
                message += ' : \n\n'
                if type(metrc_ret) in (list, tuple):
                    message += '.\n'.join([e_line.get('message') for e_line in metrc_ret])
                elif metrc_ret.get('Message'):
                    message += metrc_ret.get('Message')
                else:
                    message += 'Unexpected error ! please report this to your administrator.'
                raise UserError(message)
        self.transfer_template_created = True
        self.message_post(body=_('<p>Metrc transfer template has been created by <em> %s </em>.</p>') % (self.env.user.name))
        return True

    def create_transfer_template_validate(self):
        ret = self._create_transfer_template()
        if type(ret) == dict:
            return ret
        # Check backorder should check for other barcodes
        if self._check_backorder():
            backorders_ids = self._split_create_backorder()
            return backorders_ids
        return ret

    def _create_external_picking(self):
        metrc_account = self.env.user.ensure_metrc_account()
        move_lines_todo = self._get_metrc_moves_todo()
        # 1) create lot that need to be created, and if their lot then just update the lot.
        try:
            for move_line_id in move_lines_todo:
                existing_lot_udpates = False
                product = move_line_id.product_id
                picking_type_id = self.picking_type_id
                lot_label = False
                if picking_type_id.use_create_lots:
                    lot_label = move_line_id.lot_name
                if picking_type_id.use_existing_lots and move_line_id.lot_id:
                    lot_label = move_line_id.lot_id._get_metrc_name()
                    existing_lot_udpates = move_line_id.lot_id._fetch_metrc_package()
                if not lot_label:
                    raise UserError(_('You need to supply a lot/serial number for. %s')%(move_line_id.display_name))
                if not self.env['stock.production.lot']._is_package_exist_on_metrc(lot_label,
                                                                self.facility_license_id.license_number,
                                                                raise_for_error=False) \
                                            and not existing_lot_udpates:
                    self.env['stock.production.lot']._create_package_on_metrc(lot_label,
                                                        self.facility_license_id.license_number,
                                                            move_line_id.product_id,
                                                            quantity=move_line_id.product_uom_qty)
            # 2) Create actual transfer got lots created above

            now_dt = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now())).isoformat()
            scheduled_date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.scheduled_date)).isoformat() if self.scheduled_date else now_dt
            arrival_date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.arrival_date)).isoformat() if self.arrival_date else scheduled_date
            uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version, 'external/incoming')
            data = [{
                'ShipperLicenseNumber': self.partner_license_id.license_number,
                'ShipperName': self.partner_id.name,
                'ShipperMainPhoneNumber': self.partner_id.phone,
                'ShipperAddress1': self.partner_id.street,
                'ShipperAddress2': self.partner_id.street2,
                'ShipperAddressCity': self.partner_id.city,
                'ShipperAddressState': self.partner_id.state_id.name,
                'ShipperAddressPostalCode': self.partner_id.zip,
                'TransporterFacilityLicenseNumber': self.transporter_license_id.license_number if self.transporter_license_id else '',
                'DriverOccupationalLicenseNumber': '50',
                'DriverName': self.driver_id and self.driver_id.name or '',
                'DriverLicenseNumber': self.driver_license_number or '',
                'PhoneNumberForQuestions': self.driver_id.phone if self.driver_id else '',
                'VehicleMake': self.vehicle_id and self.vehicle_id.model_id.name or '',
                'VehicleModel': self.vehicle_id and self.vehicle_id.model_id.brand_id.name or '',
                'VehicleLicensePlateNumber': self.vehicle_id and self.vehicle_id.license_plate or '',
                'Destinations': [{
                    'RecipientLicenseNumber': self.facility_license_id.license_number,
                    'TransferTypeName': self.transfer_type_id and self.transfer_type_id.name or 'Wholesale Manifest',
                    'PlannedRoute': self.route,
                    'EstimatedDepartureDateTime': scheduled_date,
                    'EstimatedArrivalDateTime': arrival_date,
                    'Transporters': [{
                        'TransporterFacilityLicenseNumber': self.transporter_license_id.license_number if self.transporter_license_id else '',
                        'DriverOccupationalLicenseNumber': '50',
                        'DriverName': self.driver_id and self.driver_id.name or '',
                        'DriverLicenseNumber': self.driver_license_number or '',
                        'PhoneNumberForQuestions': self.driver_id.phone if self.driver_id else '',
                        'VehicleMake': self.vehicle_id and self.vehicle_id.model_id.name or '',
                        'VehicleModel': self.vehicle_id and self.vehicle_id.model_id.brand_id.name or '',
                        'VehicleLicensePlateNumber': self.vehicle_id and self.vehicle_id.license_plate or '',
                        'IsLayover': self.has_layover,
                        'EstimatedDepartureDateTime': scheduled_date,
                        'EstimatedArrivalDateTime': arrival_date,
                        }
                    ],
                    'Packages': [{
                            'PackageLabel': line.lot_id._get_metrc_name() if line.lot_id else line.lot_name,
                            'ItemName': line.product_id.metrc_name,
                            'Quantity': line.product_id.to_metrc_qty(line.product_uom_qty),
                            'UnitOfMeasureName': line.product_id.metrc_uom_id.name if line.product_id.diff_metrc_uom and line.product_id.metrc_uom_id else line.product_uom_id.name,
                            'PackagedDate': now_dt,
                            'GrossWeight': line.product_id.metrc_weight,
                            'GrossUnitOfWeightName': line.product_id.unit_weight_uom.name if line.product_id.unit_weight_uom else '',
                            'WholesalePrice': line.move_id.purchase_line_id.price_unit if line.move_id and line.move_id.purchase_line_id else line.product_id.standard_price
                        } for line in move_lines_todo]
                    }
                ]
            }]
            params = {'licenseNumber': self.facility_license_id.license_number}
            metrc_account.fetch('POST', uri, params=params, data=data)
            self.external_transfer = True
            self.message_post(body=_('<p>Created a external incoming created, authorized by <em> %s </em>.</p>') % (self.env.user.name))
        except Exception as ex:
            raise ex
        return True

    def create_external_incoming_validate(self):
        self._create_external_picking()
        # Check backorder should check for other barcodes
        if self._check_backorder():
            backorders_ids = self._split_create_backorder()
            return backorders_ids
        return True
    
    def action_open_metrc_transfer(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Processed METRC Transfers',
            'res_model': 'metrc.transfer',
            'view_mode': 'tree,form',
            'domain': [('move_line_id', 'in', self.move_line_ids.ids)],
            'search_view_id': self.env.ref('metrc_stock.view_metrc_transfer_search').id,
            'context': {
                'search_default_groupby_manifest': 1,
            }
        }

    def search_metrc_transfer_lot(self, lot_name, transfer_type=False, license_number=False, move_strict=True, latest_only=True):
        MetrcTransfer = self.env['metrc.transfer']
        domain = [('package_label', '=', lot_name)]
        order = None
        if transfer_type:
            domain.append(('transfer_type', '=', transfer_type))
        if license_number:
            domain.append(('src_license', '=', license_number))
        if move_strict:
            domain.append(('move_line_id', '=', False))
        if latest_only:
            order = 'created_date_time desc'
        metrc_transfer_ids = MetrcTransfer.search(domain, order=order)

        if latest_only and metrc_transfer_ids:
            metrc_transfer_ids = metrc_transfer_ids[:1]
        return metrc_transfer_ids

    def _action_assign_metrc_moves(self, move_lines_todo, done=False):
        notify_user = ''
        lots_processed_qty = {}
        MetrcTransfer = self.env['metrc.transfer']
        MetrcProdctAlias = self.env['metrc.product.alias']
        StockProductionLot = self.env['stock.production.lot']
        move_lines_not_done = self.env['stock.move.line']
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for move_line_id in move_lines_todo:
            product = move_line_id.product_id
            picking_type_id = move_line_id.mapped('move_id.picking_id.picking_type_id')
            lot_label = False

            if product and picking_type_id and product.tracking != 'none' and (move_line_id.lot_name or move_line_id.lot_id):
                if picking_type_id.use_create_lots:
                    lot_label = move_line_id.lot_name
                if picking_type_id.use_existing_lots and move_line_id.lot_id:
                    lot_label = move_line_id.lot_id._get_metrc_name()
                if not lot_label:
                    notify_user += _('You need to supply a lot/serial number for product "%s"')%(product.display_name)
            else:
                #notify_user += _('\n - Missing product package (lot/serial) numbers, please add package (lot/serial) for {} before validating.'.format(product.display_name))
                move_line_id.qty_done = 0
            if lot_label:
                #search for package in metrc transfer table and only get the latest transfer.
                metrc_transfer_ids = self.search_metrc_transfer_lot(lot_label,
                                                        transfer_type=self._get_picking_type(),
                                                        license_number=self.facility_license_id.license_number,
                                                        latest_only=True)
                # if no package update found or latest transfer is rejected/returned  then we will try one more sync and get update from  last sync to now
                # so if  transfer was received recently then we will have then synced now.
                if not metrc_transfer_ids or metrc_transfer_ids[0].shipment_package_state in ['Rejected','Returned']:
                    #Force update in past 24 Hours, regardless of what when was last synced.
                    MetrcTransfer.with_context(update_transfer_icp=False)._cron_do_import_transfers([self._get_picking_type()],
                                                            self.facility_license_id,
                                                            automatic=False,
                                                            raise_for_error=False,
                                                            ignore_last_modfied_filter=True)
                    metrc_transfer_ids = self.search_metrc_transfer_lot(lot_label,
                                                        transfer_type=self._get_picking_type(),
                                                        license_number=self.facility_license_id.license_number,
                                                        latest_only=True)
                if metrc_transfer_ids:
                    # we have packages and try to use them.
                    for metrc_transfer_id in metrc_transfer_ids:
                        move_qty_done = move_line_id.product_uom_qty if self._is_in() else move_line_id.qty_done
                        if metrc_transfer_id.shipment_package_state != 'Accepted':
                            # assuming we are waiting for update, we will ask for update
                            metrc_transfer_id.update_transfer_package()
                        if (self._is_in() and metrc_transfer_id.shipment_package_state == 'Accepted') \
                           or (self._is_out() and metrc_transfer_id.shipment_package_state in ['Shipped', 'Accepted']):
                            item_received_uom_qty = metrc_transfer_id.received_quantity if self._is_in() else metrc_transfer_id.shipped_quantity
                            # Metrc allow receiving product in diff uom , so march Metrc received uom to Odoo
                            # do qty conversion and make sure they receive what is actual
                            if metrc_transfer_id.shipment_package_state != 'Shipped' and metrc_transfer_id.received_unit_of_measure_name and ((move_line_id.product_id.diff_metrc_uom and metrc_transfer_id.received_unit_of_measure_name != move_line_id.product_id.metrc_uom_id.name) or (not move_line_id.product_id.diff_metrc_uom and metrc_transfer_id.received_unit_of_measure_name != move_line_id.product_uom_id.name)):
                                pack_uom_id = self.env['uom.uom'].search([
                                                                ('metrc_uom', '!=', False),
                                                                ('name', '=', metrc_transfer_id.received_unit_of_measure_name)
                                                            ], limit=1)
                                if pack_uom_id:
                                    product_to_uom = move_line_id.product_id.metrc_uom_id if move_line_id.product_id.diff_metrc_uom and move_line_id.product_id.metrc_uom_id else  move_line_id.product_uom_id
                                    item_received_uom_qty = pack_uom_id._compute_quantity(item_received_uom_qty, product_to_uom, round=False)
                                else:
                                    notify_user += ('\n - Product "%s" package "%s" received quantity unit of measure "%s" is not configured.')%(
                                                                product.display_name, lot_label, metrc_transfer_id.received_unit_of_measure_name)
                                    continue
                            package_received_uom_qty = move_line_id.product_id.from_metrc_qty(item_received_uom_qty)

                            if lot_label not in lots_processed_qty:
                                lots_processed_qty.update({lot_label: package_received_uom_qty})
                            lot_avalible_qty = lots_processed_qty[lot_label]
                            move_line_id.qty_done = lot_avalible_qty
                            lots_processed_qty.pop(lot_label)
                            if done:
                                metrc_transfer_id.move_line_id = move_line_id
                                manifest_numbers = set((self.manifest_number if self.manifest_number else '').split())
                                manifest_numbers.add(metrc_transfer_id.manifest_number)
                                metrc_delivery_ids = set((self.metrc_delivery_id if self.metrc_delivery_id else '').split())
                                metrc_delivery_ids.add(str(metrc_transfer_id.delivery_id))
                                self.write({
                                    'manifest_number': ','.join(manifest_numbers),
                                    'metrc_delivery_id': ','.join(metrc_delivery_ids),
                                })
                                self.message_post(body=_('Associated Metrc transfer package manifest \
                                        <a href=# data-oe-model=metrc.transfer data-oe-id=%d>%s</a>.') % (
                                                metrc_transfer_id.id, metrc_transfer_id.manifest_number))
                                if self._is_in() and move_line_id.lot_id:
                                    lot_to_sync = move_line_id.lot_id
                                    resp = StockProductionLot._is_package_exist_on_metrc(lot_to_sync._get_metrc_name(), license=self.facility_license_id.license_number, raise_for_error=False)
                                    if resp and resp.get('Quantity'):
                                        lot_to_sync.write({
                                            'metrc_id': resp['Id'],
                                            'metrc_qty': resp['Quantity'],
                                            'labtest_state': resp['LabTestingState'],
                                            'testing_state_date': resp['LabTestingStateDate'],
                                            'name_readonly': True
                                        })
                                if metrc_transfer_id.product_name != move_line_id.product_id.display_name:
                                    MetrcProdctAlias.upsert_alias(metrc_transfer_id.product_name, move_line_id.product_id,
                                                                  self.partner_license_id)

                        elif metrc_transfer_id.shipment_package_state in ['Rejected', 'Returned']:
                            move_line_id.qty_done = 0
                        else:
                            notify_user += _('\n - Package "%s" is shipped but not received yet, please process \
                                                    the transfer in Metrc first and the click Validate') % (lot_label)
                else:
                    # check if lot is not scheduled under different license for same transfer type if so let user know of it.
                    diff_metrc_transfer_ids = self.search_metrc_transfer_lot(lot_label, transfer_type=self._get_picking_type(), move_strict=False)
                    if diff_metrc_transfer_ids:
                        all_metrc_transfer_ids = self.search_metrc_transfer_lot(lot_label, move_strict=False)
                        in_package_ids = all_metrc_transfer_ids.filtered(lambda mti: mti.transfer_type == 'incoming')
                        out_package_ids = all_metrc_transfer_ids.filtered(lambda mti: mti.transfer_type == 'outgoing')
                        if len(in_package_ids) == len(out_package_ids):
                            diff_metrc_transfer_ids = diff_metrc_transfer_ids - (in_package_ids + out_package_ids)
                        for dmt in diff_metrc_transfer_ids:
                            notify_user += _('\n - The product "%s" package "%s" is list on "%s" transfer \
                                                under recipient license %s (the package state "%s").') % (
                                                                        move_line_id.product_id.display_name,
                                                                        dmt.package_label,
                                                                        dmt.transfer_type,
                                                                        dmt.src_license,
                                                                        dmt.shipment_package_state)
                            if dmt.move_line_id and move_line_id.mapped('move_id.picking_id'):
                                notify_user += _('The package is already processed on picking %s' % (move_line_id.move_id.picking_id.name))
                    else:
                        # if no package found then let user know that their no such lot
                        # and add context to what is done and they can do to resolve this.
                        notfound_msg = '\n - No transfer package found for the serial "%s" in Metrc, make sure transfer is initiated \
                                                in Metrc before validating the transfer.' % (lot_label)
                        if self.transfer_template_created:
                            notfound_msg += '( A transfer template has been created in Metrc for the picking.)'
                        elif self.external_transfer:
                            notfound_msg += '( An external incoming transfer has been created in Metrc for the picking.)'
                        notify_user += _(notfound_msg)
                    move_lines_not_done |= move_line_id

        for package, qty in lots_processed_qty.items():
            notify_user += _('\n - Package "%s" can not be processed partially, \
                                    the package still has %f unprocessed quantity') % (package, qty)
        if notify_user:
            notify_user = _('Facility License: %s \n %s') % (self.facility_license_id.license_number, notify_user)
            raise UserError(notify_user)
        return move_lines_not_done

    def validate_with_metrc(self):
        self.env.user.ensure_metrc_account()
        facility_license_id = self.facility_license_id

        if not self.partner_license_id or not facility_license_id:
            raise UserError(_('Missing "Partner License" or "Facility License" for the transfer, \
                                make sure they are configured before validating transfer.'))

        move_lines_todo = self._get_metrc_moves_todo()
        # For outgoing create transfer template if not created yet
        if move_lines_todo and self._is_out() \
                    and not self.transfer_template_created and not self.not_metrc_enabled:
            # self._check_move_consume(move_lines_todo)
            message = '''<p>
<p>Create a transfer manifest for outgoing transfer. Package details</p>
<ul>
%s
</ul>
<p>Facility License : <em>%s</em></p>
            </p>''' % (self._prepare_transfer_lot_message(move_lines_todo), facility_license_id.license_number)
            wiz = self.env['stock.transfer.wizard'].create({
                                            'picking_id': self.id,
                                            'message': message,
                                        })
            action = self.env.ref('metrc_stock.action_view_stock_transfer_wizard').read()[0]
            action.update({
                'views': [(self.env.ref('metrc_stock.wizard_view_stock_transfer_manifest_form').id, 'form')],
                'res_id': wiz.id
            })
            return action
        # run package allocation against metrc transfer using user enter package details.
        move_lines_not_done = self._action_assign_metrc_moves(move_lines_todo)
        if self._is_in() and not self.external_transfer:
            # After assigning package in case of incoming see if it's possible external transfer
            # and offer user to create one.
            if move_lines_not_done and move_lines_not_done == move_lines_todo:
                message = '''<p>
<p>No matching package(s) were found for all Metrc enabled product for the transfer.
Below are list product packages with quantities being processed:</p>
<ul>
%s
</ul>

<p>Facility License : <em>%s</em></p>

<p>You can either wait for an update from Metrc and try to validate transfer later (choose No and press Wait button), or<br/>
if know that this transfer manifest are for external incoming, then you can create external incoming in Metrc and that will
validate transfer and will create back order of rest products. (choose Yes(I authorize), fill required field for external transfer and click Validate with Metrc)</p>
                </p>''' % (self._prepare_transfer_lot_message(move_lines_todo), facility_license_id.license_number)
                wiz = self.env['stock.transfer.wizard'].create({
                                                'picking_id': self.id,
                                                'message': message,
                                            })
                action = self.env.ref('metrc_stock.action_view_stock_transfer_wizard').read()[0]
                action.update({
                    'views': [(self.env.ref('metrc.wizard_view_stock_transfer_external_form').id, 'form')],
                    'res_id': wiz.id
                })
                return action
        elif move_lines_not_done and move_lines_not_done != move_lines_todo:
            # TOOD: Find more cases that will fall here, for now this does not let any pass
            #       in-case of bad reservations.
            raise UserError(_('One or more package partially processed and requires review of the packages.\n \
                                Package details: %s\n \
                                if you want to process partial packages quantity then spit the package to required quantity or\
                                 removed detailed operation lines to skip and create backorder.')%(self._prepare_transfer_lot_message(move_lines_todo)))
        # finally for one more time make sure everything is processed and their no partial moves
        # if self.picking_type_id.use_existing_lots:
        #     self._check_move_consume(move_lines_todo)
        return True

    def button_validate(self):
        if self.require_metrc_validation and self.moving_metrc_product:
            # Reserving available quantities
            self.action_recheck_availability()
            return_val = self.validate_with_metrc()
            if isinstance(return_val, dict):
                return return_val
        res = super(StockPicking, self).button_validate()
        return res

    def action_recheck_availability(self):
        invalid_lines = self.env['stock.move.line']
        for move in self.move_lines.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available', 'assigned']):
            if move.picking_id._is_in() and not move.move_orig_ids:
                for line in move.move_line_ids.filtered(lambda l: (l.qty_done > 0.00) and (l.product_uom_qty < l.qty_done)):
                    line.product_uom_qty = min(move.product_uom_qty, line.qty_done)
            else:
                for line in move.move_line_ids.filtered(lambda l: l.qty_done > 0.00 and l.lot_qty > 0.00 and l.product_uom_qty < l.qty_done):
                    if float_compare(line.qty_done, line.lot_qty, precision_rounding=line.product_uom_id.rounding) < 0 and \
                       line.product_id.is_metric_product:
                        invalid_lines |= line
                        continue
                    if not float_is_zero(line.lot_qty, precision_rounding=line.product_uom_id.rounding) and \
                       float_compare(line.lot_qty, line.qty_done, precision_rounding=line.product_uom_id.rounding) >= 0:
                        line._free_reservation(line.product_id, line.move_id.location_id, line.qty_done, lot_id=line.lot_id)
                        taken_qty = line.move_id._update_reserved_quantity(line.qty_done, line.lot_qty,
                                                                           move.location_id, lot_id=line.lot_id, strict=True)
            move._recompute_state()
        if invalid_lines:
            msg = 'Following product(s) packages(lot) "Done" quantity does not match with available \
                    quantity in location {}.\n'.format(self.location_id.display_name)
            for line in invalid_lines:
                msg += '\n-  {}, {}, Available Qty: {} {}, Done Qty: {} {}.'.format(line.product_id.metrc_name, line.lot_id.name,
                                                                                   line.lot_qty, line.product_uom_id.name,
                                                                                   line.qty_done, line.product_uom_id.name)
            msg += '\n\nPlease update the packages(lot) "Done" quantity to match with available quantity \
                        for the packages(lot) under Operations > Details Operations and try validating the picking again.'
            raise UserError(_(msg))

    def _action_done(self):
        if self.require_metrc_validation and self.moving_metrc_product:
            move_lines_todo = self._get_metrc_moves_todo()
            # self._check_move_consume(move_lines_todo)
            move_lines_not_done = self._action_assign_metrc_moves(move_lines_todo, True)
            if move_lines_not_done:
                raise UserError(_('Invalid allocations of following packages. Package Details : \n\
                                        %s') % (self._prepare_transfer_lot_message(move_lines_not_done)))
        ret = super(StockPicking, self)._action_done()
        return ret

    def _get_lines_to_consolidate(self):
        '''
        function to find the finished move lines of the multi batch split MO from which lots
        encoded on current picking's move lines are created.
        '''
        if not self.moving_metrc_product:
            return False
        move_lines_todo = self._get_metrc_moves_todo()
        return self.env['stock.move.line'].search([('production_id', '!=', False), ('move_id.raw_material_production_id', '=', False),
                                                              ('production_id.split_lot_multi', '=', True), ('state', '=', 'done'),
                                                              ('lot_id', 'in', move_lines_todo.mapped('lot_id').ids)])

    def action_consolidate_lots(self):
        warehouse_id = self.location_id.get_warehouse()
        done_move_lines = self._get_lines_to_consolidate()
        if not done_move_lines:
            raise UserError(_("No lots are available to consolidate on current picking."))
        move_lines_todo = self._get_metrc_moves_todo()
        lots_to_exclude = (move_lines_todo.mapped('lot_id') - done_move_lines.mapped('lot_id'))
        done_move_lots = done_move_lines.mapped('lot_id')
        move_lines = self.move_line_ids.filtered(lambda l: l.lot_id in done_move_lots)
        if done_move_lines and len(done_move_lines.mapped('production_id')) < len(move_lines.mapped('lot_id')):
            lot_datas = {prod: [] for prod in done_move_lines.mapped('product_id')}
            for lot in move_lines.mapped('lot_id'):
                if lot.product_id in lot_datas.keys():
                    lot_datas[lot.product_id].append(lot)
            new_lot_lines = []
            for prod, lots in lot_datas.items():
                qty_available = []
                for lot in lots:
                    prod.flush()
                    prod = prod.with_context(lot_id=lot.id, warehouse=warehouse_id.id)
                    qty_available.append(prod.qty_available)
                new_lot_lines.append({
                    'lot_ids': [(6, 0, [l.id for l in lots])],
                    'product_id': prod.id,
                    'qty_available': sum(qty_available),
                    'quantity': sum(qty_available)
                    })
            wiz = self.env['lot.merge.wizard'].create({
                'picking_id': self.id,
                'warehouse_id': warehouse_id.id,
                'source_lot_ids': [(6, 0, move_lines.mapped('lot_id').ids)],
                'target_lot_ids': [(0, 0, lot_line) for lot_line in new_lot_lines],
            })
            if len(lots_to_exclude) > 0:
                lot_details = ''
                for product in lots_to_exclude.mapped('product_id'):
                    lot_names = [l._get_metrc_name() for l in lots_to_exclude.filtered(lambda lot: lot.product_id == product)]
                    lot_details += "<tr><td>{}</td><td>{}</td></tr>".format(product.display_name, ','.join(lot_names))
                wiz.message_body = "<p><h3>Following lots does not originate from the same picking or they are single split lots.</h3><p><br/>" \
                                   "<br/><table class='table table-bordered'><tr><th>Product</th><th>Lots</th></tr>{}"\
                                   "</table><p><h3>Do you want to proceed with the consolidation?</h3></p>".format(lot_details)
                return {
                    'name': _('Consolidation Confirmation'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'lot.merge.wizard',
                    'res_id': wiz.id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'views': [(self.env.ref('metrc.merge_lot_confirmation_yes_no').id, 'form')],
                    'context': {},
                    'domain': {},
                    'target': 'new'
                }
            action_data = self.env.ref('metrc_stock.action_open_merge_lot_wizard').read()[0]
            action_data['res_id'] = wiz.id
            return action_data
