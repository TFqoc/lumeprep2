# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare


class SplitLotWizard(models.TransientModel):
    _name = 'lot.split.wizard'
    _description = "Split Lot Wizard"

    lot_id = fields.Many2one('stock.production.lot')
    warehouse_id = fields.Many2one('stock.warehouse')
    facility_license_id = fields.Many2one(related="location_id.facility_license_id")
    location_id = fields.Many2one('stock.location')
    lot_qty = fields.Float(string="Location available quantity", compute="_compute_lot_qty", digits='Product Unit of Measure')
    warehouse_lot_qty = fields.Float(string="Warehouse available quantity", compute="_compute_lot_qty", digits='Product Unit of Measure')
    product_qty = fields.Float(string="Split location quantity", digits='Product Unit of Measure')
    new_lot_quantity = fields.Float(string="Remaining location quantity", compute="_compute_new_lot_qty", digits='Product Unit of Measure')
    new_lot_number = fields.Char(string="Unused metrc tag")
    picking_id = fields.Many2one('stock.picking')
    uom_id = fields.Many2one(related="lot_id.product_id.uom_id")
    reserved_objects = fields.Html()
    # fields for whole batch split
    product_id = fields.Many2one(related='lot_id.product_id')
    product_packages = fields.One2many(related='product_id.packaging_ids')
    packaging_id = fields.Many2one(string="Packaging", comodel_name='product.packaging')
    split_type = fields.Selection(string="Split Type", selection=[('Single', 'Single'), ('Multiple', 'Multiple')], default='Single',
                                   help="Field to determine type of split.")
    case_size = fields.Float(string="Case size", digits='Product Unit of Measure', help="Size of case.")
    metrc_tag_start = fields.Char(string="Start", help="First metrc tag in the sequence.")
    metrc_tag_end = fields.Char(string="End", help="Last metrc tag in the sequence.")
    split_lot_lines = fields.One2many(comodel_name='lot.split.wizard.line', inverse_name='split_id', string="Metrc tags")
    metrc_tags_count = fields.Integer(compute='_compute_metrc_tags_count')
    total_quantity = fields.Float(compute='_compute_metrc_tags_count', digits='Product Unit of Measure')

    @api.onchange('case_size', 'metrc_tag_start', 'metrc_tag_end')
    def on_change_tag_sequence(self):
        if self.split_type == 'Multiple' and self.case_size and \
           self.metrc_tag_start and self.metrc_tag_end:
            if self.case_size < 0.00:
                raise UserError(_('Case size should be a positive number.'))
            ts1 = self.metrc_tag_start[:15]
            te1 = self.metrc_tag_end[:15]
            if ts1 != te1:
                raise UserError(_("Starting and ending tag pattern doesn't match."))

    def _compute_metrc_tags_count(self):
        for record in self:
            if record.split_lot_lines:
                record.metrc_tags_count = len(record.get_tags_to_split())
                record.total_quantity = sum(record.split_lot_lines.mapped('product_qty'))
            else:
                record.metrc_tags_count = 0
                record.total_quantity = 0

    @api.onchange('packaging_id')
    def onchange_packaging(self):
        if self.packaging_id:
            self.case_size = self.packaging_id.qty

    @api.depends('location_id')
    def _compute_lot_qty(self):
        Quants = self.env['stock.quant']
        for wiz in self:
            location_warehouse = wiz.location_id.get_warehouse()
            wh_product = wiz.lot_id.product_id.with_context(lot_id=wiz.lot_id.id, warehouse=location_warehouse.id)
            loc_product = wiz.lot_id.product_id.with_context(lot_id=wiz.lot_id.id, location=wiz.location_id.id)
            quants = Quants._gather(wiz.lot_id.product_id, wiz.location_id, lot_id=wiz.lot_id, strict=True)
            reserved_qty = sum(quants.mapped('reserved_quantity'))
            wiz.warehouse_lot_qty = wh_product.qty_available - reserved_qty
            wiz.lot_qty = loc_product.qty_available - reserved_qty
            if wiz.picking_id:
                move_lines = wiz.picking_id.mapped('move_line_ids').filtered(lambda l: l.lot_id == wiz.lot_id)
                wiz.warehouse_lot_qty = wiz.warehouse_lot_qty + sum(move_lines.mapped('product_uom_qty'))
                wiz.lot_qty = wiz.lot_qty + sum(move_lines.mapped('product_uom_qty'))

    @api.depends('lot_qty', 'product_qty')
    def _compute_new_lot_qty(self):
        for wiz in self:
            wiz.new_lot_quantity = wiz.lot_qty - wiz.product_qty

    def get_tags_to_split(self):
        if not self.case_size:
            raise UserError(_("Please provide case size to proceed."))
        tags_required = self.lot_qty / self.case_size
        tags = []
        ts1 = self.metrc_tag_start[:15]
        ts2 = self.metrc_tag_start[-9:]
        chunk = ts2
        while tags_required > 0:
            next_tag = ''.join([ts1, chunk])
            tags.append(next_tag)
            chunk = str(int(chunk) + 1).zfill(9)
            if next_tag == self.metrc_tag_end:
                break
            tags_required -= 1
        # if len(tags) < tags_required:
        #     raise UserError(_("Insufficent metrc tag sequence supplied.\nPlease provide larger sequence."))
        if float_compare((len(tags) * self.case_size), self.lot_qty, precision_rounding=self.uom_id.rounding) > 0:
            raise UserError(_("Can not split more then what is available."))
        return tags

    def populate_lots(self):
        tags = self.get_tags_to_split()
        StockProductLot = self.env['stock.production.lot']
        lines = []
        invalid_lots = []
        for tag in tags:
            resp = StockProductLot._is_package_exist_on_metrc(tag, raise_for_error=False)
            if resp:
                invalid_lots.append(tag)
            lines.append((0, 0, {
                'metrc_tag': tag,
                'product_qty': self.case_size
                }))
        if invalid_lots:
            msg = _("Following lots are already used. Please choose a different sequence.\n")
            for tag in invalid_lots:
                msg += "- {}\n".format(tag)
            raise UserError(msg)
        if lines:
            self.write({'split_lot_lines': lines})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Metrc Tags',
            'res_model': 'lot.split.wizard',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(self.env.ref('metrc_stock.multiple_lot_split_wizard_form').id, 'form')],
            'domain': [],
            'context': {},
            'target': 'new'
        }

    def confirm_split(self):
        if self.metrc_tags_count > 150:
            raise UserError(_("You can not split into more then 150 metrc tags at a time."))
        tags = self.get_tags_to_split()
        self.reserved_objects = "<p>You have indicated that you would like to produce %d cases of %.2f, is that correct?</p>" % (len(tags), self.case_size)
        return {
            'name': _('Split Confirmation'),
            'type': 'ir.actions.act_window',
            'res_model': 'lot.split.wizard',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(self.env.ref('metrc_stock.split_lot_confirmation').id, 'form')],
            'domain': [],
            'context': {},
            'target': 'new',
        }

    def modify_split(self):
        return {
            'name': _('Batch Split'),
            'type': 'ir.actions.act_window',
            'res_model': 'lot.split.wizard',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'views': [(self.env.ref('metrc_stock.split_lot_wizard_form').id, 'form')],
            'context': {},
            'domain': [],
            'target': 'new'
        }

    def create_lot_multi(self):
        total_quantity = sum(self.split_lot_lines.mapped('product_qty'))
        StockProductLot = self.env['stock.production.lot']
        if any([float_is_zero(line.product_qty, precision_rounding=self.lot_id.product_uom_id.rounding) for line in self.split_lot_lines]):
            raise UserError(_("Can not produce lot with 0.00 quantity."))
        if float_compare(total_quantity, self.lot_qty, precision_rounding=self.lot_id.product_uom_id.rounding) > 0:
            raise UserError(_("Can not split more then what is available."))
        if not self.warehouse_id.metrc_manu_type_id:
            raise UserError(_("Operation type for split lot is not configured on warehouse {}".format(self.warehouse_id.name)))
        production_order = self.env['mrp.production'].create({
            'picking_type_id': self.warehouse_id.metrc_manu_type_id.id,
            'product_id': self.lot_id.product_id.id,
            'location_src_id': self.location_id.id,
            'location_dest_id': self.location_id.id,
            'product_uom_id': self.lot_id.product_id.uom_id.id,
            'product_qty': total_quantity,
            'qty_producing': total_quantity,
            'split_lot_multi': True,
            'origin': self.env.context.get('move_ref', '')
        })
        production_order.write({'move_finished_ids': [(0,0, move_vals) for move_vals in production_order._get_moves_finished_values()]})
        production_order._generate_raw_move_split_multi(self.split_lot_lines)
        production_order.move_raw_ids._action_confirm()
        production_order.move_finished_ids._action_confirm()
        production_order.move_raw_ids.with_context(force_lot_id=self.lot_id.id)._action_assign()
        message_body = "This lot is created from metrc package: {} using manufacturing order: <a href=# data-oe-model=mrp.production data-oe-id={}>{}</a>".format(self.lot_id._get_metrc_name(), production_order.id, production_order.name)
        lots_dict = {}
        for line in self.split_lot_lines:
            lot = StockProductLot.search(['|', '&', ('is_legacy_lot', '=', True), ('metrc_tag', '=', line.metrc_tag),
                ('name', '=', line.metrc_tag), ('product_id', '=', self.lot_id.product_id.id)], limit=1)
            if not lot:
                lot = StockProductLot.create({
                        'name': line.metrc_tag,
                        'company_id': production_order.company_id.id,
                        'product_id': self.lot_id.product_id.id,
                        'is_production_batch': self.lot_id.is_production_batch,
                        'batch_number': self.lot_id.batch_number,
                    })
            lots_dict.update({line.metrc_tag: lot})
        for move in production_order.move_finished_ids:
            quantity = production_order.product_qty
            location_dest_id = move.location_dest_id._get_putaway_strategy(production_order.product_id).id or move.location_dest_id.id
            for line in self.split_lot_lines:
                vals = {
                  'move_id': move.id,
                  'product_id': move.product_id.id,
                  'production_id': production_order.id,
                  'product_uom_qty': quantity,
                  'product_uom_id': move.product_uom.id,
                  'qty_done': line.product_qty,
                  'lot_id': lots_dict[line.metrc_tag].id,
                  'location_id': move.location_id.id,
                  'location_dest_id': location_dest_id,
                }
                self.env['stock.move.line'].create(vals)
        for raw_move, finish_move in zip(production_order.move_raw_ids.mapped('move_line_ids'), production_order.finished_move_line_ids):
            raw_move.write({'qty_done': raw_move.product_qty})
        try:
            if self.env.context.get('move_line_id'):
                move_line = self.env['stock.move.line'].sudo().browse(int(self.env.context.get('move_line_id')))
                move_line._free_reservation(move_line.product_id, move_line.move_id.location_id, move_line.qty_done, lot_id=move_line.lot_id)
            result = production_order.button_mark_done()
            if isinstance(result, (dict)) and result.get('type', False) == 'ir.actions.act_window':
                lot_to_unlink = production_order.finished_move_line_ids.mapped('lot_id')
                production_order.finished_move_line_ids.unlink()
                production_order.move_raw_ids.mapped('move_line_ids').unlink()
                production_order.action_cancel()
                lot_to_unlink.unlink()
                # returning the reserved quantities wizard after cancelling the MO.
                return result
            for lot in lots_dict.values():
                lot._update_custom_fields(self.lot_id)
                lot.message_post(body=_(message_body), message_type="notification", subtype_xmlid="mail.mt_comment")
        except UserError as e:
            raise UserError(e)
        except ValidationError as ve:
            raise ValidationError(ve)
        except Exception:
            lot_to_unlink = production_order.finished_move_line_ids.mapped('lot_id')
            production_order.button_unreserve()
            production_order.action_cancel()
            lot_to_unlink.unlink()
            raise UserError(_("Failed to process the manufacturing order {} for batch split.".format(production_order.name)))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Multi-Batch Split',
            'res_model': 'mrp.production',
            'res_id': production_order.id,
            'view_type': 'form',
            'view_mode': 'form',
            'context': {},
            'domain': [],
            'target': 'self'
        }

    def temp_create_lot(self):
        StockProductLot = self.env['stock.production.lot']
        resp = False
        for wiz in self:
            total_quantity = sum(wiz.split_lot_lines.mapped('product_qty'))
            is_multi = True if wiz.split_type == 'Multiple' else False
            product_qty = total_quantity if is_multi else wiz.product_qty
            if float_compare(product_qty, wiz.lot_qty, precision_rounding=wiz.lot_id.product_uom_id.rounding) > 0:
                raise UserError(_("Can not split more then what is available."))
            if is_multi:
                if any([float_is_zero(line.product_qty, precision_rounding=self.lot_id.product_uom_id.rounding) for line
                        in self.split_lot_lines]):
                    raise UserError(_("Can not produce lot with 0.00 quantity."))
            else:
                if float_compare(wiz.product_qty, 0.0, precision_rounding=wiz.lot_id.product_uom_id.rounding) < 0:
                    raise UserError(_("Initial demand must be a positive number."))
                if float_compare(wiz.lot_qty, wiz.new_lot_quantity,
                                 precision_rounding=wiz.lot_id.product_uom_id.rounding) == 0:
                    raise UserError(_("Available lot quantity and new lot quantity can not be same."))
            if not wiz.warehouse_id.metrc_manu_type_id:
                raise UserError(
                    _("Operation type for split lot is not configured on warehouse {}".format(wiz.warehouse_id.name)))
            if not is_multi:
                resp = StockProductLot._is_package_exist_on_metrc(wiz.new_lot_number, raise_for_error=False)
                if resp:
                    raise UserError(_(
                        "Package {} already exist in metrc. Please use another package tag to produce. \n".format(
                                resp['Label'])))
            if is_multi:
                qty_to_produce = sum(self.split_lot_lines.mapped('product_qty'))
            else:
                qty_to_produce = wiz.new_lot_quantity
                if (float_compare(wiz.lot_qty, wiz.product_qty, precision_rounding=wiz.uom_id.rounding) == 0) \
                        and (float_is_zero(wiz.new_lot_quantity, precision_rounding=wiz.uom_id.rounding)):
                    #  Re-tagging the whole lot
                    qty_to_produce = wiz.product_qty

            order_vals = {
                'picking_type_id': wiz.warehouse_id.metrc_manu_type_id.id,
                'product_id': wiz.lot_id.product_id.id,
                'location_src_id': wiz.location_id.id,
                'location_dest_id': wiz.location_id.id,
                'product_uom_id': wiz.lot_id.product_id.uom_id.id,
                'product_qty': qty_to_produce,
                'origin': self.env.context.get('move_ref', '')
            }
            if is_multi:
                order_vals.update({'split_lot_multi': True})
            else:
                order_vals.update({'split_lot': True})
            production_order = self.env['mrp.production'].create()
            production_order._generate_finished_moves()
            if is_multi:
                production_order._generate_raw_move_split_multi(wiz.split_lot_lines)
            else:
                production_order._generate_raw_move_split()
            production_order.move_raw_ids._action_confirm()
            production_order.move_finished_ids._action_confirm()
            production_order.move_raw_ids.with_context(force_lot_id=wiz.lot_id.id)._action_assign()

            new_lot_numbers = []
            if is_multi:
                new_lot_numbers.append(wiz.split_lot_lines.mapped('metrc_tag'))
            else:
                new_lot_numbers.append(wiz.new_lot_number)
            existing_lots = StockProductLot.search(
                    ['|', '&', ('is_legacy_lot', '=', True), ('metrc_tag', 'in', new_lot_numbers),
                     ('name', 'in', new_lot_numbers), ('product_id', '=', wiz.lot_id.product_id.id)])
            to_create_lots = list(set(new_lot_numbers) - set(existing_lots.mapped('metrc_tag')))
            lots_dict = {}
            lot = False
            for final_lot in to_create_lots:
                lot = StockProductLot.create({
                    'name': final_lot,
                    'company_id': production_order.company_id.id,
                    'product_id': wiz.lot_id.product_id.id
                })
                if is_multi:
                    lots_dict.update({final_lot: lot})

            for raw_move_line, finish_move in zip(production_order.move_raw_ids.mapped('move_line_ids'),
                                                  production_order.finished_move_line_ids):
                if is_multi:
                    raw_move_line.write(
                            {'lot_produced_ids': [(4, finish_move.lot_id.id)], 'qty_done': raw_move_line.product_qty})
                else:
                    raw_move_line.write({'lot_produced_ids': [(4, lot.id)], 'qty_done': raw_move_line.product_qty})
            for move in production_order.move_finished_ids:
                quantity = production_order.product_qty
                location_dest_id = move.location_dest_id._get_putaway_strategy(
                    production_order.product_id).id or move.location_dest_id.id
                vals = {
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'production_id': production_order.id,
                    'product_uom_qty': quantity,
                    'product_uom_id': move.product_uom.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': location_dest_id,
                }
                if is_multi:
                    for line in self.split_lot_lines:
                        vals.update({'lot_id': lots_dict[line.metrc_tag].id, 'qty_done': line.product_qty})
                        self.env['stock.move.line'].create(vals)
                else:
                    vals.update({'lot_id': lot.id, 'qty_done': quantity})
                    self.env['stock.move.line'].create(vals)
            try:
                if self.env.context.get('move_line_id'):
                    move_line = self.env['stock.move.line'].sudo().browse(int(self.env.context.get('move_line_id')))
                    move_line._free_reservation(move_line.product_id, move_line.move_id.location_id, move_line.qty_done,
                                                lot_id=move_line.lot_id)
                result = production_order.button_mark_done()
                # returning the reserved quantities wizard after cancelling the MO.
                if isinstance(result, (dict)) and result.get('type', False) == 'ir.actions.act_window':
                    lot_to_unlink = production_order.finished_move_line_ids.mapped('lot_id')
                    production_order.finished_move_line_ids.unlink()
                    production_order.move_raw_ids.mapped('move_line_ids').unlink()
                    production_order.action_cancel()
                    lot_to_unlink.unlink()
                    return result
                message_body = "This lot is created from metrc package: {} using manufacturing order: <a href=# data-oe-model=mrp.production data-oe-id={}>{}</a>".format(
                    wiz.lot_id._get_metrc_name(), production_order.id, production_order.name)
                if is_multi:
                    for lot in lots_dict.values():
                        lot._update_custom_fields(wiz.lot_id)
                        lot.message_post(body=_(message_body), message_type="notification", subtype_xmlid="mail.mt_comment")
                else:
                    lot._update_custom_fields(wiz.lot_id)
                    lot.message_post(body=_(message_body), message_type="notification", subtype_xmlid="mail.mt_comment")
            except UserError as e:
                raise UserError(e)
            except ValidationError as ve:
                raise ValidationError(ve)
            except Exception:
                lot_to_unlink = production_order.finished_move_line_ids.mapped('lot_id')
                production_order.button_unreserve()
                production_order.action_cancel()
                lot_to_unlink.unlink()
                raise UserError(
                    _("Failed to process the manufacturing order {} for batch split.".format(production_order.name)))
            action = {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'context': {},
                'domain': [],
                'target': 'self'
            }
            if is_multi:
                action.update({
                    'name': 'Multi-Batch Split',
                    'res_model': 'mrp.production',
                    'res_id': production_order.id,
                })
            else:
                action.update({
                    'name': 'Newly Created Lot',
                    'res_model': 'stock.production.lot',
                    'res_id': lot.id,
                    'views': [(self.env.ref('stock.view_production_lot_form').id, 'form')],
                })
            return action

    def create_lot(self):
        StockProductLot = self.env['stock.production.lot']
        for wiz in self:
            if float_compare(wiz.product_qty, wiz.lot_qty, precision_rounding=wiz.lot_id.product_uom_id.rounding) > 0:
                raise UserError(_("Can not split more then what is available."))
            if float_compare(wiz.product_qty, 0.0, precision_rounding=wiz.lot_id.product_uom_id.rounding) < 0:
                raise UserError(_("Initial demand must be a positive number."))
            if float_compare(wiz.lot_qty, wiz.new_lot_quantity, precision_rounding=wiz.lot_id.product_uom_id.rounding) == 0:
                raise UserError(_("Available lot quantity and new lot quantity can not be same."))
            resp = StockProductLot._is_package_exist_on_metrc(wiz.new_lot_number, raise_for_error=False)
            if resp:
                raise UserError(_("Package {} already exist in metrc. Please use another package tag to produce.".format(resp['Label'])))
            else:
                if not wiz.warehouse_id.metrc_manu_type_id:
                    raise UserError(_("Operation type for split lot is not configured on warehouse {}".format(wiz.warehouse_id.name)))
                qty_to_produce = wiz.new_lot_quantity
                if (float_compare(wiz.lot_qty, wiz.product_qty, precision_rounding=wiz.uom_id.rounding) == 0) \
                   and (float_is_zero(wiz.new_lot_quantity, precision_rounding=wiz.uom_id.rounding)):
                    #  Re-tagging the whole lot
                    qty_to_produce = wiz.product_qty
                production_order = self.env['mrp.production'].create({
                    'picking_type_id': wiz.warehouse_id.metrc_manu_type_id.id,
                    'product_id': wiz.lot_id.product_id.id,
                    'location_src_id': wiz.location_id.id,
                    'location_dest_id': wiz.location_id.id,
                    'product_uom_id': wiz.lot_id.product_id.uom_id.id,
                    'product_qty': qty_to_produce,
                    'qty_producing': qty_to_produce,
                    'split_lot': True,
                    'origin': self.env.context.get('move_ref', '')
                })
                finished_move_vals = production_order._get_moves_finished_values()
                production_order.write({'move_finished_ids': [(0,0, move_vals) for move_vals in finished_move_vals]})
                production_order._generate_raw_move_split()
                production_order.move_raw_ids._action_confirm()
                production_order.move_finished_ids._action_confirm()
                production_order.move_raw_ids.with_context(force_lot_id=wiz.lot_id.id)._action_assign()
                lot = StockProductLot.search(['|', '&', ('is_legacy_lot', '=', True), ('metrc_tag', '=', wiz.new_lot_number), ('name', '=', wiz.new_lot_number), ('product_id', '=', wiz.lot_id.product_id.id)], limit=1)
                if not lot:
                    lot = StockProductLot.create({
                            'name': wiz.new_lot_number,
                            'product_id': wiz.lot_id.product_id.id,
                            'company_id': production_order.company_id.id,
                            'is_production_batch': wiz.lot_id.is_production_batch,
                            'batch_number': wiz.lot_id.batch_number,
                            'metrc_product_name': wiz.lot_id.metrc_product_name,
                        })
                production_order.lot_producing_id = lot
                for raw_move_line in production_order.move_raw_ids.mapped('move_line_ids'):
                    raw_move_line.write({'qty_done': raw_move_line.product_qty})
                for move in production_order.move_finished_ids:
                    quantity = production_order.product_qty
                    location_dest_id = move.location_dest_id._get_putaway_strategy(production_order.product_id).id or move.location_dest_id.id
                    vals = {
                      'move_id': move.id,
                      'product_id': move.product_id.id,
                      'production_id': production_order.id,
                      'product_uom_qty': quantity,
                      'product_uom_id': move.product_uom.id,
                      'qty_done': quantity,
                      'lot_id': lot.id,
                      'location_id': move.location_id.id,
                      'location_dest_id': location_dest_id,
                    }
                    self.env['stock.move.line'].create(vals)
                try:
                    if self.env.context.get('move_line_id'):
                        move_line = self.env['stock.move.line'].sudo().browse(int(self.env.context.get('move_line_id')))
                        move_line._free_reservation(move_line.product_id, move_line.move_id.location_id, move_line.qty_done, lot_id=move_line.lot_id)
                    result = production_order.button_mark_done()
                    if isinstance(result, (dict)) and result.get('type', False) == 'ir.actions.act_window':
                        lot_to_unlink = production_order.finished_move_line_ids.mapped('lot_id')
                        production_order.finished_move_line_ids.unlink()
                        production_order.move_raw_ids.mapped('move_line_ids').unlink()
                        production_order.action_cancel()
                        lot_to_unlink.unlink()
                        # returning the reserved quantities wizard after cancelling the MO.
                        return result
                    lot._update_custom_fields(wiz.lot_id)
                except UserError as e:
                    raise UserError(e)
                except ValidationError as ve:
                    raise ValidationError(ve)
                except Exception:
                    lot_to_unlink = production_order.finished_move_line_ids.mapped('lot_id')
                    production_order.button_unreserve()
                    production_order.action_cancel()
                    lot_to_unlink.unlink()
                    raise UserError(_("Failed to process the manufacturing order {} for batch split.".format(production_order.name)))
                message_body = "This lot is created from metrc package: {} using manufacturing order: <a href=# data-oe-model=mrp.production data-oe-id={}>{}</a>".format(wiz.lot_id._get_metrc_name(), production_order.id, production_order.name)
                lot.message_post(body=_(message_body), message_type="notification", subtype_xmlid="mail.mt_comment")
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Newly Created Lot',
                    'res_model': 'stock.production.lot',
                    'res_id': lot.id,
                    'views': [(self.env.ref('stock.view_production_lot_form').id, 'form')],
                    'view_type': 'form',
                    'view_mode': 'form',
                    'context': {},
                    'domain': [],
                    'target': 'self'
                }


class SplitLotWizardLines(models.TransientModel):
    _name = 'lot.split.wizard.line'
    _description = "Split Lot Wizard Lines"

    split_id = fields.Many2one(comodel_name='lot.split.wizard', string='Batch Split Reference',
                               help='Relation field to batch split model.')
    metrc_tag = fields.Char(string='Metrc Tag')
    product_qty = fields.Float(string='Package Quantity', digits='Product Unit of Measure')
