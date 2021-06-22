# -*- coding: utf-8 -*-

import logging
from odoo import fields, models
_logger = logging.getLogger(__name__)


class MetrcTransferTypes(models.Model):
    _name = 'metrc.customer.types'
    _description = 'Metrc Transfer Type'
    name = fields.Char(string='Name', index=True)

    def _import_metrc_customer_types(self, raise_for_error=True):
        metrc_account = self.env.user.ensure_metrc_account()
        existing_ctypes = self.search([])
        existing_ctypes_names = existing_ctypes.mapped('name')
        try:
            url = '{}/{}/{}'.format('/sales', metrc_account.api_version, 'customertypes')
            resp = metrc_account.fetch('GET', url)
            for ctype in resp:
                if ctype not in existing_ctypes_names:
                    self.create({'name': ctype})
        except Exception as ex:
            raise ex
