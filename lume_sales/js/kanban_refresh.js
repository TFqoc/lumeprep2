console.log("KanbanRefresh has been loaded. Testing pause the reload. messages");
odoo.define('lume_sales.kanban_refresh', function(require){
    "use strict";

    const { patch } = require("web.utils");
    const SearchBar = require("web.SearchBar");
    const { bus } = require("web.core");
    var QuickCreate = require('web.kanban_record_quick_create');

    patch(SearchBar, "Refresh search every 10 seconds", {
        mounted() {
            this._super(...arguments);
            setInterval(this.refresh.bind(this), 15000);
            bus.on('quick_create_start', this, this.pause);
            bus.on('quick_create_end', this, this.unpause);
            this.paused = false;
        },
        refresh(){
            if (!this.paused){
                this.model.dispatch('search');
                console.log("Reloading");
            }
            else{
                console.log("Not Reloading");
            }
        },
        pause(){
            this.paused = true;
            console.log("Trigger start caught");
        },
        unpause(){
            this.paused = false;
            console.log("Trigger end caught");
        }
    });

    QuickCreate.include({
        init: function (options) {
            this._super.apply(this, arguments);
            bus.trigger('quick_create_start');
            console.log("Trigger start");
        },
        _add: function (options) {
            this._super.apply(this, arguments);
            bus.trigger('quick_create_end');
            console.log("Trigger end");
        },
        _cancel: function () {
            this._super.apply(this, arguments);
            bus.trigger('quick_create_end');
            console.log("Trigger ends");
        },
    });
    
    return QuickCreate;

    // Somewhere else
    // bus.trigger();

    // var KanbanRenderer = require('web.KanbanRenderer');
    // KanbanRenderer.include({
    //     init: function (parent, state, params) {
    //         this._super.apply(this, arguments);
    //         // this.refresh = setInterval(this._renderView.bind(this), 10000);
    //     },
    //     _renderView_debug: function(){
    //         // this._renderView();
    //         console.log("Re-rendering (commented)");
    //     },
    // });

    // return KanbanRenderer;
});
