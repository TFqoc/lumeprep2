import requests
import requests_mock
import json
import re
import pkgutil
from datetime import datetime, timedelta
from odoo import fields
import dateutil.parser
import logging


_logger = logging.getLogger(__name__)

dummy_mock_response = {
    "dummy": True

}

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)
        
class MetrcMocker:
    def _load_seed_file(self, filename):
        return pkgutil.get_data(__name__, F'seed_data/{filename}').decode()

    def apply_test_case_mutations(self, quantity, package):
        # Apply Metrc package rules for different test scenearios
        qty_str = str(quantity)

        if re.search('\.001', qty_str):
            package['ShippedQuantity'] = package['ShippedQuantity'] / 2
            package['ReceivedQuantity'] = package['ReceivedQuantity'] / 2

        if re.search('\.002', qty_str):
            package['ShippedQuantity'] = package['ShippedQuantity'] * 2
            package['ReceivedQuantity'] = package['ReceivedQuantity'] * 2

        if re.search('\.003', qty_str):
            package = None

        if re.search('\.004', qty_str):
            package['ShipmentPackageState'] = 'Rejected'

        if re.search('\.005', qty_str):
            package['ShipmentPackageState'] = 'Returned'
            
        return package

    def response_handler_get_package(self, request, context):
        package_label = request.path.split('/')[3].upper()
        lot = self.env['stock.production.lot'].search([
                ('name', '=', package_label)
            ])
        
        if not lot or len(lot.quant_ids) ==0:
            context.status_code = 404
            return "{}"
        
        uom = lot.product_id.metrc_uom_id if lot.product_id.diff_metrc_uom and lot.product_id.metrc_uom_id else lot.product_uom_id
        qty = lot.product_id.to_metrc_qty(lot.product_qty)
        
        
        package = {
            "Id": lot.id,
            "Label": lot.name,
            "PackageType": "Product",
            "SourceHarvestNames": "",
            "LocationId": None,
            "LocationName": None,
            "LocationTypeName": None,
            "RoomId": None,
            "RoomName": None,
            "Quantity": qty,
            "UnitOfMeasureName": uom.name,
            "UnitOfMeasureAbbreviation": uom.abbrv_name,
            "PatientLicenseNumber": "",
            "ProductId": lot.product_id.id,
            "ProductName": lot.product_id.name,
            "ProductCategoryName": lot.product_id.metrc_item_cat_id.name,
            "ItemFromFacilityLicenseNumber": "NEEDTOMOCK",
            "ItemFromFacilityName": "NEEDTOMOCK",
            "ItemStrainName": "Hybrid",
            "ItemUnitCbdPercent": None,
            "ItemUnitCbdContent": None,
            "ItemUnitCbdContentUnitOfMeasureName": None,
            "ItemUnitThcPercent": None,
            "ItemUnitThcContent": None,
            "ItemUnitThcContentUnitOfMeasureName": None,
            "ItemUnitVolume": None,
            "ItemUnitVolumeUnitOfMeasureName": None,
            "ItemUnitWeight": None,
            "ItemUnitWeightUnitOfMeasureName": None,
            "ItemServingSize": "",
            "ItemSupplyDurationDays": None,
            "ItemUnitQuantity": None,
            "ItemUnitQuantityUnitOfMeasureName": None,
            "Note": "",
            "PackagedDate": lot.create_date,
            "InitialLabTestingState": "TestPassed",
            "LabTestingState": "TestPassed",
            "LabTestingStateDate": lot.create_date,
            "IsProductionBatch": False,
            "ProductionBatchNumber": "",
            "IsTradeSample": False,
            "IsDonation": False,
            "SourcePackageIsDonation": False,
            "IsTestingSample": False,
            "IsProcessValidationTestingSample": False,
            "ProductRequiresRemediation": False,
            "ContainsRemediatedProduct": False,
            "RemediationDate": None,
            "ReceivedDateTime": lot.create_date,
            "ReceivedFromManifestNumber": "0",
            "ReceivedFromFacilityLicenseNumber": "NEEDTOMOCK",
            "ReceivedFromFacilityName": "NEEDTOMOCK",
            "IsOnHold": False,
            "ArchivedDate": None,
            "FinishedDate": None,
            "LastModified": lot.write_date
        }

        #self.apply_test_case_mutations(lot.product_qty, package)

        return json.dumps(package, cls=Encoder)

    def response_handler_transfer_deliveries_packages(self, request, context):
        stock_pick_id = int(request.path.split('/')[4])
        sp = self.env['stock.picking'].browse([stock_pick_id])
    
        packages =[]
        
        for sm in sp.move_lines:
            package_split_qty =0
            if len(sm.move_line_ids) != 0:
                package_split_qty = sm.product_id.to_metrc_qty(sm.product_uom_qty)/len(sm.move_line_ids)
                
            for mli in sm.move_line_ids:
                uom_name = mli.product_id.metrc_uom_id.name if mli.product_id.diff_metrc_uom and mli.product_id.metrc_uom_id else mli.product_uom_id.name
                
               
                package = {
                    "PackageId": mli.lot_id.id,
                    "PackageLabel": mli.lot_id.name,
                    "PackageType": "Product",
                    "SourceHarvestNames": None,
                    "SourcePackageLabels": None,
                    "ProductName": mli.product_id.name,
                    "ProductCategoryName": mli.product_id.metrc_item_cat_id.name,
                    "ItemStrainName": mli.product_id.strain_id.name,
                    "ItemUnitCbdPercent": None,
                    "ItemUnitCbdContent": None,
                    "ItemUnitCbdContentUnitOfMeasureName": None,
                    "ItemUnitThcPercent": None,
                    "ItemUnitThcContent": None,
                    "ItemUnitThcContentUnitOfMeasureName": None,
                    "ItemUnitVolume": None,
                    "ItemUnitVolumeUnitOfMeasureName": None,
                    "ItemUnitWeight": None,
                    "ItemUnitWeightUnitOfMeasureName": None,
                    "ItemServingSize": "",
                    "ItemSupplyDurationDays": None,
                    "ItemUnitQuantity": None,
                    "ItemUnitQuantityUnitOfMeasureName": None,
                    "LabTestingState": "NotSubmitted",
                    "ProductionBatchNumber": None,
                    "IsTradeSample": False,
                    "IsDonation": False,
                    "SourcePackageIsDonation": False,
                    "IsTestingSample": False,
                    "ProductRequiresRemediation": False,
                    "ContainsRemediatedProduct": False,
                    "RemediationDate": None,
                    "ShipmentPackageState": "Accepted",
                    "ShippedQuantity": package_split_qty,
                    "ShippedUnitOfMeasureName": uom_name,
                    "GrossUnitOfWeightName": None,
                    "ReceivedQuantity": package_split_qty,
                    "ReceivedUnitOfMeasureName": uom_name
                }

                package = self.apply_test_case_mutations(sm.product_uom_qty, package)
                if package:
                    packages.append(package)

        return json.dumps(packages, cls=Encoder)

    def response_handler_transfers_incoming(self, request, context):
        
        stock_pickings = self.env['stock.picking'].search([
           ('state','=','assigned'),
           ('write_date','>=',fields.Datetime.to_string(datetime.now() - timedelta(minutes=2880)))
        ])
        transfers = []
        license_number = request.qs.get('licensenumber')[0].upper()
        for sp in stock_pickings:
            if sp.facility_license_id.license_number == license_number:
                transfer =  {
                    "Id": sp.id,
                    "ManifestNumber": str(sp.id),
                    "ShipmentLicenseType": "Licensed",
                    "ShipperFacilityLicenseNumber": sp.partner_license_id.license_number,
                    "ShipperFacilityName": "NC3 Systems, INC.",
                    "Name": None,
                    "TransporterFacilityLicenseNumber": "",
                    "TransporterFacilityName": "",
                    "DriverName": "",
                    "DriverOccupationalLicenseNumber": "",
                    "DriverVehicleLicenseNumber": "",
                    "VehicleMake": "",
                    "VehicleModel": "",
                    "VehicleLicensePlateNumber": "",
                    "DeliveryCount": 1,
                    "ReceivedDeliveryCount": 1,
                    "PackageCount": 6,
                    "ReceivedPackageCount": 6,
                    "ContainsPlantPackage": False,
                    "ContainsProductPackage": True,
                    "ContainsTradeSample": False,
                    "ContainsDonation": False,
                    "ContainsTestingSample": False,
                    "ContainsProductRequiresRemediation": False,
                    "ContainsRemediatedProductPackage": False,
                    "CreatedDateTime": "2019-12-03T22:22:39+00:00",
                    "CreatedByUserName": "Derrick Franco",
                    "LastModified": "2019-12-03T23:09:38+00:00",
                    "DeliveryId": sp.id,
                    "RecipientFacilityLicenseNumber": sp.facility_license_id.license_number,
                    "RecipientFacilityName": "NC3 SYSTEMS, INC.",
                    "ShipmentTypeName": "Transfer",
                    "ShipmentTransactionType": "Standard",
                    "EstimatedDepartureDateTime": datetime.now(),
                    "ActualDepartureDateTime": None,
                    "EstimatedArrivalDateTime": datetime.now(),
                    "ActualArrivalDateTime": None,
                    "DeliveryPackageCount": 6,
                    "DeliveryReceivedPackageCount": 6,
                    "ReceivedDateTime": datetime.now(),
                    "EstimatedReturnDepartureDateTime": None,
                    "ActualReturnDepartureDateTime": None,
                    "EstimatedReturnArrivalDateTime": None,
                    "ActualReturnArrivalDateTime": None
                }
                transfers.append(transfer)
        return json.dumps(transfers, cls=Encoder)


    def injectMock(self, env, session):
        self.env = env

        adapter = requests_mock.Adapter()

        adapter.register_uri('GET', re.compile('http://api-ca.metrc.mock/transfers/v1/delivery/.*/packages'),
                             text=self.response_handler_transfer_deliveries_packages)

        adapter.register_uri('GET', '/transfers/v1/incoming',
                             text=self.response_handler_transfers_incoming)

        adapter.register_uri('GET', 'http://api-ca.metrc.mock/facilities/v1',
                             text=self._load_seed_file('facilities_v1.json'))

        adapter.register_uri('GET', 'http://api-ca.metrc.mock/facilities/v1',
                             text=self._load_seed_file('facilities_v1.json'))

        adapter.register_uri('GET', re.compile('http://api-ca.metrc.mock/packages/v1/adjust/reasons.*'),
                             text=self._load_seed_file('packages_v1_adjust_reasons.json'))


        adapter.register_uri('GET', 'http://api-ca.metrc.mock/unitsofmeasure/v1/active',
                             text=json.dumps(dummy_mock_response))

        adapter.register_uri('GET', 'http://api-ca.metrc.mock/items/v1/categories',
                             text=self._load_seed_file('items_v1_categories.json'))

        adapter.register_uri('GET', 'http://api-ca.metrc.mock/labtests/v1/types',
                             text=self._load_seed_file('labtest_v1_types.json'))

        adapter.register_uri('GET', 'http://api-ca.metrc.mock/transfers/v1/types',
                             text=self._load_seed_file('transfers_v1_types.json'))

        adapter.register_uri('GET', 'http://api-ca.metrc.mock/items/v1/active',
                             text="[]")

        adapter.register_uri('POST', 'http://api-ca.metrc.mock/items/v1/create',
                             text=json.dumps(dummy_mock_response))

        adapter.register_uri('GET', 'http://api-ca.metrc.mock/strains/v1/active',
                             text="[]")

        adapter.register_uri('POST', 'http://api-ca.metrc.mock/strains/v1/create',
                             text=json.dumps(dummy_mock_response))

        adapter.register_uri('GET', re.compile('http://api-ca.metrc.mock/packages/v1(?!(/adjust/reasons|/active)).*'),
                             text=self.response_handler_get_package)

        adapter.register_uri('POST',
                             'http://api-ca.metrc.mock/packages/v1/adjust',
                             text=json.dumps({
                                 "LabTestingState": "DUDE!",
                                 "LabTestingStateDate": datetime.now()
                             },
                                 indent=4, sort_keys=True, default=str)
                             )

        session.mount('http://', adapter)
