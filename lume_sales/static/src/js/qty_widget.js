console.log("QTY widget has been loaded 1");
odoo.define('lume_sales.qty_widget', function (require) {
    "use strict";
    
    var fieldRegistry = require('web.field_registry');
    var Widget = require('web.Widget');
    var FieldFloat = require('web.basic_fields').FieldFloat;
    var core = require('web.core');
    var qweb = core.qweb;
    
    var QTYWidget = FieldFloat.extend({
        template: 'qty_template',
        init: function (parent,value) {
            this._super.apply(this, arguments);
//             this.className = 'o_field_widget o_readonly_modifier timer-normal ml-auto h5 ml-4 font-weight-bold';
        },
        start: function(){
            // Rendering is done so bind methods to the buttons
            this.$el.children().first().click(this.subtractQty.bind(this));
            this.$el.children().first().next().text(this.value);
            this.$el.children().last().click(this.addQty.bind(this));
            return this._super.apply(this, arguments);;
        },
        addQty: async function(){
            await this._setValue((this.value + 1) + "", {});
            this.$el.children().first().next().text(this.value);
        },
        subtractQty: async function(){
            await this._setValue((this.value - 1) + "", {});
            this.$el.children().first().next().text(this.value);
        },
    });
    
    fieldRegistry.add('qty_widget', QTYWidget);
    
    });
