console.log("Many2OneAvatarPartner has been loaded");
odoo.define('lume.Many2OneAvatarPartner', function (require) {
    "use strict";

    const fieldRegistry = require('web.field_registry');
    const { Many2OneAvatar } = require('web.relational_fields');

    const { Component } = owl;

    const Many2OneAvatarPartner = Many2OneAvatar.extend({
        events: Object.assign({}, Many2OneAvatar.prototype.events, {
            'click .o_m2o_avatar': '_onAvatarClicked',
        }),
        // This widget is only supported on many2ones pointing to 'res.users'
        supportedModels: ['res.partner'],

        init() {
            this._super(...arguments);
            if (!this.supportedModels.includes(this.field.relation)) {
                throw new Error(`This widget is only supported on many2one fields pointing to ${JSON.stringify(this.supportedModels)}`);
            }
            if (this.mode === 'readonly') {
                this.className += ' o_clickable_m2o_avatar';
            }
        },

        //----------------------------------------------------------------------
        // Handlers
        //----------------------------------------------------------------------

        /**
         * When the avatar is clicked, open a DM chat window with the
         * corresponding user.
         *
         * @private
         * @param {MouseEvent} ev
         */
        async _onAvatarClicked(ev) {
            ev.stopPropagation(); // in list view, prevent from opening the record
            //const env = Component.env;
            //await env.messaging.openChat({ userId: this.value.res_id });
        }
    });

    const KanbanMany2OneAvatarPartner = Many2OneAvatarPartner.extend({
        _template: 'mail.KanbanMany2OneAvatarUser',
    });

    fieldRegistry.add('many2one_avatar_partner', Many2OneAvatarPartner);
    fieldRegistry.add('kanban.many2one_avatar_partner', KanbanMany2OneAvatarPartner);

    return {
        Many2OneAvatarPartner,
        KanbanMany2OneAvatarPartner,
    };

});