console.log("Loaded lame section and note");
odoo.define('lume_sales.so_section_and_note', function (require) {
"use strict";
var SectionAndNote = require('account.section_and_note_backend');
// var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
var fieldRegistry = require('web.field_registry');

// We create a custom widget because this is the cleanest way to do it:
var SoSectionAndNoteFieldOne2Many = SectionAndNote.extend({
    /**
     * @override
     */
     _renderButtons: function () {
        // We don't want to render any buttons with this widget
    },
});

fieldRegistry.add('so_section_and_note', SoSectionAndNoteFieldOne2Many);

return SoSectionAndNoteFieldOne2Many;
});
