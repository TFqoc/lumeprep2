# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import pytz
import logging

from datetime import datetime, timedelta
from dateutil import parser

from odoo import api, fields, models, registry, _
from odoo.tools import float_compare, float_round, pycompat
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class MetrcReceipts(models.Model):

    _name = 'metrc.receipts'
    _description = 'Metrc Receipts'
    _rec_name = 'package_label'

    receipt_type = fields.Selection(selection=[
                                        ('incoming', 'incoming'),
                                        ('outgoing', 'outgoing'),
                                        ('rejected', 'rejected'),
                                    ], string='Metrc receipt Type', index=True)
    src_license = fields.Char(string='Source License', index=True)
    active = fields.Boolean(string='Active', default=True)

    #https://api-ca.metrc.com/Documentation/#Sales.get_sales_v1_receipts
    receipt_id = fields.Integer(string='Receipt ID')
    receipt_number = fields.Char(string='Receipt Number')
    sales_date_time = fields.Char(string='Sales Date Time')
    sales_customer_type = fields.Char(string='Sales Customer Type')
    patient_license_number = fields.Char(string='Patient License Number')
    caregiver_license_number = fields.Char(string='Caregiver License Number')
    identification_method = fields.Char(string='Identification Method')
    total_packages = fields.Integer(string='Total Packages')
    total_price = fields.Char(string='Total Price')
    is_final = fields.Boolean(string='Is Final')
    archived_date = fields.Char(string='Archived Date')
    recorded_date_time = fields.Char(string='Recorded Date Time')
    recorded_by_user_name = fields.Char(string='Recorded By User Name')
    last_modified = fields.Char(string='Last Modified')
    #Transactions o2m relation in Metrc o2o here
    package_id = fields.Integer(string='Package Id')
    package_label = fields.Char(string='Package Label')
    product_name = fields.Char(string='Product Name')
    product_category_name = fields.Char(string='Product Category Name')
    item_strain_name = fields.Char(string='Item Strain Name')
    item_unit_cbd_percent = fields.Char(string='Item Unit Cbd Percent')
    item_unit_cbd_content = fields.Char(string='Item Unit Cbd Content')
    item_unit_cbd_content_unit_of_measure_name = fields.Char(string='Item Unit Cbd Content Unit Of Measure Name')
    item_unit_thc_percent = fields.Char(string='Item Unit Thc Percent')
    item_unit_thc_content = fields.Char(string='Item Unit Thc Content')
    item_unit_thc_content_unit_of_measure_name = fields.Char(string='Item Unit Thc Content Unit Of Measure Name')
    item_unit_volume = fields.Char(string='Item Unit Volume')
    item_unit_volume_unit_of_measure_name = fields.Char(string='Item Unit Volume Unit Of Measure Name')
    item_unit_weight = fields.Char(string='Item Unit Weight')
    item_unit_weight_unit_of_measure_name = fields.Char(string='Item Unit Weight Unit Of Measure Name')
    item_serving_size = fields.Char(string='Item Serving Size')
    item_supply_duration_days = fields.Char(string='Item Supply Duration Days')
    item_unit_quantity = fields.Char(string='Item Unit Quantity')
    item_unit_quantity_unit_of_measure_name = fields.Char(string='Item Unit Quantity Unit Of Measure Name')
    quantity_sold = fields.Char(string='Quantity Sold')
    unit_of_measure_name = fields.Char(string='Unit Of Measure Name')
    unit_of_measure_abbreviation = fields.Char(string='Unit Of Measure Abbreviation')
    total_price = fields.Char(string='Total Price')
    sales_delivery_state = fields.Char(string='Sales Delivery State')
    archived_date = fields.Char(string='Archived Date')
    recorded_date_time = fields.Char(string='Recorded Date Time')
    recorded_by_user_name = fields.Char(string='Recorded By User Name')
    last_modified = fields.Char(string='Last Modified')

    def _assert_receipts_param(self, license_number, update_date=False, receipt_date=False):
        """

        Helps maintain (getter/setter) the last sync date for given metrc license number 
        and receipt type.
        It stores values in dict format in ir.config.param with key 'metrc.receipts.last.sync'
        {
            'A12-0000015-LI': '2019-07-13 01:00:00',
            'M10-0000004-LIC': '2019-07-15 03:00:00',
            ...
        }

        @param license_number : metrc license number use for querying license Receipts
        @param update_date    : if true it will update last sync date for given license receipt type
        @param receipt_date  : receipt date will be updated last sync date for given license receipt type
                                if update_date is True, also require if update_date is True

        @return date string   : return string datetime of last sync if found else, return False
        """
        ICP = self.env['ir.config_parameter'].sudo()
        param_key = 'metrc.receipts.last.sync'
        param_date = False
        try:
            raw_receipt_values = ICP.get_param(param_key, default='{}')
            receipt_values = dict(safe_eval(raw_receipt_values))
            if update_date and receipt_date:
                prev_update_date = receipt_values.get(license_number)
                if not prev_update_date:
                    receipt_values.update({license_number: fields.Datetime.now()})
                receipt_values.update({license_number: fields.Datetime.to_string(receipt_date)})
                ICP.set_param(param_key, str(receipt_values))
            param_date = receipt_values.get(license_number)
        except Exception as ex:
            raise ex
            _logger.error('Error during config param "metrc.receipts.last.sync".\n%s'%(ex))
            pass
        return param_date

    def _map_receipt_reponse(self, receipt):
        """
        Do the field mapping of Metrc receipt repose data to model fields
        @param receipt <dict>: metrc receipt response dict

        @return <dict> : response mapped to model fields 
        """
        receipt_vals = {
            'receipt_id': receipt['Id'],
            'receipt_number': receipt['ReceiptNumber'],
            'sales_date_time': receipt['SalesDateTime'],
            'sales_customer_type': receipt['SalesCustomerType'],
            'patient_license_number': receipt['PatientLicenseNumber'],
            'caregiver_license_number': receipt['CaregiverLicenseNumber'],
            'identification_method': receipt['IdentificationMethod'],
            'total_packages': receipt['TotalPackages'],
            'total_price': receipt['TotalPrice'],
            'is_final': receipt['IsFinal'],
            'archived_date': receipt['ArchivedDate'],
            'recorded_date_time': receipt['RecordedDateTime'],
            'recorded_by_user_name': receipt['RecordedByUserName'],
            'last_modified': receipt['LastModified'],
        }
        return receipt_vals

    def _map_transaction_reponse(self, transaction):
        """
        Do the field mapping of Metrc receipt package response data to model fields
        @param receipt <dict>: metrc receipt response dict

        @return <dict> : response mapped to model fields 
        """
        transaction_vals = {
            'package_id': transaction['PackageId'],
            'package_label': transaction['PackageLabel'],
            'product_name': transaction['ProductName'],
            'product_category_name': transaction['ProductCategoryName'],
            'item_strain_name': transaction['ItemStrainName'],
            'item_unit_cbd_percent': transaction['ItemUnitCbdPercent'],
            'item_unit_cbd_content': transaction['ItemUnitCbdContent'],
            'item_unit_cbd_content_unit_of_measure_name': transaction['ItemUnitCbdContentUnitOfMeasureName'],
            'item_unit_thc_percent': transaction['ItemUnitThcPercent'],
            'item_unit_thc_content': transaction['ItemUnitThcContent'],
            'item_unit_thc_content_unit_of_measure_name': transaction['ItemUnitThcContentUnitOfMeasureName'],
            'item_unit_volume': transaction['ItemUnitVolume'],
            'item_unit_volume_unit_of_measure_name': transaction['ItemUnitVolumeUnitOfMeasureName'],
            'item_unit_weight': transaction['ItemUnitWeight'],
            'item_unit_weight_unit_of_measure_name': transaction['ItemUnitWeightUnitOfMeasureName'],
            'item_serving_size': transaction['ItemServingSize'],
            'item_supply_duration_days': transaction['ItemSupplyDurationDays'],
            'item_unit_quantity': transaction['ItemUnitQuantity'],
            'item_unit_quantity_unit_of_measure_name': transaction['ItemUnitQuantityUnitOfMeasureName'],
            'quantity_sold': transaction['QuantitySold'],
            'unit_of_measure_name': transaction['UnitOfMeasureName'],
            'unit_of_measure_abbreviation': transaction['UnitOfMeasureAbbreviation'],
            'total_price': transaction['TotalPrice'],
            'sales_delivery_state': transaction['SalesDeliveryState'],
            'archived_date': transaction['ArchivedDate'],
            'recorded_date_time': transaction['RecordedDateTime'],
            'recorded_by_user_name': transaction['RecordedByUserName'],
            'last_modified': transaction['LastModified'],
        }
        return transaction_vals


    def parse_date(self, dt_stamp):
        try:
            dt = parser.parse(dt_stamp)
            dt_utc = dt.astimezone(pytz.utc).replace(tzinfo=None)
        except:
            dt_utc = False
            pass
        return dt_utc

    def _process_receipt_transactions(self, license_number, receipts):
        """
        Method to keep the a receipt and packages between Metrc and Odoo
        Method create or updates receipt and packages details fetch from the Metrc.

        @param license_number <str> : metrc license number used for querying license Receipts
        @param receipt      <dict> : dict response of a receipt fetched from Metrc
        @param packages      <dict> : receipt package dict for given receipt on above param

        @return date string   : return record-set to created/updated receipt records.

        """
        existing_receipt_ids = False
        for receipt in receipts:
            receipt_id = receipt['Id']
            receipt_vals = self._map_receipt_reponse(receipt)
            receipt_vals.update({'src_license': license_number})
            existing_receipt_ids = self.search([
                                    ('src_license', '=', license_number),
                                    ('receipt_id', '=', receipt_id),
                                ])
            if existing_receipt_ids:
                existing_receipt_ids.write(receipt_vals)
            else:
                # we must create empty receipt lines as Metrc may give receipt 
                # without package later we will reconcile them.
                existing_receipt_ids += self.create(receipt_vals)
            transactions = receipt.get('Transactions', [])
            while transactions:
                transaction = transactions.pop()
                transaction_vals = self._map_transaction_reponse(transaction)
                package_id = transaction['PackageId']
                package_label = transaction['PackageLabel']
                #search for exact match of package with id.
                existing_transaction_ids = existing_receipt_ids.filtered(lambda pack: \
                                                            pack.receipt_id == receipt_id\
                                                        and pack.package_id == package_id\
                                                        and pack.package_label == package_label\
                                                        and pack.src_license == license_number)
                if existing_transaction_ids:
                    existing_transaction_ids.write(transaction_vals)
                    existing_receipt_ids += existing_transaction_ids
                else:
                    # look receipt that are no transaction details
                    empty_existing_transaction_ids = existing_receipt_ids.filtered(lambda pack: pack.package_id == 0\
                                                                                    and not pack.package_label\
                                                                                    and pack.receipt_id == receipt_id
                                                                                    and pack.src_license == license_number)
                    if empty_existing_transaction_ids:
                        empty_existing_transaction_ids.write(transaction_vals)
                        existing_receipt_ids += empty_existing_transaction_ids
                    else:
                        # not existing transaction or empty lines found so we create new receipt transaction
                        receipt_transaction_vals = receipt_vals.copy()
                        receipt_transaction_vals.update(transaction_vals)
                        existing_receipt_ids += self.create(receipt_transaction_vals)
        return existing_receipt_ids

    def _cron_do_import_receipts(self, metrc_license=False, force_last_sync_date=False, automatic=True, raise_for_error=False):
        metrc_account = self.env.user.ensure_metrc_account()
        if not self.env.user.metrc_account_id:
            return True
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
            dt_now = datetime.now()
            if force_last_sync_date and isinstance(force_last_sync_date, datetime):
                last_sync_date = force_last_sync_date
            else:
                license_last_sync_date = self._assert_receipts_param(license.license_number)
                last_sync_date = dt_now - timedelta(hours=23, minutes=59, seconds=0) \
                                    if not license_last_sync_date \
                                        else fields.Datetime.from_string(license_last_sync_date)
            while last_sync_date < dt_now:
                new_last_sync_date = last_sync_date + timedelta(hours=23, minutes=59, seconds=0)
                if new_last_sync_date > dt_now:
                    new_last_sync_date = dt_now
                params = {
                    'lastModifiedStart': fields.Datetime.context_timestamp(self, last_sync_date).isoformat(),
                    'lastModifiedEnd': fields.Datetime.context_timestamp(self, new_last_sync_date).isoformat(),
                    'licenseNumber': license.license_number,
                }
                uri = '/{}/{}/{}'.format('sales', metrc_account.api_version, 'receipts')
                try:
                    receipt_result = metrc_account.fetch('GET', uri, params=params)
                    receipt_ids = self._process_receipt_transactions(license.license_number, receipt_result)
                    if automatic:
                        cr.commit()
                except Exception as ex:
                    if automatic:
                        cr.rollback()
                    _logger.error('Error during synchronizing receipts \n%s' % str(ex))
                    last_sync_date = new_last_sync_date
                    if raise_for_error:
                        raise ex
                    else:
                        metrc_account.log_exception()
                if not self._context.get('update_receipt_icp'):
                    self._assert_receipts_param(license.license_number, True, last_sync_date)
                    if automatic:
                        cr.commit()
                last_sync_date = new_last_sync_date
        if automatic:
            cr.commit()
            cr.close()
        return True
