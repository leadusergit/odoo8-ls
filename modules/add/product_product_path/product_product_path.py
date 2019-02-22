# -*- coding: utf-8 -*-
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from openerp import SUPERUSER_ID
from openerp import models, fields, api, _
from openerp.osv import osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import workflow
from openerp.exceptions import ValidationError

class product_product(models.Model):
 
    _name = 'product.product'
    _inherit = 'product.product'
    _description = "Path Imagen producto"
    

    imagen_path=fields.Char('Ubicación de Imagen')