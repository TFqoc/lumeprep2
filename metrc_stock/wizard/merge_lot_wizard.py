# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class MergeLotWizard(models.TransientModel):
    _name = 'lot.merge.wizard'
    _description = '''
    Utility to consolidate lots from a picking based on their origin(MO).
    '''

    picking_id = fields.Many2one(comodel_name='stock.picking')
    warehouse_id = fields.Many2one(comodel_name='stock.warehouse')
    location_id = fields.Many2one(related='picking_id.location_id')
    location_dest_id = fields.Many2one(related='picking_id.location_dest_id')
    source_lot_ids = fields.Many2many(comodel_name='stock.production.lot')
    target_lot_ids = fields.One2many(comodel_name='lot.merge.wizard.line', inverse_name='merge_wiz_id')
    message_body = fields.Html()

    def confirm_merge(self):
        if any([(not tg.lot_name or tg.lot_name == '') for tg in self.target_lot_ids]):
            raise ValidationError(_("Please specify all 'New Metrc Tags' line with valid metrc tags."))
        lot_details = "<table class='table table-bordered'><tr><th>Product</th><th># of lots</th></tr>"
        for product in self.source_lot_ids.mapped('product_id'):
            lot_details += "<tr><td>{}</td><td>{}</td></tr>".format(product.display_name, len(self.source_lot_ids.filtered(lambda l: l.product_id == product)))
        lot_details += "</tr></table>"
        self.message_body = "<p><h3>You are about to consolidate following metrc lots! Are you sure?</h3></p><br/>{}".format(lot_details)
        return {
            'name': _('Consolidation Confirmation'),
            'type': 'ir.actions.act_window',
            'res_model': 'lot.merge.wizard',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(self.env.ref('metrc_stock.merge_lot_confirmation').id, 'form')],
            'context': {},
            'domain': {},
            'target': 'new'
        }

    def modify_merge(self):
        action_data = self.env.ref('metrc_stock.action_open_merge_lot_wizard').read()[0]
        action_data['res_id'] = self.id
        return action_data

    def consolidate_lots(self):
        picking_lots = self.picking_id.move_line_ids.mapped('lot_id')
        if self.picking_id.state != 'done':
            self.picking_id.do_unreserve()
        StockProductLot = self.env['stock.production.lot']
        lots_produced = StockProductLot
        for target_line in self.target_lot_ids:
            resp = StockProductLot._is_package_exist_on_metrc(target_line.lot_name, raise_for_error=False)
            if resp:
                raise UserError(_("Package {} already exist in metrc. Please use another package tag to produce.".format(resp['Label'])))
            else:
                if not self.warehouse_id.metrc_manu_type_id:
                    raise UserError(_("Operation type for split lot is not configured on warehouse {}".format(self.warehouse_id.name)))
                qty_to_produce = target_line.quantity
                location = self.location_id.id
                if self.picking_id.picking_type_code == 'incoming':
                    location = self.location_dest_id.id
                production_order = self.env['mrp.production'].create({
                    'picking_type_id': self.warehouse_id.metrc_manu_type_id.id,
                    'product_id': target_line.product_id.id,
                    'location_src_id': location,
                    'location_dest_id': location,
                    'product_uom_id': target_line.uom_id.id,
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
                for raw_lot in target_line.lot_ids:
                    production_order.move_raw_ids.with_context(force_lot_id=raw_lot.id)._action_assign()
                lot = StockProductLot.search(['|', '&', ('is_legacy_lot', '=', True), ('metrc_tag', '=', target_line.lot_name), ('name', '=', target_line.lot_name), ('product_id', '=', target_line.product_id.id)], limit=1)
                if not lot:
                    lot = StockProductLot.create({
                            'name': target_line.lot_name,
                            'product_id': target_line.product_id.id,
                            'company_id': production_order.company_id.id
                        })
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
                    # production_order.move_raw_ids.mapped('move_line_ids').write({'lot_produced_ids': [(4, lot.id)]})
                    lots_produced |= lot
                    lot._update_custom_fields(production_order.move_raw_ids.mapped('move_line_ids')[0].lot_id)
                except UserError as e:
                    raise UserError(e)
                except ValidationError as ve:
                    raise ValidationError(ve)
                except Exception:
                    lot_to_unlink = production_order.finished_move_line_ids.mapped('lot_id')
                    production_order.button_unreserve()
                    production_order.action_cancel()
                    lot_to_unlink.unlink()
                    raise UserError(_("Failed to process the manufacturing order {} for lot consolidation.".format(production_order.name)))
                message_body = "This lot is created using manufacturing order: <a href=# data-oe-model=mrp.production data-oe-id={}>{}</a>".format(production_order.id, production_order.name)
                lot.message_post(body=_(message_body), message_type="notification", subtype_xmlid="mail.mt_comment")
        if lots_produced:
            other_lots = picking_lots - self.target_lot_ids.mapped('lot_ids')
            for new_lot in (lots_produced + other_lots):
                reserved_move = self.picking_id.move_lines.filtered(lambda ml: ml.product_id == new_lot.product_id)
                if reserved_move:
                    reserved_move._update_reserved_quantity(reserved_move.product_uom_qty, new_lot.product_qty, reserved_move.location_id, lot_id=new_lot)
                    reserved_move._recompute_state()
            return {
                'type': 'ir.actions.act_window',
                'name': _('Consolidated Lots'),
                'res_model': 'stock.production.lot',
                'view_mode': 'tree',
                'context': {},
                'domain': [('id', 'in', lots_produced.ids)],
                'target': 'self'
            }


class MergeLotWizardLine(models.TransientModel):
    _name = 'lot.merge.wizard.line'
    _description = '''
    Lines containing lots to merge.
    '''

    lot_name = fields.Char(string='New Lot Number')
    merge_wiz_id = fields.Many2one(comodel_name='lot.merge.wizard')
    quantity = fields.Float(string='Qty to produce', digits='Product Unit of Measure')
    qty_available = fields.Float(string='Total Qty Available', digits='Product Unit of Measure')
    product_id = fields.Many2one(comodel_name='product.product')
    uom_id = fields.Many2one(related="product_id.uom_id")
    lot_ids = fields.Many2many(comodel_name='stock.production.lot')
