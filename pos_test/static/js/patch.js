console.log("Patch dot js loaded");
odoo.define('pos_test.PatchTest', function(require) {
    'use strict';

    const { patch } = require("web.utils");
    var ProductScreen = require("point_of_sale.ProductScreen");
    var NumberBuffer = require("point_of_sale.NumberBuffer");

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
        async _clickProduct(event) {
            this._super(...arguments);
            // do things
            console.log("You clicked on " + event.detail.display_name);
            console.log(event);
        },
        _setValue(val){
            this._super(...arguments);
            // do things
            console.log("Set Value: \"" + val + "\"");
            if (val == 'remove'){
                // Product was deleted (or is about to be deleted)
                var order = this.currentOrder.get_selected_orderline();
                console.log(order);
                console.log(getLocalMethods(order));
                console.log(order.constructor.name);
            }
        },
      });

    //   patch(NumberBuffer, "log delete", {
    //     _updateBuffer(input) {
    //         this._super(...arguments);
    //         // do things
    //         if (input === "Backspace"){
    //             console.log("Backspace was clicked");
    //         }
    //     },
    //   });

});