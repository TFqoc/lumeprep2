console.log("You can RPC on a renderer! 1");
odoo.define('lume_sales.ProductKanbanRenderer', function (require) {
    "use strict";
    
    const KanbanRenderer = require('web.KanbanRenderer');

    return KanbanRenderer.extend({
        _renderView: function(){
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                let params = new URLSearchParams(window.location.hash);
                 self._rpc({
                    model: 'sale.order',
                    method: 'get_cart_totals',
                    args: [parseInt(params.get('#active_id'))],
                }).then(function(data){
                    let price = data[0];
                    let qty = data[1];
                    self.$el.prepend("<div style='flex: 100%'>$${price}<br/>Qty: ${qty}</div>");
                    console.log(self.$el);
                    console.log(self.activeActions);
                 });
            });
        },
    });
});