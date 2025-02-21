import logging
from odoo import http
from odoo.http import request, Response
import json

_logger = logging.getLogger(__name__)

class Iscapop_item(http.Controller):

    # 📌 OBTENER ITEMS
    @http.route(['/api/iscapop/item', '/api/iscapop/item/<int:item_id>'], type='http', auth='user', methods=['GET'])
    def get_items(self, item_id=None, **kwargs):
        """
        Devuelve los items con sus detalles de stock y ubicación.
        Si se proporciona `item_id`, se devuelve solo ese item; de lo contrario, se devuelven todos los items creados por el usuario autenticado.
        """
        try:
            user_id = request.env.user.id  # Usuario autenticado

            if item_id:
                # Buscar un único item que pertenezca al usuario
                item = request.env['iscapop.items_model'].sudo().search([
                    ('id', '=', item_id),
                    ('create_uid', '=', user_id)
                ], limit=1)
                if not item:
                    return Response(
                        json.dumps({"success": False, "error": "Item not found"}),
                        content_type='application/json',
                        status=404
                    )
                items = item
            else:
                # Buscar todos los items del usuario autenticado
                items = request.env['iscapop.items_model'].sudo().search([
                    ('create_uid', '=', user_id)
                ])

            data = []
            for item in items:
                # Utilizar la relación one2many para obtener los detalles del item
                details_list = [
                    {
                        "id": detail.id,
                        "location_id": [detail.location_id.id, detail.location_id.name] if detail.location_id else None,
                        "stock": detail.stock,
                        "stock_status": detail.stock_status,
                        "available": detail.available
                    }
                    for detail in item.item_detail_ids
                ]
                data.append({
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "category_id": [item.category_id.id, item.category_id.name] if item.category_id else None,
                    "full_stock": item.full_stock,
                    "documentation": item.documentation,
                    "details": details_list
                })

            return Response(
                json.dumps({"success": True, "items": data}, default=str),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            return Response(
                json.dumps({"success": False, "error": str(e)}),
                content_type='application/json',
                status=500
            )


    
    # 📌 ACTUALIZAR ITEM
    @http.route('/api/iscapop/item/<int:item_id>', type='json', auth='user', methods=['PUT'])
    def update_item(self, item_id, **kwargs):
        """
        Permite modificar `name`, `description`, `category_id` y `documentation`.
        Solo se pueden modificar ítems creados por el usuario autenticado.
        """
        try:
            kwargs = request.httprequest.json
            _logger.info(f"🔹 JSON recibido para actualizar item_model {item_id}: {kwargs}")

            user_id = request.env.user.id  # 🔹 Usuario autenticado

            # 1️⃣ **Buscar el `item_model` del usuario autenticado**
            item = request.env['iscapop.items_model'].sudo().search([
                ('id', '=', item_id),
                ('create_uid', '=', user_id)  # 🔥 Solo puede modificar sus propios ítems
            ], limit=1)

            if not item:
                return {
                    "status": 404,
                    "error": f"Item with id {item_id} not found or not owned by user"
                }

            # 2️⃣ **Actualizar solo los campos que se envíen**
            updates = {}

            if 'name' in kwargs:
                updates['name'] = kwargs['name']

            if 'description' in kwargs:
                updates['description'] = kwargs['description']

            if 'documentation' in kwargs:
                updates['documentation'] = kwargs['documentation']

            if 'category_id' in kwargs:
                category = request.env['iscapop.categories_model'].sudo().search([
                    ('id', '=', kwargs['category_id'])
                ], limit=1)
                if not category:
                    return {
                        "status": 400,
                        "error": f"Category with id {kwargs['category_id']} does not exist"
                    }
                updates['category_id'] = category.id

            if not updates:
                return {
                    "status": 400,
                    "error": "No valid fields to update"
                }

            # 3️⃣ **Aplicar la actualización**
            item.sudo().write(updates)

            _logger.info(f"✅ Item {item_id} actualizado correctamente")

            return {
                "status": 200,
                "message": "Item updated successfully",
                "item": {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "category_id": [item.category_id.id, item.category_id.name] if item.category_id else None,
                    "documentation": item.documentation,
                    "full_stock": item.full_stock
                }
            }

        except Exception as e:
            _logger.error(f"❌ Error en update_item: {str(e)}", exc_info=True)
            return {
                "status": 500,
                "error": str(e)
            }

    
    # 📌 ELIMINAR ITEM
    @http.route('/api/iscapop/item/<int:item_id>', type='http', auth='user', methods=['DELETE'], csrf=False)
    def delete_item(self, item_id, **kwargs):
        """
        Permite eliminar un `item_model` si pertenece al usuario autenticado.
        """
        try:
            _logger.info(f"🔹 Intentando eliminar el item con ID: {item_id}")

            user_id = request.env.user.id  # 🔹 Usuario autenticado

            # 1️⃣ **Buscar el `item_model` del usuario autenticado**
            item = request.env['iscapop.items_model'].sudo().search([
                ('id', '=', item_id),
                ('create_uid', '=', user_id)  # 🔥 Solo puede eliminar sus propios ítems
            ], limit=1)

            if not item:
                return Response(
                    json.dumps({"status": 404, "error": "Item not found or not owned by user"}), 
                    content_type='application/json', 
                    status=404
                )

            item.unlink()
            _logger.info(f"✅ Item {item_id} eliminado correctamente")

            return Response(
                json.dumps({"status": 200, "message": "Item deleted successfully"}), 
                content_type='application/json', 
                status=200
            )

        except Exception as e:
            _logger.error(f"❌ Error al eliminar item {item_id}: {str(e)}", exc_info=True)
            return Response(
                json.dumps({"status": 500, "error": str(e)}), 
                content_type='application/json', 
                status=500
            )


    # 📌 CREAR ITEM
    @http.route('/api/iscapop/item', type='json', auth='user', methods=['POST'])
    def create_item(self, **kwargs):
        """
        Crea un nuevo item y permite asociar o crear registros en item_detail.
        - Si en "details" viene un diccionario con 'id', se vincula ese item_detail existente.
        - Si no trae 'id', se crea un nuevo item_detail.
        """
        try:
            data = request.httprequest.json
            _logger.info(f"🔹 JSON recibido para crear item: {data}")

            user_id = request.env.user.id  # Usuario autenticado

            # Validar campo obligatorio 'name'
            if not data.get('name'):
                return {"status": 400, "error": "El campo 'name' es obligatorio"}

            # Validar categoría si se proporciona
            category_id = None
            if data.get('category_id'):
                category = request.env['iscapop.categories_model'].sudo().search([
                    ('id', '=', data['category_id'])
                ], limit=1)
                if not category:
                    return {
                        "status": 400,
                        "error": f"La categoría con id {data['category_id']} no existe"
                    }
                category_id = category.id

            # Preparar la lista de comandos One2many
            details_data = data.get('details', [])
            details_commands = []
            for detail_info in details_data:
                if 'id' in detail_info and detail_info['id']:
                    # El usuario quiere vincular un item_detail existente
                    existing_detail = request.env['iscapop.item_detail'].sudo().search([
                        ('id', '=', detail_info['id'])
                    ], limit=1)

                    if not existing_detail:
                        return {
                            "status": 400,
                            "error": f"El item_detail con id {detail_info['id']} no existe"
                        }

                    # (4, ID, 0) = Vincular un registro existente a la relación One2many
                    details_commands.append((4, existing_detail.id, 0))

                else:
                    # Crear un nuevo item_detail
                    new_detail_vals = {
                        "location_id": detail_info.get('location_id'),
                        "stock": detail_info.get('stock', 0),
                        "stock_status": detail_info.get('stock_status', 'available'),
                        "available": detail_info.get('available', True),
                    }

                    # (0, 0, vals) = Crear un nuevo registro en la relación One2many
                    details_commands.append((0, 0, new_detail_vals))

            # Crear el nuevo item con sus detalles
            new_item = request.env['iscapop.items_model'].sudo().create({
                "name": data.get("name"),
                "description": data.get("description"),
                "documentation": data.get("documentation"),
                "category_id": category_id,
                "item_detail_ids": details_commands,
            })

            _logger.info(f"✅ Item creado correctamente con id {new_item.id}")

            # Preparar respuesta con detalles
            details_list = []
            for detail in new_item.item_detail_ids:
                details_list.append({
                    "id": detail.id,
                    "location_id": [detail.location_id.id, detail.location_id.name] if detail.location_id else None,
                    "stock": detail.stock,
                    "stock_status": detail.stock_status,
                    "available": detail.available
                })

            return {
                "status": 200,
                "message": "Item creado exitosamente",
                "item": {
                    "id": new_item.id,
                    "name": new_item.name,
                    "description": new_item.description,
                    "category_id": [
                        new_item.category_id.id,
                        new_item.category_id.name
                    ] if new_item.category_id else None,
                    "documentation": new_item.documentation,
                    "full_stock": new_item.full_stock,
                    "details": details_list
                }
            }

        except Exception as e:
            _logger.error(f"❌ Error al crear item: {str(e)}", exc_info=True)
            return {
                "status": 500,
                "error": str(e)
            }

