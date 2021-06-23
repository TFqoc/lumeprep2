# -*- coding: utf-8 -*-

from odoo import fields, models


class PackageItemChange(models.TransientModel):
    _name = "package.item.change"
    _description = "Used to change the package item on metrc before receiving."

    package_label = fields.Char(string="Metrc Package Label")
    product_id = fields.Many2one('product.product')
    picking_id = fields.Many2one('stock.picking')

    def change_item_in_metrc(self):
        self.ensure_one()
        metrc_account = self.env.user.ensure_metrc_account()
        params = {'licenseNumber': self.picking_id.facility_license_id.license_number}
        data = [{
            'Label': self.package_label,
            'Item': self.product_id.name
        }]
        item_change_url = '/{}/{}/{}/{}'.format('packages', metrc_account.api_version, 'change', 'item')
        resp = metrc_account.fetch('POST', item_change_url, params=params, data=data)
        if resp:
            return {'type': 'ir.actions.act_window_close'}
