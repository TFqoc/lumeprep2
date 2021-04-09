# -*- coding: utf-8 -*-
# from odoo import http


# class DlReader(http.Controller):
#     @http.route('/dl__reader/dl__reader/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dl__reader/dl__reader/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dl__reader.listing', {
#             'root': '/dl__reader/dl__reader',
#             'objects': http.request.env['dl__reader.dl__reader'].search([]),
#         })

#     @http.route('/dl__reader/dl__reader/objects/<model("dl__reader.dl__reader"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dl__reader.object', {
#             'object': obj
#         })
