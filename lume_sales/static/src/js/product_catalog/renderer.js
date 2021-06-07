console.log("You can RPC on a renderer! 1");
odoo.define('lume_sales.ProductKanbanRenderer', function (require) {
    "use strict";

    const KanbanRenderer = require('web.KanbanRenderer');

    return KanbanRenderer.extend({
        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // if (self.header) return;
                let params = new URLSearchParams(window.location.hash);
                console.log(`Requesting data from Hash: ${window.location.hash}`);
                let id = parseInt(params.get('#active_id')) || parseInt(params.get('#id'))
                self._rpc({
                    model: 'sale.order',
                    method: 'get_cart_totals',
                    args: [id],
                }).then(function (data) {
                    if (!self.header) {
                        let price = data[0];
                        let qty = data[1];
                        // let link = `#id=${id}&model=sale.order`;
                        // let style = "display: flex; padding: 5px; margin-left: 8px; margin-right: 8px; border: 1px solid #ced4da; background-color: white; width: 100%;font-weight: bold; font-size: 1.3em;";
                        let button = `<button id="catalog_back_button" class='btn btn-primary catalog_back_button'>&lt; Back</button> <button id="catalog_confirm_button" class='btn btn-primary catalog_back_button'>Confirm Order</button>`;
                        let spacer = "<div style='flex-grow: 90;'></div>";
                        let textStyle = "align-self: flex-end; text-align: right;";
                        self.header = `<div class='catalog_header'>${button}${spacer}<span style="${textStyle}"><span id="TOTAL">Total: $${price.toFixed(2)}</span><br/><span id="QTY">Quantity: ${qty.toFixed(1)}</span></span></div>`;
                        // self.header = self.header + '<div id="coverall" style="position: fixed;width: 100%;height: 100%;background-color: rgba(0,0,0, 0.7);z-index:  100;display:none;"></div>';
                        $('.o_view_controller').append('<div id="coverall" style="position: fixed;width: 100%;height: 100%;background-color: rgba(0,0,0, 0.7);z-index:  100;padding:3% 3% 6% 3%;display:none;"></div>');
                        self.$el.prepend(self.header);
                    }
                    $('#catalog_back_button').click(() => {
                        self.do_action({
                            type: 'ir.actions.act_window',
                            views: [[false, 'form']],
                            res_model: 'sale.order',
                            res_id: id,
                            flags: { mode: 'edit' },
                        });
                    });
                    $('#catalog_confirm_button').click(() => {
                        self._rpc({
                            model: 'sale.order',
                            method: 'action_confirm',
                            args: [],
                        }).then(function(action){
                            self.do_action(action);
                        });
                    });
                    $("#coverall").click(function(event){
                        event.stopPropagation();
                        $("#coverall").hide();
                    });
                    $('button.o_kanban_image').click(function(event){
                        event.stopPropagation();
                        // Should only ever be one img child
                        var src = $(event.target).attr("src");
                        src = src.replace("image_128","image_1920");
                        $('#coverall').html(`<img src='${src}' alt='Product' style='width:100%;height:100%;object-fit:contain;'/>`);
                        $('#coverall').show();
                    });

                    // Hide cards as needed
                    let hide_type = data[2];
                    _.each(self.widgets, function (record) {
                        let $el = record.$el;
                        let recordData = record.state.data;
                        let fieldName = 'thc_type';
                        //  console.log(recordData);
                        // Hide if you don't have this value
                        let val = recordData[fieldName] ? recordData[fieldName] : '';
                        let qty = $el.attr('data-qty');
                        $el.removeClass('catalog_card_hide');
                        if (val == hide_type || qty == 0) {
                            $el.addClass('catalog_card_hide');
                        }
                    });
                });
            });
        },
        _renderUngrouped: function (fragment) {
            if (this.header) {
                let node = document.createRange().createContextualFragment(this.header);
                fragment.append(node);
            }
            return this._super.apply(this, arguments);
        },
    });
});