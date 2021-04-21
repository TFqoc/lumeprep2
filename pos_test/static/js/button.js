console.log("Button dot js is loaded! Current test: rpc");
odoo.define('pos_test.CustomButton', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    const getMethods = (obj) => {
        let properties = new Set()
        let currentObj = obj
        do {
          Object.getOwnPropertyNames(currentObj).map(item => properties.add(item))
        } while ((currentObj = Object.getPrototypeOf(currentObj)))
        return [...properties.keys()].filter(item => typeof obj[item] === 'function')
      }

    class CustomButton extends PosComponent {
        constructor() {
            super(...arguments);
        }
        async onClick() {
            if (this.env.pos.proxy.printer){
                this.env.pos.proxy.printer.open_cashbox();
            }
            console.log("You clicked me!");
            // print env data
            console.log("ENV: ");
            console.log(this.env);
            console.log("ENV.POS: ");
            console.log(this.env.pos);
            console.log("ENV.POS-Methods:");
            console.log(getMethods(this.env.pos));
            console.log("Json data from current order: " + this.env.pos.export_unpaid_orders())
        }
    }
    CustomButton.template = 'CustomButton';

    Registries.Component.add(CustomButton);

    return CustomButton;
});
