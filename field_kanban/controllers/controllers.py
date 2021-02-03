# -*- coding: utf-8 -*-
# from odoo import http


# class FieldKanban(http.Controller):
#     @http.route('/field_kanban/field_kanban/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/field_kanban/field_kanban/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('field_kanban.listing', {
#             'root': '/field_kanban/field_kanban',
#             'objects': http.request.env['field_kanban.field_kanban'].search([]),
#         })

#     @http.route('/field_kanban/field_kanban/objects/<model("field_kanban.field_kanban"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('field_kanban.object', {
#             'object': obj
#         })
