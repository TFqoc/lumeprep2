# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import pytz
import logging

from datetime import datetime, timedelta
from dateutil import parser

from odoo import fields, models, registry
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class MetrcTransfer(models.Model):

    _name = 'metrc.transfer'
    _description = 'Metrc Transfers'
    _rec_name = 'package_label'

    def _valid_field_parameter(self, field, name):
        # allow tracking on abstract models; see also 'mail.thread'
        return (
            name in ('metrc_field', 'metrc_rec_name') or super()._valid_field_parameter(field, name)
        )

    transfer_type = fields.Selection(selection=[
                                        ('incoming', 'incoming'),
                                        ('outgoing', 'outgoing'),
                                        ('rejected', 'rejected'),
                                    ], string='Metrc Transfer Type', index=True)
    src_license = fields.Char(string='Source License', index=True)
    active = fields.Boolean(string='Active', default=True)
    # Transfer fields
    # - https://api-ca.metrc.com/Documentation/#Transfers.get_transfers_v1_incoming
    # - https://api-ca.metrc.com/Documentation/#Transfers.get_transfers_v1_outgoing
    # - https://api-ca.metrc.com/Documentation/#Transfers.get_transfers_v1_rejected
    transfer_id = fields.Integer(string='Transfer ID')
    manifest_number = fields.Char(string='Manifest Number')
    shipment_license_type = fields.Char(string='Shipment License Type')
    shipper_facility_license_number = fields.Char(string='Shipper Facility License Number')
    shipper_facility_name = fields.Char(string='Shipper Facility Name')
    name = fields.Char(string='Name')
    transporter_facility_license_number = fields.Char(string='Transporter Facility License Number')
    transporter_facility_name = fields.Char(string='Transporter Facility Name')
    driver_name = fields.Char(string='Driver Name')
    driver_occupational_license_number = fields.Char(string='Driver Occupational License Number')
    driver_vehicle_license_number = fields.Char(string='Driver Vehicle License Number')
    vehicle_make = fields.Char(string='Vehicle Make')
    vehicle_model = fields.Char(string='Vehicle Model')
    vehicle_license_plate_number = fields.Char(string='Vehicle License Plate Number')
    delivery_count = fields.Integer(string='Delivery Count')
    received_delivery_count = fields.Integer(string='Received Delivery Count')
    package_count = fields.Integer(string='Package Count')
    received_package_count = fields.Integer(string='Received Package Count')
    contains_plant_package = fields.Boolean(string='Contains Plant Package')
    contains_product_package = fields.Boolean(string='Contains Product Package')
    contains_testing_sample = fields.Boolean(string='Contains Testing Sample')
    contains_product_requires_remediation = fields.Boolean(string='Contains Product Requires Remediation')
    contains_remediated_product_package = fields.Boolean(string='Contains Re-mediated Product Package')
    created_date_time = fields.Char(string='Created Date Time')
    created_by_user_name = fields.Char(string='Created By User Name')
    last_modified = fields.Char(string='Last Modified')
    delivery_id = fields.Integer(string='Delivery ID')
    recipient_facility_license_number = fields.Char(string='Recipient Facility License Number')
    recipient_facility_name = fields.Char(string='Recipient Facility Name')
    shipment_type_name = fields.Char(string='Shipment Type Name')
    shipment_transaction_type = fields.Char(string='Shipment Transaction Type')
    estimated_departure_date_time = fields.Char(string='Estimated Departure Date Time')
    actual_departure_date_time = fields.Char(string='Actual Departure Date Time')
    estimated_arrival_date_time = fields.Char(string='Estimated Arrival Date Time')
    actual_arrival_date_time = fields.Char(string='Actual Arrival Date Time')
    delivery_package_count = fields.Integer(string='Delivery Package Count')
    delivery_received_package_count = fields.Integer(string='Delivery Received Package Count')
    received_date_time = fields.Char(string='Received Date Time')
    #Transfer Package fields 
    # https://api-ca.metrc.com/Documentation/#Transfers.get_transfers_v1_delivery_{id}_packages
    package_id = fields.Integer(string='Package ID')
    package_label = fields.Char(string='Package Label', index=True)
    package_type = fields.Char(string='Package Type')
    source_harvest_names = fields.Char(string='Source Harvest Names')
    product_name = fields.Char(string='Product Name')
    product_category_name = fields.Char(string='Product Category Name')
    lab_testing_state = fields.Char(string='Lab Testing State')
    production_batch_number = fields.Char(string='Production Batch Number')
    is_testing_sample = fields.Boolean(string='Is Testing Sample')
    product_requires_remediation = fields.Boolean(string='Product Requires Remediation')
    contains_remediated_product = fields.Boolean(string='Contains Re-mediated Product')
    remediation_date = fields.Char(string='Remediation Date')
    shipment_package_state = fields.Char(string='Shipment Package State')
    shipped_quantity = fields.Float(string='Shipped Quantity', digits=(16, 4))
    shipped_unit_of_measure_name = fields.Char(string='Shipped Unit Of Measure Name')
    gross_unit_of_weight_name = fields.Char(string='Gross Unit Of Weight Name')
    received_quantity = fields.Float(string='Received Quantity', digits=(16, 4))
    received_unit_of_measure_name = fields.Char(string='Received Unit Of Measure Name')
    move_line_id = fields.Many2one(comodel_name='stock.move.line', string='Associated Product Move', ondelete='set null', index=True, copy=False)

    def _assert_transfer_param(self, license_number, transfer_type, update_date=False, transfer_date=False):
        """

        Helps maintain (getter/setter) the last sync date for given metrc license number
        and transfer type.
        It stores values in dict format in ir.config.param with key 'metrc.transfer.last.sync'
        {
            'A12-0000015-LI': {'incoming': '2019-07-13 01:00:00',
                                'outgoing': '2019-07-14 02:00:00',
                                'rejected': '2019-07-15 03:00:00',},
            'M10-0000004-LIC': {'incoming': '2019-07-13 01:00:00',
                                'outgoing': '2019-07-14 02:00:00',
                                'rejected': '2019-07-15 03:00:00',},
            ...
        }

        @param license_number : metrc license number use for querying license transfers
        @param transfer_type  : takes transfer types(expected values incoming, outgoing, rejected)
        @param update_date    : if true it will update last sync date for given license transfer type
        @param transfer_date  : transfer date will be updated last sync date for given license transfer type
                                if update_date is True, also require if update_date is True

        @return date string   : return string datetime of last sync if found else, return False
        """
        ICP = self.env['ir.config_parameter'].sudo()
        param_key = 'metrc.transfer.last.sync'
        param_date = False
        try:
            raw_tran_values = ICP.get_param(param_key, default='{}')
            tran_values = dict(safe_eval(raw_tran_values))
            if update_date and transfer_date:
                lic_types = tran_values.get(license_number)
                if not lic_types:
                    tran_values.update({license_number: {transfer_type: fields.Datetime.to_string(transfer_date)}})
                tran_values[license_number].update({transfer_type: fields.Datetime.to_string(transfer_date)})
                ICP.set_param(param_key, str(tran_values))
            param_date = tran_values.get(license_number, {}).get(transfer_type)
        except Exception as ex:
            raise ex
            _logger.error('Error during config param "metrc.transfer.last.sync".\n%s' % (ex))
            pass
        return param_date

    def _map_transfer_reponse(self, transfer):
        """
        Do the field mapping of Metrc transfer repose data to model fields
        @param transfer <dict>: metrc transfer response dict

        @return <dict> : response mapped to model fields
        """
        transfer_vals = {
            'transfer_id': transfer['Id'],
            'manifest_number': transfer['ManifestNumber'],
            'shipment_license_type': transfer['ShipmentLicenseType'],
            'shipper_facility_license_number': transfer['ShipperFacilityLicenseNumber'],
            'shipper_facility_name': transfer['ShipperFacilityName'],
            'name': transfer['Name'],
            'transporter_facility_license_number': transfer['TransporterFacilityLicenseNumber'],
            'transporter_facility_name': transfer['TransporterFacilityName'],
            'driver_name': transfer['DriverName'],
            'driver_occupational_license_number': transfer['DriverOccupationalLicenseNumber'],
            'driver_vehicle_license_number': transfer['DriverVehicleLicenseNumber'],
            'vehicle_make': transfer['VehicleMake'],
            'vehicle_model': transfer['VehicleModel'],
            'vehicle_license_plate_number': transfer['VehicleLicensePlateNumber'],
            'delivery_count': transfer['DeliveryCount'],
            'received_delivery_count': transfer['ReceivedDeliveryCount'],
            'package_count': transfer['PackageCount'],
            'received_package_count': transfer['ReceivedPackageCount'],
            'contains_plant_package': transfer['ContainsPlantPackage'],
            'contains_product_package': transfer['ContainsProductPackage'],
            'contains_testing_sample': transfer['ContainsTestingSample'],
            'contains_product_requires_remediation': transfer['ContainsProductRequiresRemediation'],
            'contains_remediated_product_package': transfer['ContainsRemediatedProductPackage'],
            'created_date_time': transfer['CreatedDateTime'],
            'created_by_user_name': transfer['CreatedByUserName'],
            'last_modified': transfer['LastModified'],
            'delivery_id': transfer['DeliveryId'],
            'recipient_facility_license_number': transfer['RecipientFacilityLicenseNumber'],
            'recipient_facility_name': transfer['RecipientFacilityName'],
            'shipment_type_name': transfer['ShipmentTypeName'],
            'shipment_transaction_type': transfer['ShipmentTransactionType'],
            'estimated_departure_date_time': transfer['EstimatedDepartureDateTime'],
            'actual_departure_date_time': transfer['ActualDepartureDateTime'],
            'estimated_arrival_date_time': transfer['EstimatedArrivalDateTime'],
            'actual_arrival_date_time': transfer['ActualArrivalDateTime'],
            'delivery_package_count': transfer['DeliveryPackageCount'],
            'delivery_received_package_count': transfer['DeliveryReceivedPackageCount'],
            'received_date_time': transfer['ReceivedDateTime'],
        }
        return transfer_vals

    def _map_delivery_reponse(self, delivery):
        """
        Do the field mapping of Metrc transfer package response data to model fields
        @param transfer <dict>: metrc transfer response dict

        @return <dict> : response mapped to model fields
        """
        delivery_vals = {
            'delivery_id': delivery['Id'],
            'recipient_facility_license_number': delivery['RecipientFacilityLicenseNumber'],
            'recipient_facility_name': delivery['RecipientFacilityName'],
            'shipment_type_name': delivery['ShipmentTypeName'],
            'shipment_transaction_type': delivery['ShipmentTransactionType'],
            'estimated_departure_date_time': delivery['EstimatedDepartureDateTime'],
            'actual_departure_date_time': delivery['ActualDepartureDateTime'],
            'estimated_arrival_date_time': delivery['EstimatedArrivalDateTime'],
            'actual_arrival_date_time': delivery['ActualArrivalDateTime'],
            'delivery_package_count': delivery['DeliveryPackageCount'],
            'delivery_received_package_count': delivery['DeliveryReceivedPackageCount'],
            'received_date_time': delivery['ReceivedDateTime'],
        }
        return delivery_vals

    def _map_package_reponse(self, package):
        """
        Do the field mapping of Metrc transfer package response data to model fields
        @param transfer <dict>: metrc transfer response dict

        @return <dict> : response mapped to model fields
        """
        package_vals = {
            'package_id': package['PackageId'],
            'package_label': package['PackageLabel'],
            'package_type': package['PackageType'],
            'source_harvest_names': package['SourceHarvestNames'],
            'product_name': package['ProductName'],
            'product_category_name': package['ProductCategoryName'],
            'lab_testing_state': package['LabTestingState'],
            'production_batch_number': package['ProductionBatchNumber'],
            'is_testing_sample': package['IsTestingSample'],
            'product_requires_remediation': package['ProductRequiresRemediation'],
            'contains_remediated_product': package['ContainsRemediatedProduct'],
            'remediation_date': package['RemediationDate'],
            'shipment_package_state': package['ShipmentPackageState'],
            'shipped_quantity': package['ShippedQuantity'],
            'shipped_unit_of_measure_name': package['ShippedUnitOfMeasureName'],
            'gross_unit_of_weight_name': package['GrossUnitOfWeightName'],
            'received_quantity': package['ReceivedQuantity'],
            'received_unit_of_measure_name': package['ReceivedUnitOfMeasureName'],
        }
        return package_vals

    def _process_transfer_packages(self, transfer_type, license_number, transfer, pacakges):
        """
        Method to keep the a transfer and packages between Metrc and Odoo
        Method create or updates transfer and packages details fetch from the Metrc.

        @param license_number <str> : metrc license number used for querying license transfers
        @param transfer_type  <str> : takes transfer types(expected values incoming, outgoing, rejected)
        @param transfer      <dict> : dict response of a transfer fetched from Metrc
        @param packages      <dict> : transfer package dict for given transfer on above param

        @return date string   : return record-set to created/updated transfer records.

        """
        transfer_id = transfer['Id']
        manifest_number = transfer['ManifestNumber']
        transfer_vals = self._map_transfer_reponse(transfer)
        transfer_vals.update({
            'transfer_type': transfer_type,
            'src_license': license_number
        })
        existing_transfer_ids = self.search([
                                ('src_license', '=', license_number),
                                ('transfer_type', '=', transfer_type),
                                ('manifest_number', '=', manifest_number),
                                ('transfer_id', '=', transfer_id),
                            ])
        if existing_transfer_ids:
            # do no update transfers where stock move is assigned.
            # this give room finding gap in Metrc in Odoo.
            if existing_transfer_ids.filtered(lambda eti: not eti.move_line_id):
                # update all package/transfer lines with transfer details.
                existing_transfer_ids.filtered(lambda eti: not eti.move_line_id).write(transfer_vals)
        else:
            # we must create empty transfer lines as Metrc may give transfer
            # without package later we will reconcile them.
            existing_transfer_ids = self.create(transfer_vals)
        while pacakges:
            package = pacakges.pop()
            package_vals = self._map_package_reponse(package)
            transfer_id = transfer['Id']
            delivery_id = transfer['DeliveryId']
            package_id = package['PackageId']
            package_label = package['PackageLabel']
            #search for exact match of package with id.
            existing_package_id = existing_transfer_ids\
                                                .filtered(lambda pack: \
                                                        pack.transfer_id == transfer_id\
                                                    and pack.package_id == package_id\
                                                    and pack.package_label == package_label\
                                                    and pack.manifest_number == manifest_number\
                                                    and pack.transfer_type == transfer_type\
                                                    and pack.src_license == license_number)
            if existing_package_id:
                # perfect match found, update package vals. If they are mutable
                # i.e. stock_move_id is not assigned
                mutable_transfer_ids = existing_package_id.filtered(lambda eti: not eti.move_line_id)
                if mutable_transfer_ids:
                    mutable_transfer_ids.write(package_vals)
            else:
                # look transfer that are no package detail
                empty_transfer_id = existing_transfer_ids.filtered(lambda pack: not pack.package_id\
                                                                                and pack.transfer_id == transfer_id
                                                                                and pack.manifest_number == manifest_number\
                                                                                and pack.transfer_type == transfer_type\
                                                                                and pack.src_license == license_number)
                if empty_transfer_id:
                    # Found transfer line that is empty and can be updated with new transfer package details
                    # if multiple packages are created then update one and leave second for next turn.
                    # this would reconcile transfer  when new transfer package appear for empty transfer
                    empty_mutable_transfer_id = empty_transfer_id.filtered(lambda eti: not eti.move_line_id)
                    if empty_mutable_transfer_id:
                        empty_mutable_transfer_id.write(package_vals)
                else:
                    # no existing package of empty lines found so we create new transfer package
                    transfer_package_vals = transfer_vals.copy()
                    transfer_package_vals.update(package_vals)
                    existing_transfer_ids += self.create(transfer_package_vals)
        return existing_transfer_ids

    def parse_date(self, dt_stamp):
        try:
            dt = parser.parse(dt_stamp)
            dt_utc = dt.astimezone(pytz.utc).replace(tzinfo=None)
        except:
            dt_utc = False
            pass
        return dt_utc

    def update_transfer_packages(self, ignore_last_modified_filter=False):
        """
        Update given transfer if license_number, last_modified and manifest_number configured
        This will be stand alone
        """
        skipped_transfers = []
        for transfer in self:
            if transfer.src_license and transfer.last_modified and transfer.manifest_number and not transfer.move_line_id:
                _transfer_updated = False
                metrc_account = self.env.user.ensure_metrc_account()
                license = self.env['metrc.license'].search([('license_number', '=', transfer.src_license)], limit=1)
                if not license or not metrc_account:
                    skipped_transfers.append(transfer)
                    continue
                dt_now = datetime.now()
                utc_last_modified = self.parse_date(transfer.last_modified)
                last_sync_date = dt_now - timedelta(hours=23, minutes=59, seconds=0) if not utc_last_modified else utc_last_modified.replace(hour=0, minute=0, second=0)
                print (last_sync_date, dt_now)
                while last_sync_date < dt_now:
                    if _transfer_updated:
                        break
                    new_last_sync_date = last_sync_date + timedelta(hours=24)
                    if new_last_sync_date > dt_now:
                        new_last_sync_date = dt_now
                    params = {
                        'licenseNumber': license.license_number,
                    }
                    if not ignore_last_modified_filter:
                        params.update({
                            'lastModifiedStart': last_sync_date.isoformat(),
                            'lastModifiedEnd': new_last_sync_date.isoformat(),
                            })
                    uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version, transfer.transfer_type)
                    transfer_result = []
                    try:
                        transfer_result = metrc_account.fetch('GET', uri, params=params)
                    except Exception as ex:
                        raise ex
                    last_sync_date = new_last_sync_date if not ignore_last_modified_filter else dt_now
                    matching_transfers = [ t_res for t_res in transfer_result if t_res.get('ManifestNumber') and t_res.get('ManifestNumber') == transfer.manifest_number ]
                    while matching_transfers:
                        trans = matching_transfers.pop()
                        transfer_vals = self._map_transfer_reponse(trans)
                        transfer_id = trans.get('Id')
                        ex_to_raise = False
                        delivery_error = False
                        try:
                            delivery_uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version,
                                                                    '{}/deliveries'.format(transfer.transfer_id))
                            deliveries = metrc_account.fetch('GET', delivery_uri)
                            package_result = []
                            for delivery in deliveries:
                                delivery_id = delivery.get('Id')
                                package_uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version,
                                                                    'delivery/{}/packages'.format(delivery_id))
                                package_result += metrc_account.fetch('GET', package_uri, params={'licenseNumber': license.license_number})
                            transfer_ids = self._process_transfer_packages(transfer.transfer_type, license.license_number, trans, package_result)
                        except Exception as ex:
                            ex_to_raise = ex
                            metrc_account.log_exception()
                            delivery_error = True
                        if delivery_error:
                            try:
                                delivery_id = trans.get('DeliveryId')
                                package_uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version,
                                                                    'delivery/{}/packages'.format(delivery_id))
                                package_result = metrc_account.fetch('GET', package_uri, params={'licenseNumber': license.license_number})
                                transfer_ids = self._process_transfer_packages(transfer.transfer_type, license.license_number, trans, package_result)
                                delivery_error = False
                            except Exception as ex:
                                ex_to_raise = ex
                                metrc_account.log_exception()
                        if delivery_error and ex_to_raise:
                            raise ex_to_raise
                    else:
                        _transfer_updated = True
            else:
                skipped_transfers.append(transfer)
        else:
            if skipped_transfers:
                _logger.info('skipped update_transfer_package for following transfers %s' % (','.join([str(st.id) for st in skipped_transfers])))

    def update_transfer_package(self):
        """
        Method that updates transfer package details based on delivery id
        Pull all the packages for the given delivery
        """
        skipped_transfers = []
        for transfer in self:
            metrc_account = self.env.user.ensure_metrc_account()
            if (transfer.move_line_id or (not transfer.transfer_id and not metrc_account and not transfer.src_license)):
                skipped_transfers.append(transfer)
                continue
            ex_to_raise = False
            delivery_error = False
            package_result = False
            try:
                delivery_uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version, '{}/deliveries'.format(transfer.transfer_id))
                deliveries = metrc_account.fetch('GET', delivery_uri)
                for delivery in deliveries:
                    delivery_id = delivery.pop('Id')
                    package_uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version, 'delivery/{}/packages'.format(delivery_id))
                    package_result = metrc_account.fetch('GET', package_uri, params={'licenseNumber': transfer.src_license})
            except Exception as ex:
                ex_to_raise = ex
                metrc_account.log_exception()
                delivery_error = True
            if delivery_error:
                try:
                    delivery_id = transfer.delivery_id
                    package_uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version, 'delivery/{}/packages'.format(delivery_id))
                    package_result = metrc_account.fetch('GET', package_uri, params={'licenseNumber': transfer.src_license})
                    delivery_error = False
                except Exception as ex:
                    ex_to_raise = ex
                    metrc_account.log_exception()
            if ex_to_raise and delivery_error:
                raise ex_to_raise
            while package_result:
                package = package_result.pop()
                if package.get('PackageLabel') == transfer.package_label and package.get('PackageId') == transfer.package_id:
                    package_vals = self._map_package_reponse(package)
                    transfer.write(package_vals)
        else:
            if skipped_transfers:
                _logger.info('skipped update_transfer_package for following transfers %s' % (str(skipped_transfers)))

    def do_import_transfers(self, transfer_type, metrc_license=False):
        """
        Do Implement this method for all metrc.meta child who needs one time import,
        cron import does no require license so any model that requires license will
        be reject (skipped) by the cron.
        """
        # make sure we have transfer types, it can be single or can be list
        if isinstance(transfer_type, str):
            transfer_type = list(transfer_type)
        elif isinstance(transfer_type, (list, tuple)):
            transfer_type = transfer_type
        else:
            _logger.info('Missing transfer types, existing cron.')

        # Check is if licensed are passed and if passed then id, list of id or object itself
        licenses = False
        if not metrc_license:
            licenses = self.env['metrc.license'].search([])
        elif isinstance(metrc_license, int) or isinstance(metrc_license, (list, tuple)):
            licenses = self.env['metrc.license'].browse(metrc_license)
        elif isinstance(metrc_license, models.BaseModel):
            licenses = metrc_license
        else:
            _logger.info('No licenses passed (%s) or found, existing cron.' % (str(metrc_license)))
            return True
        self._cron_do_import_transfers(transfer_type, automatic=True, raise_for_error=True)
        return True

    def _cron_do_import_transfers(self, transfer_type, metrc_license=False, force_last_sync_date=False, automatic=True, raise_for_error=False, ignore_last_modfied_filter=False):
        metrc_account = self.env.user.ensure_metrc_account()
        if not transfer_type or not metrc_account:
            return True

        # make sure we have transfer types, it can be single or can be list
        if isinstance(transfer_type, str):
            transfer_type = list(transfer_type)
        elif isinstance(transfer_type, (list, tuple)):
            transfer_type = transfer_type
        else:
            _logger.info('Missing transfer types, existing cron.')

        # Check is if licensed are passed and if passed then id, list of id or object itself
        licenses = False
        if not metrc_license:
            licenses = self.env['metrc.license'].search([('base_type', '=', 'Internal')])
        elif isinstance(metrc_license, int) or isinstance(metrc_license, (list, tuple)):
            licenses = self.env['metrc.license'].browse(metrc_license)
        elif isinstance(metrc_license, models.BaseModel):
            licenses = metrc_license
        else:
            _logger.info('No licenses passed (), existing cron.' % (str(metrc_license)))
            return True
        if automatic:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        # No need to filter licenses based on current users account.
        # Not every inventory user's metrc account will be associated with metrc license.
        # IT Will fix the issue of just being able to validate the outgoing pickings but other users are not.
        # licenses = licenses.filtered(lambda lic: lic.metrc_account_id == self.env.user.metrc_account_id)
        for license in licenses:
            license = license[0]
            for ttype in transfer_type:
                dt_now = datetime.now()
                if force_last_sync_date and isinstance(force_last_sync_date, datetime):
                    last_sync_date = force_last_sync_date
                elif ignore_last_modfied_filter:
                    last_sync_date = dt_now - timedelta(minutes=2)
                else:
                    license_last_sync_date = self._assert_transfer_param(license.license_number, ttype)
                    last_sync_date = dt_now - timedelta(hours=23, minutes=59, seconds=0) \
                                        if not license_last_sync_date \
                                            else fields.Datetime.from_string(license_last_sync_date)
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
                    uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version, ttype)
                    transfer_result = []
                    try:
                        transfer_result = metrc_account.fetch('GET', uri, params=params)
                    except Exception as ex:
                        if automatic:
                            cr.rollback()
                        _logger.error('Error during synchronizing transfers \n%s' % str(ex))
                        last_sync_date = new_last_sync_date
                        if raise_for_error:
                            raise ex
                        else:
                            metrc_account.log_exception()
                    while transfer_result:
                        trans = transfer_result.pop()
                        transfer_vals = self._map_transfer_reponse(trans)
                        transfer_id = trans.get('Id')
                        delivery_error = False
                        ex_to_raise = False
                        try:
                            package_result = []
                            delivery_uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version, '{}/deliveries'.format(transfer_id))
                            deliveries = metrc_account.fetch('GET', delivery_uri)
                            for delivery in deliveries:
                                delivery_id = delivery.pop('Id')
                                package_uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version, 'delivery/{}/packages'.format(delivery_id))
                                package_result = metrc_account.fetch('GET', package_uri, params={'licenseNumber': license.license_number})
                            transfer_ids = self._process_transfer_packages(ttype, license.license_number, trans, package_result)
                            if automatic:
                                cr.commit()
                        except Exception as ex:
                            if automatic:
                                cr.rollback()
                            delivery_error = True
                            _logger.error('Error during synchronizing transfer_id %s:\n%s' % (trans['Id'], str(ex)))
                            if raise_for_error:
                                ex_to_raise = ex
                            else:
                                metrc_account.log_exception()
                        if delivery_error:
                            try:
                                delivery_id = trans.get('DeliveryId')
                                package_uri = '/{}/{}/{}'.format('transfers', metrc_account.api_version, 'delivery/{}/packages'.format(delivery_id))
                                package_result = metrc_account.fetch('GET', package_uri, params={'licenseNumber': license.license_number})
                                transfer_ids = self._process_transfer_packages(ttype, license.license_number, trans, package_result)
                                delivery_error = False
                                if automatic:
                                    cr.commit()
                            except Exception as ex:
                                if automatic:
                                    cr.rollback()
                                _logger.error('Error during synchronizing transfers for transfer_id %s: \n%s' % (trans['Id'], str(ex)))
                                if raise_for_error or delivery_error:
                                    ex_to_raise = ex
                                else:
                                    metrc_account.log_exception()
                        if delivery_error and raise_for_error and ex_to_raise:
                            raise ex_to_raise
                    if not self._context.get('update_transfer_icp'):
                        self._assert_transfer_param(license.license_number, ttype, True, last_sync_date)
                        if automatic:
                            cr.commit()
                    last_sync_date = new_last_sync_date
        if automatic:
            cr.commit()
            cr.close()
        return True

    def _cron_do_history_transfers(self, transfer_type, metrc_license=False, force_last_sync_date=False, automatic=True, raise_for_error=False):
        metrc_account = self.env.user.ensure_metrc_account()
        if not transfer_type or not metrc_account:
            return True

        # make sure we have transfer types, it can be single or can be list
        if isinstance(transfer_type, str):
            transfer_type = list(transfer_type)
        elif isinstance(transfer_type, (list, tuple)):
            transfer_type = transfer_type
        else:
            _logger.info('Missing transfer types, existing cron.')

        # Check is if licensed are passed and if passed then id, list of id or object itself
        licenses = False
        if not metrc_license:
            licenses = self.env['metrc.license'].search([])
        elif isinstance(metrc_license, int) or isinstance(metrc_license, (list, tuple)):
            licenses = self.env['metrc.license'].browse(metrc_license)
        elif isinstance(metrc_license, models.BaseModel):
            licenses = metrc_license
        else:
            _logger.info('No licenses passed (), existing cron.' % (str(metrc_license)))
            return True
        if automatic:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        licenses = licenses.filtered(lambda lic: lic.metrc_account_id == metrc_account)
        for license in licenses:
            license = license[0]
            for ttype in transfer_type:
                transfers = self.search([
                        ('src_license', '=', license.license_number),
                        ('transfer_type', '=', ttype),
                        ('move_line_id', '=', False)
                    ])
                for transfer in transfers:
                    try:
                        lot_id = self.env['stock.production.lot'].search([
                                        '|', ('name', '=', transfer.package_label),
                                            '&', ('name', '=', transfer.package_label),
                                                 ('is_legacy_lot', '!=', False)
                                        ], limit=1)
                        move_line_id = self.env['stock.move.line'].search([
                                        ('lot_id.name', '=', transfer.package_label),
                                        ('move_id.picking_id.picking_type_code', '=', ttype),
                                        ('state', '=', 'done')
                                    ], limit=1)
                        if lot_id and move_line_id:
                            # _logger.info("\t| {:10}, {:3}, {:25} {:5} {:5} {:10} {:10} {}".format(
                            #                     ttype, len(transfers),transfer.package_label,
                            #                     move_line_id.id, lot_id.id, move_line_id.qty_done,
                            #                     transfer.received_quantity,
                            #                     transfer.received_quantity==move_line_id.qty_done))
                            received_quantity = move_line_id.product_id.from_metrc_qty(transfer.received_quantity)
                            transfer.move_line_id = move_line_id
                            ## This code is used for exact match but we agreed the if package found for
                            ## given picking type then histrionically, record were received/send correct.
                            ## so above line will simple assign stock_move and reconcile for ready run.
                            # if float_compare(transfer.received_quantity, move_line_id.qty_done, precision_rounding=move_line_id.product_uom_id.rounding) == 0:
                            #     transfer.move_line_id = move_line_id
                            #     _logger.info('Assigned transfer tag %s to product %s related to picking %s. (license: %s)'
                            #                     ''%(transfer.package_label,
                            #                         move_line_id.product_id.metrc_name,
                            #                         move_line_id.move_id.picking_id.name if move_line_id.move_id.picking_id else move_line_id.move_id.origin,
                            #                         license.license_number))
                            # else:
                            #     _logger.warning('The tag %s received quantity %f do not match with product move qty %f (license# %s, lot %d, stock move: %d)'%(
                            #                         transfer.package_label, transfer.received_quantity,
                            #                         move_line_id.qty_done, license.license_number,
                            #                         lot_id.id, move_line_id.id))
                        else:
                            _logger.warning('No lot (%d) and/or stock move (%d) found for tag %s (license: %s)' % (
                                                    lot_id.id or 0,
                                                    move_line_id.id or 0,
                                                    transfer.package_label,
                                                    license.license_number))
                        if automatic:
                            cr.commit()
                    except Exception as ex:
                        if automatic:
                            cr.rollback()
                        _logger.error('Error during synchronizing transfers \n%s' % str(ex))
                        if raise_for_error:
                            raise ex
                        else:
                            metrc_account.log_exception()
        if automatic:
            cr.commit()
            cr.close()
        return True
