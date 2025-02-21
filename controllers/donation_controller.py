# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request, Response
import json

_logger = logging.getLogger(__name__)

class Iscapop_donation(http.Controller):

    # 📌 CREAR DONACIÓN
    @http.route('/api/iscapop/donation', type='json', auth='user', methods=['POST'])
    def create_donation(self, **kwargs):
        """
        Endpoint para realizar una donación de un ítem desde `item_detail`.
        Reduce el stock en `item_detail` y crea un registro en `iscapop.donations`.
        """
        try:
            kwargs = request.httprequest.json
            _logger.info(f"🔹 JSON recibido: {kwargs}")

            user_id = request.env.user.id  # 🔹 Usuario autenticado

            # 1️⃣ **Validar que se envíen los datos requeridos**
            required_fields = ['item_detail_id', 'stock_shared']
            missing_fields = [field for field in required_fields if field not in kwargs]

            if missing_fields:
                return {
                    "status": 400,
                    "error": f"Missing required fields: {missing_fields}"
                }

            item_detail_id = kwargs.get('item_detail_id')
            stock_to_donate = kwargs.get('stock_shared')

            # 2️⃣ **Validar que el `item_detail` existe y pertenece al usuario**
            item_detail = request.env['iscapop.item_detail'].sudo().search([
                ('id', '=', item_detail_id),
                ('create_uid', '=', user_id)  # 🔥 Solo los ítems creados por el usuario
            ], limit=1)

            if not item_detail:
                return {
                    "status": 404,
                    "error": f"Item Detail with id {item_detail_id} not found or not owned by user"
                }

            # 3️⃣ **Verificar stock suficiente**
            if stock_to_donate <= 0:
                return {
                    "status": 400,
                    "error": "Stock shared must be greater than 0"
                }

            if stock_to_donate > item_detail.stock:
                return {
                    "status": 400,
                    "error": f"Not enough stock available. Available: {item_detail.stock}"
                }

            # 4️⃣ **Reducir stock en `item_detail`**
            item_detail.sudo().write({
                'stock': item_detail.stock - stock_to_donate
            })

            # 5️⃣ **Crear la donación**
            donation = request.env['iscapop.donations'].sudo().create({
                'item_id': item_detail.item_id.id,
                'location_id': item_detail.location_id.id,
                'donated_by': user_id,
                'stock_shared': stock_to_donate,
                'reserved': False 
            })

            _logger.info(f"✅ Donación creada correctamente con ID: {donation.id}")

            # 6️⃣ **Respuesta en el formato solicitado**
            return {
                "status": 201,
                "donation": {
                    "id": donation.id,
                    "item_id": donation.item_id.id,
                    "location_id": donation.location_id.id,
                    "donation_date": str(donation.donation_date),
                    "donated_by": donation.donated_by.id,
                    "stock_shared": donation.stock_shared,
                    "reserved": donation.reserved
                },
                "item_detail": {
                    "id": item_detail.id,
                    "remaining_stock": item_detail.stock
                }
            }

        except Exception as e:
            _logger.error(f"❌ Error en create_donation: {str(e)}", exc_info=True)
            return {
                "status": 500,
                "error": str(e)
            }


    # 📌 VER DONACIONES
    @http.route(['/api/iscapop/donations', '/api/iscapop/donations/<int:donation_id>'], type='http', auth='user', methods=['GET'])
    def get_donations(self, donation_id=None, **kwargs):
        """
        Devuelve todas las donaciones realizadas por el usuario autenticado.
        Si se proporciona `donation_id`, devuelve solo esa donación.
        """
        try:
            user_id = request.env.user.id  # 🔹 Usuario autenticado

            if donation_id:
                donation = request.env['iscapop.donations'].sudo().search([
                    ('id', '=', donation_id),
                    ('donated_by', '=', user_id)  # 🔥 Solo sus propias donaciones
                ], limit=1)

                if not donation:
                    return Response(
                        json.dumps({"success": False, "error": "Donation not found"}), 
                        content_type='application/json', 
                        status=404
                    )

                data = [{
                    "id": donation.id,
                    "item": {
                        "id": donation.item_id.id,
                        "name": donation.item_id.name,
                        "description": donation.item_id.description,
                        "category_id": [donation.item_id.category_id.id, donation.item_id.category_id.name] if donation.item_id.category_id else None,
                        "full_stock": donation.item_id.full_stock,
                        "documentation": donation.item_id.documentation,
                    },
                    "location_id": [donation.location_id.id, donation.location_id.name],
                    "destination_location_id": [donation.destination_location_id.id, donation.destination_location_id.name] if donation.destination_location_id else None,
                    "stock_shared": donation.stock_shared,
                    "reserved": donation.reserved,
                    "reserved_by": [donation.reserved_by.id, donation.reserved_by.name] if donation.reserved_by else None,
                    "donated_by": [donation.donated_by.id, donation.donated_by.name] if donation.donated_by else None,
                    "donation_date": str(donation.donation_date)
                }]
            else:
                donations = request.env['iscapop.donations'].sudo().search([
                    ('donated_by', '=', user_id)  # 🔥 Solo donaciones del usuario autenticado
                ])

                data = []
                for donation in donations:
                    data.append({
                        "id": donation.id,
                        "item": {
                            "id": donation.item_id.id,
                            "name": donation.item_id.name,
                            "description": donation.item_id.description,
                            "category_id": [donation.item_id.category_id.id, donation.item_id.category_id.name] if donation.item_id.category_id else None,
                            "full_stock": donation.item_id.full_stock,
                            "documentation": donation.item_id.documentation,
                        },
                        "location_id": [donation.location_id.id, donation.location_id.name],
                        "destination_location_id": [donation.destination_location_id.id, donation.destination_location_id.name] if donation.destination_location_id else None,
                        "stock_shared": donation.stock_shared,
                        "reserved": donation.reserved,
                        "reserved_by": [donation.reserved_by.id, donation.reserved_by.name] if donation.reserved_by else None,
                        "donated_by": [donation.donated_by.id, donation.donated_by.name] if donation.donated_by else None,
                        "donation_date": str(donation.donation_date)
                    })

            return Response(
                json.dumps({"success": True, "donations": data}, default=str), 
                content_type='application/json', 
                status=200
            )

        except Exception as e:
            return Response(
                json.dumps({"success": False, "error": str(e)}), 
                content_type='application/json', 
                status=500
            )
