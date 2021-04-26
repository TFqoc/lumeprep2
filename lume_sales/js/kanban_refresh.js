console.log("KanbanRefresh has been loaded");
odoo.define('lume_sales.kanban_refresh', function(require){
    "use strict";

    var KanbanRenderer = require('web.KanbanRenderer');
    KanbanRenderer.include({
        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            // this.refresh = setInterval(this._renderView.bind(this), 10000);
        },
        _renderView_debug: function(){
            // this._renderView();
            console.log("Re-rendering (commented)");
        },
    });

    return KanbanRenderer;
});
