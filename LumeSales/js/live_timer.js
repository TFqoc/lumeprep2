//alert("Unread Messages has been loaded");
console.log("Live Timer has been loaded");
odoo.define('LumeSales.live_timer', ['web.rpc'], function(require){
    "use strict";

    var rpc = require('web.rpc');
    var model = 'project.task';
    function update_timer(data){
        //Loop through records
        // update associated cards
    }
    function get_tasks(){
        
        // Use an empty array to search for all the records
        var domain = [['is_timer_running', '=', true]];
        // Use an empty array to read all the fields of the records
        var fields = ['timer_counter'];
        task_data = rpc.query({
            model: this.model,
            method: 'search_read',
            args: [domain, fields],
        }).then(function (data) {
            console.log(data);
            // Loop through records
            // Update associated card
            return data;
        });
    }
    async function loop(){
        data = get_tasks();
        while (true){
            update_timer(data);
            await new Promise(r => setTimeout(r, 1000));
        }
    }
    //

    loop();

    return model;
});
