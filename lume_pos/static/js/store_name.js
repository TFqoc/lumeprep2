console.log("Store Name 1");
odoo.define('lume_pos.StoreName', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class StoreName extends PosComponent {
        get store_name(){
            // In case the pos or config is not loaded yet
            try{
                return this.env.pos.config.project_id[1];
            }
            catch(err){
                return "Loading...";
            }
        }
    }
    StoreName.template = 'StoreName';

    Registries.Component.add(StoreName);

    return StoreName;
});
