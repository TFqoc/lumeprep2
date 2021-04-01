from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    task = fields.Many2one(comodel_name="project.task", readonly=True)

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
        ret = super(SaleOrder, self).action_confirm()
        if ret and self.task:
            self.task.next_stage()

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