from odoo import api, fields, models

class CouponProgram(models.Model):
    _inherit='coupon.program'

    recurring = fields.Boolean()
    recurring_cycle = fields.Selection([('every','Every'),('1','First'),('2','Second'),('3','Third'),('4','Fourth'),('5','Fifth')])
    recurring_day = fields.Char(compute='_compute_day')

    @api.model
    def _filter_on_validity_dates(self, order):
        res = super(CouponProgram, self)._filter_on_validity_dates(order)
        recurring_promos = self.filtered(lambda program:
            program.recurring and program.rule_date_from.weekday() == order.date_order.weekday()
        )
        return res + recurring_promos

    @api.depends('rule_date_from')
    def _compute_day(self):
        for record in self:
            if record.rule_date_from:
                record.recurring_day = record.rule_date_from.strftime("%A")
            else:
                record.recurring_day = ""