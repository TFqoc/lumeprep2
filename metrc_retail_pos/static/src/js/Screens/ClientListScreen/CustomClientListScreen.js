odoo.define('metrc_retail_pos.CustomClientListScreen', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const { patch } = require('web.utils');
    const ClientListScreen = require('point_of_sale.ClientListScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    patch(ClientListScreen, 'CustomClientListScreen', {
        editClient() {
            // Patch for fetching customer_type for the current selected partenr.
            this._super(...arguments);
            this.state.editModeProps.customer_types = this.customer_types;
            if (this.state.editModeProps.partner.id) {
                this.rpc({
                    model: 'res.partner',
                    method: 'read',
                    args: [this.state.editModeProps.partner.id, ['customer_type']],
                }).then(res => {
                    this.state.editModeProps.partner.customer_type = res[0]['customer_type'];
                    this.render();
                });
            }
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