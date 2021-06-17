from odoo import api, fields, models

class Weekday(models.Model):
    _name = 'lume.weekday'

    name = fields.Char()
    int_day = fields.Integer()

    def day_list(self):
        l = []
        for record in self:
            l.append(record.int_day)
        return l