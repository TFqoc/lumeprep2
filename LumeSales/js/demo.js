alert("Demo has been loaded");
console.log("Demo has been loaded");
odoo.define('LumeSales.Demo', ['web.kanban_record_quick_create'], function(require){
    "use strict";

    var Quick = require('web.kanban_record_quick_create');
    Quick.include({
        _add: function (options) {
            this._super.apply(this, arguments);
            return this._rpc({
                model: 'project.task',
                method: 'delete_recent',
                args: [[],[]]
            });
        },
    });

    return Quick;
});
