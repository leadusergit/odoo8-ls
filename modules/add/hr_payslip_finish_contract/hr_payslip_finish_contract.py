# -*- coding: utf-8 -*-
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

from openerp import api, tools
from openerp.osv import fields, osv
from openerp.addons.hr_nomina.payroll_tools import *
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools.safe_eval import safe_eval as eval
import logging
    
"""class hr_tipo_desvinculacion(osv.osv):
    _name = 'hr.tipo.desvinculacion'
    
    _columns = {
        'tipo_id': fields.char('Tipo de Salida'),
        'descripcion':fields.char('Descripción')
        }
        """     
    
class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'
    __logger = logging.getLogger(_inherit) 
    
    _columns = {
        #'tipo_id':fields.many2one('hr.tipo.desvinculacion','Tipo de Desvinculacion'),
        'period_end': fields.date('Fecha de Liquidacion', required=True), 
        'liquidacion':fields.boolean('Desvinculación del Empleado',help="Rol de Liquidacion de Contracto o Desvinculacion del empleado"),
        'tipo_liquidacion': fields.selection([
            ('a', 'Por despido intempestivo'),
            ('b', 'Por finalización de contrato'),
            ('c', 'Por finalización de tiempo pactado'),
            ('d', 'Por mutuo acuerdo'),
            ('e', 'Por desicion unilateral'),
            ('f', 'Por sentencia ejecutoriada'),
            ('g', 'Por liquidacion o clausura definitiva de la Empresa'),
            ('h', 'Por no regresar a su empleo, terminada la suspensión'),
            ('i', 'Por jubilación'),
            ('j', 'Por muerte del empleado'),
            ], 'Tipo de Desvinculación', select=True,required=True)
    }
    
    



    def get_inputs_liquidacion(self, cr, uid, contract_ids, date_from, date_to, context=None):
        res = []
        contract_obj = self.pool.get('hr.contract')
        rule_obj = self.pool.get('hr.salary.rule')

        structure_ids = contract_obj.get_all_structures(cr, uid, contract_ids, context=context)
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]

        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
            for rule in rule_obj.browse(cr, uid, sorted_rule_ids, context=context):
                if rule.input_ids:
                    for input in rule.input_ids:
                                                
                        inputs = {
                             'name': input.name,
                             'code': input.code,
                             'contract_id': contract.id,
                             'employee_id': contract.employee_id.id,
                        }
                        res += [inputs]
            
                    
        return res
    
    def onchange_employee_liquid_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
        empolyee_obj = self.pool.get('hr.employee')
        contract_obj = self.pool.get('hr.contract')
        worked_days_obj = self.pool.get('hr.payslip.worked_days')
        
        if context is None:
            context = {}
        #delete old worked days lines
        old_worked_days_ids = ids and worked_days_obj.search(cr, uid, [('payslip_id', '=', ids[0])], context=context) or False
        if old_worked_days_ids:
            worked_days_obj.unlink(cr, uid, old_worked_days_ids, context=context)

        #delete old input lines
        old_input_ids = ids and input_obj.search(cr, uid, [('payslip_id', '=', ids[0])], context=context) or False
        if old_input_ids:
            input_obj.unlink(cr, uid, old_input_ids, context=context)
        
        #defaults
        res = {'value':{
                      'line_ids':[],
                      'input_line_ids': [],
                      'worked_days_line_ids': [],
                      #'details_by_salary_head':[], TODO put me back
                      'name':'',
                      'contract_id': False,
                      'struct_id': False,
                      }
            }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        employee_id = empolyee_obj.browse(cr, uid, employee_id, context=context)
        res['value'].update({
                    'name': _('Salary Slip of %s for %s') % (employee_id.name, tools.ustr(ttyme.strftime('%B-%Y'))),
                    'company_id': employee_id.company_id.id
        })

        if not context.get('contract', False):
            #fill with the first contract of the employee
            contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)
        else:
            if contract_id:
                #set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
            else:
                #if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)

        
        
        if not contract_ids:
            return res
        contract_record = contract_obj.browse(cr, uid, contract_ids[0], context=context)
        res['value'].update({
                    'contract_id': contract_record and contract_record.id or False
        })
        """struct_record = contract_record and contract_record.struct_id or False
        if not struct_record:
            return res
        res['value'].update({
                    'struct_id': struct_record.id,
        })"""
      
        #computation of the salary input
        worked_days_line_ids = self.get_worked_day_lines(cr, uid, contract_ids, date_from, date_to, context=context)              
        input_line_ids = self.get_inputs_liquidacion(cr, uid, contract_ids, date_from, date_to, context=context)
        res['value'].update({
                    'worked_days_line_ids': worked_days_line_ids,
                    'input_line_ids': input_line_ids,
        })
        return res
    
 
        
    def load_info1(self, cr, uid, ids, context={}):
        print"liquidacion=%s"
        self.load_info(cr, uid, ids, context)
        
        for obj in self.browse(cr, uid, ids):
            vals = {'contract_id': obj.contract_id.id,
                    'employee_id': obj.employee_id.id,
                    'payslip_id': obj.id}
            print"valores liquidacion=%s"%vals 

            contract_obj = self.pool.get('hr.contract')
            input_obj = self.pool.get('hr.payslip.input')
            rule_obj = self.pool.get('hr.salary.rule')
            structure_ids = contract_obj.get_all_structures(cr, uid, obj.contract_id.id, context=context)
            rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
            sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
            
            for contract in contract_obj.browse(cr, uid,obj.contract_id.id , context=context):
                for rule in rule_obj.browse(cr, uid, sorted_rule_ids, context=context):
                    if rule.condition_select == 'none':
                        print"rule.condition_select  =%s"%rule.condition_select 

                        input_obj.create(cr, uid, dict({'id': rule.id,
                                                        'code': rule.code,
                                                        'name':rule.name,
                                                        'sequence':rule.id,
                                                        'amount': 0.00,
                                                        'contract_id':contract.id,
                                                        'employee_id': contract.employee_id.id,
                                                        'payslip_id':obj.id}))
            
            