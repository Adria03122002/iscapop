import logging
from odoo import http
from odoo.http import request, Response
import json

_logger = logging.getLogger(__name__)

class Iscapop_item_detail(http.Controller):
    
    # 📌 OBTENER DETALLES DE ITEMS
    @http.route(['/api/iscapop/item_detail', '/api/iscapop/item_detail/<int:item_detail_id>'], type='http', auth='user', methods=['GET'])
    def get_item_details(self, item_detail_id=None, **kwargs):
        """
        Devuelve los item_detail relacionados a los ítems creados por el usuario autenticado.
        """
        try:
            user_id = request.env.user.id

            domain = [('item_id.create_uid', '=', user_id)]
            if item_detail_id:
                domain.append(('id', '=', item_detail_id))
                item_detail = request.env['iscapop.item_detail'].sudo().search(domain, limit=1)
                if not item_detail:
                    return Response(
                        json.dumps({"success": False, "error": "Item detail not found or not accessible by the user"}), 
                        content_type='application/json',
                        status=404
                    )
                data = item_detail.read(['id', 'item_id', 'location_id', 'stock', 'stock_status', 'available'])
            else:
                item_details = request.env['iscapop.item_detail'].sudo().search(domain)
                data = item_details.read(['id', 'item_id', 'location_id', 'stock', 'stock_status', 'available'])

            return Response(
                json.dumps({"success": True, "item_details": data}, default=str),
                content_type='application/json',
                status=200
            )
        except Exception as e:
            return Response(
                json.dumps({"success": False, "error": str(e)}),
                content_type='application/json',
                status=500
            )
