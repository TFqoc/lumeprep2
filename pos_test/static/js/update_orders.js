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
                //                 console.log(linked_sale_order_ids);
                this.rpc({
                    'model': 'sale.order',
                    'method': 'get_orders',
                    args: [linked_sale_order_ids, this.env.pos.pos_session.id],
                    // Pass session_id, session object has reference to config object
                }).then((result) => {
                    // TODO check returned orders against what we have.
                    // delete the ones that are outdated
                    var data = JSON.parse(result);
                    for (let order of this.env.pos.get_order_list()){
                        if (data.old_orders.includes(order.sale_order_id)){
                            order.destroy();
                            console.log("Deleting order");
                        }
                        else if (data.update_orders.includes(order.sale_order_id)){
                            // TODO update order data here
                            var index = data.update_orders.findIndex((el) => el == order.sale_order_id);
                            order.initialize({}, {pos:this.env.pos, json:data.update_orders[index]});
                            // var i;
                            // var j;
                            // for (let update_line of data.update_orders.lines){
                            //     for (let pos_line of order.orderlines){
                            //         if (update_line.product_id == pos_line.product.id){

                            //         }
                            //     }
                            // }
                            // if order is current order, then re-render it or product screen or whatever
                            if (this.env.pos.get_order().uid == order.uid){
                                order.render();
                            }
                        }
                        console.log("Sparing order");
                    }
//                     console.log("I got these sale orders: " + result);
//                     console.log(JSON.stringify(data.new_orders));
                    this.env.pos.import_orders(JSON.stringify(data.new_orders));
                    
                    // TODO Add something to update the records with the update data and re-render them
                    
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