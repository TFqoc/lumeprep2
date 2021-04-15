console.log("ProductItem dot js loaded. Test catching event");
odoo.define('pos_test.ProductItem', function(require) {
    'use strict';

    const ProductItem = require("point_of_sale.ProductItem");
    const { useListener } = require('web.custom_hooks');

    class ProductClick extends ProductItem {
        constructor(){
            super(...arguments);
            useListener('click-product', this.onAddProduct);
        }
        onAddProduct({ detail: product }){
            console.log("You just added a product!");
            console.log(product);
        }
    }
    // ProductClick.template = 'CustomButton';

    Registries.Component.add(ProductClick);

    return ProductClick;
});