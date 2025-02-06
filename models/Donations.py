from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class Donation(models.Model):
    _name = 'iscapop.donations'
    _description = 'Material Donations'

    item_id = fields.Many2one('iscapop.items_model', string='Item', required=True)
    location_id = fields.Many2one('iscapop.locations_model', string='Origin Location', required=True)
    donation_date = fields.Date(string='Donation Date', required=True, default=fields.Date.today)
    donated_by = fields.Many2one('res.users', string='Donated By', default=lambda self: self.env.user, required=True)
    reserved = fields.Boolean(string='Reserved', default=False)
    reserved_by = fields.Many2one('res.users', string='Reserved By')
    stock_shared = fields.Integer(string='Shared Stock', required=True)
    is_generated_pdf = fields.Boolean(string='generated_pdf', default=False)

    # Campo para la ubicación de destino
    destination_location_id = fields.Many2one(
        'iscapop.locations_model',
        string='Destination Warehouse',
        domain="[('location_type', '=', 'warehouse')]",
    )

    # Campo de categoría
    category_id = fields.Many2one(
        'iscapop.categories_model', 
        string='Category'
    )

    @api.depends('item_id', 'location_id')
    def _compute_stock_shared(self):
        for record in self:
            details = self.env['iscapop.item_detail'].search([
                ('item_id', '=', record.item_id.id),
                ('location_id', '=', record.location_id.id)
            ])
            record.stock_shared = sum(detail.stock for detail in details)

    def action_reserve_item(self):
        for record in self:
            if record.reserved:
                raise ValidationError("This donation is already reserved.")
            if record.donated_by == self.env.user:
                raise ValidationError("You cannot reserve your own donation.")
            
            record.write({
                'reserved': True,
                'reserved_by': self.env.user.id,
            })
    
    def action_confirm_donation(self):
        """
        Confirmar la donación para que esté lista para ser asignada.
        """
        for record in self:
            if not record.reserved:
                raise ValidationError("Only reserved donations can be confirmed.")
            if not record.destination_location_id or not record.category_id:
                raise ValidationError("You must specify both the Destination Warehouse and the Category.")
            
            # Confirmación
            record.write({'reserved': True})

    def action_assign_to_warehouse(self):
        """
        Mover el stock al almacén de destino y registrar correctamente el ítem en `iscapop.items_model` e `iscapop.item_detail`,
        asegurando que no se duplique el stock.
        """
        for record in self:
            if not record.reserved:
                raise ValidationError("Only reserved donations can be assigned to a warehouse.")
            if not record.destination_location_id or not record.category_id:
                raise ValidationError("You must specify both the Destination Warehouse and the Category.")

            # 1️⃣ Buscar si existe un ítem en la categoría
            existing_item = self.env['iscapop.items_model'].search([
                ('category_id', '=', record.category_id.id)
            ], limit=1)

            if existing_item:
                # 2️⃣ Buscar si ya hay un detalle en la ubicación
                item_detail = self.env['iscapop.item_detail'].search([
                    ('item_id', '=', existing_item.id),
                    ('location_id', '=', record.destination_location_id.id),
                ], limit=1)

                if item_detail:
                    # 3️⃣ Si ya existe, actualizar stock SOLO en `item_detail`
                    item_detail.stock += record.stock_shared
                else:
                    # 4️⃣ Si no existe, crear uno nuevo
                    self.env['iscapop.item_detail'].create({
                        'item_id': existing_item.id,
                        'location_id': record.destination_location_id.id,
                        'stock': record.stock_shared,
                        'stock_status': 'available',
                    })
                
                # 5️⃣ **Actualizar stock en `iscapop.items_model` SOLO UNA VEZ**
                existing_item.full_stock = sum(detail.stock for detail in existing_item.item_detail_ids)
            else:
                # 6️⃣ Si no existe un ítem en la categoría, crear uno nuevo
                new_item = self.env['iscapop.items_model'].create({
                    'name': record.item_id.name,
                    'category_id': record.category_id.id,
                    'description': 'Created from donation',
                    'photo': record.item_id.photo,
                    'full_stock': record.stock_shared,
                })

                # 7️⃣ Crear también su detalle en `item_detail`
                self.env['iscapop.item_detail'].create({
                    'item_id': new_item.id,
                    'location_id': record.destination_location_id.id,
                    'stock': record.stock_shared,
                    'stock_status': 'available',
                })

            # 8️⃣ Eliminar la donación después de transferir el stock
            record.unlink()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'iscapop.donations',
            'view_mode': 'tree,form',
            'target': 'current',
        }




    def action_generate_pdf(self):
        """
        Generar un informe PDF para la donación seleccionada.
        """
        self.is_generated_pdf = True
        return self.env.ref('iscapop.action_report_iscapop_reserved_items').report_action(self)
    
    def action_cancel_reservation(self):
        """
        Cancela la reserva de la donación, eliminando la marca de 'Reserved'
        y al usuario que reservó el producto.
        """
        for record in self:
            if not record.reserved:
                raise ValidationError("The donation is not currently reserved.")
            
            # Cancelar la reserva
            record.write({
                'reserved': False,
                'reserved_by': False,
            })

    def action_cancel_donation(self):
        """
        Cancela la donación y devuelve el stock al almacén de origen, 
        siempre que el PDF no se haya generado.
        """
        for record in self:
            if record.is_generated_pdf:
                raise ValidationError("You cannot cancel a donation after the PDF has been generated.")

            # Buscar el detalle del ítem en el almacén de origen
            origin_item_detail = self.env['iscapop.item_detail'].search([
                ('item_id', '=', record.item_id.id),
                ('location_id', '=', record.location_id.id),
            ], limit=1)

            if origin_item_detail:
                # Si existe, devolver el stock al almacén de origen
                origin_item_detail.stock += record.stock_shared
            else:
                # Si no existe, crear un nuevo detalle con el stock devuelto
                self.env['iscapop.item_detail'].create({
                    'item_id': record.item_id.id,
                    'location_id': record.location_id.id,
                    'stock': record.stock_shared,
                    'stock_status': 'available',
                })

            # Eliminar la donación
            record.unlink()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'iscapop.donations',
            'view_mode': 'tree,form',
            'target': 'current',
        }
