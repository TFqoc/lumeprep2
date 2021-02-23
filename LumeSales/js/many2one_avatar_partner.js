console.log("Many2OneAvatarPartner has been loaded");
odoo.define('lume.Many2OneAvatarPartner', ['mail.Many2OneAvatarUser','web.field_registry'], function (require) {
    "use strict";

    const fieldRegistry = require('web.field_registry');
    const { Many2OneAvatarUser } = require('mail.Many2OneAvatarUser');

    const Many2OneAvatarPartner = Many2OneAvatarUser.extend({
        // This widget is only supported on many2ones pointing to 'res.users'
        supportedModels: ['res.users','res.partner'],
    });

    // const KanbanMany2OneAvatarPartner = Many2OneAvatarPartner.extend({
    //     _template: 'mail.KanbanMany2OneAvatarUser',
    // });

    // fieldRegistry.add('many2one_avatar_partner', Many2OneAvatarPartner);
    // fieldRegistry.add('kanban.many2one_avatar_partner', KanbanMany2OneAvatarPartner);

    // return {
    //     Many2OneAvatarPartner,
    //     KanbanMany2OneAvatarPartner,
    // };
    return Many2OneAvatarPartner;

});