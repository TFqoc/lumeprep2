console.log("Loaded Project kanban lume clickthrough");
odoo.define('lume_sales.project_kanban_custom', function (require) {
    'use strict';
    
    var ProjectKanbanController = require('project.project_kanban');
    var KanbanRecord = require('web.KanbanRecord');

    KanbanRecord.include({
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @override
         * @private
         */
         _openRecord: function () {
            // console.log("Calling _openRecord");
            // console.log(this.recordData);
            if (this.modelName === 'project.task') {
                var self = this;
                var superfun = this._super.bind(this);
                this._rpc({
                    model: 'project.task',
                    method: 'search_read',
                    domain: [
                        ['id', '=', this.recordData.id]
                    ],
                }).then(function (result) {
                    let sale_order = result[0].sales_order[0];
                    // console.log("doing action");
                    // console.log(sale_order);
                    if (sale_order){
                        self.do_action({
                            type: 'ir.actions.act_window',
                            views: [[false, 'form']],
                            res_model: 'sale.order',
                            res_id: sale_order,
                            flags: {mode: 'edit'},
                        });
                    }
                    else{
                        // console.log("Calling superfun");
                        superfun.apply(self, arguments);
                    }
                });
                
            } else {
                console.log("Calling super");
                this._super.apply(this, arguments);
            }
        },
        // _openRecord: function () {
        //     if (this.modelName === 'project.task' && this.recordData.sales_order) {
        //         this.do_action({
        //                 type: 'ir.actions.act_window',
        //                 view_type: 'form',
        //                 view_mode: 'form',
        //                 res_model: 'sale.order',
        //                 // 'target': 'new', #for popup style window
        //                 res_id: this.recordData.sales_order,
        //         });
        //     } else {
        //         this._super.apply(this, arguments);
        //     }
        // },
    });
    
    return KanbanRecord;
    });
    