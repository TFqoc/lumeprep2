# -*- coding: utf-8 -*-
# from odoo import http


# class ContactMod(http.Controller):
#     @http.route('/contact_mod/contact_mod/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/contact_mod/contact_mod/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('contact_mod.listing', {
#             'root': '/contact_mod/contact_mod',
#             'objects': http.request.env['contact_mod.contact_mod'].search([]),
#         })

#     @http.route('/contact_mod/contact_mod/objects/<model("contact_mod.contact_mod"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('contact_mod.object', {
#             'object': obj
#         })
