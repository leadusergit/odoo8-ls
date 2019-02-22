# -*- coding: utf-8 -*-

import time
import datetime
from datetime import date
from datetime import datetime
from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
import openerp.addons.decimal_precision as dp


"""class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    
    _columns = {
                'provisionfr': fields.boolean('Fondos de Reserva', help="Seleccionar si el Empleado tiene fondos de Reserva"),
     }    
    
hr_employee()"""


class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    
    _columns = {
         'num_dias_vacacion': fields.integer ('Número Días Vacacion'),
         'fecha_limite_cv': fields.date ('Fecha Cálculo de NºDV'),
     }    
    
    
    def get_info(self, cr, uid, ids, context={}):
        
        for contract in self.browse(cr, uid, ids):
                vals = {'contract_id': contract.id,
                        'employee_id': contract.employee_id.id
                        }
                print"vals1 =%s"%vals
                fecha_contrato =contract.date_start
                #mes_c = fecha_contrato[3:5]
                fecha_p = contract.fecha_limite_cv#str(date.today())#time.strftime("%d/%m/%y")
                #mes_p = fecha_p[3:5]
                formato_fecha = "%Y-%m-%d"
                fecha_inicial = datetime.strptime(contract.date_start,formato_fecha)
                fecha_final = datetime.strptime(fecha_p,formato_fecha)
                calcdate = fecha_final - fecha_inicial
                print "calcdate=%s"%calcdate
                # Imprimo el resultado final
                print "calcdate.days=%s"%calcdate.days
               # id_d =self.pool.get('hr.holidays').search(cr, uid, [('employee_id', '=', contract.employee_id.id),('type', '=', 'remove')])
                #n=self.pool.get('hr.holidays').browse(cr, uid,id_d).number_of_days_temp  
                anios=calcdate.days/350
                aniosmod=calcdate.days%anios
                print"aniosmod=%s"%aniosmod
                
                if calcdate.days >= 350 and anios <=5:
                    contract.num_dias_vacacion=15
                if anios==6:
                    contract.num_dias_vacacion=16
                if anios==7:
                    contract.num_dias_vacacion=17
                if anios==8:
                    contract.num_dias_vacacion=18
                if anios==9:
                    contract.num_dias_vacacion=19
                if anios==10:
                    contract.num_dias_vacacion=20
                if anios==11:
                    contract.num_dias_vacacion=21
                if anios==12:
                    contract.num_dias_vacacion=22
                if anios==13:
                    contract.num_dias_vacacion=23
                if anios==14:
                    contract.num_dias_vacacion=24
                if anios==15:
                    contract.num_dias_vacacion=25
                if anios==16:
                    contract.num_dias_vacacion=26
                if anios==17:
                    contract.num_dias_vacacion=27
                if anios==18:
                    contract.num_dias_vacacion=28
                if anios==19:
                    contract.num_dias_vacacion=29
                if anios==20:
                    contract.num_dias_vacacion=30
                    
    
hr_contract()