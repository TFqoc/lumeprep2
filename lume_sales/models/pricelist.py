from odoo import models, fields, api

class Pricelist(models.Model):
    _inherit = 'product.pricelist'

    price_tier_top = fields.Float(default=0,string="Top Tier")
    price_tier_mid = fields.Float(default=0,string="Mid Tier")
    price_tier_value = fields.Float(default=0,string="Value Tier")
    price_tier_cut = fields.Float(default=0,string="Fresh Cut Tier")

    def get_tiered_price(self, tier):
        self.ensure_one()
        price = 0
        if tier == 'top':
            price = self.price_tier_top
        elif tier == 'mid':
            price = self.price_tier_mid
        elif tier == 'value':
            price = self.price_tier_value
        elif tier == 'cut':
            price = self.price_tier_cut
        return price