# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import sys
import json
import logging
import requests
import traceback

from requests.auth import HTTPBasicAuth
from datetime import datetime

from odoo import models, fields, api, _
from odoo.tools import float_compare, float_round
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class MetrcAccount(models.Model):

    _inherit = 'metrc.account'

    import_customer_types = fields.Boolean(string='Import Customer Types', help='Import Customer Types from metrc.')

    def do_import_customer_types(self):
        self.ensure_one()
        self.env['metrc.customer.types']._import_metrc_customer_types(self)
