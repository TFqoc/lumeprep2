# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PointOfSale(models.Model):
    _inherit = 'pos.config'

    project_id = fields.Many2one('project.project')
    store_name = fields.Char(related="project_id.name", store=True)