from odoo import models, fields, api

class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    batch_threshold = fields.Integer(string="Batch Threshold")