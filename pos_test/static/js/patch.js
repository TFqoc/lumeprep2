console.log("Patch dot js loaded. Test patching models.js");
odoo.define('pos_test.PatchTest', function(require) {
    'use strict';

    const { patch } = require("web.utils");
    var ProductScreen = require("point_of_sale.ProductScreen");
    const models = require("point_of_sale.models");
    const ProductItem = require("point_of_sale.ProductItem");
    const { useListener } = require('web.custom_hooks');


    const getMethods = (obj) => {
        let properties = new Set()
        let currentObj = obj
        do {
          Object.getOwnPropertyNames(currentObj).map(item => properties.add(item))
        } while ((currentObj = Object.getPrototypeOf(currentObj)))
        return [...properties.keys()].filter(item => typeof obj[item] === 'function')
      }

    const getLocalMethods = (obj) => Object.getOwnPropertyNames(obj).filter(item => typeof obj[item] === 'function')

    patch(ProductScreen, "log message", {
        // async _clickProduct(event) {
        //     this._super(...arguments);
        //     // do things
        //     console.log("You clicked on " + event.detail.display_name);
        //     console.log(event);
        // },
        _setValue(val){
            // do things
            console.log("Set Value: \"" + val + "\"");
            if (val == 'remove'){
                // Product was deleted (or is about to be deleted)
                // TODO Looks like the selected orderline is moved before this method is called.
                var order = this.currentOrder.get_selected_orderline();
                console.log(order);
                console.log(getLocalMethods(order));
                // console.log(order.constructor.name); // Turns out this name is already printed as part of the default log statement
            }
            this._super(...arguments);
        },
      });

    patch(models.Orderline, "log quantity",{
      set_quantity: function(quantity, keep_price){
        this.order.assert_editable();
        if(quantity === 'remove'){
            console.log("Product about to be deleted!");
        }
        else{
          console.log("Setting quantity to: " + quantity + " on " + this.product.display_name);
        }
        this._super(...arguments);
    },
    });

    patch(ProductItem,"Product Click",{
      async willStart() {
        this._super(...arguments);
        useListener('click-product', this.onAddProduct);
      },
      onAddProduct({ detail: product }){
        console.log("You just added a product!");
        console.log(product); // product should have all fields from the db model that were imported into pos.
    }
    });

});