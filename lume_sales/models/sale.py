from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

ORDER_HISTORY_DOMAIN = [('state', 'not in', ('draft', 'sent'))]

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    task = fields.Many2one(comodel_name="project.task", readonly=True)
    is_delivered = fields.Boolean(compute='_compute_delivered', store=True)
    # For product validation
    # None state means they haven't selected any medical or adult products yet
    order_type = fields.Selection(selection=[('medical','Medical'),('adult','Adult'),('caregiver','Caregiver'),('none','None'),('merch','Merchandise')],compute="_compute_order_type")
    ordered_qty = fields.Float(compute='_compute_ordered_qty')
    fulfillment_type = fields.Selection(selection=[('store','In Store'),('delivery','Delivery'),('online','Website'),('curb','Curbside')], default='store')

    # Fields for the Order History Screen
    pos_terminal_id = fields.Many2one('pos.config')
    session_id = fields.Many2one('pos.session')
    fulfillment_partner_id = fields.Many2one('res.partner')
    cashier_partner_id = fields.Many2one('res.partner')
    payment_method = fields.Char()

    partner_sale_order_count = fields.Integer(related="partner_id.sale_order_count")
    partner_image = fields.Image(related='partner_id.image_1920',max_width=1920, max_height=1920,store=True)

    # Fields for Timer and colors
    timer_start = fields.Datetime(default=lambda self: fields.datetime.now())
    threshold1 = fields.Integer(related="task.project_id.so_threshold1")
    threshold2 = fields.Integer(related="task.project_id.so_threshold2")
    threshold3 = fields.Integer(related="task.project_id.so_threshold3")

    # Override
    def action_cancel(self):
        cancel_warning = self._show_cancel_wizard()
        if cancel_warning:
            return super(SaleOrder, self).action_cancel()
        else:
            if self.task:
                self.task.write({'active':False})
            return super(SaleOrder, self).action_cancel()

    def open_notes(self):
        notes = []
        for note in self.env['lume.note'].search([('source_partner_id','=',self.partner_id.id)]):
            notes.append((4,note.id,0))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Notes',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': 'note.wizard',
            'target': 'new',
            # 'res_id': self.id,
            'context': {'default_partner_id': self.partner_id.id,'default_note_ids':notes},
        }

    def open_catalog(self):
        self.ensure_one()
        domain = ["&","&",("type","!=","service"),("sale_ok","=",True),"|",("is_product_variant","=",False),"&",("is_product_variant","=",True),("quantity_at_warehouses","ilike",self.warehouse_id.name)]
        domain += [('type','!=','service'),('sale_ok','=',True)]
        if not self.partner_id.can_purchase_medical:
            domain.append(('thc_type','!=','medical'))
        if not self.partner_id.is_over_21:
            domain.append(('thc_type','=','adult'))
        # Grab the first sale order line that isn't a merch product
        # show_medical = self.order_type
        return {
                'type': 'ir.actions.act_window',
                'name': 'Product Catalog',
                'view_type': 'kanban',
                'view_mode': 'kanban',
                'res_model': 'product.product',
                'view_id': self.env.ref('lume_sales.product_product_kanban_catalog').id,
                'target': 'current',
                'res_id': self.id,
                'context': {'lpc_sale_order_id': self.id, 'type': self.order_type, 'warehouse_id':self.warehouse_id.id,'store_id':self.task.project_id.id},
                'domain': domain,
                # 'search_view_id': (id, name),
            }

    def open_order_history(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Order History',
            'view_type': 'kanban',
            'view_mode': 'kanban',
            'res_model': 'sale.order',
            'view_id': self.env.ref('lume_sales.view_sale_order_history_kanban').id,
            'target': 'current',
            'res_id': self.id,
            'context': {'search_default_partner_id': self.partner_id.id, 'default_partner_id': self.partner_id.id},
            'domain': ORDER_HISTORY_DOMAIN,
        }

    @api.depends('picking_ids.move_ids_without_package.state')
    def _compute_delivered(self):
        for record in self:
            res = len(record.picking_ids) > 0
            for delivery in record.env['stock.picking'].search([('sale_id','=',record.id)]):
                for line in delivery.move_ids_without_package:
                    if line.state != 'done':
                        res = False
                        break
            record.is_delivered = res
            if record.is_delivered:
                record.on_fulfillment()

    @api.depends('order_line')
    def _compute_ordered_qty(self):
        for record in self:
            qty = 0
            for line in record.order_line:
                qty += line.product_uom_qty
            record.ordered_qty = qty

    @api.depends('order_line')
    def _compute_order_type(self):
        for record in self:
            record.order_type = 'none'
            if self.order_line:
                for line in self.order_line:
                    type_order = line.product_id.thc_type
                    if type_order in ['medical','adult']:
                        record.order_type = type_order
                        break
    
    @api.onchange('fulfillment_type')
    def change_fulfillment(self):
        if self.task:
            self.task.fulfillment_type = self.fulfillment_type

    # Onchange doesn't seem to trigger for calculated fields
    # @api.onchange('is_delivered')
    def on_fulfillment(self):
        if self.task.stage_id.name != 'Order Ready':
            self.task.change_stage(3)

    # @api.onchange('partner_id')
    # def check_order_lines(self):
    #     for order in self.order_line:
    #         if order.product_id.is_medical is not self.partner_id.is_medical:
    #             warning = {
    #             'warning': {'title': "Warning", 'message': "You can't set a " + ("medical" if self.partner_id.is_medical else "recreational") + " customer here because there is at least one " + ("medical" if order.product_id.is_medical else "recreational") + " product in the order!",}
    #             }
    #             self.partner_id = False
    #             return warning

    @api.model
    def get_cart_totals(self, id):
        record = self.browse(id)
        # FIXME Right now caregiver type (curently unused) will always be hidden
        hide_type = '' if record.order_type == 'none' else 'medical' if record.order_type == 'adult' else 'adult'
        return (record.amount_total, record.ordered_qty, hide_type)

    def action_confirm(self):
        if not self.order_line:
            raise ValidationError("You must have at least one sale order line in order to confirm this Sale Order!")
        for line in self.order_line:
            if self.order_type != line.product_id.thc_type and line.product_id.thc_type not in [False, 'merch']:
                raise ValidationError("You can't confirm a cart with both Medical and Recreational products!")
        ret = super(SaleOrder, self).action_confirm()
        if ret and self.task:
            self.task.change_stage(2)
        # return ret
        return {
            "type":"ir.actions.act_window",
            "res_model":"project.task",
            "views":[[False, "kanban"]],
            "name": 'Tasks',
            "target": 'main',
            "res_id": self.task.project_id.id,
            "domain": [('project_id', '=', self.task.project_id.id)],
            "context": {'default_project_id': self.task.project_id.id},
        }
        # POS will now pick up the SO because it is in 'sale' state
 
    ######################
    # Promotion methods
    ######################
    
    # # Override NO SUPER
    # def _get_applicable_programs(self):
    #     """
    #     This method is used to return the valid applicable programs on given order.
    #     """
    #     self.ensure_one()
    #     programs = self.env['coupon.program'].with_context(
    #         no_outdated_coupons=True,
    #     ).search([
    #         ('company_id', 'in', [self.company_id.id, False]),
    #         '|', ('rule_date_from', '=', False), ('rule_date_from', '<=', self.date_order),
    #         '|', ('rule_date_to', '=', False), ('rule_date_to', '>=', self.date_order),
    #     ], order="id")._filter_programs_from_common_rules(self)
    #     # no impact code...
    #     # should be programs = programs.filtered if we really want to filter...
    #     # if self.promo_code:
    #     #     programs._filter_promo_programs_with_code(self)
    #     return programs

    # # Override NO SUPER
    # def _get_applicable_no_code_promo_program(self):
    #     self.ensure_one()
    #     programs = self.env['coupon.program'].with_context(
    #         no_outdated_coupons=True,
    #         applicable_coupon=True,
    #     ).search([
    #         ('promo_code_usage', '=', 'no_code_needed'),
    #         '|', ('rule_date_from', '=', False), ('rule_date_from', '<=', self.date_order),
    #         '|', ('rule_date_to', '=', False), ('rule_date_to', '>=', self.date_order),
    #         '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False),
    #     ])._filter_programs_from_common_rules(self)
    #     return programs

    # Override
    def _create_new_no_code_promo_reward_lines(self):
        '''Apply new programs that are applicable'''
        self.ensure_one()
        order = self
        programs = order._get_applicable_no_code_promo_program()
        programs = programs._keep_only_most_interesting_auto_applied_global_discount_program()
        for program in programs:
            # VFE REF in master _get_applicable_no_code_programs already filters programs
            # why do we need to reapply this bunch of checks in _check_promo_code ????
            # We should only apply a little part of the checks in _check_promo_code...
            error_status = program._check_promo_code(order, False)
            if not error_status.get('error'):
                if program.promo_applicability == 'on_next_order':
                    order._create_reward_coupon(program)
                elif program.discount_line_product_id.id not in self.order_line.mapped('product_id').ids:
                    self.write({'order_line': [(0, False, value) for value in self._get_reward_line_values(program)]})
                order.no_code_promo_program_ids |= program
            else:
                logger.info("Program Error Message: %s" % error_status.get("error"))

    # Override
    def _is_global_discount_already_applied(self):
        # Saying that a global discount is never applied allows us to stack as many as we want.
        # Stacking rules are applied elsewhere
        return False

class SaleLine(models.Model):
    _inherit = 'sale.order.line'

    order_type = fields.Selection(related="order_id.order_type")

    @api.onchange('product_uom_qty')
    def ensure_valid_quantity(self):
        if self.product_uom_qty <= 0:
            self.product_uom_qty = self._origin.product_uom_qty
            return {
                'warning': {'title': "Warning", 'message': "You can't set a quantity to a negative number!",}
                }
        

    # @api.onchange('product_id')
    # def check_order_line(self):
    #     if self.product_id and self.order_id.partner_id:
    #         if self.product_id.is_medical is not self.order_id.partner_id.is_medical:
    #             warning = {
    #                 'warning': {'title': "Warning", 'message': "You can't add a " + ("medical" if self.product_id.is_medical else "recreational") + " product to a " + ("medical" if self.order_id.partner_id.is_medical else "recreational") + " customer's order!",}
    #                 }
    #             self.product_id = False
    #             self.name = False
    #             self.price_unit = False
    #             return warning

