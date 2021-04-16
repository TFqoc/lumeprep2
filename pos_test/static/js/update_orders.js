console.log("UpdateOrders dot js loaded. Test looping calls");
odoo.define('pos_test.UpdateOrders', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const TicketButton = require('point_of_sale.TicketButton');
    const Registries = require('point_of_sale.Registries');
    import { useRef } from "owl/hooks";

    class UpdateOrders extends PosComponent {
        constructor(){
            super(...arguments);
            this.ticketRef = useRef("TicketButton");
        }
        mounted() {
            console.log("Update is mounting");
            this.getOrders();
            this.getter = setInterval(this.getOrders.bind(this), 10000);
        }
        async getOrders(){
                var linked_sale_order_ids = [];
                var i;
                let order_list = this.env.pos.get_order_list();
                for (i=0; i<order_list.length; i++){
                    if (order_list[i].sale_order_id){// if exists
                        linked_sale_order_ids.push(order_list[i].sale_order_id);
                        console.log("Adding Linked Order");
                    }
                }
                this.rpc({
                    'model': 'sale.order',
                    'method': 'get_orders',
                    args: [linked_sale_order_ids, this.env.pos.pos_session.id],
                    // Pass session_id, session object has reference to config object
                    // Pass list of so ids from current orders
                    // Pass this.pos.pos_session.id
                    // this.config.id (pos shop id)
                    // this.config.current_session_id (pos.session id)
                }).then((result) => {
                    // TODO check returned orders against what we have.
                    //console.log("I got these sale orders: " + result);
                    this.env.pos.import_orders(result);
                    this.ticketRef.render();
                },
                (args) => {
                    console.log("Failed to get new orders from backend.");
                });
        }
        syncOrders(orders){
            if (orders.length > 0){
                // TODO create orders
            }
        }
    }
    UpdateOrders.template = 'UpdateOrders';

    Registries.Component.add(UpdateOrders);

    return UpdateOrders;
});