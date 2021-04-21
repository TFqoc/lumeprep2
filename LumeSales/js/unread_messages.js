console.log("Unread Messages has been loaded");
odoo.define('LumeSales.Unread_Messages', ['web.AbstractField','web.field_registry'], function(require){
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var CounterWidget = AbstractField.extend({

        /**
         * @param {Object} options
         * @param {string} options.attrs.title
         * @param {string} options.attrs.text same as title
         * @param {string} options.attrs.tooltip
         * @param {string} options.attrs.bg_color
         */
        
        checker: null,
        message_number: 0,

        init: function (parent, data, options) {
            this._super.apply(this, arguments);
            //console.log(this.record.data.message_unread_counter);// This is correct
            this.text = this.record.data.message_unread_counter.toString();
            this.className = 'o_MessagingMenu_counter badge badge-pill';
            this.checker = setInterval(async ()=> {
                //console.log(this.res_id);
                this.message_number = await this._getCounterValue();
                //console.log(this.message_number);
                this.$el.text(this.message_number.toString());
            }, 10000);
        },
        start: function(){
            //return new Promise(() => this.$el.text(this.record.data.message_unread_counter.toString()));
            return this.$el.text(this.record.data.message_unread_counter.toString());
        },
        _getCounterValue: function(){
            return this._rpc({
                model: 'project.task',
                method: 'get_message_count',
                args: [null, this.res_id]
            });
        },
        
    });

    fieldRegistry.add('count_counter', CounterWidget);

    return CounterWidget;
});
