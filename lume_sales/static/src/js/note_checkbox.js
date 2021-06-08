console.log("Checkbox widget has been loaded 1");
odoo.define('lume_sales.note_checkbox', function (require) {
    "use strict";
    
    var fieldRegistry = require('web.field_registry');
    var core = require('web.core');

    var {FieldBoolean} = require('web.basic_fields.deprecated');
    
    var NoteCheckbox = FieldBoolean.extend({
        /**
     * @override
     * @returns {jQuery} the focusable checkbox input
     */
    getFocusableElement: function () {
        return this.$input || $();
    },
    });
    
    fieldRegistry.add('note_checkbox', NoteCheckbox);
    
    });
