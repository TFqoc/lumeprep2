console.log("Patch dot js loaded");
odoo.define('pos_test.PatchTest', function(require) {
    'use strict';

    const { patch } = require("web.utils");
    var ProductScreen = require("point_of_sale.ProductScreen");
    var NumberBuffer = require("point_of_sale.NumberBuffer");

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
            if (val == 'remove'){
                // Product was deleted
                // I don't know what product was removed, just that one was, or will be down the line
                console.log("Set Value: " + val);
            }
        },
        async _updateSelectedOrderline(event) {
            if(this.state.numpadMode === 'quantity' && this.env.pos.disallowLineQuantityChange()) {
                let order = this.env.pos.get_order();
                let selectedLine = order.get_selected_orderline();
                let lastId = order.orderlines.last().cid;
                let currentQuantity = this.env.pos.get_order().get_selected_orderline().get_quantity();

                if(selectedLine.noDecrease) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Invalid action'),
                        body: this.env._t('You are not allowed to change this quantity'),
                    });
                    return;
                }
                if(lastId != selectedLine.cid)
                    this._showDecreaseQuantityPopup();
                else if(currentQuantity < event.detail.buffer)
                    this._setValue(event.detail.buffer);
                else if(event.detail.buffer < currentQuantity)
                    this._showDecreaseQuantityPopup();
            } else {
                let { buffer } = event.detail;
                let val = buffer === null ? 'remove' : buffer;
                if (val == 'remove'){
                    console.log(this.env.pos.get_order().get_selected_orderline());
                }
                this._setValue(val);
            }
        }
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