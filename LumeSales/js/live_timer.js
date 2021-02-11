//alert("Unread Messages has been loaded");
console.log("Live Timer has been loaded");
odoo.define('LumeSales.live_timer', ['web.rpc'], function(require){
    "use strict";

    var rpc = require('web.rpc');

    var task_data = false;

    function update_timer(){
        //Loop through records
        if (task_data){
            var d;
            for (d in task_data){

            }
        }
        // update associated cards
    }
    function get_tasks(){
        
        // Use an empty array to search for all the records
        var domain = [['id', '>', 1]];
        // Use an empty array to read all the fields of the records
        var fields = [];
        task_data = rpc.query({
            model: 'project.task',
            method: 'search_read',
            args: [domain, fields],
        }).then(function (data) {
            console.log(data);
            task_data = data;
        });
    }
    async function loop(){
        task_data = get_tasks();
        while (true){
            update_timer();
            await new Promise(r => setTimeout(r, 1000));
        }
    }

    loop();

    return 'live_timer';
});
