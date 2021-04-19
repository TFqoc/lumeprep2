console.log("Patch dot js loaded. Test patching models.js");
odoo.define('pos_test.PatchTest', function(require) {
    'use strict';

    const { patch } = require("web.utils");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const models = require("point_of_sale.models");
    const ProductItem = require("point_of_sale.ProductItem");
    const { useListener } = require('web.custom_hooks');
    var core = require('web.core');
    var _t = core._t;


    const getMethods = (obj) => {
        let properties = new Set()
        let currentObj = obj
        do {
          Object.getOwnPropertyNames(currentObj).map(item => properties.add(item))
        } while ((currentObj = Object.getPrototypeOf(currentObj)))
        return [...properties.keys()].filter(item => typeof obj[item] === 'function')
      }

    const getLocalMethods = (obj) => Object.getOwnPropertyNames(obj).filter(item => typeof obj[item] === 'function')

    patch(ProductScreen, "log message", {
        // async _clickProduct(event) {
        //     this._super(...arguments);
        //     // do things
        //     console.log("You clicked on " + event.detail.display_name);
        //     console.log(event);
        // },
        _setValue(val){
            console.log("Set Value: \"" + val + "\"");
            if (val == 'remove'){
                // Product was deleted (or is about to be deleted)
                if (this.currentOrder.sale_order_id){
                  let order = this.currentOrder.get_selected_orderline();
                  // Tell the backend which product to remove
                  console.log("Deleting product id \""+order.product.id+"\" from sale id \""+this.currentOrder.sale_order_id+"\"");
                  this.rpc({
                    'model': 'sale.order',
                    'method': 'remove_item',
                    args: [this.currentOrder.sale_order_id, order.product.id],
                  });
                }
            }
            else{
              console.log("Updating product id \""+order.product.id+"\" from sale id \""+this.currentOrder.sale_order_id+"\" to qty: " + val);
                  this.rpc({
                    'model': 'sale.order',
                    'method': 'update_item_quantity',
                    args: [this.currentOrder.sale_order_id, order.product.id, val],
                  });
            }
            this._super(...arguments);
        },
      });

    patch(models.Orderline, "log quantity",{
      set_quantity: function(quantity, keep_price){
        this.order.assert_editable();
        if(quantity === 'remove'){
            console.log("Product about to be deleted!");
        }
        else{
          // console.log("Setting quantity to: " + quantity + " on " + this.product.display_name);
        }
        this._super(...arguments);
    },
    });

    patch(models.Order, "ensure uid",{
      initialize: function(attributes,options){
        this._super(...arguments);
        // event for when product gets added
        this.orderlines.on('add',this.onAddProduct, this);
        // Since I am making orders manually on the backend
        // this ensures that all the uids are being generated
        // from the same place.
        if (!this.uid){
          this.uid  = this.generate_unique_id();
          this.name = _.str.sprintf(_t("Order %s"), this.uid);
        }
      },
      init_from_JSON: function(json) {
        this._super(...arguments);
        if (!this.sale_order_id){
          this.sale_order_id = json.sale_order_id;
        }
      },
      onAddProduct: function(){
        let product = this.pos.get_order().get_last_orderline().product;
        console.log("Adding product id \""+product.id+"\" from sale id \""+this.pos.get_order().sale_order_id+"\"");
        this.pos.rpc({
          'model': 'sale.order',
          'method': 'add_item',
          args: [this.pos.get_order().sale_order_id, product.id, 1],
        });
      }
    });

    patch(ProductItem,"Product Click",{
      async willStart() {
        this._super(...arguments);
        useListener('click-product', this.onAddProduct);
      },
      onAddProduct({ detail: product }){
        console.log("You just added a product!");
        console.log(product); // product should have all fields from the db model that were imported into pos.
    }
    });

});