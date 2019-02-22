# -*- coding: utf-8 -*-

import time
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, api
from openerp.exceptions import Warning


"""class ResParter(models.Model):
    _inherit = 'res.partner'

    authorisation_ids = fields.One2many(
        'account.authorisation',
        'partner_id',
        'Autorizaciones'
        )"""


class AccountJournal(models.Model):

    _inherit = 'account.journal'

    auth_id = fields.Many2one(
        'account.authorisation',
        help='Autorización utilizada para Facturas y Liquidaciones de Compra',
        string='Autorización'
        )
    auth_ret_id = fields.Many2one(
        'account.authorisation',
        string='Autorización de Ret.',
        help='Autorizacion utilizada para Retenciones, facturas y liquidaciones'
        )

