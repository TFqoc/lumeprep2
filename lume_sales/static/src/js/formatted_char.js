odoo.define('lume_sales.formatted_char', function(require){
    "use strict";

    var {FieldChar} = require('web.basic_fields');
    var fieldRegistry = require('web.field_registry');
    
    var FormattedChar = FieldChar.extend({
        _render: function(){
            this._super.apply(this, arguments);
            // Forces the text to appear capitalized. Actual capitalization of text needs to be
            // handled in python, preferably in an onChange method
            this.$el.attr('style', 'text-transform: uppercase;');
        },

    });

    fieldRegistry.add('formatted_char', FormattedChar);
    return FormattedChar;
});
