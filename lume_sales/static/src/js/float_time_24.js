odoo.define('lume_sales.float_time_24', function(require){
    "use strict";

    var {FieldFloatTime} = require('web.basic_fields');
    var fieldRegistry = require('web.field_registry');
    
    var FieldFloatTime24 = FieldFloatTime.extend({
        _setValue: function (value, options) {
            console.log("Value: " + value);
            console.log("Type: " + typeof(value));
            if (value >= 24){
                value = 23.99;
            }
            else if (value < 0){
                value = 0;
            }
            return this._super(value, options);
        },
    });

    fieldRegistry.add('float_time_24', FieldFloatTime24);
    return FieldFloatTime24;
});
