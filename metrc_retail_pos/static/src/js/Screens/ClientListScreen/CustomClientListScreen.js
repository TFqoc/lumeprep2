odoo.define('metrc_retail_pos.CustomClientListScreen', function (require) {
    'use strict';

    const models = require('point_of_sale.models')
    const { patch } = require('web.utils');
    const ClientListScreen = require('point_of_sale.ClientListScreen');

    models.load_fields('res.partner', ['customer_type', 'license_ids']);
    models.load_models([{
        model:  'patient.id.method',
        fields: ['name'],
        loaded: function(self, methods) {
            self.id_methods = methods.map( (idm) => {
                return idm.name;
            });
        }
    }, {
        model :  'metrc.license',
        fields : ['id', 'license_number'],
        domain : function (self) {return [['base_type', '=', 'Patient']]},
        loaded: function(self, pls) {
            self.patient_licenses = pls;
        }
    }, {
        model :  'metrc.customer.types',
        fields : ['name'],
        loaded: function(self, ctypes) {
            self.customer_types = ctypes.map((ct) => {
                return ct.name;
            });
        }
    }])
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attr,options) {
            console.log(this);
            _super_order.initialize.apply(this, arguments);
            this.patient_license_number = '';
            this.caregiver_license_number = '';
            this.ext_patient_id_method = '';
            this.save_to_db();
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            json.patient_license_number = this.patient_license_number;
            json.caregiver_license_number = this.caregiver_license_number;
            json.ext_patient_id_method = this.ext_patient_id_method;
            console.log(json);
            return json;
        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this,arguments);
            json.patient_license_number = this.patient_license_number;
            json.caregiver_license_number = this.caregiver_license_number;
            json.ext_patient_id_method = this.ext_patient_id_method;
            return json;
        },
    });

    patch(ClientListScreen, 'CustomClientListScreen', {
        editClient() {
            // Patch for fetching customer_type for the current selected partner.
            this._super(...arguments);
            this.state.editModeProps.customer_types = this.env.pos.customer_types;
        },
    });
});