# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ResUsers(models.Model):
    _inherit = 'res.users'

    metrc_account_id = fields.Many2one('metrc.account', string='Associated Metrc Account')

    @api.constrains('metrc_account_id')
    def _check_o2o_metrc_account(self):
        for user in self.filtered(lambda ru: ru.metrc_account_id):
            existing_account = self.search_count([
                                            ('metrc_account_id', '=', user.metrc_account_id.id),
                                            ('id', '!=', user.id)
                                        ])
            if existing_account:
                raise ValidationError(_('The Metrc account \'%s\' is already associated with other user, '
                                        'you can not use this account again') % (self.metrc_account_id.name))

    def ensure_metrc_account(self):
        """
        Utility function to check Whether the user is associated with metrc account or not.
        :return: Will return the METRC account if found.
                 Throw error message if not found.
        """
        self.ensure_one()
        if not self.metrc_account_id:
            raise UserError(_("Metrc account not configured for user {}. Cannot perform this operation.".format(self.name)))
        return self.metrc_account_id
