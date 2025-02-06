from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockStatusWizard(models.TransientModel):
    _name = 'iscapop.stock_status_wizard'
    _description = 'Wizard to Change Stock Status'

    stock_status = fields.Selection(
        [
            ('donate', 'To Donate'),
            ('available', 'Available'),
            ('discard', 'To Discard')
        ],
        string="Stock Status",
        default='available',
        required=True
    )

    location_id = fields.Many2one('iscapop.locations_model', string="Location", readonly=True)

    item_detail_ids = fields.Many2many('iscapop.item_detail', string='Items to Modify', domain="[('location_id', '=', location_id)]")

    stock_quantity = fields.Integer(string="Stock Quantity", required=True)

    def _process_stock_change(self, item, stock_quantity, stock_status, location_id):
        if not item:
            raise ValidationError("The item is not valid.")
        
        if item.stock < stock_quantity:
            raise ValidationError(f"Not enough stock of {item.item_id.name} to complete the operation.")
        
        # Reduce the stock
        item.stock -= stock_quantity

        # Search for an existing item with the same stock status and location
        existing_item = self.env['iscapop.item_detail'].search([
            ('item_id', '=', item.item_id.id),  
            ('stock_status', '=', stock_status),
            ('location_id', '=', location_id),
        ], limit=1)

        # Update or create the item with the new stock quantity
        if existing_item:
            existing_item.stock += stock_quantity
        else:
            self.env['iscapop.item_detail'].create({
                'item_id': item.item_id.id, 
                'location_id': location_id,
                'stock': stock_quantity,
                'stock_status': stock_status,
            })
        
        # Check if the item should be removed because the stock is now 0
        if item.stock <= 0:
            item.unlink()


    def change_stock_status(self):
        for record in self:
            if not record.location_id:
                raise ValidationError("The location cannot be null.")
            
            if not record.item_detail_ids:
                raise ValidationError("No items were selected for modification.")
            
            for item in record.item_detail_ids:
                if item.location_id.location_type != 'warehouse':
                    raise ValidationError("The change can only be applied in warehouses.")
                
                record._process_stock_change(
                    item=item,
                    stock_quantity=record.stock_quantity,
                    stock_status=record.stock_status,
                    location_id=record.location_id.id
                )
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def create(self, vals):
        record = super(StockStatusWizard, self).create(vals)

        if record.item_detail_ids:
            for item in record.item_detail_ids:
                record._process_stock_change(
                    item=item,
                    stock_quantity=record.stock_quantity,
                    stock_status=record.stock_status,
                    location_id=record.location_id.id
                )
        
        return record

    def write(self, vals):
        result = super(StockStatusWizard, self).write(vals)
        
        for record in self:
            if record.item_detail_ids:
                for item in record.item_detail_ids:
                    record._process_stock_change(
                        item=item,
                        stock_quantity=record.stock_quantity,
                        stock_status=record.stock_status,
                        location_id=record.location_id.id
                    )
        return result
