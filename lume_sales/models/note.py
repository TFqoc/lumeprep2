from odoo import models, fields, api
import datetime
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class Note(models.Model):
    _name = 'lume.note'
    _order = 'create_date desc'

    logged_partner_id = fields.Many2one('res.partner')
    source_partner_id = fields.Many2one('res.partner')
    message = fields.Char()
    completed = fields.Boolean()

    @api.model
    def set_completed(self,id,val):
        self.env['lume.note'].browse(id).completed = val
        _logger.info('NOTE: %s', val)