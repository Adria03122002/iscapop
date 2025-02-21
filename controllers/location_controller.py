import logging
from odoo import http
from odoo.http import request, Response
import json

_logger = logging.getLogger(__name__)

class Iscapop_location(http.Controller):

    # 📌 OBTENER UBICACIONES
    @http.route(['/api/iscapop/location', '/api/iscapop/location/<int:location_id>'], type='http', auth='user', methods=['GET'])
    def get_locations(self, location_id=None, **kwargs):
        """
        Devuelve todas las ubicaciones creadas por el usuario autenticado.
        Si se proporciona `location_id`, devuelve solo esa ubicación.
        """
        try:
            user_id = request.env.user.id  # 🔹 Usuario autenticado

            if location_id:
                # 🔹 Buscar UNA ubicación específica creada por el usuario autenticado
                locations = request.env['iscapop.locations_model'].sudo().search([
                    ('id', '=', location_id),
                    ('create_uid', '=', user_id)  # 🔥 Solo ubicaciones creadas por el usuario autenticado
                ], limit=1)

                if not locations:
                    return Response(
                        json.dumps({"success": False, "error": "Location not found or does not belong to the user"}), 
                        content_type='application/json', 
                        status=404
                    )
            else:
                # 🔹 Buscar TODAS las ubicaciones creadas por el usuario autenticado
                locations = request.env['iscapop.locations_model'].sudo().search([
                    ('create_uid', '=', user_id)
                ])

            # 🔹 Datos a devolver
            data = locations.read(['id', 'name', 'description', 'location_type', 'item_detail_ids'])
            return Response(json.dumps({"success": True, "locations": data}, default=str), content_type='application/json', status=200)

        except Exception as e:
            return Response(json.dumps({"success": False, "error": str(e)}), content_type='application/json', status=500)
        

    # 📌 CREAR UBICACIÓN
    @http.route('/api/iscapop/location', type='json', auth='user', methods=['POST'])
    def create_location(self, **kwargs):
        """
        Endpoint para crear una nueva ubicación en `iscapop.locations_model`
        La ubicación se registra con `create_uid` igual al usuario autenticado.
        """
        try:
            kwargs = request.httprequest.json 
            _logger.info(f"🔹 JSON recibido: {kwargs}")

            # 1️⃣ **Validar que se envíen los datos requeridos**
            required_fields = ['name', 'location_type']
            missing_fields = [field for field in required_fields if field not in kwargs]

            if missing_fields:
                return {
                    "status": 400,
                    "error": f"Missing required fields: {missing_fields}"
                }

            # 2️⃣ **Validar que `location_type` sea válido**
            valid_location_types = ['classroom', 'warehouse']
            location_type = kwargs.get('location_type')

            if location_type not in valid_location_types:
                return {
                    "status": 400,
                    "error": f"Invalid location_type. Must be one of: {valid_location_types}"
                }

            # 3️⃣ **Crear la ubicación en la base de datos con el usuario autenticado**
            location = request.env['iscapop.locations_model'].sudo().create({
                'name': kwargs.get('name'),
                'description': kwargs.get('description', ''),
                'location_type': location_type,
                'create_uid': request.env.user.id  # 🔥 Se asigna al usuario autenticado
            })

            _logger.info(f"✅ Location creada correctamente con ID: {location.id}, create_uid = {location.create_uid.id}")

            # 4️⃣ **Construir la respuesta en el formato solicitado**
            return {
                "status": 201,
                "location": {
                    "id": location.id,
                    "name": location.name,
                    "description": location.description,
                    "location_type": location.location_type,
                    "create_uid": location.create_uid.id, 
                    "write_uid": location.write_uid.id
                }
            }

        except Exception as e:
            _logger.error(f"❌ Error en create_location: {str(e)}", exc_info=True)
            return {
                "status": 500,
                "error": str(e)
            }
