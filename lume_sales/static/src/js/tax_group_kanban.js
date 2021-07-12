// console.log("Loaded lame section and note");
odoo.define('lume_sales.tax_group_kanban', function (require) {
"use strict";
var TaxGroup = require('account.tax_group');
// var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
var fieldRegistry = require('web.field_registry');

// We create a custom widget because this is the cleanest way to do it:
var TaxGroupKanban = TaxGroup.extend({
    _render: function () {
        var self = this;
        // Display the pencil and allow the event to click and edit only on purchase that are not posted and in edit mode.
        // since the field is readonly its mode will always be readonly. Therefore we have to use a trick by checking the 
        // formRenderer (the parent) and check if it is in edit in order to know the correct mode.
        var displayEditWidget = self._isPurchaseDocument() && this.record.data.state === 'draft' && this.getParent().mode === 'edit';
        this.$el.html($(QWeb.render('LumeTaxGroupKanbanTemplate', {
            lines: self.value,
            displayEditWidget: displayEditWidget,
        })));
    },
});

fieldRegistry.add('tax_group_kanban', TaxGroupKanban);

return TaxGroupKanban;
});
