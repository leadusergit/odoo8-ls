# -*- coding: utf-8 -*-

import time
import datetime
from datetime import date
from datetime import datetime
from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
from openerp.exceptions import ValidationError
import logging
import openerp.addons.decimal_precision as dp


class hr_employee_loan(osv.osv):
    _inherit = 'hr.employee.loan'
    
    _columns = {
        'tipo' : fields.selection([('anti', 'Anticipo Sueldo'),
                                   ('prestemp', 'Préstamo Empresarial') ], 'Tipo', select=True,required=True)
    }
    _defaults = {
            'tipo':'anti'
    }
   
class Payslip(osv.osv):
    _inherit = 'hr.payslip'  
        
    def load_info(self, cr, uid, ids, context={}):
        self.clear_info(cr, ids)
      
        class Expense(object):
            def __init__(self, model, ref, excluir):
                self.model = model
                self.ref = ref
                self.excluir = excluir
        
        for obj in self.browse(cr, uid, ids):
            vals = {'contract_id': obj.contract_id.id,
                    'employee_id': obj.employee_id.id,
                    'payslip_id': obj.id}
            print"vals =%s"%vals 
            if not obj.contract_id.id:
                raise ValidationError(u'No se puede generar Rol de empleado %s en este periodo ¡¡Verificar fecha de inicio de Contrato!!'%obj.employee_id.name_related)
     
            #===================================================================
            # INGRESOS
            
            incomes_model = self.pool.get('hr.income')
            incomesadm_model = self.pool.get('hr.adm.incomes')
            payslip_model = self.pool.get('hr.payslip.input') 
                                
            """for adm_id in self.pool.get('hr.adm.incomes').browse(cr, uid, self._get_incomes_ids(cr, uid, obj.id)):
                if adm_id.type == 'static_value':
                    print"adm_id.type=%s"%adm_id.type
                    if adm_id in obj.employee_id.incomes_ids:
                        value = adm_id.default_value
                        print"value-base-hr_payroll183=%s"%value
                        if value:
                            periodo= obj.date_from[:7]#obj.period_id.code
                            anio=periodo[:4]
                            mes=periodo[5:]
                            periodo1=mes+'/'+anio
                            id_periodo =self.pool.get('hr.contract.period').search(cr, uid, [('code', '=', periodo1)])
                            code=self.pool.get('hr.contract.period').browse(cr ,uid, id_periodo ,context=context).id
                            print"period_id-payslip=%s"%code
                            
                            payslip_model.create(cr, uid, dict({'id': adm_id.id,
                                                                'adm_id': adm_id.id,
                                                                'code': adm_id.code,
                                                                'name':adm_id.name,
                                                                'sequence':adm_id.id,
                                                                'amount': adm_id.default_value,
                                                                'contract_id':obj.contract_id.id,
                                                                'employee_id': obj.employee_id.id,
                                                                'tipo':'i',
                                                                'period_id': code,
                                                                'payslip_id': obj.id}))
                            
                            

                            if code:
                                self.clear_info_ingresos(cr, ids,code,obj.employee_id.id)
                            else:
                                continue
                            
                            incomes_model.create(cr, uid, dict({'id': adm_id.id,
                                                                'adm_id': adm_id.id,
                                                                'code': adm_id.code,
                                                                'name':adm_id.code,
                                                                'value': adm_id.default_value,
                                                                'contract_id':obj.contract_id.id,
                                                                'employee_id': obj.employee_id.id,
                                                                'period_id': code}))
                    else:
                        continue"""
            
            for income_id in self.pool.get('hr.income').browse(cr, uid, self._get_income_ids(cr, uid, obj.employee_id.id)):
                print"income_id =%s"%income_id
                value = income_id.value
                if income_id.employee_id.id == obj.employee_id.id and value:
                    periodo= obj.date_from[:7]#obj.period_id.code
                    anio=periodo[:4]
                    mes=periodo[5:]
                    periodo1=mes+'/'+anio
                    id_periodo =self.pool.get('hr.contract.period').search(cr, uid, [('code', '=', periodo1)])
                    code_e=self.pool.get('hr.contract.period').browse(cr ,uid, id_periodo ,context=context).id
                    code_name=self.pool.get('hr.contract.period').browse(cr ,uid, id_periodo ,context=context).code
                    type_id=self.pool.get('hr.income').browse(cr ,uid, income_id.id ,context=context).adm_id.id                            
                    code_type=self.pool.get('hr.adm.incomes').browse(cr ,uid, type_id ,context=context).code
                            
                    if income_id.period_id.code == code_name:
                        payslip_model.create(cr, uid, dict({'id': income_id.id,
                                                        'code':code_type,
                                                        'adm_id': type_id,
                                                        'name':income_id.name,
                                                        'sequence':11,
                                                        'amount': income_id.value,
                                                        'contract_id':obj.contract_id.id,
                                                        'employee_id':obj.employee_id.id,
                                                        'tipo':'i',
                                                        'period_id': code_e,
                                                        'payslip_id': obj.id}))
                    else:
                        continue
                           
                            
                    if income_id.period_id.code == code_name:
                        continue
                    else:
                        incomes_model.create(cr, uid, dict({'id': income_id.id,
                                                            'adm_id': type_id,
                                                            'code': code_type,
                                                            'name':income_id.name,
                                                            'value': income_id.value,
                                                            'contract_id':obj.contract_id.id,
                                                            'employee_id': obj.employee_id.id,
                                                            'period_id': code_e}))
                           
                else:
                        continue           
            #===================================================================
            # EGRESOS
            expense_model = self.pool.get('hr.expense')
            #for expense_id in self.pool.get('hr.expense').browse(cr, uid, self._get_expense_ids(cr, uid, obj.contract_id.id)):
            for expense_id in self.pool.get('hr.expense').browse(cr, uid, self._get_expense_ids(cr, uid, obj.contract_id.id)):
                    print"expense_id =%s"%expense_id 
                    if expense_id.employee_id == obj.employee_id and expense_id.name !='Aporte Personal': 
                        value = expense_id.value
                        if value:
                            
                            periodo= obj.date_from[:7]#obj.period_id.code
                            anio=periodo[:4]
                            mes=periodo[5:]
                            periodo1=mes+'/'+anio
                            id_periodo =self.pool.get('hr.contract.period').search(cr, uid, [('code', '=', periodo1)])
                            code_e=self.pool.get('hr.contract.period').browse(cr ,uid, id_periodo ,context=context).id
                            code_name=self.pool.get('hr.contract.period').browse(cr ,uid, id_periodo ,context=context).code
                            print"period_id-payslip-egresos=%s"%code_name
                            print"period_id-expense_id.period_id.code=%s"%expense_id.period_id.code
                            type_id=self.pool.get('hr.expense').browse(cr ,uid, expense_id.id ,context=context).expense_type_id.id                            
                            code_type=self.pool.get('hr.expense.type').browse(cr ,uid, type_id ,context=context).description
                            
                            if expense_id.period_id.code == code_name:
                                payslip_model.create(cr, uid, dict({'id': expense_id.id,
                                                        'code':code_type,
                                                        'expense_type_id': type_id,
                                                        'name':expense_id.name,
                                                        'sequence':10,
                                                        'amount': expense_id.value,
                                                        'contract_id':obj.contract_id.id,
                                                        'employee_id':obj.employee_id.id,
                                                        'tipo':'e',
                                                        'period_id': code_e,
                                                        'payslip_id': obj.id}))
                            else:
                                continue
                           
                            
                            if expense_id.period_id.code == code_name:
                                continue
                            else:
                                expense_model.create(cr, uid, dict({'id': expense_id.id,
                                                                'expense_type_id': type_id,
                                                                'code': code_type,
                                                                'name':expense_id.name,
                                                                'value': expense_id.value,
                                                                'contract_id':obj.contract_id.id,
                                                                'employee_id': obj.employee_id.id,
                                                                'period_id': code_e}))
                           
                        else:
                             continue  
            #===================================================================
            # Préstamos        
            
            for loan_id in self.pool.get('hr.employee.loan').browse(cr, uid, self._get_loan_ids1(cr, uid, obj.id)):
                idloan=loan_id.id
                print"idloan=%s"%idloan
                
                if loan_id.employee_id == obj.employee_id:
                    print"loan_id.employee_id =%s"%loan_id.employee_id 
                    print"obj.employee_id=%s"%obj.employee_id
                    for loan in self.pool.get('hr.employee.loan.plan').browse(cr, uid, self._get_loan_ids(cr, uid,idloan)):                                                           
                        print"for loan"
                        print"idloan=%s"%idloan
                        print"loan_id=%s"%loan_id.id
                        if idloan==loan.loan_id.id:
                            value = loan.amount                  
                            
                            fecha1=obj.date_from[:7]
                            anio=fecha1[:4]
                            mes=fecha1[5:]
                            fecha=mes+'/'+anio
                            id_periodo =self.pool.get('hr.contract.period').search(cr, uid, [('code', '=', fecha)])
                            code_p=self.pool.get('hr.contract.period').browse(cr ,uid, id_periodo ,context=context).id

                            print"loan.period_id.code=%s"%loan.period_id.code
                            print"fecha=%s"%fecha
                            
                            if loan.period_id.code == fecha: 
                                if loan_id.tipo== 'prestemp':
                                    print"loan.tipo prest=%s"%loan_id.tipo              
                                    payslip_model.create(cr, uid, dict({'id':loan.id,
                                                        'code': 'PRESTEMP',
                                                        'name':'Préstamo Empresarial',
                                                        'sequence':10,
                                                        'amount': value,
                                                        'contract_id':obj.contract_id.id,
                                                        'employee_id': obj.employee_id.id,
                                                        'tipo':'e',
                                                        'period_id': code_p,
                                                        'payslip_id': obj.id})) 
                                if loan_id.tipo== 'anti':
                                    print"loan.tipo ant=%s"%loan_id.tipo               
                                    payslip_model.create(cr, uid, dict({'id':loan.id,
                                                        'code': 'ANTI',
                                                        'name':'Anticipo de Remuneración',
                                                        'sequence':37,
                                                        'amount': value,
                                                        'contract_id':obj.contract_id.id,
                                                        'employee_id': obj.employee_id.id,
                                                        'tipo':'e',
                                                        'period_id': code_p,
                                                        'payslip_id': obj.id})) 
                            else:
                                continue

            for payslip in self.browse(cr, uid, ids):
                vals = {'contract_id': payslip.contract_id.id,
                        'employee_id': payslip.employee_id.id,
                        'payslip_id': payslip.id}
                print"vals1 =%s"%vals
                
                formato_fecha = "%Y-%m-%d"
                if payslip.contract_id.id:
                    fecha_contrato = datetime.strptime(payslip.contract_id.date_start,formato_fecha)
                    fecha_actual = datetime.strptime(str(date.today()),formato_fecha) 
                    calcdate = fecha_actual - fecha_contrato
                    print "calcdate.days=%s"%calcdate.days
                else:
                    raise ValidationError(u'No se puede generar Rol de empleado %s en este periodo ¡¡Verificar Contrato!!'%payslip.employee_id.name_related)

            
                if calcdate.days >=365:
                    payslip.time_in= int(calcdate.days/365)
                    payslip.num_dias= calcdate.days
                else:
                    payslip.time_in= 0
                    payslip.num_dias= calcdate.days
                    
                    
                                
               

Payslip()