# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    def _get_warehouse_license(self):
        return self.warehouse_id.license_id and self.warehouse_id.license_id.license_number or False


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def _get_available_quantity(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False, allow_negative=False):
        if self.env.context.get('force_lot_id') and product_id and product_id.is_metric_product:
            lot_obj = self.env['stock.production.lot'].browse(self.env.context.get('force_lot_id'))
            lot_id = lot_obj
            strict = True
        return super(StockQuant, self). _get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict, allow_negative=allow_negative)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    lot_qty = fields.Float(string="Available lot qty", compute="_compute_split_needed")
    split_needed = fields.Boolean(compute="_compute_split_needed")
    bypass_metrc_reporting = fields.Boolean(copy=True)

    @api.constrains('lot_id', 'lot_name')
    def check_lot_existance(self):
        for sml in self.filtered(lambda l: l.product_id.is_metric_product and (l.product_id.tracking == 'lot') and l.lot_id and l.location_dest_id.usage == 'internal'):
            lot_name = sml.lot_id._get_metrc_name() if sml.lot_id else sml.lot_name
            target_warehouse = sml.location_dest_id.get_warehouse()
            curr_lot_warehouses = sml.lot_id.get_all_warehouse()
            dup_lot = self.env['stock.production.lot'].search(['|', ('name', '=', lot_name), ('metrc_tag', '=', lot_name), ('product_id', '!=', sml.product_id.id)], limit=1)
            message = ""
            if dup_lot:
                message = "Can not proceed with the transfer.\n-This lot is duplicate of {} lot having {} product.\n".format(dup_lot._get_metrc_name(), dup_lot.product_id.metrc_name)
            elif curr_lot_warehouses and target_warehouse not in curr_lot_warehouses and \
                 float_compare(sml.qty_done, sml.lot_qty, precision_rounding=sml.product_uom_id.rounding) < 0:
                message = "Lot {} can not exists in multiple warehouses.\n".format(lot_name)
                message += "- It is already available on {}, and you are going to make it available at {}". format(','.join(curr_lot_warehouses.mapped('name')), target_warehouse.name)
            if message:
                raise UserError(_(message))

    @api.depends('lot_id')
    def _compute_split_needed(self):
        Quants = self.env['stock.quant']
        for record in self:
            if not record.lot_id:
                record.lot_qty = 0
                record.split_needed = False
        for line in self.filtered(lambda l: l.lot_id):
            warehouse = line.location_id.get_warehouse()
            if warehouse:
                lot_product = line.product_id.with_context(lot_id=line.lot_id.id, warehouse=warehouse.id)
            else:
                lot_product = line.product_id.with_context(lot_id=line.lot_id.id, location=line.location_id.id)
            line.lot_qty = lot_product.qty_available
            if not lot_product.qty_available:
                line.lot_qty = 0
            reserved_quantity = 0.00
            quants = Quants._gather(line.product_id, line.location_id, lot_id=line.lot_id, strict=True)
            if quants:
                reserved_quantity = sum(quants.mapped('reserved_quantity'))
            if not float_is_zero(reserved_quantity, precision_rounding=line.product_uom_id.rounding) and \
               float_compare(reserved_quantity, line.product_uom_qty, precision_rounding=line.product_uom_id.rounding) > 0:
                line.lot_qty = lot_product.qty_available + line.product_uom_qty - reserved_quantity
            line.split_needed = True if line.lot_qty > line.product_uom_qty else False

    def split_quantity(self):
        self.ensure_one()
        if self.lot_id and self.lot_id.metrc_id == 0:
            raise UserError(_("Lot {} is not synced with metrc.\nOnly metrc synced lots can be splitted.".format(self.lot_id._get_metrc_name())))
        if float_is_zero(self.lot_id.product_qty, precision_rounding=self.product_uom_id.rounding) or self.lot_id.product_qty < 0.00:
            raise ValidationError(_("Lot with 0.00 or negative quantity can not be splitted."))
        locations = self.lot_id.quant_ids.filtered(lambda q: q.location_id.usage == 'internal').mapped('location_id')
        if not locations:
            raise UserError(_("Product {} with lot number {} not found on any physical location.\n Can not proceed with splitting.".format(self.product_id.metrc_name, self.lot_id._get_metrc_name())))
        reserved_move_lines = self.lot_id.get_reserved_move_lines(locations)
        message = False
        if (reserved_move_lines-self) and sum((reserved_move_lines-self).mapped('product_uom_qty')) > self.lot_qty:
            result = self.lot_id.with_context(picking=self.picking_id.sudo()).show_reserved_documents()
            if result:
                return result
        wiz = self.env['lot.split.wizard'].create({
            'lot_id': self.lot_id.id,
            'location_id': locations[0].id,
            'warehouse_id': locations[0].get_warehouse().id,
            'product_qty': self.product_uom_qty,
            'picking_id': self.picking_id.id,
            'reserved_objects': message
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'lot.split.wizard',
            'res_id': wiz.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'views': [(self.env.ref('metrc_stock.split_lot_wizard_form').id, 'form')],
            'context': {'move_ref': self.picking_id.name, 'move_line_id': self.id},
            'domain': [],
            'target': 'new'
        }

    def toggle_bypass_metrc_reporting(self):
        for move_line in self.filtered(lambda l: l.production_id and l.lot_id):
            move_line.bypass_metrc_reporting = not move_line.bypass_metrc_reporting
            if move_line.bypass_metrc_reporting:
                self.production_id.message_post(body=_("Metrc package <b>{}</b> set as not to be reported to metrc by <b>{}</b>".format(move_line.lot_id.name, self.env.user.name)))


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    reason_id = fields.Many2one('metrc.package.adjust.reason', string="Adjustment Reason")
    reason_note = fields.Char()
    note_required = fields.Boolean(related="reason_id.note_required")
    warehouse_id = fields.Many2one('stock.warehouse')
    facility_license_id = fields.Many2one('metrc.license', compute="_compute_facility_license_id", store=True, string="Facility License")
    is_metrc_adjustment = fields.Boolean(compute="_compute_is_metrc_adjustment")
    banner_message = fields.Html(compute="_compute_banner_message")
    downstream = fields.Boolean(help="Adjustment from METRC -> ODOO")
    do_not_adjust = fields.Boolean(string="Don't report to METRC", help="Check this field to bypass metrc reporting.")
    
    @api.onchange('location_ids')
    def onchange_location(self):
        licenses = self.location_ids.mapped('facility_license_id')
        if len(licenses) > 1:
            raise ValidationError(_('Can not perform adjustments for multiple metrc licenses.'))

    @api.depends('product_ids', 'line_ids')
    def _compute_is_metrc_adjustment(self):
        for inventory in self:
            inventory.is_metrc_adjustment = False
            if inventory.product_ids and any([p.is_metric_product for p in inventory.product_ids]):
                inventory.is_metrc_adjustment = True
            elif inventory.line_ids and any([line.is_metric_product for line in inventory.line_ids]):
                inventory.is_metrc_adjustment = True
            if inventory.line_ids and all([line.do_not_adjust for line in inventory.line_ids.filtered(lambda l: l.is_metric_product)]):
                inventory.is_metrc_adjustment = False

    @api.depends('downstream', 'is_metrc_adjustment')
    def _compute_banner_message(self):
        for inventory in self:
            inventory.banner_message = ''
            if inventory.is_metrc_adjustment:
                banner_inner_message = ""
                if inventory.downstream:
                    banner_inner_message += "Product quantities adjusted from Metrc."
                else:
                    if inventory.state == 'done':
                        banner_inner_message += "Product quantities adjusted in Metrc."
                    else:
                        banner_inner_message += "By validating inventory adjustment, you will attempt reporting product lot adjustments to Metrc."
                inventory.banner_message = "<div style='background-color: #%s; border-color:#%s; font-size: 18px;'>\
                                    <center> <em>The inventory adjustment contains Metrc product(s).</em><br/>%s<center></div>" % (
                    "fff3cd" if inventory.state != 'done' else "d4edda",
                    "ffeeba" if inventory.state != 'done' else "c3e6cb",
                    banner_inner_message
                )

    @api.depends('location_ids')
    def _compute_facility_license_id(self):
        for inventory in self.filtered(lambda i: i.location_ids):
            license = inventory.location_ids.mapped('facility_license_id')
            inventory.facility_license_id = license if len(license) == 1 else False

    def action_start(self):
        result = super(StockInventory, self).action_start()
        self._compute_is_metrc_adjustment()
        return result

    def _get_inventory_lines_values(self):
        values = super(StockInventory, self)._get_inventory_lines_values()
        ProductProduct = self.env['product.product']
        for val in values:
            product = ProductProduct.browse(val['product_id'])
            val.update({
                'reason_id': product.is_metric_product and self.reason_id and self.reason_id.id or False,
                'reason_note': self.reason_note,
                'do_not_adjust': self.do_not_adjust,
            })
        return values

    def action_check(self):
        if not self.env.context.get('bypass_check'):
            for inventory in self.filtered(lambda x: x.state not in ('done', 'cancel') and x.facility_license_id and x.facility_license_id.metrc_type == 'metrc'):
                if any([line.lot_required and not line.prod_lot_id for line in inventory.line_ids]):
                    msg = "Lot/Serial number not provided in inventory lines for following products.\n"
                    for inv_line in inventory.line_ids.filtered(lambda l: l.lot_required and not l.prod_lot_id):
                        msg += "- {}\n".format(inv_line.product_id.display_name)
                    raise UserError(_(msg))
        return super(StockInventory, self).action_check()

    def _action_done(self):
        res = super(StockInventory, self)._action_done()
        if self.is_metrc_adjustment and not self.env.context.get('bypass_adjust'):
            metrc_account = self.env.user.ensure_metrc_account()
            for inventory in self.filtered(lambda l: l.is_metrc_adjustment and l.facility_license_id
                                                     and l.facility_license_id.metrc_type == 'metrc'):
                data = []
                url = '{}/{}/{}'.format('/packages', metrc_account.api_version, 'adjust')
                params = {'licenseNumber': inventory.facility_license_id.license_number}
                invalid_inv_lines = []
                aggrigated_lines = {}
                non_metrc_inv_lines = []
                for line in inventory.line_ids.filtered(lambda l: l.is_metric_product and not l.do_not_adjust):
                    lot_name = line.prod_lot_id._get_metrc_name()
                    if lot_name not in aggrigated_lines.keys():
                        aggrigated_lines[lot_name] = {'theoretical_qty': 0.00, 'product_qty': 0.00}
                    aggrigated_lines[lot_name]['theoretical_qty'] += line.theoretical_qty
                    aggrigated_lines[lot_name]['product_qty'] += line.product_qty
                    aggrigated_lines[lot_name]['diff'] = aggrigated_lines[lot_name]['theoretical_qty'] - aggrigated_lines[lot_name]['product_qty']
                metrc_adjustments = {lot: False for lot in aggrigated_lines.keys()}
                for inventory_line in inventory.line_ids.filtered(lambda l: not l.theoretical_qty == l.product_qty and
                                                                            l.is_metric_product and not l.do_not_adjust):
                    facility_license = inventory_line.location_id.get_warehouse().license_id.license_number
                    if not inventory_line.reason_id:
                        invalid_inv_lines.append(inventory_line)
                    if not inventory_line.prod_lot_id:
                        raise UserError(_("Lot not provided for product {} in inventory lines."
                                          . format(inventory_line.product_id.metrc_name)))
                    warehouse_quantity = inventory_line._get_qty_by_warehouse(inventory_line.prod_lot_id,
                                                                              inventory_line.location_id.get_warehouse())
                    lot_name = inventory_line.prod_lot_id._get_metrc_name()
                    if not float_is_zero(aggrigated_lines[lot_name]['diff'],
                                         precision_rounding=inventory_line.product_uom_id.rounding):
                        resp = inventory_line.prod_lot_id._is_package_exist_on_metrc(inventory_line.prod_lot_id._get_metrc_name(),
                                                                                     license=facility_license, raise_for_error=False)
                        if resp and ('Quantity' in resp):
                            if warehouse_quantity != inventory_line.product_id.from_metrc_qty(resp['Quantity']):
                                metrc_qty = warehouse_quantity - inventory_line.prod_lot_id.product_id.from_metrc_qty(resp['Quantity'])
                                if metrc_adjustments.get(lot_name):
                                    metrc_adjustments[lot_name]['Quantity'] += inventory_line.prod_lot_id.product_id.to_metrc_qty(metrc_qty)
                                else:
                                    metrc_adjustments[lot_name] = {
                                        "Label": lot_name,
                                        "Quantity": inventory_line.prod_lot_id.product_id.to_metrc_qty(metrc_qty),
                                        "UnitOfMeasure": inventory_line.prod_lot_id.metrc_uom_id.name,
                                        "AdjustmentReason": inventory_line.reason_id and inventory_line.reason_id.name or inventory.reason_id.name,
                                        "AdjustmentDate": fields.Date.to_string(fields.Date.today()),
                                        "ReasonNote": inventory_line.reason_note or inventory.reason_note
                                    }
                                inventory_line.metrc_adjust_qty = metrc_qty
                                aggrigated_lines[lot_name]['diff'] = 0.00
                            else:
                                # Quantity matches after inventory adjustment is done.
                                continue
                        else:
                            non_metrc_inv_lines.append(inventory_line)
                    else:
                        inventory_line.do_not_adjust = True
                for lot, adjustment_payload in metrc_adjustments.items():
                    if adjustment_payload:
                        data.append(adjustment_payload)
                if invalid_inv_lines:
                    msg = "Package adjust reason was not specified for the following product packages. \nCan not perform package adjustment in METRC without package adjustment reason.\n"
                    for inv_line in invalid_inv_lines:
                        msg += '- {} [{}]\n'.format(inv_line.prod_lot_id._get_metrc_name(), inv_line.product_id.metrc_name)
                    raise UserError(_(msg))
                if non_metrc_inv_lines:
                    msg = "Packages not found in METRC for following packages. \nCan not perform package adjustment for them.\n"
                    for inv_line in non_metrc_inv_lines:
                        license = inv_line.location_id.facility_license_id.license_number
                        msg += '- {} [{}], Location: {}[{}]\n'.format(inv_line.prod_lot_id._get_metrc_name(), inv_line.product_id.metrc_name, inv_line.location_id.display_name, license)
                    raise UserError(_(msg))
                _logger.info("Inventory Adjustment will be done for following lines.")
                _logger.info(data)
                if data:
                    metrc_account.fetch('POST', url, params=params, data=data)
                    lot_name = [d['Label'] for d in data]
                    stock_production_lots = self.env['stock.production.lot'].search([('name', 'in', lot_name)]).filtered(lambda l: not l.metrc_qty == l.product_qty)
                    for stock_production_lot in stock_production_lots:
                        resp = stock_production_lot._fetch_metrc_package(license=inventory.facility_license_id)
                        if resp and resp.get('Quantity') and stock_production_lot.metrc_qty != resp.get('Quantity'):
                            stock_production_lot.write({
                                'metrc_qty': resp['Quantity']
                            })
        return res

    def action_open_inventory_lines(self):
        action_data = super(StockInventory, self).action_open_inventory_lines()
        if self.reason_id:
            action_data['context'].update({'default_reason_id': self.reason_id.id})
        if self.reason_note:
            action_data['context'].update({'default_reason_note': self.reason_note})
        if self.do_not_adjust:
            action_data['context'].update({'default_do_not_adjust': self.do_not_adjust})
        return action_data


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    reason_id = fields.Many2one('metrc.package.adjust.reason')
    is_metric_product = fields.Boolean(related='product_id.is_metric_product')
    reason_note = fields.Char()
    lot_required = fields.Boolean(compute="_compute_lot_required")
    do_not_adjust = fields.Boolean(string="Don't report to Metrc")
    metrc_adjust_qty = fields.Float(string="Metrc Adjustment Qty", help="Quantity adjusted in metrc.")

    def _compute_lot_required(self):
        for inv_line in self:
            inv_line.lot_required = True if (inv_line.product_id.tracking in ['lot', 'serial']) else False

    def _get_qty_by_warehouse(self, lot_id, warehouse_id):
        warehouse_locations = self.env['stock.location'].search([('location_id', 'child_of', warehouse_id.view_location_id.id), ('usage', '=', 'internal')])
        quants = lot_id.quant_ids.filtered(lambda q: q.location_id.id in warehouse_locations.ids)
        return sum(quants.mapped('quantity'))
