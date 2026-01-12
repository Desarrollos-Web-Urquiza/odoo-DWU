from odoo import models, fields

class HolaOdoo(models.Model):
    _name = 'hola.odoo'
    _description = 'Hola Odoo'

    name = fields.Char(string='Mensaje', required=True)
