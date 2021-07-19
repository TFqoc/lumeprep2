from odoo import models, fields, api, _
from odoo.tools import float_repr
from odoo.exceptions import ValidationError

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

# Not a member of class, so self will have to be passed in here explicitly
# Object is model name
def get_selection_label(self, object, field_name, field_value):
  return dict(self.env[object].fields_get(allfields=[field_name])[field_name]['selection'])[field_value]

class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    applied_on = fields.Selection(selection_add=[('2.5_tier','Tier')])
    tier = fields.Selection(selection=[
                            ('top','Top'),
                            ('mid','Mid'),
                            ('value','Value'),
                            ('cut','Fresh Cut')])

    # Override No Super
    @api.constrains('product_id', 'product_tmpl_id', 'categ_id')
    def _check_product_consistency(self):
        for item in self:
            if item.applied_on == "2_product_category" and not item.categ_id:
                raise ValidationError(_("Please specify the category for which this rule should be applied"))
            elif item.applied_on == "1_product" and not item.product_tmpl_id:
                raise ValidationError(_("Please specify the product for which this rule should be applied"))
            elif item.applied_on == "0_product_variant" and not item.product_id:
                raise ValidationError(_("Please specify the product variant for which this rule should be applied"))
            elif item.applied_on == "2.5_tier" and not item.tier:
                raise ValidationError(_("Please specify the tier for which this rule should be applied"))

    # Override No Super
    @api.depends('applied_on', 'categ_id', 'product_tmpl_id', 'product_id', 'compute_price', 'fixed_price', \
        'pricelist_id', 'percent_price', 'price_discount', 'price_surcharge')
    def _get_pricelist_item_name_price(self):
        for item in self:
            if item.categ_id and item.applied_on == '2_product_category':
                item.name = _("Category: %s") % (item.categ_id.display_name)
            elif item.product_tmpl_id and item.applied_on == '1_product':
                item.name = _("Product: %s") % (item.product_tmpl_id.display_name)
            elif item.product_id and item.applied_on == '0_product_variant':
                item.name = _("Variant: %s") % (item.product_id.with_context(display_default_code=False).display_name)
            elif item.tier and item.applied_on == '2.5_tier':
                item.name = _("Tier: %s") % (get_selection_label(item,'product.pricelist.item','tier',item.tier))
            else:
                item.name = _("All Products")

            if item.compute_price == 'fixed':
                decimal_places = self.env['decimal.precision'].precision_get('Product Price')
                if item.currency_id.position == 'after':
                    item.price = "%s %s" % (
                        float_repr(
                            item.fixed_price,
                            decimal_places,
                        ),
                        item.currency_id.symbol,
                    )
                else:
                    item.price = "%s %s" % (
                        item.currency_id.symbol,
                        float_repr(
                            item.fixed_price,
                            decimal_places,
                        ),
                    )
            elif item.compute_price == 'percentage':
                item.price = _("%s %% discount", item.percent_price)
            else:
                item.price = _("%(percentage)s %% discount and %(price)s surcharge", percentage=item.price_discount, price=item.price_surcharge)
