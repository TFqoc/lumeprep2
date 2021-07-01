odoo.define('metrc_base.MetrcSystrayMenu', function (require) {
    "use strict";
    
    var core = require('web.core');
    var session = require('web.session');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var QWeb = core.qweb;
    
    const { Component } = owl;
    
    /**
     * Menu item appended in the systray part of the navbar, redirects to the next
     * activities of all app
     */
    var MetrcSystrayMenu = Widget.extend({
        name: 'metrc_api_status',
        template:'metrc_base.MetrcSystrayMenu',
        start: function () {
            if (this.is_metrc_user) {
                this._updateMetrcApiStatus();
            };
            return this._super();
        },
        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return session.user_has_group('metrc_base.group_metrc_user').then(function (has_group) {
                    self.is_metrc_user = has_group;
                });
            });
        },
        //--------------------------------------------------
        // Private
        //--------------------------------------------------
        /**
         * Make RPC and get current user's activity details
         * @private
         */
         _updateMetrcApiStatus: function () {
            var self = this;
            return self._rpc({
                model: 'ir.logging',
                method: 'get_api_status',
                args: [],
                kwargs: {context: session.user_context},
            }).then(function (data) {
                console.log(data);
                self.$el.replaceWith(QWeb.render('metrc_base.MetrcSystrayMenu', data));
            });
        },
    });
    
    SystrayMenu.Items.push(MetrcSystrayMenu);
    
    return MetrcSystrayMenu;
    
    });