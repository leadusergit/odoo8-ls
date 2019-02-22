# -*- encoding: utf-8 -*-
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import time
from datetime import datetime, time
from openerp.report import report_sxw

UNIDADES = ('', 'UN ', 'DOS ', 'TRES ', 'CUATRO ', 'CINCO ', 'SEIS ', 'SIETE ', 'OCHO ', 'NUEVE ', 'DIEZ ', 'ONCE ', 'DOCE ', 'TRECE ', 'CATORCE ', 'QUINCE ', 'DIECISEIS ', 'DIECISIETE ',
	    'DIECIOCHO ', 'DIECINUEVE ', 'VEINTE ')
DECENAS = ('VENTI', 'TREINTA ', 'CUARENTA ', 'CINCUENTA ', 'SESENTA ', 'SETENTA ', 'OCHENTA ', 'NOVENTA ', 'CIEN ')
CENTENAS = ('CIENTO ', 'DOSCIENTOS ', 'TRESCIENTOS ', 'CUATROCIENTOS ', 'QUINIENTOS ', 'SEISCIENTOS ', 'SETECIENTOS ', 'OCHOCIENTOS ', 'NOVECIENTOS ')

def toWord(number):

    """
    Converts a number into string representation
    """
    converted = ''

    if not (0 < number < 999999999):

        return 'No es posible convertir el numero a letras'

    number_str = str(number).zfill(9)
    millones = number_str[:3]
    miles = number_str[3:6]
    cientos = number_str[6:]

    if(millones):
        if(millones == '001'):
            converted += 'UN MILLON '
        elif(int(millones) > 0):
            converted += '%sMILLONES ' % __convertNumber(millones)

    if(miles):
        if(miles == '001'):
            converted += 'MIL '
        elif(int(miles) > 0):
            converted += '%sMIL ' % __convertNumber(miles)

    if(cientos):
        if(cientos == '001'):
            converted += 'UN '
        elif(int(cientos) > 0):
            converted += '%s ' % __convertNumber(cientos)

    converted += ''

    return converted.title()

def __convertNumber(n):
    """
    Max length must be 3 digits
    """
    output = ''

    if(n == '100'):
        output = "CIEN "
    elif(n[0] != '0'):
        output = CENTENAS[int(n[0]) - 1]

    k = int(n[1:])
    if(k <= 20):
        output += UNIDADES[k]
    else:
        if((k > 30) & (n[2] != '0')):
            output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
        else:
            output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

    return output

class payroll_report(report_sxw.rml_parse):
    
    def emp_ubicacion(self, ubi=''):
		print 'ubicaion', ubi
		res = ''
		if ubi == 'oper':
			res = 'OPERATIVA'
			print res
			return res
		elif ubi == 'admin':
			res = 'ADMINISTRATIVA'
			print res
			return res
		elif ubi == 'prod':
			res = 'EMP. PRODUCCION'
			print res
			return res
		else:
		    return ubi		
	   
    def cambiar_fecha(self, fecha):
    	fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
    	return fecha.strftime('%B DEL %Y')
		
	def num_let(self, rol, form):
   		pe = int(rol.total)
   		dec = rol.total - pe
        letras = toWord(pe)
        print form, letras
        return letras + ',' + str(dec)[2:4] + '/' + '100******'
    
    def get_info_method_payment(self, rol):
        res = ''
        #[[ o.employee_id.bank_account_id.res_bank_id.name ]] en la cuenta: No. [[ o.employee_id.bank_account_id.name]]
        employee = rol.employee_id
        
        if not employee.bank_account_id:
        	return "No configurado" 
        
        #Verificar si el tipo de pago
        if rol.employee_id.modo_pago:
	        if rol.employee_id.modo_pago == 'transferencia':
	            res = employee.bank_account_id.bank_name + ' en la cuenta: No ' + employee.bank_account_id.acc_number
	        else:
	            res = 'Pago con cheque'
        else:
	    	return "No configurado"
        return res
       
    def ordenar(self, employee, id):
    	
        if employee:      


			self.cr.execute(""" select hra.id , hri.name, hri.value, hra.code,hrp.id as payroll_id from hr_income as hri
		 		 			join hr_payroll as hrp on (hri.payroll_id=hrp.id)
		 					join hr_adm_incomes as hra on (hri.adm_id=hra.id)
		 		 			where hrp.employee_id = %s and hrp.id=%s 
							order by hra.orden """, (employee.id , id,))
        
        res = self.cr.dictfetchall()
        #print ' res antes ', res
        
        for res_data in res:
        	
            code = res_data['code']
            if not code.startswith('hora'):
            	continue
            	
            query = "select " + code + " as info from hr_resumen_line as hrl join hr_payroll as hp on (hrl.payroll_id = hp.id) where hp.id = " + str(res_data['payroll_id'])
            #print ' query ', query
            self.cr.execute(query)
            res_info_horas = self.cr.dictfetchall()
            res_data['name'] = res_data['name'] + " (" + str(res_info_horas[0]['info']) + ")" 
				
        #print ' res despues ', res	
        return res
    
    
    def get_info_hours_expense(self, expense):
    	
    	res = ''
    	code = expense.expense_type_id.code
    	payroll_id = expense.payroll_id.id
    	if code == 'FAINJ':
    	    query = "select falta_inj as info from hr_resumen_line as hrl join hr_payroll as hp on (hrl.payroll_id = hp.id) where hp.id = " + str(payroll_id)
    	    self.cr.execute(query)
            res_info_horas = self.cr.dictfetchall()
            res = expense.name[0:40] + ' (' + str(res_info_horas[0]['info']) + ')'
            return res
        elif code == 'ATR':
            query = "select perm_particular as info from hr_resumen_line as hrl join hr_payroll as hp on (hrl.payroll_id = hp.id) where hp.id = " + str(payroll_id)
            self.cr.execute(query)
            res_info_horas = self.cr.dictfetchall()
            res = expense.name[0:40] + ' (' + str(res_info_horas[0]['info']) + ')'
            return res
        elif code == 'PEPAR' or code == 'SUBIE':
            query = "select sum(number_of_days) as info from hr_permission where payroll_id = " + str(payroll_id)
            self.cr.execute(query)
            res_info_horas = self.cr.dictfetchall()
            res = expense.name[0:40] + ' (' + str(res_info_horas[0]['info']) + ')'
            return res
        else:
            return expense.name[0:40]
 
    def horas_lab(self,payroll):
        return payroll.num_dias * 8
    
    def __init__(self, cr, uid, name, context):
        super(payroll_report, self).__init__(cr, uid, name, context)
        self.localcontext.update(
                                 {'time' : time,
                                  'cambiar_fecha': self.cambiar_fecha,
                                  'lang':context['lang'],
                                  'emp_ubicacion': self.emp_ubicacion,
                                  'method_payment':self.get_info_method_payment,
                                  'ordenar': self.ordenar,
                                  'info_expense':self.get_info_hours_expense,
                                  'horas_lab':self.horas_lab,
                                  }
                                 )
       
report_sxw.report_sxw('report.hr.payrolll', 'hr.payroll', "hr_payroll/report/payroll_report.rml", parser=payroll_report, header=False)
