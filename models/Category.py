from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class CategoriesModel(models.Model):
    _name = 'iscapop.categories_model'
    _description = 'Categories'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    child_ids = fields.One2many('iscapop.categories_model', 'father_id', string='Childs')
    father_id = fields.Many2one('iscapop.categories_model', string='Father')
    item_ids = fields.One2many('iscapop.items_model', 'category_id', string='Items')