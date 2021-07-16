# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MetrcTransfer(models.Model):
    _inherit = 'metrc.transfer'

    tier = fields.Selection(selection=[
                            ('top','Top'),
                            ('mid','Mid'),
                            ('value','Value'),
                            ('cut','Fresh Cut')])