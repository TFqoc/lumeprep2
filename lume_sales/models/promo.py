from odoo import api, fields, models
import datetime
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

def date_compare(d1, d2):
    return d1.year == d2.year and d1.month == d2.month and d1.day == d2.day

class CouponProgram(models.Model):
    _inherit='coupon.program'

    recurring = fields.Boolean()
    recurring_cycle = fields.Selection([('every','Every'),('1','Every First'),('2','Every Second'),('3','Every Third'),('4','Every Fourth'),('5','Every Fifth')], default="every")
    recurring_day = fields.Char(compute='_compute_day')

    # Override
    @api.model
    def _filter_on_validity_dates(self, order):
        res = super(CouponProgram, self)._filter_on_validity_dates(order)
        data = [{'id':p.id, 'recurring':p.recurring, 'rule weekday':p.rule_date_from.weekday(), 'order weekday':order.date_order.weekday(), 'cycle':p.recurring_cycle} for p in res]
        logger.info("DEBUG: %s" % data)
        return res.filtered(lambda program:
            (program.recurring and program.rule_date_from.weekday() == order.date_order.weekday()
             and 
             (program.recurring_cycle == 'every' or program.is_numbered_day(order.date_order,program.recurring_cycle)))
             or not program.recurring
        )

    @api.depends('rule_date_from')
    def _compute_day(self):
        for record in self:
            if record.rule_date_from:
                record.recurring_day = record.rule_date_from.strftime("%A")
            else:
                record.recurring_day = ""

    def is_numbered_day(self, date_order, number):
        try:
            number = int(number)
            # Do more stuff here
            # Since we know the weekday is right, just check each "Friday" and intcrement a counter until date is today. Then we know if we are 3rd Friday or whatver
            wday = self.rule_date_from.weekday()
            # today = datetime.date.today()
            date = datetime.date(date_order.year,date_order.month,1)
            while date.weekday() != wday:
                date += timedelta(days=1)
            counter = 1
            while not date_compare(date, date_order):
                date += timedelta(days=7)
                counter += 1
            return counter == number
        except ValueError as v:
            return False