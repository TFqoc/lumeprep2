odoo.define('lume_sales.float_time_24', function(require){
    "use strict";

    var {FieldFloatTime} = require('web.basic_fields');
    var fieldRegistry = require('web.field_registry');
    
    var FieldFloatTime24 = FieldFloatTime.extend({
        _setValue: function (value, options) {
            console.log("Value: " + value);
            console.log("Type: " + typeof(value));
            let timePair = value.split(':');
            let hours = parseInt(timePair[0]);
            if (hours >= 24){
                value = '23.59';
            }
            else if (hours < 0){
                value = '00:' + timePair[1];
            }
            return this._super(value, options);
        },
    });

    fieldRegistry.add('float_time_24', FieldFloatTime24);
    return FieldFloatTime24;
});
