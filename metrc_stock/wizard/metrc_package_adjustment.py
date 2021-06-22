# -*- coding: utf-8 -*-

import io
import base64
from odoo import fields, models, _
from odoo.tools import pycompat, float_round
from odoo.exceptions import UserError


class MetrcPackageAdjustment(models.TransientModel):
    _name = "metrc.package.adjustment"
    _description = "Metrc Package Adjustment"

    file_data = fields.Binary(string="Inventory CSV File", required=True)
    file_name = fields.Char()
    warehouse_id = fields.Many2one('stock.warehouse')

    def process(self):
        csv_data = self.file_data
        license = self.warehouse_id.license_id
        csv_iterator = pycompat.csv_reader(
            io.BytesIO(base64.b64decode(csv_data)))
        csv_rows = [line for line in csv_iterator]
        csv_data = {line[0]: {'quantity': line[1], 'location': line[2], 'reason': line[4]} for line in csv_rows[1:]}
        csv_locations = [line[2] for line in csv_rows[1:]]
        csv_locations = set(csv_locations)
        csv_data_by_locations = {loc: [] for loc in csv_locations}
        all_lots = []
        reasons = []
        for line in csv_rows[1:]:
            csv_data_by_locations[line[2]].append(line[0])
            all_lots.append(line[0])
            reasons.append(line[4])
        lot_objects = self.env['stock.production.lot'].search([('name', 'in', all_lots)])
        locations = self.env['stock.location'].search([('location_id', 'child_of', self.warehouse_id.view_location_id.id)])
        if locations and any([loc not in locations.mapped('display_name') for loc in csv_locations]):
            undefined_locations = [loc for loc in csv_locations if loc not in locations.mapped('display_name')]
            raise UserError(_("Locations on csv [{}] not found in the current warehouse {}. Please prepare the csv again with valid data.".format(','.join(undefined_locations), self.warehouse_id.display_name)))
        reasons = self.env['metrc.package.adjust.reason'].search([('name', 'in', reasons)])
        reason_ids = {reason['name']: reason['id'] for reason in reasons}
        loc_not_processed = []
        for loc, lots in csv_data_by_locations.items():
            location = locations.filtered(lambda l: l.display_name == loc)
            if not location:
                loc_not_processed.append(location)
                continue
            inv_adjst = self.env['stock.inventory'].create({
                'name': 'METRC: Bulk package adjustment [%s]' % (license.license_number),
                'filter': 'partial',
                'location_id': location.id,
                'warehouse_id': self.warehouse_id.id,
                'facility_license_id': license.id
                })
            inv_adjst.action_start()
            inv_line_datas = []
            for lot in lots:
                lot = lot_objects.filtered(lambda l: l._get_metrc_name() == lot)
                lot_data = csv_data[lot._get_metrc_name()]
                reason = reason_ids.get(lot_data['reason'])
                line_data = (0, 0, {
                    'product_id': lot.product_id.id,
                    'product_uom_id': lot.product_id.uom_id.id,
                    'location_id': location.id,
                    'prod_lot_id': lot.id,
                    'reason_id': reason,
                    'do_not_adjust': (float(lot_data['quantity']) <= 0.00),
                    'product_qty': float_round(float(lot_data['quantity']), precision_rounding=lot.product_uom_id.rounding)
                })
                inv_line_datas.append(line_data)
            inv_adjst.write({'line_ids': inv_line_datas})
            return {
                'type': 'ir.actions.act_window',
                'name': 'Bulk Inventory Adjustment',
                'res_model': 'stock.inventory',
                'res_id': inv_adjst.id,
                'view_type': 'form',
                'view_mode': 'form',
                'domain': [],
                'context': {}
            }
        if loc_not_processed:
            message = "Packages from following locations could not be processed. Please try again after correcting them.\n"
            for loc in loc_not_processed:
                message += "- {}".format(loc)
            raise UserError(_(message))
