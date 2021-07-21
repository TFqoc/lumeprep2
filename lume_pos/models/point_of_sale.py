# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PointOfSale(models.Model):
    _inherit = 'pos.config'

    project_id = fields.Many2one('project.project')
    store_name = fields.Char(related="project_id.name", store=True)

    def _default_pricelist(self):
        return super()._default_pricelist()
    # Override
    pricelist_id = fields.Many2one('product.pricelist', string='Default Pricelist', required=True, default=_default_pricelist,
        help="The pricelist used if no customer is selected or if the customer has no Sale Pricelist configured.",
        compute="_get_store_pricelist",store=True)

    @api.depends('project_id.store_pricelist')
    def _get_store_pricelist(self):
        for record in self:
            if record.project_id:
                record.pricelist_id = record.project_id.store_pricelist or record._default_pricelist()
            else:
                record.pricelist_id = record._default_pricelist()

    @api.onchange('project_id')
    def _change_store(self):
        if self.project_id:
            self.pricelist_id = self.project_id.store_pricelist or self._default_pricelist()
        else:
            self.pricelist_id = False
