//alert("Unread Messages has been loaded");
console.log("Live Timer has been loaded");
odoo.define('LumeSales.live_timer', function(require){
    "use strict";

    var Timer_timer = require('timer.timer');
    var fieldRegistry = require('web.field_registry');

    var LiveTimer = Timer_timer.extend({

        init: function (parent, name, record, options) {
            this._super.apply(this, arguments);
            this.className = 'o_field_widget o_readonly_modifier text-danger ml-auto h5 ml-4 font-weight-bold';

        },

    });

    fieldRegistry.add('LumeSales.live_timer', LiveTimer);

    return LiveTimer;
});
