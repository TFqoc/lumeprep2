console.log("Button dot js is loaded! Current test: rpc");
odoo.define('pos_test.CustomButton', function(require) {
    'use strict';

    const { useState } = owl;
    const { useListener } = require('web.custom_hooks');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    // const rpc = require('web.rpc');

    class CustomButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click-product', this.onAddProduct);
            // this.state = useState({ label: 'Click Me!' });
            // this.confirmed = null;
        }
        // get translatedLabel() {
        //     return this.env._t(this.state.label);
        // }
        async onClick() {
            var result = await this.rpc({
                'model': 'sale.order',
                'method': 'get_all',
                // args: [some, args],
            });
            console.log("You clicked me!");
            console.log(result);
        }
        onAddProduct({ detail: clickedProduct }){
            console.log("You just added a product!");
            console.log(clickedProduct); // clickedProduct should have all fields from the db model that were imported into pos.
        }
    }
    CustomButton.template = 'CustomButton';

    Registries.Component.add(CustomButton);

    return CustomButton;
});
