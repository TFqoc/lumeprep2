# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    def action_scan_license(self):
        self.name = "Silly Corp"
        return 0