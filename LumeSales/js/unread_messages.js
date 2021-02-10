//alert("Unread Messages has been loaded");
console.log("Unread Messages has been loaded");
odoo.define('LumeSales.Unread_Messages', ['web.rpc'], function(require){
    "use strict";

    var rpc = require('web.rpc')
    function update_icon(){
        var model = 'project.task';
        // Use an empty array to search for all the records
        var domain = [['message_unread_counter', '<', 0]];
        // Use an empty array to read all the fields of the records
        var fields = [];
        rpc.query({
            model: model,
            method: 'search_read',
            args: [domain, fields],
        }).then(function (data) {
            console.log(data);
            // Loop through records
            // Update associated card
        });
    }
    async function loop(){
        while (true){
            update_icon();
            await new Promise(r => setTimeout(r, 10000));
        }
    }

    loop();

    return model;
});
