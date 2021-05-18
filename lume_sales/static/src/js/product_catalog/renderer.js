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
                    let style = "flex: 100%; justify-content: space-between; padding: 5px; margin-left: 8px; margin-right: 8px; border: 1px solid #ced4da; background-color: white; width: 100%; text-align: right; font-weight: bold; font-size: 1.3em;";
                    self.$el.prepend(`<div style='${style}'><p id="TOTAL">Total: $${price.toFixed(2)}</p><p id="QTY">Quantity: ${qty.toFixed(1)}</p></div>`);
                 });
            });
        },
    });
});