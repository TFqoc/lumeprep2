from odoo import api, fields, models

class Return(models.Model):
    _name = 'lume.return'

    refund_type = fields.Selection([
        ('full','Full'),
        ('partial','Partial')
        ])
    issue_type = fields.Selection([
        ('cash','Cash'),
        ('gift_card','Gift Card')
    ])
    return_lines = fields.One2many('lume.return.line',inverse_name='return_id')
    refund_total = fields.Float(compute='_compute_refund_total')
    sale_id = fields.Many2one('sale.order', required=True)
    currency_id = fields.Many2one('res.currency', required=True)

    def _compute_refund_total(self):
        for record in self:
            record.refund_total = sum(record.return_lines.total_price)

class ReturnLine(models.Model):
    _name = 'lume.return.line'

    return_id = fields.Many2one('lume.return')
    product_id = fields.Many2one('product.product')
    lot_id = fields.Many2one('stock.production.lot')
    price = fields.Float()
    total_price = fields.Float(compute='_compute_total')
    original_qty = fields.Float(default=0)
    return_qty = fields.Float(default=0)
    reason_code = fields.Selection([
        ('defect','Defective'),
        ('taste','Taste'),
        ('quality','Quality'),
        ('contam','Contamination'),
        ('seeds','Seeds'),
        ('weight','Weight'),
        ('dry','Dry'),
        ('overcharge','Overcharge'),
        ('exchange','Exchange')
    ], required=True)

    def _compute_total(self):
        for record in self:
            record.total_price = record.price * record.return_qty

    @api.onchange('return_qty')
    def onchange_return_qty(self):
        # You can't return more than you originally bought
        if self.return_qty > self.original_qty:
            self.return_qty = self.original_qty