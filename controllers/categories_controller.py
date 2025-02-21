# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request, Response
import json

_logger = logging.getLogger(__name__)

class Iscapop_Categories(http.Controller):

    # CATEGORÍAS - GET (Todas o una en específico)
    @http.route(['/api/iscapop/categories', '/api/iscapop/categories/<int:category_id>'], type='http', auth='user', methods=['GET'])
    def get_categories(self, category_id=None, **kwargs):
        try:
            centro_id = request.env.user.id  # 🔹 Filtrar por el ID del usuario autenticado

            if category_id:
                # 🔹 Buscar UNA categoría específica
                category = request.env['iscapop.categories_model'].sudo().search([
                    ('id', '=', category_id),
                    ('create_uid', '=', centro_id)
                ], limit=1)

                if not category:
                    return Response(
                        json.dumps({"success": False, "error": "Category not found"}), 
                        content_type='application/json', 
                        status=404
                    )

                data = category.read(['id', 'name', 'description', 'child_ids', 'father_id', 'item_ids'])
            else:
                # 🔹 Buscar TODAS las categorías del usuario autenticado
                categories = request.env['iscapop.categories_model'].sudo().search([
                    ('create_uid', '=', centro_id)
                ])
                data = categories.read(['id', 'name', 'description', 'child_ids', 'father_id', 'item_ids'])

            return Response(
                json.dumps({"success": True, "categories": data}, default=str), 
                content_type='application/json', 
                status=200
            )

        except Exception as e:
            return Response(
                json.dumps({"success": False, "error": str(e)}), 
                content_type='application/json', 
                status=500
            )

    # CATEGORÍAS - DELETE
    @http.route('/api/iscapop/categories/<int:category_id>', type='http', auth='user', methods=['DELETE'], csrf=False)
    def delete_category(self, category_id):
        try:
            centro_id = request.env.user.id  # 🔹 Obtener el ID del usuario autenticado

            _logger.info(f"🔹 Intentando eliminar la categoría con ID: {category_id}")

            # 1️⃣ Buscar la categoría que pertenece al usuario autenticado
            category = request.env['iscapop.categories_model'].sudo().search([
                ('id', '=', category_id),
                ('create_uid', '=', centro_id)
            ], limit=1)

            if not category:
                _logger.warning(f"❌ No se encontró la categoría con ID {category_id} para el usuario {centro_id}")
                return Response(
                    json.dumps({"status": 404, "error": "Category not found or not owned by user"}), 
                    content_type='application/json', 
                    status=404
                )

            # 2️⃣ Buscar y eliminar los `items` relacionados con la categoría
            items = request.env['iscapop.items_model'].sudo().search([('category_id', '=', category_id)])
            if items:
                _logger.info(f"🔹 Eliminando {len(items)} items asociados a la categoría {category_id}")
                items.unlink()

            # 3️⃣ Eliminar la categoría después de eliminar los items
            _logger.info(f"🔹 Eliminando la categoría con ID: {category_id}")
            category.unlink()
            _logger.info(f"✅ Categoría eliminada correctamente")

            return Response(
                json.dumps({"status": 200, "message": "Category deleted successfully"}), 
                content_type='application/json', 
                status=200
            )
        except Exception as e:
            _logger.error(f"❌ Error al eliminar categoría {category_id}: {str(e)}", exc_info=True)
            return Response(
                json.dumps({"status": 500, "error": str(e)}), 
                content_type='application/json', 
                status=500
            )

    # CATEGORÍAS - PUT (Actualizar)
    @http.route('/api/iscapop/categories/<int:category_id>', type='json', auth='user', methods=['PUT'])
    def update_category(self, category_id, **kwargs):
        """
        Endpoint para actualizar una categoría (`categories_model`).
        """
        try:
            centro_id = request.env.user.id  # 🔹 Obtener el ID del usuario autenticado
            kwargs = request.httprequest.json  # 🔹 Asegura que Odoo procese el JSON correctamente

            _logger.info(f"🔹 JSON recibido para actualizar categoría {category_id}: {kwargs}")

            # 1️⃣ **Buscar la categoría del usuario autenticado**
            category = request.env['iscapop.categories_model'].sudo().search([
                ('id', '=', category_id),
                ('create_uid', '=', centro_id)
            ], limit=1)

            if not category:
                return {
                    "status": 404,
                    "error": f"Category with id {category_id} not found or not owned by user"
                }

            # 2️⃣ **Actualizar solo los campos que se envíen**
            updates = {}

            if 'name' in kwargs:
                updates['name'] = kwargs['name']

            if 'description' in kwargs:
                updates['description'] = kwargs['description']

            if not updates:
                return {
                    "status": 400,
                    "error": "No valid fields to update"
                }

            # 3️⃣ **Aplicar la actualización**
            category.sudo().write(updates)

            _logger.info(f"✅ Categoría {category_id} actualizada correctamente")

            # 4️⃣ **Construir la respuesta en el formato solicitado**
            return {
                "status": 200,
                "message": "Category updated successfully",
                "category": {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description
                }
            }

        except Exception as e:
            _logger.error(f"❌ Error en update_category: {str(e)}", exc_info=True)
            return {
                "status": 500,
                "error": str(e)
            }
