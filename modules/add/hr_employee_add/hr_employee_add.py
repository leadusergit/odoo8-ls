# -*- coding: utf-8 -*-

import time
from datetime import date
from datetime import datetime
from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    
    _columns = {
                'provisiondt': fields.boolean('Cobra Décimo Tercero', help="Seleccionar si el empleado cobra provisión Décimo Tercero (no acumula)"),
                'provisiondc': fields.boolean('Cobra Décimo Cuarto', help="Seleccionar si el empleado cobra provisión Décimo Cuarto (no acumula)"),                 
                'no_provision': fields.boolean('No tiene Provisiones', help="Seleccionar si el empleado no tiene provisiones Fondos de Reserva, Décimos"),                 

     }    
    
hr_employee()