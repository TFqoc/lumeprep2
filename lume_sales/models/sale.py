from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    task = fields.Many2one(comodel_name="project.task", readonly=True)
    is_delivered = fields.Boolean(compute='_compute_delivered', store=True)

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
        ret = super(SaleOrder, self).action_confirm()
        if ret and self.task:
            self.task.next_stage()
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