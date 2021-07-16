console.log("Progress bar loading 1");
odoo.define('lume_sales.KanbanProgressBar', function (require) {
    'use strict';

    var ProgressBar = require('web.KanbanColumnProgressBar');

    ProgressBar.include({
        init: function (parent, options, columnState) {
            this.colors = _.extend({}, columnState.progressBarValues.colors, {
                // These colors got changed in the scss file, so these names are legacy now
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