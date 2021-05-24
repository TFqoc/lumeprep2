console.log("You can RPC on a renderer! 1");
odoo.define('lume_sales.ProductKanbanRenderer', function (require) {
    "use strict";
    
    const KanbanRenderer = require('web.KanbanRenderer');

    return KanbanRenderer.extend({
        _renderView: function(){
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if (self.header) return;
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
                    // let style = "display: flex; padding: 5px; margin-left: 8px; margin-right: 8px; border: 1px solid #ced4da; background-color: white; width: 100%;font-weight: bold; font-size: 1.3em;";
                    let button = `<a href='${link}' class='btn btn-primary catalog_back_button'>&lt; Back</a>`;
                    let spacer = "<div style='flex-grow: 90;'></div>";
                    let textStyle = "align-self: flex-end; text-align: right;";
                    self.header = `<div class='catalog_header'>${button}${spacer}<span style="${textStyle}"><span id="TOTAL">Total: $${price.toFixed(2)}</span><br/><span id="QTY">Quantity: ${qty.toFixed(1)}</span></span></div>`;
                    self.$el.prepend(self.header);
                 });
            });
        },
        _renderUngrouped: function (fragment) {
            if (this.header){
                let node = document.createRange().createContextualFragment(this.header);
                fragment.append(node);
            }
            return this._super.apply(this, arguments);
        },
    });
});