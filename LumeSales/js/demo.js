alert("Demo has been loaded");
console.log("Demo has been loaded");
odoo.define('LumeSales.Demo', ['web.kanban_record_quick_create'], function(require){
    "use strict";

    var Quick = require('web.kanban_record_quick_create');
    Quick.include({
        events:{'click .o_kanban_cancel': '_onCancelClicked',},
    });

    return Quick;
});
