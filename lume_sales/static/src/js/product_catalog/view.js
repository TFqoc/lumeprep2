odoo.define('lume_sales.ProductKanbanView', function (require) {
    "use strict";
    
    const KanbanView = require('web.KanbanView');
    const KanbanModel = require('lume_sales.ProductKanbanModel');
    const KanbanRenderer = require('lume_sales.ProductKanbanRenderer');
    const viewRegistry = require('web.view_registry');
    
    const ProductKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Model: KanbanModel,
            Renderer: KanbanRenderer,
        }),
    });
    
    viewRegistry.add('lpc_product_kanban', ProductKanbanView);
    
    });
    