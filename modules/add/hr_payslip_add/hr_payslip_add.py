# -*- coding: utf-8 -*-

import time
import datetime
from datetime import date
from datetime import datetime
from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging
import openerp.addons.decimal_precision as dp


class Payslip(osv.osv):
    _inherit = 'hr.payslip' 
    __logger = logging.getLogger(_inherit) 
    
            
    def _get_loan_ids(self, cr, uid, id):
        """Método para obtener los ids de las filas correspondientes al empleado """
        return self.pool.get('hr.employee.loan.plan').search(cr, uid, [], order='loan_id ')
    def _get_loan_ids1(self, cr, uid, id):
        """Método para obtener los ids de las filas correspondientes al empleado """
        return self.pool.get('hr.employee.loan').search(cr, uid, [], order='contract_id ')
    
    def _get_incomes_ids(self, cr, uid, id):
        """Método para obtener los ids de las filas correspondientes al empleado """
        return self.pool.get('hr.adm.incomes').search(cr, uid, [], order='orden')
    def _get_income_ids(self, cr, uid, id):
        """Método para obtener los ids de las filas correspondientes al empleado """
        return self.pool.get('hr.income').search(cr, uid, [], order='employee_id')

    def _get_expense_ids(self, cr, uid, id):
        """Método para obtener los ids de las filas correspondientes al empleado """
        return self.pool.get('hr.expense').search(cr, uid, [], order='contract_id')
    
    def _get_contract_ids(self, cr, uid, id):
        """Método para obtener los ids de las filas correspondientes al empleado """
        return self.pool.get('hr.contract').search(cr, uid, [], order='employee_id')
     
        
    def clear_info(self, cr,payslip_id):
        """Método para limpiar tabla hr.payslip.input ,esto permite cargar los datos una sola vez """
        cr.execute('DELETE FROM hr_payslip_input WHERE payslip_id=ANY(%s)', (payslip_id,)) 
     
    def clear_info_ingresos(self, cr,payslip_id,code,employee_id):   
        cr.execute('DELETE FROM hr_income WHERE period_id=%s and employee_id=%s', (code,employee_id))

    
        
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
     
            """fecha_contrato = str(obj.contract_id.date_start)             
            anio_c = fecha_contrato[:4]
            fecha_p = time.strftime("%d/%m/%y")
            anio_p = fecha_p[:4]
            timein= int(anio_p) - int(anio_c)
            print"timein=%s"%timein"""
            #===================================================================
            # INGRESOS
            
            incomes_model = self.pool.get('hr.income')
            incomesadm_model = self.pool.get('hr.adm.incomes')
            payslip_model = self.pool.get('hr.payslip.input') 
                                
            for adm_id in self.pool.get('hr.adm.incomes').browse(cr, uid, self._get_incomes_ids(cr, uid, obj.id)):
                if adm_id.type == 'static_value':
                    print"adm_id.type=%s"%adm_id.type
                    """income_ids = incomes_model.search(cr, uid, [('adm_id', '=', adm_id.id),
                                                                ('employee_id', '=', obj.employee_id),
                                                                ('contract_id', '=', obj.contract_id)])"""
                    if adm_id in obj.employee_id.incomes_ids:
                        value = adm_id.default_value
                        print"value-base-hr_payroll183=%s"%value
                        if value:
                            payslip_model.create(cr, uid, dict({'id': adm_id.id,
                                                                'code': adm_id.code,
                                                                'name':adm_id.code,
                                                                'sequence':10,
                                                                'amount': adm_id.default_value,
                                                                'contract_id':obj.contract_id.id,
                                                                'payslip_id': obj.id}))
                            
                            
                            periodo= obj.date_from[:7]#obj.period_id.code
                            anio=periodo[:4]
                            mes=periodo[5:]
                            periodo1=mes+'/'+anio
                            id_periodo =self.pool.get('hr.contract.period').search(cr, uid, [('code', '=', periodo1)])
                            code=self.pool.get('hr.contract.period').browse(cr ,uid, id_periodo ,context=context).id
                            print"period_id-payslip=%s"%code
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
                        continue
            
            
            #===================================================================
            # EGRESOS
            expense_model = self.pool.get('hr.expense')
            """expense_model.search(cr, uid, expense_model.search(cr, uid, [('employee_id', '=', obj.employee_id.id),
                                                                         ('contract_id', '=', obj.contract_id.id),
                                                                         ('period_id', '=', obj.period_id.id),
                                                                         ('auto', '=', False)]))"""
                                                                                            

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
                                                        'name':expense_id.name,
                                                        'sequence':10,
                                                        'amount': expense_id.value,
                                                        'contract_id':obj.contract_id.id,
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
                            print"loan.period_id.code=%s"%loan.period_id.code
                            print"fecha=%s"%fecha
                            
                            if loan.period_id.code == fecha: 
                                print"fechaif=%s"%fecha                 
                                payslip_model.create(cr, uid, dict({'id':loan.id,
                                                        'code': 'PRESTEMP',
                                                        'name':'Préstamo',
                                                        'sequence':10,
                                                        'amount': value,
                                                        'contract_id':obj.contract_id.id,
                                                        'payslip_id': obj.id}))  
                            else:
                                    continue

            for payslip in self.browse(cr, uid, ids):
                vals = {'contract_id': payslip.contract_id.id,
                    'employee_id': payslip.employee_id.id,
                    'payslip_id': payslip.id}
                print"vals1 =%s"%vals
                fecha_contrato = str(payslip.contract_id.date_start)             
                anio_c = fecha_contrato[:4]
                print"anio_c=%s"%anio_c
                fecha_p = str(date.today())#time.strftime("%d/%m/%y")
                anio_p = fecha_p[:4]
                print"anio_p=%s"%anio_p
                
                payslip.time_in= int(anio_p) - int(anio_c)
                payslip.num_dias= payslip.time_in * 12 * 30
                print"timein=%s"%payslip.time_in
             
                                                                    
       
    
    _columns = {                
        'num_dias': fields.integer ('Número Días Trabajados',readonly=False,states={'done': [('readonly', True)]}),
        #'time_in': fields.int ('Número de Años de Servicio',digits=(12, 2),readonly=False,states={'done': [('readonly', True)]}),
        'time_in': fields.integer('Número de Años de Servicio',readonly=False,states={'done': [('readonly', True)]}),         
       }
             
       
    _defaults = {
        'num_dias': 0,
        'time_in':0,
        #'nomina_type':'Normal',
        }
    
Payslip()