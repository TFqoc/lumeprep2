console.log("Progress bar loading 1");
odoo.define('lume_sales.KanbanProgressBar', function (require) {
    'use strict';

    var ProgressBar = require('web.KanbanColumnProgressBar');

    ProgressBar.include({
        init: function (parent, options, columnState) {
            this.colors = _.extend({}, columnState.progressBarValues.colors, {
                store: 'steelblue',
                online: 'goldenrod',
                curb: 'firebrick',
                delivery: 'mediumseagreen',
            });
            this._super.apply(this, arguments);
        }
    });

    return ProgressBar;

});