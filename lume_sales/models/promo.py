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
    stackability = fields.Selection([('not stackable','Non Stackable'),('stackable','Stackable With')], required=True, default='not stackable')
    
    stackable_with = fields.Many2many(comodel_name='coupon.program',relation='coupon_program_stackable_rel',column1='promo1',column2='promo2')
    # stackable_with_reverse = fields.Many2many()

    @api.onchange('stackable_with')
    def onchange_stackables(self):
        logger.info('Old: %s New: %s' % (len(self._origin.stackable_with), len(self.stackable_with)))
        # Remove old links from programs we are no longer stackable with
        logger.info("Self: %s" % self.id)
        for program in (self._origin.stackable_with - self.stackable_with):
            logger.info("Removing self from program id: %s" % program.id)
            program.update({'stackable_with' : [(3,self.id,0)]})
        # Add backwards link on all new programs we are stackable with
        for program in self.stackable_with:
            if not self in program.stackable_with:
                logger.info("Adding self to program id: %s" % program.id)
                # Update works the same as write but works for pseudo records
                program.update({'stackable_with' : [(4,self.id,0)]})

    @api.model
    def _filter_programs_from_common_rules(self, order, next_order=False):
        res = super(CouponProgram, self)._filter_programs_from_common_rules(order, next_order)
        res = res._filter_on_validity_dates(order)
        return res

    # Override
    @api.model
    def _filter_on_validity_dates(self, order):
        res = super(CouponProgram, self)._filter_on_validity_dates(order)
        # data = [{'id':p.id, 'recurring':p.recurring, 'rule weekday':p.rule_date_from.weekday() if p.rule_date_from else False, 'order weekday':order.date_order.weekday(), 'cycle':p.recurring_cycle, 'test':p.is_numbered_day(order.date_order,p.recurring_cycle)} for p in res]
        # logger.info("DEBUG: %s" % data)
        res = res.filtered(lambda program:
            (program.recurring and program.rule_date_from.weekday() == order.date_order.weekday()
             and 
             (program.recurring_cycle == 'every' or program.is_numbered_day(order.date_order,program.recurring_cycle)))
             or not program.recurring
        )
        # data = [{'id':p.id, 'recurring':p.recurring, 'rule weekday':p.rule_date_from.weekday() if p.rule_date_from else False, 'order weekday':order.date_order.weekday(), 'cycle':p.recurring_cycle, 'test':p.is_numbered_day(order.date_order,p.recurring_cycle)} for p in res]
        # logger.info("DEBUG: %s" % data)
        return res

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

    # Override
    def _keep_only_most_interesting_auto_applied_global_discount_program(self):
        # Probably don't want this super call down the road
        return super(CouponProgram, self)._keep_only_most_interesting_auto_applied_global_discount_program()