from odoo import api, fields, models
import logging

logger = logging.getLogger(__name__)

class Weekday(models.Model):
    _name = 'lume.weekday'

    name = fields.Char()
    int_day = fields.Integer()

    def day_list(self):
        l = []
        for record in self:
            l.append(record.int_day)
        logger.info("DAY LIST: %s" % l)
        return l