from odoo import api, fields, models
import datetime
from datetime import timedelta
import math
import logging

logger = logging.getLogger(__name__)

def date_compare(d1, d2):
    return d1.year == d2.year and d1.month == d2.month and d1.day == d2.day
# Gets the integer value from a string like NewId_###
def id_from_string(id):
    if type(id) == int:
        return id
    id = str(id)
    index = id.find('_')
    if index == -1:
        return index
    id = int(id[index+1:])
    return id

class CouponProgram(models.Model):
    _inherit='coupon.program'

    recurring = fields.Boolean()
    recurring_cycle = fields.Selection([('every','Every'),('1','Every First'),('2','Every Second'),('3','Every Third'),('4','Every Fourth'),('5','Every Fifth')], default="every")
    # recurring_day = fields.Char(compute='_compute_day')
    recurring_days = fields.Many2many('lume.weekday')
    stackability = fields.Selection([('not stackable','Non Stackable'),('stackable','Stackable With')], required=True, default='not stackable')
    
    stackable_with = fields.Many2many(comodel_name='coupon.program',relation='coupon_program_stackable_rel',column1='promo1',column2='promo2')
    # stackable_with_reverse = fields.Many2many()
    store_ids = fields.Many2many(comodel_name='project.project')

    @api.onchange('stackable_with')
    def onchange_stackables(self):
        # Causes issues when creating a new promotion

        # logger.info('Old: %s New: %s' % (len(self._origin.stackable_with), len(self.stackable_with)))
        # Remove old links from programs we are no longer stackable with
        # logger.info("Self: %s" % self.id) # Prints as "NewId_4"
        try:
            selfid = id_from_string(self.id)
        except ValueError as v:
            # If we get a value error then this is being called at a point when there is
            # undefined behavior, such as during a record's creation
            # So we should just do nothing in this case
            logger.info("Value Error in promo: %s" % v)
            return
        for program in (self._origin.stackable_with - self.stackable_with):
            # logger.info("Removing self from program id: %s" % program.id)
            # program.update({'stackable_with' : [(3,self.id,0)]})
            self.env['coupon.program'].browse(id_from_string(program.id)).stackable_with = [(3,selfid,0)]
        # Add backwards link on all new programs we are stackable with
        for program in self.stackable_with:
            if not self in program.stackable_with:
                # logger.info("Adding self to program id: %s" % program.id)
                # Update works the same as write but works for pseudo records
                # program.update({'stackable_with' : [(4,self.id,0)]})
                self.env['coupon.program'].browse(id_from_string(program.id)).stackable_with = [(4,selfid,0)]

    # Override
    @api.model
    def _filter_programs_from_common_rules(self, order, next_order=False):
        res = super(CouponProgram, self)._filter_programs_from_common_rules(order, next_order)
        res = res._filter_on_store(order)
        res = res._filter_on_validity_dates(order)
        return res

    @api.model
    def _filter_on_store(self, order):
        return self.filtered(lambda program: (order.task and order.task.project_id in program.store_ids) or not program.store_ids)

    # Override
    @api.model
    def _filter_on_validity_dates(self, order):
        res = super(CouponProgram, self)._filter_on_validity_dates(order)
        data = [{'id':p.id, 'recurring':p.recurring, 'rule weekday':p.recurring_days.day_list() if p.rule_date_from else False, 'order weekday':order.date_order.weekday(), 'cycle':p.recurring_cycle, 'test':p.is_numbered_day(order.date_order,p.recurring_cycle)} for p in res]
        logger.info("DEBUG: %s" % data)
        res = res.filtered(lambda program:
            (program.recurring and order.date_order.weekday() in program.recurring_days.day_list()
            # (program.recurring and program.rule_date_from.weekday() == order.date_order.weekday()
             and 
             (program.recurring_cycle == 'every' or program.is_numbered_day(order.date_order,program.recurring_cycle)))
             or not program.recurring
        )
        data = [{'id':p.id, 'recurring':p.recurring, 'rule weekday':p.recurring_days.day_list() if p.rule_date_from else False, 'order weekday':order.date_order.weekday(), 'cycle':p.recurring_cycle, 'test':p.is_numbered_day(order.date_order,p.recurring_cycle)} for p in res]
        logger.info("DEBUG: %s" % data)
        return res

    # @api.depends('rule_date_from')
    # def _compute_day(self):
    #     for record in self:
    #         if record.rule_date_from:
    #             record.recurring_day = record.rule_date_from.strftime("%A")
    #         else:
    #             record.recurring_day = ""

    def is_numbered_day(self, date_order, number):
        try:
            number = int(number)
            # Do more stuff here
            # Since we know the weekday is right, just check each "weekday" and intcrement a counter until date is today. Then we know if we are 3rd Friday or whatver
            wday = date_order.weekday()
            # today = datetime.date.today()
            date = datetime.date(date_order.year,date_order.month,1)
            # This loop should get the first occurance of weekday in the month
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
        # TODO This loop creates redundant results. Could make this more efficient in the future
        logger.info("TYPE OF RECORDSET: %s" % type(self))
        possibilities = []
        for p in self:
            d = p
            if p.stackability == 'stackable':
                for program in self:
                    logger.info("D Recordset: %s, D Stackables: %s " % (d,d.stackable_with))
                    if program not in d and program.stackability == 'stackable':
                        stackable = True
                        for r in d:
                            if program not in r.stackable_with:
                                stackable = False
                                break
                        if stackable:
                            d |= program
            possibilities.append(d)
        logger.info("Total possibilities: %s" % possibilities)
        # Pick best combo here
        combos = []
        for index, promos in enumerate(possibilities):
            discount_total = math.prod([1-(promo.discount_percentage/100) for promo in promos])
            combos.append((index, discount_total))
        combos.sort(key=lambda p: p[1],reverse=False)
        logger.info("Combos in order: %s" % combos)
        # Combo[0] is the best one
        index = combos[0][0]
        return possibilities[index]
        # return_set = False
        # for program in possibilities[index]:
        #     if not return_set:
        #         return_set = program
        #     else:
        #         return_set |= program
        # # Add up single recordsets with |= to make a full recordset to return
        # return return_set