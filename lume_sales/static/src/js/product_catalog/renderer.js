odoo.define('lume_sales.ProductKanbanRenderer', function (require) {
    "use strict";
    
    const KanbanRenderer = require('web.KanbanRenderer');

    return KanbanRenderer.extend({
        _renderView: function(){
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                console.log(self.$el);
            });
        }
    });

    
    });
    