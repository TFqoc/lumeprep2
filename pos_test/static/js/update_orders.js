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
            // destroy all current orders
            for (let order of this.env.pos.get_order_list()){
                order.destroy();
                console.log("Destroying old order");
            }
            // get a clean set of orders from the backend
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
                        else if (data.update_orders.unpaid_orders.some(e => e.sale_order_id == order.sale_order_id)){
                            // TODO update order data here
                            // Remove all line data to be replaced by the updated data
                            for (let line in order.get_orderlines()){
                                order.remove_orderline(line);
                            }
                            // Add updated data
                            var index = data.update_orders.unpaid_orders.findIndex((el) => el.sale_order_id == order.sale_order_id);
                            
                            // This method will work, but invoke all the update events
                            // order.init_from_JSON(data.update_orders.unpaid_orders[index]);

                            // Other idea would be to list the fields to change and do that manually here
                            
                            // if order is current order, then re-render it or product screen or whatever
                            // Might auto render due to changes, so this might not be needed
                            // if (this.env.pos.get_order().uid == order.uid){
                            //     order.render();
                            // }
                        }
                        else{
                            console.log("Sparing order");
                        }
                    }
                    console.log(data.new_orders);
                    console.log(this.env.pos.get_order_list().length);
                    // console.log(JSON.stringify(data.new_orders));
                    this.env.pos.import_orders(JSON.stringify(data.new_orders));
                    console.log(this.env.pos.get_order_list().length);
                    
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