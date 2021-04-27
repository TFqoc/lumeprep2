# -*- coding: utf-8 -*-

from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    metrc_retail_reporting = fields.Boolean(string="Metrc Retail Reporting")
