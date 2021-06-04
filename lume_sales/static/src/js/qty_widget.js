console.log("QTY widget has been loaded 7");
odoo.define('lume_sales.qty_widget', function (require) {
    "use strict";
    
    var fieldRegistry = require('web.field_registry');
    var Widget = require('web.Widget');
    var FieldFloat = require('web.basic_fields').FieldFloat;
    
    var QTYWidget = FieldFloat.extend({
        template: 'qty_template',
        init: function (parent,value) {
            this._super.apply(this, arguments);
//             this.className = 'o_field_widget o_readonly_modifier timer-normal ml-auto h5 ml-4 font-weight-bold';
        },
        start: function(){
            // Rendering is done so bind methods to the buttons
            this.$el.children().first().click(this.subtractQty.bind(this));
            this.$el.children().last().click(this.addQty.bind(this));
            return Promise.resolve();
        },
        addQty: function(){
            this._setValue((this.value + 1) + "", {});
        },
        subtractQty: function(){
            this._setValue((this.value - 1) + "", {});
        }
        
    });
    
    fieldRegistry.add('qty_widget', QTYWidget);
    
    });
