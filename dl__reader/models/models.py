# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class dl__reader(models.Model):
#     _name = 'dl__reader.dl__reader'
#     _description = 'dl__reader.dl__reader'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
