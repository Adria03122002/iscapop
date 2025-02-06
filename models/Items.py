from odoo import models, fields, api

class ItemsModel(models.Model):
    _name = 'iscapop.items_model'
    _description = 'School Materials'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    photo = fields.Binary(string='Photo')
    category_id = fields.Many2one('iscapop.categories_model', string='Category', required=True)
    documentation = fields.Text(string='Documentation')
    item_detail_ids = fields.One2many('iscapop.item_detail', 'item_id', string='Details')
    full_stock = fields.Integer(string='Total Stock', compute='_compute_full_stock', store=True)
    
    @api.depends('item_detail_ids.stock')
    def _compute_full_stock(self):
        for item in self:
            item.full_stock = sum(detail.stock for detail in item.item_detail_ids)

    