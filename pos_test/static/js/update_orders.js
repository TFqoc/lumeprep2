console.log("UpdateOrders dot js loaded. Test looping calls");
odoo.define('pos_test.UpdateOrders', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const TicketButton = require('point_of_sale.TicketButton');
    const Registries = require('point_of_sale.Registries');
    const { useRef } = owl.hooks;
    
    class UpdateOrders extends PosComponent {
        //static components = { TicketButton };
        constructor(){
            super(...arguments);
            
        }
        mounted() {
            //console.log("Update is mounting");
            //this.getOrders();
            this.getter = setInterval(this.getOrders.bind(this), 10000);
            //console.log("Getting ref");
            this.ticketRef = useRef("TicketButton");
        }
        async willStart(){
            await this.getOrders();
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
                }).then((result) => {
                    // TODO check returned orders against what we have.
                    // delete the ones that are outdated
                    this.env.pos.orders.foreach((order)=>{
                        if (!order.sale_order_id || result.old_orders.includes(order.sale_order_id)){
                            order.destroy();
                        }
                    }, this);

                    //console.log("I got these sale orders: " + result);
                    this.env.pos.import_orders(result.new_orders);

                    
                    // console.log("calling render on: ");
                    // console.log(this.ticketRef);
                    //this.ticketRef.comp.render();
                },
                (args) => {
                    console.log("Failed to get new orders from backend.");
                });
        }
    }
    UpdateOrders.template = 'UpdateOrders';

    Registries.Component.add(UpdateOrders);

    return UpdateOrders;
});