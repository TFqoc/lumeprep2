odoo.define('metrc_retail_pos.CustomClientListScreen', function (require) {
    'use strict';

    const models = require('point_of_sale.models')
    const { patch } = require('web.utils');
    const ClientListScreen = require('point_of_sale.ClientListScreen');

    models.load_fields('res.partner', ['customer_type']);

    patch(ClientListScreen, 'CustomClientListScreen', {
        editClient() {
            // Patch for fetching customer_type for the current selected partner.
            this._super(...arguments);
            this.state.editModeProps.customer_types = this.customer_types;
        },
        async willStart() {
            this._super(...arguments);
            this.rpc({
                model: 'res.partner',
                method: 'get_customer_types_for_pos',
            }).then(res => {
                this.customer_types = res;
            });
        }
    });
});