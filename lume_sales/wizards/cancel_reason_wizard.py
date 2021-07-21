from odoo import models, fields

class CancelWizard(models.TransientModel):
    _name = 'sale.order.cancel.reason'
    _description = 'Cancel Reason'

    order_id = fields.Many2one('sale.order')
    reason = fields.Selection([('no_stock','Product not in stock/unavailable'),('no_funds','Insufficient Funds'),('bad_price','Pricing Dissatisfaction'),('merge','Merged Order')],default='no_stock')

    def action_ok(self):
        """ close wizard"""
        self.order_id.cancel_reason = self.reason
        self.order_id.action_cancel()
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}