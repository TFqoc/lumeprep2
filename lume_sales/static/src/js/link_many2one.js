console.log("load link m2o");
odoo.define('lume_sales.link_many2one', function(require){
    "use strict";

    var {FieldMany2One} = require('web.relational_fields');
    var fieldRegistry = require('web.field_registry');
    
    var LinkM2O = FieldMany2One.extend({
        init: function (parent, name, record, options) {
            this._super.apply(this, arguments);
            // this.m2o_value = this.record.data.display_name;
        }

    });

    fieldRegistry.add('link_many2one', LinkM2O);
    return LinkM2O;
});
