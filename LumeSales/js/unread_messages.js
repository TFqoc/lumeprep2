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
        
        
        message_number: 0,

        init: function (parent, data, options) {
            this._super.apply(this, arguments);
            //this.text = options.attrs.title || options.attrs.text;
            //this.tooltip = options.attrs.tooltip;
            this.className = 'o_MessagingMenu_counter badge badge-pill';
        },
        /*_render: function () {
            this._super.apply(this, arguments);
            this._startCounter();
        },
        _startCounter: async function () {
            if (this.record.data.timer_start) {
                const serverTime = this.record.data.timer_pause || await this._getServerTime();
                this.time = Timer.createTimer(0, this.record.data.timer_start, serverTime);
                this.$el.text(this.time.toString());
                this.timer = setInterval(() => {
                    if (this.record.data.timer_pause) {
                        clearInterval(this.timer);
                    } else {
                        this.time.addSecond();
                        this.$el.text(this.time.toString());
                    }
                }, 1000);
            } else if (!this.record.data.timer_pause){
                clearInterval(this.timer);
            }
        },*/

        _getCounterValue: function(){
            return this._rpc({
                model: 'project.task',
                method: 'get_server_time',
                args: [this.record.data.id]
            });
        },
        checker: setInterval(()=> {
            this.message_number = this._getCounterValue();
            this.$el.text(this.message_number.toString());
        }, 10000),
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
