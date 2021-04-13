console.log("Patch dot js loaded");
odoo.define('pos_test.CustomButton', function(require) {
    'use strict';

    const { patch } = require("web.utils");
    var ProductScreen = require("point_of_sale.ProductScreen");

    patch(ProductScreen, "log message", {
        async _clickProduct(event) {
            this._super(...arguments);
            // do things
            console.log("You clicked on a product");
            console.log(event);
        },
      });

});