# -*- coding: utf-8 -*-

from odoo import api, fields, models


class IrCron(models.Model):
    _inherit = "ir.cron"

    is_metrc = fields.Boolean(string="Is Metrc Cron?")
