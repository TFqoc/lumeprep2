odoo.define('metrc_retail_pos.LicensePopup', function(require) {
    'use strict';

    const { useState, useRef } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    // formerly TextInputPopupWidget
    class LicensePopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            const current_order = this.env.pos.get_order();
            this.state = useState({ 
                customerType: this.env.pos.get_client().customer_type,
                customerLicense: current_order.patient_license_number,
                caregiverLicense: current_order.caregiver_license_number,
                customerIdMethod: current_order.ext_patient_id_method,
            });
        }
        getPayload() {
            return {
                customerType: this.state.customerType,
                customerLicense: this.state.customerLicense,
                caregiverLicesne: this.state.caregiverLicense,
                customerIdMethod: this.state.customerIdMethod,
            }
        }
    }
    LicensePopup.template = 'LicensePopup';
    LicensePopup.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: 'Select License',
    };

    Registries.Component.add(LicensePopup);

    return LicensePopup;
});
