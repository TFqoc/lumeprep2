console.log("load link m2o");
odoo.define('lume_sales.link_many2one', function(require){
    "use strict";

    var {FieldMany2One} = require('web.relational_fields');
    var fieldRegistry = require('web.field_registry');
    
    var LinkM2O = FieldMany2One.extend({
        // _render: function(){
            
        // },

    });

    fieldRegistry.add('link_many2one', LinkM2O);
    return LinkM2O;
});
