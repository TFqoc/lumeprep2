# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class MetrcProductAlias(models.Model):
    _name = 'metrc.product.alias'
    _description = 'Product Metrc Alias'

    name = fields.Char(string='Name', compute='_compute_full_name')
    alias_name = fields.Char(string='Alias Name', required=True, index=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Product', index=True, required=True, ondelete='cascade')

    @api.depends('alias_name', 'product_id')
    def _compute_full_name(self):
        for record in self:
            record.name = '%s in alias of product %s' % (
                                record.alias_name,
                                record.product_id.display_name
                            )

    def upsert_alias(self, alias_name, product_id):
        if not alias_name and not product_id:
            return False
        alias_id = self.search([
                            ('alias_name', '=', alias_name),
                            ('product_id', '=', product_id.id)
                        ], limit=1)
        if not alias_id:
            alias_id = self.create({
                'alias_name': alias_name,
                'product_id': product_id.id,
            })
        return alias_id
