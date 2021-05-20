console.log("Store Name 1");
odoo.define('lume_pos.StoreName', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class StoreName extends PosComponent {
        get store_name(){
            return this.pos.config.project_id[1];
        }
    }
    StoreName.template = 'StoreName';

    Registries.Component.add(StoreName);

    return StoreName;
});
