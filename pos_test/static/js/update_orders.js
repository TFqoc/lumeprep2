console.log("UpdateOrders dot js loaded. Test looping calls");
odoo.define('pos_test.UpdateOrders', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class UpdateOrders extends PosComponent {
        constructor(){
            super(...arguments);
        }
        mounted() {
            getOrders();
        }
        async getOrders(){
            this.getter = setInterval(() => {
                this.rpc({
                    'model': 'sale.order',
                    'method': 'get_all',
                    // args: [some, args],
                }).then((result) => {
                    // TODO check returned orders against what we have.
                    console.log("I got these sale orders: " + result);
                },
                (args) => {
                    console.log("Failed to get new orders from backend.");
                });
            }, 10000);// 10 second delay
        }
    }
    // UpdateOrders.template = 'CustomButton';

    Registries.Component.add(UpdateOrders);

    return UpdateOrders;
});