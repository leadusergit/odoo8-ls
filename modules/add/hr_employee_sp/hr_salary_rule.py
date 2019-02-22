# -*- coding: utf-8 -*-

import time
from datetime import date
from datetime import datetime
from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class hr_salary_rule(osv.osv):
    _inherit = 'hr.salary.rule'
    
    _columns = {
        'tag_impresion': fields.char('Tag para Impresión', help="Colocar la descripció para impresión en reporte"),
     } 
    
       
    _defaults = {
        'tag_impresion': 'Regla',

    }
    
hr_salary_rule()