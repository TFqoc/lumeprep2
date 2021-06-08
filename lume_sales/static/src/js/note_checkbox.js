console.log("Checkbox widget has been loaded 10");
odoo.define('lume_sales.note_checkbox', function (require) {
    "use strict";

    var fieldRegistry = require('web.field_registry');
    var { FavoriteWidget } = require('web.basic_fields');

    var NoteCheckbox = FavoriteWidget.extend({
        _render: function () {
            let checked = this.value ? 'checked' : '';
            var template = `<a href="#"><input type="checkbox" style="transform : scale(3);margin-top: 11px;margin-right:13px;" ${checked}/></a>`;
            this.$el.empty().append(template);
        },
        _setFavorite: function (event) {
            this._super.apply(this, arguments);
            console.log(this.$el);
        },
    });

    fieldRegistry.add('note_checkbox', NoteCheckbox);

});
