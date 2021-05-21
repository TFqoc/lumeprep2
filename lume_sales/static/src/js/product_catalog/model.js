odoo.define('lume_sales.ProductKanbanModel', function (require) {
    "use strict";
    
    const KanbanModel = require('web.KanbanModel');
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
            if (this.modelName === 'product.product') {
                // TODO open product details
                return;
            }
            else{
                this._super.apply(this, arguments);
            }
         },
        });
    
    return KanbanModel.extend({
    
        /**
         * Handles the field `lpc_quantity`.
         * Saving this field cannot be done as any regular field
         * since it might require additional actions from the user.
         * e.g. set product serial numbers
         * @param {string} recordID
         * @param {object} options
         * @returns {Promise<string>} Changed fields
         * @override
         */
        async save(recordID, options) {
            const record = this.localData[recordID];
            const changes = record._changes;
            if (changes.lpc_quantity !== undefined) {
                const quantity = changes.lpc_quantity;
                delete changes.lpc_quantity;
                const changedFields = await Promise.all([
                    this._super(...arguments),
                    this._saveLPCQuantity(record, quantity),
                ]);
                await this._fetchRecord(record);
                return changedFields.flat();
            }
            return this._super(...arguments);
        },
    
        /**
         * Saves the LPC quantity.
         * @param {object} record
         * @param {number} quantity
         * @returns {Promise<string>} changed field
         */
        async _saveLPCQuantity(record, quantity) {
            const action = await this._rpc({
                model: 'product.product',
                method: 'set_lpc_quantity',
                args: [record.data.id, quantity],
                context: record.getContext(),
            });
            if (typeof action === 'object') {
                await new Promise((resolve) => {
                    this.do_action(action, { on_close: resolve });
                });
            }
            return ['lpc_quantity'];
        },
    
    });
    
    });
    