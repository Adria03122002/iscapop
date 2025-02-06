from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class ItemDetail(models.Model):
    _name = 'iscapop.item_detail'
    _description = 'Material Detail'
    _rec_name = "item_id"

    item_id = fields.Many2one('iscapop.items_model', string='Item', required=True)
    location_id = fields.Many2one('iscapop.locations_model', string='Location',   domain="[('create_uid', '=', uid)]", required=True)
    stock = fields.Integer(string='Stock', default=0)
    photo = fields.Image(string='Photo')
    stock_status = fields.Selection(
        [
            ('donate', 'For Donation'),
            ('available', 'Available'),
            ('discard', 'For Discard'),
        ],
        string="Stock Status",
        default='available',
        required=True
    )
    display_name = fields.Char(string="Display Name", compute="_compute_display_name", store=True)
    available = fields.Boolean(string="Available for Deletion", default=True)  

    @api.constrains('stock')
    def _check_stock_positive(self):
        for record in self:
            if record.stock < 0:
                raise ValidationError("Stock cannot be negative.")

    @api.constrains('stock_status', 'location_id')
    def _check_location_stock_status(self):
        for record in self:
            if record.location_id.location_type != 'warehouse' and record.stock_status != 'available':
                raise ValidationError("The stock status can only be modified if the location is a warehouse.")

    @api.depends('item_id.name', 'stock')
    def _compute_display_name(self):
        for record in self:
            stock_status = dict(self._fields['stock_status'].selection).get(record.stock_status, 'Unknown')
            record.display_name = f"{record.item_id.name or 'Unknown'} ({record.stock} in stock, {stock_status})"

    

    @api.onchange('stock')
    def _onchange_stock(self):
        if self.stock == 0:
            self.unlink()



