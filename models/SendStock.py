from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class SendStockWizard(models.TransientModel):
    _name = 'iscapop.send_stock_wizard'
    _description = 'Wizard to Send Stock to Another Location'

    item_id = fields.Many2one(
        'iscapop.item_detail',
        string='Item',
        required=True,
        domain="[('location_id', '=', source_location_id), ('stock', '>', 0)]"
    )
    source_location_id = fields.Many2one(
        'iscapop.locations_model',
        string='Source Location',
        required=True
    )
    destination_location_id = fields.Many2one(
        'iscapop.locations_model',
        string='Destination Location',
        required=True
    )
    quantity = fields.Integer(string='Quantity to Send', required=True)

    @api.constrains('quantity')
    def _check_quantity(self):
        for wizard in self:
            if wizard.quantity <= 0:
                raise ValidationError("The quantity to send must be greater than 0.")

    @api.constrains('source_location_id', 'destination_location_id')
    def _check_locations(self):
        for wizard in self:
            if wizard.source_location_id == wizard.destination_location_id:
                raise ValidationError("The source and destination locations must be different.")

    def action_send_stock(self):
        """
        Validates stock availability, updates the stock in both source and destination,
        and removes the item if the stock in the source reaches zero.
        """
        if not self or len(self) != 1:
            raise ValidationError("The wizard must be executed for a single record.")

        item = self.item_id

        # Validate sufficient stock
        if item.stock < self.quantity:
            raise ValidationError("Insufficient stock available to move.")

        # Reduce stock in the source location
        item.stock -= self.quantity

        # Find or create the item in the destination location
        item_in_destination = self.env['iscapop.item_detail'].search([
            ('item_id', '=', item.item_id.id),
            ('location_id', '=', self.destination_location_id.id),
        ], limit=1)

        if item_in_destination:
            item_in_destination.stock += self.quantity
        else:
            self.env['iscapop.item_detail'].create({
                'item_id': item.item_id.id,
                'location_id': self.destination_location_id.id,
                'stock': self.quantity,
            })

        # Remove item from the source if the stock becomes zero
        if item.stock <= 0:
            item.unlink()

        # Display a confirmation message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'{self.quantity} units of {item.item_id.name} sent to {self.destination_location_id.name}.',
                'type': 'success',
                'sticky': False,
            },
        }

    def action_cancel(self):
        """
        Closes the wizard without making any changes.
        """
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def create(self, vals):
        """
        Automatically processes the stock transfer upon creation.
        """
        record = super(SendStockWizard, self).create(vals)
        record.action_send_stock()
        return record
