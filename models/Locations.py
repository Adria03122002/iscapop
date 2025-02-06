from odoo import models, fields, api
from odoo.exceptions import ValidationError

class LocationsModel(models.Model):
    _name = 'iscapop.locations_model'
    _description = 'Locations'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    item_detail_ids = fields.One2many('iscapop.item_detail', 'location_id', string='Items')
    location_type = fields.Selection(
        [('classroom', 'Classroom'), ('warehouse', 'Warehouse')], 
        string='Location Type', 
        required=True, 
        default='classroom',
    )
    

    def action_donate(self):
        """
        Marks the items with stock > 0 in the location as 'donated' and creates donation records.
        """
        for location in self:
            # Filter items with stock > 0
            items_to_donate = location.item_detail_ids.filtered(
                lambda item: item.stock_status == 'donate' and item.stock > 0
            )

            if not items_to_donate:
                raise ValidationError("There are no items marked as 'To Donate' with stock greater than 0 in this location.")

            for item in items_to_donate:
                # Create a donation record
                self.env['iscapop.donations'].create({
                    'item_id': item.item_id.id,
                    'location_id': item.location_id.id,
                    'donation_date': fields.Date.today(),
                    'donated_by': self.env.user.id,
                    'stock_shared': item.stock,
                })

                # Remove the donated item
                item.unlink()

        return {
            'type': 'ir.actions.act_window_close',
        }


    def action_generate_discard_pdf(self):
        """
        Genera un informe PDF de los ítems marcados como "Para Descarte" en la ubicación.
        En lugar de eliminarlos, se marca `available = False` para que sean eliminados después.
        """
        for location in self:
            if location.location_type != 'warehouse':
                raise ValidationError("Only warehouses can perform this action.")

            # ✅ Obtener los ítems "Para Descarte"
            items_to_discard = self.env['iscapop.item_detail'].search([
                ('location_id', '=', location.id),
                ('stock_status', '=', 'discard'),
                ('available', '=', True)  # ✅ Solo los que aún no han sido procesados
            ])

            if not items_to_discard:
                raise ValidationError("There are no items marked as 'To Discard' in this warehouse.")

            # ✅ Generar el PDF
            report_action = self.env.ref('iscapop.action_report_iscapop_discard_items').report_action(items_to_discard)

            # ✅ Marcar los ítems como NO DISPONIBLES para futura eliminación
            items_to_discard.write({'available': False})

            return report_action
        

    def action_delete_discarded_items(self):
        """
        Elimina definitivamente los ítems que ya fueron descartados y marcados como `available = False`.
        """
        for location in self:
            if location.location_type != 'warehouse':
                raise ValidationError("Only warehouses can perform this action.")

            # ✅ Buscar los ítems marcados como no disponibles
            items_to_delete = self.env['iscapop.item_detail'].search([
                ('location_id', '=', location.id),
                ('stock_status', '=', 'discard'),
                ('available', '=', False)  # ✅ Solo los ya procesados en el PDF
            ])

            if not items_to_delete:
                raise ValidationError("There are no items ready for deletion.")

            # ✅ Eliminar los registros
            items_to_delete.unlink()








