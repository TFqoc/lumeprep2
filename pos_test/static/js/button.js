odoo.define('pos_test.button', function (require) {
    "use strict";
    
    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    
    //Custom Code
    var CustomButton = screens.ActionButtonWidget.extend({
    template: 'Chrome',
    events: {
        'click button': 'button_click',
        },
    button_click: function(){
    
    var self = this;
    
    self.custom_function();
    
    },
    
    custom_function: function(){
    
    console.log('Hi I am button click of CustomButton');
    
    }
    
    });
    
    screens.define_action_button({
    
    'name': 'custom_button',
    
    'widget': CustomButton,
    
    });

    return CustomButton;    
});