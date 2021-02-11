//alert("Unread Messages has been loaded");
console.log("Unread Messages has been loaded");
odoo.define('LumeSales.Unread_Messages', ['web.rpc'], function(require){
    "use strict";

    var rpc = require('web.rpc');
    var model = 'project.task';
    function update_icon(){
        
        // Use an empty array to search for all the records
        var domain = [['id', '>', 10]];
        // Use an empty array to read all the fields of the records
        var fields = [];
        rpc.query({
            model: this.model,
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

    return model;
});
