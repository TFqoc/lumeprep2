console.log("Loaded Project kanban lume clickthrough");
odoo.define('lume_sales.project_kanban_custom', function (require) {
    'use strict';
    
    var ProjectKanbanController = require('project.project_kanban');
    // var KanbanView = require('web.KanbanView');
    // var KanbanColumn = require('web.KanbanColumn');
    // var view_registry = require('web.view_registry');
    var KanbanRecord = require('web.KanbanRecord');

    KanbanRecord.include({
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @override
         * @private
         */
        // YTI TODO: Should be transformed into a extend and specific to project
        _openRecord: function () {
            if (this.modelName === 'project.task' && this.recordData.sales_order) {
                this.do_action({
                        type: 'ir.actions.act_window',
                        view_type: 'form',
                        view_mode: 'form',
                        res_model: 'sale.order',
                        // 'target': 'new', #for popup style window
                        res_id: this.recordData.sales_order,
                });
            } else {
                this._super.apply(this, arguments);
            }
        },
    });
    
    ProjectKanbanController.include({

    });
    
    return ProjectKanbanController;
    });
    