console.log("Click test 1")
odoo.define('lume_sales.lpc_product_quantity', function (require) {
    "use strict";

    var FieldInteger = require('web.basic_fields').FieldInteger;

    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var qweb = core.qweb;

    var _t = core._t;


    /**
     * LPCProductQty is a widget to  get the LPC Product Quantity in product kanban view
     */
    var LPCProductQty = FieldInteger.extend({
        description: _t("LPC Product Quantity"),
        template: "LPCProductQuantity",
        events: {
            'click .o_target_to_set': '_onKanbanTargetClicked',
        },

        /**
         * @override
         */
        init: function (parent, name, record, options) {
            this._super.apply(this, arguments);
            if (record.context.hide_qty_buttons) {
                this.isReadonly = true;
            }
            //         if (this.$el){
            //             var $target = this.$el;
            //             var self = this;
            //                console.log("Calling widget start.");
            //             $target.prev().on("click",(function(event){self._valueChange('lpc_quantity', -1);console.log("-");}).bind(self));
            //             $target.next().on("click",(function(event){self._valueChange('lpc_quantity', 1);console.log("+");}).bind(self));
            //         }
        },
        /*
        * @override
        */
        start: function () {
            this._super.apply(this, arguments);
            //     var $target = this.$el;
            //     var self = this;
            //     console.log("Calling widget start.");
            //     $target.prev().on("click",(function(event){self._valueChange('lpc_quantity', -1);console.log("-");}).bind(self));
            //     $target.next().on("click",(function(event){self._valueChange('lpc_quantity', 1);console.log("+");}).bind(self));
            return Promise.resolve();
        },
        renderElement: function () {
            this._super.apply(this, arguments);
            var $target = this.$el;
            var self = this;
            console.log("Calling widget render.");
            console.log(this.$el);
            $target.prev().on("click", (function (event) { self._valueChange('lpc_quantity', -1); console.log("-"); }).bind(self));
            $target.next().on("click", (function (event) { self._valueChange('lpc_quantity', 1); console.log("+"); }).bind(self));
        },

        /**
         * @private
         * @param {OdooEvent} e
         */
        _valueChange: function (target_name, value) {
            var target_name = target_name;
            var target_value = value;
            if (isNaN(target_value)) {
                this.do_warn(false, _t("Please enter an integer value"));
            } else {
                var changes = {};
                changes[target_name] = parseInt(target_value);
                this.trigger_up('field_changed', {
                    dataPointID: this.dataPointID,
                    changes: changes,
                });
                // TODO RPC here
                // console.log("RPC Call")
                // let params = new URLSearchParams(window.location.hash);
                // this._rpc({
                //     model: 'sale.order',
                //     method: 'get_cart_totals',
                //     context: { lpc_sale_order_id: parseInt(params.get('#active_id')), },
                //     args: [parseInt(params.get('#active_id'))],
                // }).then(function (data) {
                //     $("#TOTAL").text(`Total: $${data[0].toFixed(2)}`);
                //     $("#QTY").text(`Quantity: ${data[1].toFixed(1)}`);
                //     console.log(`RPC Data: ${data}`);
                // });
            }
        },
        _onKanbanTargetClicked: function (e) {
            var self = this;
            var $target = $(e.currentTarget);
            var target_name = $target.attr('name');
            var target_value = $target.attr('value');

            if (this.isReadonly) {
                return;
            }
            var $input = $('<input/>', { type: "text", class: 'o_input oe_inline d-inline-block text-center', style: "width: 40px; font-size: 24px", name: target_name });
            if (target_value) {
                $input.attr('value', target_value);
            }
            $input.on('keyup input', function (e) {
                if (e.which === $.ui.keyCode.ENTER) {
                    $input.blur();
                }
            });
            $input.on('blur', function () {
                self._valueChange(target_name, $input.val());
            });
            $input.replaceAll($target)
                .focus()
                .select();
        },
        /**
             * Render the widget when it is NOT edited.
         *
         * @override
         */
        _renderReadonly: function () {
            this.$el.html(qweb.render('LPCProductQuantity', { qty: this.recordData.lpc_quantity }));
        },
    });

    field_registry.add('lpcProductQuantity', LPCProductQty);

    return {
        LPCProductQty: LPCProductQty,
    };

});

function update_data() {
    setTimeout(function () {
        let params = new URLSearchParams(window.location.hash);
        $.ajax({
            url: "/web/dataset/call_kw/sale.order/get_cart_totals",
            data: JSON.stringify({
                method: 'call',
                params: {
                    kwargs: {},
                    model: 'sale.order',
                    args: [parseInt(params.get('#active_id'))],
                    method: 'get_cart_totals',
                },

            }),
            success: function (data) {
                $("#TOTAL").text(`Total: $${data.result[0].toFixed(2)}`);
                $("#QTY").text(`Quantity: ${data.result[1].toFixed(1)}`);
            },
            dataType: 'json',
            type: 'POST',
            contentType: 'application/json'
        });
    },50);
}