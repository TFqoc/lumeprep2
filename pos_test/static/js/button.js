odoo.define('pos_test.CustomButton', function(require) {
    'use strict';

    const { useState } = owl;
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class CustomButton extends PosComponent {
        constructor() {
            super(...arguments);
            this.state = useState({ label: 'Click Me!' });
            // this.confirmed = null;
        }
        get translatedLabel() {
            return this.env._t(this.state.label);
        }
        onClick() {
            console.log("You clicked me!");
        }
    }
    CustomButton.template = 'CustomButton';

    Registries.Component.add(CustomButton);

    return CustomButton;
});
