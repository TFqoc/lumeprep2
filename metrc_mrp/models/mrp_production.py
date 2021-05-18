# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    split_lot = fields.Boolean(string="Split Lots Production Order")
    split_lot_multi = fields.Boolean(string="Multi Lot Batch Split")
    is_metric_product = fields.Boolean(related="product_id.is_metric_product", string='Metrc Product')
    reporting_successful = fields.Boolean(string="Metrc Reporting Successful", help="Successfully reported all produced lots to metrc or not.",
                                          compute="_compute_metrc_reported")

    def _compute_metrc_reported(self):
        for production in self:
            if all(production.finished_move_line_ids.filtered(lambda l: not l.bypass_metrc_reporting).mapped('reported_to_metrc')) or \
               all([mid > 0 for mid in production.finished_move_line_ids.filtered(lambda l: not l.bypass_metrc_reporting).mapped('lot_id.metrc_id')]):
                production.reporting_successful = True
            else:
                production.reporting_successful = False

    def get_consumed_ingredients(self, check_metrc_existance=False):
        """
        Function to calculate raw material consumptions for METRC product manufacturing.
        METRC requires ingredients when creating any new package.

        @returns <list>: Containing quantity consumed for each raw material line like below.
            [
                {
                    'Package': 1A4FF020000025E000000481,
                    'Quantity': 1.0,
                    'UnitOfMeasure': Grams,
                    }
                },
                {
                    'Package': 1A4FF020000025E000000482,
                    'Quantity': 1.0,
                    'UnitOfMeasure': Grams,
                    }
                },

            ]
        """
        raw_matirial_lines = self.move_raw_ids.mapped('move_line_ids').filtered(lambda m: m.product_id.is_metric_product and m.qty_done > 0.00 and m.lot_id)
        if check_metrc_existance and any([line.lot_id.metrc_id == 0 for line in raw_matirial_lines]):
            messages = "Following metrc lots are not synced. Can not proceed with the manufacturing.\n"
            for line in raw_matirial_lines.filtered(lambda l: l.lot_id.metrc_id == 0):
                messages += "- {} [{}]\n".format(line.product_id.metrc_name, line.lot_id._get_metrc_name())
            raise UserError(_(messages))
        finished_move_line_ids = self.finished_move_line_ids\
                                        .filtered(lambda ml: ml.state == 'done'\
                                            and ml.qty_done > 0.00\
                                            and ml.move_id.has_tracking != 'none'\
                                            and ml.lot_id and ml.product_id.is_metric_product)
        total_qty_produced = sum(finished_move_line_ids.mapped('qty_done'))
        result = {line.id: [] for line in finished_move_line_ids}
        raw_move_lots = raw_matirial_lines.mapped('lot_id')
        lot_uom_dict = {lot._get_metrc_name(): lot.metrc_uom_id.name for lot in raw_move_lots}
        for finished_move in finished_move_line_ids:
            ingredients = []
            move_lot_by_qty = {lot._get_metrc_name(): [] for lot in raw_move_lots}
            for move_line in raw_matirial_lines:
                lot_name = move_line.lot_id._get_metrc_name()
                product_qty = move_line.lot_id.product_id\
                                    .to_metrc_qty((move_line.qty_done * finished_move.qty_done) / total_qty_produced)
                move_lot_by_qty[lot_name].append(product_qty)
            for lot, quantities in move_lot_by_qty.items():
                ingredients.append({
                    'Package': lot,
                    'Quantity': sum(quantities),
                    'UnitOfMeasure': lot_uom_dict[lot]
                    })
            result[finished_move.id] = ingredients
        return result

    def _cal_price(self, consumed_moves):
        """Set a price unit on the finished move according to `consumed_moves`.
        Overloading this to calulate cost for byproducts also.
        """
        result = super(MrpProduction, self)._cal_price(consumed_moves)
        work_center_cost = 0
        finished_moves = self.move_finished_ids.filtered(lambda x: x.product_id.is_metric_product\
                                                                  and x.product_id != self.product_id\
                                                                  and x.state not in ('done', 'cancel')\
                                                                  and x.quantity_done > 0)
        for finished_move in finished_moves:
            for work_order in self.workorder_ids:
                time_lines = work_order.time_ids.filtered(lambda x: x.date_end and not x.cost_already_recorded)
                duration = sum(time_lines.mapped('duration'))
                time_lines.write({'cost_already_recorded': True})
                work_center_cost += (duration / 60.0) * work_order.workcenter_id.costs_hour
            if finished_move.product_id.cost_method in ('fifo', 'average'):
                qty_done = finished_move.product_uom._compute_quantity(finished_move.quantity_done, finished_move.product_id.uom_id)
                extra_cost = self.extra_cost * qty_done
                finished_move.price_unit = (sum([-m.stock_valuation_layer_ids.value for m in consumed_moves.sudo()]) + work_center_cost + extra_cost) / qty_done
        return result

    def button_mark_done(self):
        if (self.picking_type_id._get_warehouse_license() and self.picking_type_id.warehouse_id.license_id.metrc_type != 'metrc') or not self.picking_type_id._get_warehouse_license():
            return super(MrpProduction, self).button_mark_done()
        move_lines = self.move_raw_ids.mapped('move_line_ids').filtered(lambda l: l.product_id.is_metric_product)
        lots_to_check = move_lines.mapped('lot_id')
        result = lots_to_check.with_context(production=self.sudo()).show_reserved_documents()
        if result and (not self.split_lot or self.split_lot_multi):
            return result
        # Inform metrc on new lot being created
        ProdctionLot = self.env['stock.production.lot']
        license = self.picking_type_id._get_warehouse_license()
        packages_not_exists = []
        for move_line in move_lines:
            lot_name = move_line.lot_id._get_metrc_name()
            result = ProdctionLot._is_package_exist_on_metrc(lot_name, license)
            if not result:
                packages_not_exists.append(lot_name)
        if packages_not_exists:
            raise UserError(_('Package {} does not exist in METRC. Can not be used in the production.'.format(','.join(packages_not_exists))))
        res = super(MrpProduction, self).button_mark_done()
        finished_move_lines = self.finished_move_line_ids.filtered(lambda ml: ml.state == 'done' and ml.move_id.has_tracking != 'none' and ml.lot_id and ml.product_id.is_metric_product and ml.qty_done > 0.00)
        self._report_lots_to_metrc(finished_move_lines)
        move_lines.mapped('lot_id')._update_metrc_id()
        return res

    def reattempt_metrc_reporting(self):
        self.ensure_one()
        move_lines = self.move_raw_ids.mapped('move_line_ids').filtered(lambda l: l.product_id.is_metric_product)
        finished_move_lines = self.finished_move_line_ids.filtered(lambda ml: ml.state == 'done' and ml.move_id.has_tracking != 'none' and \
                                                                   ml.lot_id and ml.product_id.is_metric_product and ml.qty_done > 0.00 and \
                                                                   ml.reported_to_metrc == False and ml.bypass_metrc_reporting == False and \
                                                                   ml.lot_id.metrc_id == 0)
        self._report_lots_to_metrc(finished_move_lines)
        move_lines.mapped('lot_id')._update_metrc_id()

    def _report_lots_to_metrc(self, move_line_ids):
        if not self.location_dest_id.metrc_location_id:
            raise UserError(_("Metrc Location is not set on {}.\n"
                              "Please configure one to proceed.".format(self.location_dest_id.name)))
        metrc_location = self.location_dest_id.metrc_location_id.name
        consumed_quantities = self.get_consumed_ingredients()
        metrc_reported_lines = self.env['stock.move.line']
        ProdctionLot = self.env['stock.production.lot']
        license = self.picking_type_id._get_warehouse_license()
        package_data = []
        for line in move_line_ids.filtered(lambda l: not l.bypass_metrc_reporting):
            # checking for lot is availbale to be assigend or not.
            lot_name = line.lot_id._get_metrc_name()
            resp = ProdctionLot._is_package_exist_on_metrc(lot_name, raise_for_error=False)
            if resp:
                raise UserError(_("Package {} already exist in METRC. Please use another package tag to produce.".format(resp['Label'])))
            ingredients = consumed_quantities.get(line.id, [])
            if not ingredients:
                msg = "Manufacturing order to produce lot {} for METRC product {} can not be processed!\nFollowing ingredient products are not consumed due to unavailability.".format(lot_name, line.lot_id.product_id.metrc_name)
                for raw_move in self.move_raw_ids.filtered(lambda m: m.product_id.is_metric_product):
                    msg += "\n- {} Qty required {}, Qty done {}".format(raw_move.product_id.metrc_name, raw_move.product_uom_qty, raw_move.quantity_done)
                raise UserError(_(msg))
            package_data.append({
                'Tag': lot_name,
                'Location': metrc_location,
                'Item': line.product_id.metrc_name,
                'Quantity': line.product_id.to_metrc_qty(line.qty_done),
                'UnitOfMeasure': line.product_id.metrc_uom_id.name if line.product_id.diff_metrc_uom and line.product_id.metrc_uom_id else line.product_id.uom_id.name,
                'Ingredients': ingredients,
                'ActualDate': fields.Date.to_string(fields.Date.today()),
                'PatientLicenseNumber': 'n/a',
                'IsProductionBatch': line.lot_id.is_production_batch,
                'ProductionBatchNumber': line.lot_id.batch_number or '',
            })
        metrc_account = self.env.user.ensure_metrc_account()
        uri = '/{}/{}/{}'.format('packages', metrc_account.api_version, 'create')
        params = {'licenseNumber': license}
        metrc_account.fetch('POST', uri, params=params, data=package_data, raise_for_error=True)
        move_line_ids.mapped('lot_id')._update_metrc_id()
        for line in move_line_ids.filtered(lambda l: not l.bypass_metrc_reporting and l.lot_id.metrc_id > 0):
            line.lot_id.name_readonly = True
            line.reported_to_metrc = True
            metrc_reported_lines |= line
        if metrc_reported_lines:
            metrc_msg = "Following packages are created in <b>METRC</b> using this manufacturing order.<br/><ul>"
            for line in metrc_reported_lines:
                metrc_msg += "<li>{}: [<b>{}</b>], Qty: <b>{} {}</b></li>".format(line.product_id.metrc_name, line.lot_id._get_metrc_name(), line.product_id.to_metrc_qty(line.lot_id.product_qty), line.lot_id.metrc_uom_id.name)
                matirials = consumed_quantities.get(line.id, [])
                if matirials:
                    metrc_msg += '''<div class="col-md-6"><table class="table table-bordered">
                                        <thead>
                                            <tr>
                                                <th colspan='2' style="border: 1px solid black"><center><b>Ingredients</b></center></th>
                                            </tr>
                                        </thead>
                                        <tbody>'''
                    for matirial in matirials:
                        metrc_msg += "<tr><td style='border: 1px solid black'>&nbsp;{}&nbsp;</td><td style='border: 1px solid black'>&nbsp;{} {}&nbsp;</td></tr>".format(matirial['Package'], matirial['Quantity'], matirial['UnitOfMeasure'])
                    metrc_msg += "</tbody></table></div>"
            metrc_msg += "</ul>"
            self.message_post(body=_(metrc_msg), message_type="notification", subtype_xmlid="mail.mt_comment")

    def _generate_raw_move_split(self, quantity=False):
        consume_qty = quantity or self.product_qty
        original_quantity = (self.qty_producing - self.qty_produced) or 1.0
        data = {
            'name': self.name,
            'date': self.date_planned_start,
            'date_deadline': self.date_planned_start,
            'bom_line_id': False,
            'product_id': self.product_id.id,
            'product_uom_qty': consume_qty,
            'product_uom': self.product_uom_id.id,
            'location_id': self.location_src_id.id,
            'location_dest_id': self.product_id.property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'price_unit': self.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'state': 'draft',
            'warehouse_id': self.location_src_id.get_warehouse().id,
            'group_id': self.procurement_group_id.id,
            'propagate_cancel': self.propagate_cancel,
            'unit_factor': self.product_qty / original_quantity,
        }
        return self.env['stock.move'].create(data)

    def _generate_raw_move_split_multi(self, lot_lines=False):
        for lot_line in lot_lines:
            self._generate_raw_move_split(quantity=lot_line.product_qty)
