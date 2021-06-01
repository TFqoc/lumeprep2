from odoo import models, fields, api
from odoo.exceptions import ValidationError

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

    # def open_catalog(self):
    #     self.ensure_one()
    #     return {
    #             'type': 'ir.actions.act_window',
    #             'name': 'Product Catalog',
    #             'view_type': 'kanban',
    #             'view_mode': 'kanban',
    #             'res_model': 'product.product',
    #             'view_id': self.env.ref('lume_sales.product_product_kanban_catalog').id,
    #             'target': 'new',
    #             'res_id': self.id,
    #             'context': {'lpc_sale_order_id': self.id},
    #             'domain': [],
    #             'search_view_id': ('category_grouping_search', 'Catagory Grouping'),
    #         }
    def open_catalogV2(self):
        self.ensure_one()
        domain = [('type','!=','service'),('sale_ok','=',True)]
        if not self.partner_id.can_purchase_medical:
            domain.append(('thc_type','!=','medical'))
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
                'context': {'lpc_sale_order_id': self.id, 'type': self.order_type, 'warehouse_id':self.warehouse_id.id},
                'domain': domain,
                # 'search_view_id': (id, name),
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
        ret = super(SaleOrder, self).action_confirm()
        if ret and self.task:
            self.task.change_stage(2)
        return ret
        # POS will now pick up the SO because it is in 'sale' state

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

