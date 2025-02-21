# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request, Response
import json

_logger = logging.getLogger(__name__)

class Iscapop(http.Controller):
    @http.route('/iscapop/iscapop', auth='public')
    def index(self, **kw):
        return "Hello, world"

    
    @http.route('/api/iscapop/move_items', type='json', auth='user', methods=['PUT'])
    def move_items(self, **kwargs):
        """
        Mueve múltiples `item_detail` a una nueva ubicación.
        Se debe proporcionar:
        - `item_detail_ids`: Lista de IDs de `item_detail` a mover.
        - `new_location_id`: ID de la nueva ubicación.
        """
        try:
            kwargs = request.httprequest.json  # 🔹 Asegura que Odoo procese el JSON correctamente
            _logger.info(f"🔹 JSON recibido para mover múltiples items: {kwargs}")

            # 1️⃣ **Validar que se envíen los datos requeridos**
            if 'item_detail_ids' not in kwargs or 'new_location_id' not in kwargs:
                return {
                    "status": 400,
                    "error": "Missing required fields: 'item_detail_ids' and 'new_location_id'"
                }

            item_detail_ids = kwargs['item_detail_ids']
            new_location_id = kwargs['new_location_id']

            if not isinstance(item_detail_ids, list) or not all(isinstance(i, int) for i in item_detail_ids):
                return {
                    "status": 400,
                    "error": "'item_detail_ids' must be a list of integers"
                }

            if not isinstance(new_location_id, int):
                return {
                    "status": 400,
                    "error": "'new_location_id' must be an integer"
                }

            # 🔹 Obtener el usuario autenticado
            user_id = request.env.user.id

            # 2️⃣ **Validar que todos los `item_detail` existen y pertenecen al usuario**
            items_to_move = request.env['iscapop.item_detail'].sudo().search([
                ('id', 'in', item_detail_ids),
                ('create_uid', '=', user_id)  # 🔥 Filtrar solo los creados por el usuario
            ])

            if not items_to_move or len(items_to_move) != len(item_detail_ids):
                return {
                    "status": 404,
                    "error": "One or more item_detail_ids not found or do not belong to the user"
                }

            # 3️⃣ **Validar que la nueva ubicación existe y pertenece al usuario**
            new_location = request.env['iscapop.locations_model'].sudo().search([
                ('id', '=', new_location_id),
                ('create_uid', '=', user_id)  # 🔥 Solo permitir ubicaciones del usuario
            ], limit=1)

            if not new_location:
                return {
                    "status": 404,
                    "error": f"Location with id {new_location_id} not found or not owned by the user"
                }

            # 4️⃣ **Actualizar la ubicación de los `item_detail`**
            items_to_move.sudo().write({'location_id': new_location_id})

            _logger.info(f"✅ {len(items_to_move)} items movidos a la nueva ubicación {new_location_id}")

            return {
                "status": 200,
                "message": "Items moved successfully",
                "moved_items": [{
                    "id": item.id,
                    "item_id": [item.item_id.id, item.item_id.name],
                    "new_location_id": [item.location_id.id, item.location_id.name],
                    "stock": item.stock,
                    "stock_status": item.stock_status
                } for item in items_to_move]
            }

        except Exception as e:
            _logger.error(f"❌ Error en move_items: {str(e)}", exc_info=True)
            return {
                "status": 500,
                "error": str(e)
            }
