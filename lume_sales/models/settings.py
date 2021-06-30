from odoo import models, fields, api

class Settings(models.Model):
    _inherit = 'res.config.settings'

    batch_threshold = fields.Integer(string="Batch Threshold")