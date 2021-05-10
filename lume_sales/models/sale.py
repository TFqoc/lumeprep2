from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    task = fields.Many2one(comodel_name="project.task", readonly=True)
    is_delivered = fields.Boolean(compute='_compute_delivered', store=True)

# <button class="oe_stat_button" type="object" name="open_tracebility" icon="fa-arrows-v" string="Tracebility" widget="statinfo"/>


# @api.multi
# def open_tracebility(self):
#     res = self.env['ir.actions.act_window'].for_xml_id('custom_module_name', 'wizard_action')
#     return res

# https://www.odoo.com/forum/help-1/how-to-execute-a-python-function-on-kanban-click-130496

    def open_catalog(self):
        self.ensure_one()
        return {
                'type': 'ir.actions.act_window',
                'name': 'Product Catalog',
                'view_type': 'kanban',
                'view_mode': 'kanban',
                'res_model': 'product.product',
                'view_id': self.env.ref('lume_sales.product_product_kanban_catalog').id,
                'target': 'new',
                'res_id': self.id,
                'context': {'lpc_sale_order_id': self.id},
                'domain': [],
                'search_view_id': ('category_grouping_search', 'Catagory Grouping'),
            }
    def open_catalogV2(self):
        self.ensure_one()
        # action = self.env.ref('lume_sales.lume_product_catalog')
        # action.update({
        #     'view_id': self.env.ref('lume_sales.product_product_kanban_catalog').id,
        #     'target': 'current',
        #     'res_id': self.id,
        #     'context': {'lpc_sale_order_id': self.id},
        #     'domain': [],
        # })
        # return action
        return {
                'type': 'ir.actions.act_window',
                'name': 'Product Catalog',
                'view_type': 'kanban',
                'view_mode': 'kanban',
                'res_model': 'product.product',
                'view_id': self.env.ref('lume_sales.product_product_kanban_catalog').id,
                'target': 'current',
                'res_id': self.id,
                'context': {'lpc_sale_order_id': self.id},
                'domain': [],
                # 'search_view_id': (id, name),
            }

    @api.depends('picking_ids.move_ids_without_package.state')
    def _compute_delivered(self):
        for record in self:
            res = len(record.picking_ids) > 0
            for delivery in record.env['stock.picking'].search([('sale_id','=',record.id)]):
                for line in delivery.move_ids_without_package:
                    if delivery.state != 'done':
                        res = False
                        break
            record.is_delivered = res
            if record.is_delivered:
                record.on_fulfillment()

    # Onchange doesn't seem to trigger for calculated fields
    # @api.onchange('is_delivered')
    def on_fulfillment(self):
        if self.task.stage_id.name != 'Order Ready':
            self.task.next_stage() 

    @api.onchange('partner_id')
    def check_order_lines(self):
        for order in self.order_line:
            if order.product_id.is_medical is not self.partner_id.is_medical:
                warning = {
                'warning': {'title': "Warning", 'message': "You can't set a " + ("medical" if self.partner_id.is_medical else "recreational") + " customer here because there is at least one " + ("medical" if order.product_id.is_medical else "recreational") + " product in the order!",}
                }
                self.partner_id = False
                return warning

    def action_confirm(self):
        if not self.order_line:
            raise ValidationError("You must have at least one sale order line in order to confirm this Sale Order!")
        ret = super(SaleOrder, self).action_confirm()
        if ret and self.task:
            self.task.next_stage()
        return ret
        # POS will now pick up the SO because it is in 'sale' state

class SaleLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def check_order_line(self):
        if self.product_id and self.order_id.partner_id:
            if self.product_id.is_medical is not self.order_id.partner_id.is_medical:
                warning = {
                    'warning': {'title': "Warning", 'message': "You can't add a " + ("medical" if self.product_id.is_medical else "recreational") + " product to a " + ("medical" if self.order_id.partner_id.is_medical else "recreational") + " customer's order!",}
                    }
                self.product_id = False
                self.name = False
                self.price_unit = False
                return warning