# -*- encoding: utf-8 -*-

from openerp import fields, models, api

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    x_id_liquidation = fields.Integer(string='Referencia de la liquidacion', required=False)
    x_is_liquidation = fields.Boolean(string='Esta en liquidacion', default=False)
