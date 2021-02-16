//alert("Unread Messages has been loaded");
console.log("Unread Messages has been loaded");
odoo.define('LumeSales.Unread_Messages', ['web.AbstractField','web.field_registry'], function(require){
    "use strict";

    //var rpc = require('web.rpc');
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
            console.log(this.record.data.message_unread_counter);// This is correct
            this.text = this.record.data.message_unread_counter.toString();
            this.className = 'o_MessagingMenu_counter badge badge-pill';
            this.checker = setInterval(async ()=> {
                //console.log(this.res_id);
                this.message_number = await this._getCounterValue();
                this.$el.text(this.message_number.toString());
            }, 10000);
        },
        _getCounterValue: function(){
            return this._rpc({
                model: 'project.task',
                method: 'get_message_count',
                args: [this.res_id]
            });
        },
        
    });

    fieldRegistry.add('count_counter', CounterWidget);

    return CounterWidget;

    /*function update_icon(){
        
        // Use an empty array to search for all the records
        var domain = [['id', '>', 10]];
        // Use an empty array to read all the fields of the records
        var fields = [];
        rpc.query({
            model: 'project.task',
            method: 'search_read',
            args: [domain, fields],
        }).then(function (data) {
            //console.log(data);
            // Loop through records
            // Update associated card
        });
    }
    async function loop(){
        while (false){
            update_icon();
            await new Promise(r => setTimeout(r, 10000));
        }
    }

    loop();

    return 'Unread Messages';*/
});
