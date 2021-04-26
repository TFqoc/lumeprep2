console.log("Patch dot js loaded. Test patching models.js");
odoo.define('lume_pos.PatchTest', function(require) {
    'use strict';

    const { patch } = require("web.utils");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const ReceiptScreen = require("point_of_sale.ReceiptScreen");
    const TicketButton = require("point_of_sale.TicketButton");
    const models = require("point_of_sale.models");
    const ProductItem = require("point_of_sale.ProductItem");
    const ActionpadWidget = require("point_of_sale.ActionpadWidget");
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const { posbus } = require('point_of_sale.utils');
    var core = require('web.core');
    var _t = core._t;


    // const getMethods = (obj) => {
    //     let properties = new Set()
    //     let currentObj = obj
    //     do {
    //       Object.getOwnPropertyNames(currentObj).map(item => properties.add(item))
    //     } while ((currentObj = Object.getPrototypeOf(currentObj)))
    //     return [...properties.keys()].filter(item => typeof obj[item] === 'function')
    //   }

    // const getLocalMethods = (obj) => Object.getOwnPropertyNames(obj).filter(item => typeof obj[item] === 'function')

    patch(ProductScreen, "log message", {
        // async _clickProduct(event) {
        //     this._super(...arguments);
        //     // do things
        //     console.log("You clicked on " + event.detail.display_name);
        //     console.log(event);
        // },
        _setValue(val){
            // console.log("Set Value: \"" + val + "\"");
            let order = this.currentOrder.get_selected_orderline();
            if (!order.updating){
              if (val == 'remove'){
                  // Product was deleted (or is about to be deleted)
                  if (this.currentOrder.sale_order_id){
                    // Tell the backend which product to remove
                    // console.log("Deleting product id \""+order.product.id+"\" from sale id \""+this.currentOrder.sale_order_id+"\"");
                    this.rpc({
                      'model': 'sale.order',
                      'method': 'remove_item',
                      args: [this.currentOrder.sale_order_id, order.product.id],
                    });
                  }
              }
              else{
                // console.log("Updating product id \""+order.product.id+"\" from sale id \""+this.currentOrder.sale_order_id+"\" to qty: " + val);
                    this.rpc({
                      'model': 'sale.order',
                      'method': 'update_item_quantity',
                      args: [this.currentOrder.sale_order_id, order.product.id, val],
                    });
              }
            }
            this._super(...arguments);
        },
        // Override previous method
        _onClickPay(){
          if (this.env.pos.get_order().state != 'ready'){
            this.showPopup('ErrorPopup', {
              title: this.env._t('Order not Picked!'),
              body: this.env._t('This order has not been picked by the back room yet!'),
            });
          }
          else{
            this.showScreen('PaymentScreen');
          }
        }
      });

    patch(models.Orderline, "log quantity",{
      set_quantity: function(quantity, keep_price){
        this.order.assert_editable();
        if(quantity === 'remove'){
            // console.log("Product about to be deleted!");
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
        // if (!this.uid || isNaN(this.uid)){
        //   this.sequence_number = this.pos.pos_session.sequence_number++;
        //   this.uid  = this.generate_unique_id();
        //   this.name = _.str.sprintf(_t("Order %s"), this.uid);
        // }
      },
      init_from_JSON: function(json) {
        this._super(...arguments);
        if (!this.sale_order_id){
          this.sale_order_id = json.sale_order_id;
          // console.log("Added id: " + this.sale_order_id + " to initialized order");
        }
        if (!this.uid){
          this.sequence_number = json.name;
          this.uid = this.generate_unique_id();
          this.name = _.str.sprintf(_t("Order %s"), this.uid);
        }
      },
      onAddProduct: function(){
        if (!this.pos.get_order().updating){
          let product = this.pos.get_order().get_last_orderline().product;
          // console.log("Adding product id \""+product.id+"\" from sale id \""+this.pos.get_order().sale_order_id+"\"");
          this.pos.rpc({
            'model': 'sale.order',
            'method': 'add_item',
            args: [this.pos.get_order().sale_order_id, product.id, 1],
          });
        }
      }
    });

    patch(models.PosModel, "No load json", {
      load_orders: function(){},
      _load_orders: function(){},
    });

    patch(PaymentScreen, "update backend SO",{
      _finalizeValidation: async function(isForceValidate) {
          await this._super(...arguments);
          this.rpc({
            'model': 'sale.order',
            'method': 'finalize',
            args: [this.env.pos.get_order().sale_order_id],
          });
      }
  });

    patch(ProductItem,"Product Click",{
      async willStart() {
        this._super(...arguments);
        useListener('click-product', this.onAddProduct);
      },
      onAddProduct({ detail: product }){
        // console.log("You just added a product!");
        // console.log(product); // product should have all fields from the db model that were imported into pos.
    }
    });
    
    patch(TicketButton,"Re-render trigger", {
       mounted(){
          this._super(...arguments);
          posbus.on('re-render', this, this.render);
       } ,
    });

    patch(ActionpadWidget, "disable payment button", {
      async render(){
        await this._super(...arguments);
        if (this.env.pos.get_order().state == 'ready'){
          $("#PaymentButton").removeClass("disabled");
        }
        else{
          $("#PaymentButton").addClass("disabled");
        }
        console.log("Rendering Actionpad");
      }
    });

    const PatchedReceiptScreen = (ReceiptScreen) => {
      class PatchedReceiptScreen extends ReceiptScreen {
        get nextScreen(){
          return {name: 'TicketScreen'};
        }
      }
      return PatchedReceiptScreen;
    }
    Registries.Component.extend(ReceiptScreen, PatchedReceiptScreen);
  // patch(ReceiptScreen, "next button", {
  //   orderDone: function() {
  //     this.currentOrder.finalize();
  //     //const { name, props } = 'name';
  //     this.showScreen('TicketScreen');
  // }
  // });

    

});