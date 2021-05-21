console.log("UpdateOrders dot js loaded. 2");
odoo.define('lume_pos.UpdateOrders', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { posbus } = require('point_of_sale.utils');
    const { useRef } = owl.hooks;
    
    class UpdateOrders extends PosComponent {
        constructor(){
            super(...arguments);
            
        }
        mounted() {
            this.getter = setInterval(this.getOrders.bind(this), 10000);
        }
        async willStart(){
            // destroy all current orders
            for (let order of this.env.pos.get_order_list()){
                order.destroy();
                // console.log("Destroying old order");
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
                        // console.log("Adding Linked Order");
                    }
                }
                this.rpc({
                    'model': 'sale.order',
                    'method': 'get_orders',
                    args: [linked_sale_order_ids, this.env.pos.pos_session.id, this.env.pos.user.id, this.env.pos.db.partner_sorted],
                    // Pass session_id, session object has reference to config object
                }).then((result) => {
                    // delete the ones that are outdated
                    console.log(this.env.pos);
                    var data = JSON.parse(result);
                    console.log(data.new_customers);
                    for (let order of this.env.pos.get_order_list()){
                        if (data.old_orders.includes(order.sale_order_id)){
                            order.destroy();
                            // console.log("Deleting order");
                        }
                        else if (data.update_orders.unpaid_orders.some(e => e.sale_order_id == order.sale_order_id)){
                            // Add updated data
                            var index = data.update_orders.unpaid_orders.findIndex((el) => el.sale_order_id == order.sale_order_id);
                            
                            order.updating = true;
                            // Remove all old lines
                            var orderlines = order.orderlines.models;
                            while (orderlines.length > 0){
                                order.remove_orderline(orderlines[0]);
                                // console.log("Removing a line");
                            }
                            // use json to add new lines and update order values
                            order.init_from_JSON(data.update_orders.unpaid_orders[index]);
                            order.updating = false;

                            if (order == this.env.pos.get_order()){// If order is current order
                                posbus.trigger('updated_order');
                            }
                        }
                        else{
                            // console.log("Sparing order");
                        }
                    }
                    console.log(data.update_orders);
                    this.env.pos.db.add_partners(data.new_customers.new_customers);

                    // console.log(this.env.pos.get_order_list().length);
                    // console.log(JSON.stringify(data.new_orders));
                    this.env.pos.import_orders(JSON.stringify(data.new_orders));
                    // console.log(this.env.pos.get_order_list().length);
                    
                    // console.log("re-rendering ticket button");
                    posbus.trigger('re-render');
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