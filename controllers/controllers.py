# -*- coding: utf-8 -*-
# from odoo import http


# class Iscapop(http.Controller):
#     @http.route('/iscapop/iscapop', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/iscapop/iscapop/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('iscapop.listing', {
#             'root': '/iscapop/iscapop',
#             'objects': http.request.env['iscapop.iscapop'].search([]),
#         })

#     @http.route('/iscapop/iscapop/objects/<model("iscapop.iscapop"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('iscapop.object', {
#             'object': obj
#         })

