odoo.define('metrc_retail_pos.CustomProductScreen', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const ActionPadWidget = require('point_of_sale.ActionpadWidget');
    const { useListener } = require('web.custom_hooks');
    const { useState } = require('web.custom_hooks');

    const CustomProductScreen = (ProductScreen) => {
        class CustomProductScreen extends ProductScreen {
            constructor() {
                super(...arguments);
                useListener('click-license', this._onClickLicense);
            }
            async _onClickLicense() {
                const currentLicense = this.currentOrder.patient_license_number;
                const licenseList = this.env.pos.patient_licenses.map(license => {
                    return license.license_number;
                });
                const { confirmed, payload: licenseData } = await this.showPopup(
                    'LicensePopup',
                    {
                        customer_types: this.env.pos.customer_types,
                        customer_licenses: licenseList,
                        id_methods: this.env.pos.id_methods,
                    }
                );
                if (confirmed) {
                    const client = this.currentOrder.get_client();
                    if (licenseData.customerType != client.customer_type) {
                        try {
                            let partnerId = await this.rpc({
                                model: 'res.partner',
                                method: 'create_from_ui',
                                args: [{
                                    id: client.id,
                                    customer_type: licenseData.customerType,
                                }],
                            });
                            await this.env.pos.load_new_partners();
                        } catch (error) {
                            if (error.message.code < 0) {
                                await this.showPopup('OfflineErrorPopup', {
                                    title: this.env._t('Offline'),
                                    body: this.env._t('Unable to save changes.'),
                                });
                            } else {
                                throw error;
                            }
                        }
                    }
                    client.customer_type = licenseData.customerType;
                    this.currentOrder.customer_type = licenseData.customerType;
                    this.currentOrder.patient_license_number = licenseData.customerLicense;
                    if (client.customer_type == 'ExternalPatient') {
                        this.currentOrder.ext_patient_id_method = licenseData.customerIdMethod;
                    }
                    if (client.customer_type == 'Caregiver') {
                        this.currentOrder.caregiver_license_number = licenseData.caregiverLicense;
                    }
                }
                this.render();
            };
        };
        return CustomProductScreen;
    };
    const CustomActionPadWidget = (ActionPadWidget) => {
        class CustomActionPadWidget extends ActionPadWidget {
            get license() {
                return this.env.pos.get_order().patient_license_number;
            }
        }
        return CustomActionPadWidget;
    }
    Registries.Component.extend(ProductScreen, CustomProductScreen);
    Registries.Component.extend(ActionPadWidget, CustomActionPadWidget);

    return CustomProductScreen;
}); 