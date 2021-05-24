console.log("You can RPC on a renderer! 1");
odoo.define('lume_sales.ProductKanbanRenderer', function (require) {
    "use strict";
    
    const KanbanRenderer = require('web.KanbanRenderer');

    return KanbanRenderer.extend({
        _renderView: function(){
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                let params = new URLSearchParams(window.location.hash);
                console.log(`Requesting data from Hash: ${window.location.hash}`);
                let id = parseInt(params.get('#active_id')) || parseInt(params.get('#id'))
                 self._rpc({
                    model: 'sale.order',
                    method: 'get_cart_totals',
                    args: [id],
                }).then(function(data){
                    let price = data[0];
                    let qty = data[1];
                    let link = `#id=${id}&model=sale.order`;
                    let style = "display: flex; padding: 5px; margin-left: 8px; margin-right: 8px; border: 1px solid #ced4da; background-color: white; width: 100%;font-weight: bold; font-size: 1.3em;";
                    let button = `<a href='${link}' class='btn btn-primary' style='align-self: center; text-align: center; color:white;'>&lt; Back</a>`;
                    let spacer = "<div style='flex-grow: 90;'/>";
                    let textStyle = "align-self: flex-end; text-align: right;";
                    self.$el.prepend(`<div style='${style}'>${button}${spacer}<span style="${textStyle}"><span id="TOTAL">Total: $${price.toFixed(2)}</span><br/><span id="QTY">Quantity: ${qty.toFixed(1)}</span></span></div>`);
                     console.log(`Data: ${data}`);
                 });
            });
        },
    });
});