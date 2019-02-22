# -*- coding: utf-8 -*-
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

from openerp import api, tools
from openerp.osv import osv, fields
from psycopg2 import IntegrityError

    
class wizard_generate_contract(osv.osv_memory):
    """genera payslip de empleados seleccionados desde objeto hr.employee """
    _name = 'wizard.generate.payslip'
    
    _columns = {
        'journal_id':fields.many2one('account.journal', 'Diario', required=True),
        'period_from': fields.date('Date From', required=True), 
        'period_to': fields.date('Date To', required=True),
        'employee_ids':fields.many2many('hr.employee', 'employee_wizard_payslip', 'wiz_id', 'employee_id', 'Empleados',
                                         domain=[('state_emp', '=', 'active')], default=lambda self: self._get_defaults('employee_ids')),
        'contrat_id':fields.many2many('hr.employee', 'employee_wizard_payslip', 'wiz_id', 'employee_id', 'Empleados',
                                         domain=[('state_emp', '=', 'active')], default=lambda self: self._get_defaults('employee_ids')),

        'notes': fields.char('Novedades', readonly=True),
        'state': fields.selection([('draft', 'Borrador'), 
                                   ('done', 'Generado')], select=True,readonly=False, copy=False)

    }
    
    def _get_defaults(self, cr, uid, field, context=None):
        context, res = context or {}, {}
        if context.get('active_model') == 'hr.employee':
            employee_ids = self.pool.get('hr.employee').search(cr, uid, [('id', 'in', context['active_ids']),
                                                                         ('state_emp', '=', 'active')])
            #print"employee_ids=%s"%employee_ids
            res['employee_ids'] = employee_ids
        return res.get(field)
    
    def generate(self, cr, uid, ids, context):
        payslip_model = self.pool.get('hr.payslip')
        
        obs = u''
        for obj in self.read(cr, uid, ids, ['period_from','period_to','employee_ids','journal_id']):
            #print"obj=%s"%obj
            names = dict(self.pool.get('hr.employee').name_get(cr, uid, obj['employee_ids']))
            
            print"obj['employee_ids']=%s"%obj['employee_ids']
            for employee_id in obj['employee_ids']:
                ttyme = datetime.fromtimestamp(time.mktime(time.strptime(obj['period_from'], "%Y-%m-%d")))
                #name = self.pool.get('hr.employee').browse(cr ,uid, obj['employee_ids'] ,context=context).name
                #contract_id = self.pool.get('hr.employee').browse(cr ,uid, obj['employee_ids'] ,context=context).contract_id.id
                name = self.pool.get('hr.employee').browse(cr ,uid, employee_id ,context=context).name
                contract_id = self.pool.get('hr.employee').browse(cr ,uid, employee_id ,context=context).contract_id.id
                struct_id = self.pool.get('hr.contract').browse(cr ,uid, contract_id ,context=context).struct_id.id
                
                print"contract_id=%s"%contract_id
                if not contract_id:
                    obs += '%s, no posee un contrato en el periodo.'%names[employee_id]
                    continue
                #contract_id = contract_id
                vals1 ={ 'employee_id': employee_id, 
                        'contract_id': contract_id,
                        'struct_id':struct_id ,
                        'date_from': obj['period_from'],
                        'date_to': obj['period_to'],
                        'journal_id': obj['journal_id'][0],
                       }  

                vals = dict(employee_id= employee_id, 
                            contract_id=  contract_id,
                            struct_id= struct_id ,
                            date_from=  obj['period_from'],
                            date_to=  obj['period_to'],
                            journal_id=  obj['journal_id'][0],
                            name = ('Rol de Pagos de %s para %s') % (name, tools.ustr(ttyme.strftime('%B-%Y'))),
                            worked_days_line_ids= [(0, 0, dict(code= 'WORK100', 
                                                               contract_id= contract_id, 
                                                               sequence=  1, 
                                                               number_of_days=  30.0, 
                                                               number_of_hours=  240.0, 
                                                               name= 'Dias trabajo normales pagados con el 100%'
                                                               ))]
                            )              
                
                if not payslip_model.search(cr, uid, [(key, '=', val) for key, val in vals1.iteritems()]):                   
                    try:
                        #worked_days_line_ids= {} 
                        #worked_days= payslip_model.get_worked_day_lines(cr, uid, contract_id, obj['period_from'], obj['period_to'], context=context)
                        #vals.update(payslip_model.onchange_employee_id(cr, uid, [], obj['period_from'], obj['period_to'], employee_id,contract_id, context=None)['value'])
                        print" /////vals/////=%s"% vals
                        payslip_id = payslip_model.create(cr, uid, vals, context=context)
                        print" payslip_id =%s"% payslip_id 
                        payslip_model.load_info(cr, uid, [payslip_id], context)
                        payslip_model.compute_sheet(cr, uid, [payslip_id], context)
                        continue
                    except IntegrityError as exc:
                        obs += u'%s:  %s.\n'%(names[employee_id], exc.pgerror)
                    except osv.except_osv as exc:
                        obs += u'%s:  %s.\n'%(names[employee_id], exc.value)
                else:
                    obs += u'%s:  Ya tiene generado un rol de pagos.\n'%names[employee_id]
        self.write(cr, uid, ids, {'state': 'done', 'notes': obs})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Roles de pago generados',
            'res_model': self._name,
            'res_id': ids[0],
            'view_mode': 'form',
            'target': 'new'
        }
    
    _defaults = {
        'state': lambda *a: 'draft',
        'period_from': lambda *a: time.strftime('%Y-%m-01'),
        'period_to': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
    }

wizard_generate_payslip()



class hr_payment_decimos_desde_employee_wizard(osv.osv_memory):
    
    _name = 'hr.payments.decimos.desde.employee.wizard'

    _columns = {
            'journal_id': fields.many2one('account.journal', 'Método de pago', required=True, domain=[('type', '=', 'bank')]),
            'date':fields.date('Fecha', default=time.strftime('%Y-%m-%d'),required=True),
            'ref':fields.char('Referencia', required=True),
            #'employee_ids':fields.many2many('hr.employee', 'employee_nomina_rel', 'address_home_id', 'employee_id', 'Employees'),
            'employee_ids':fields.many2many('hr.employee', 'employee_decimo_rel', 'wiz_id', 'employee_id', 'Empleados',
                                         domain=[('state_emp', '=', 'active')], default=lambda self: self._get_defaults('employee_ids')),

            'pago_dt':fields.boolean('Pago Decimo Tercero', default= False, readonly=False,),
            'pago_dc':fields.boolean('Pago Decimo Cuarto', default= True , readonly=False)
    }

    
    
    def _get_defaults(self, cr, uid, field, context=None):
        context, res = context or {}, {}
        if context.get('active_model') == 'hr.employee':
            employee_ids = self.pool.get('hr.employee').search(cr, uid, [('id', 'in', context['active_ids']),
                                                                         ('state_emp', '=', 'active')])
            #print"employee_ids=%s"%employee_ids
            res['employee_ids'] = employee_ids
        return res.get(field)

    def compute_decimos(self, cr, uid, ids, context):
        voucher_model = self.pool.get('account.voucher')
        for obj in self.read(cr, uid, ids, ['date','ref','employee_ids','journal_id','pago_dt','pago_dc']):
            #print"obj=%s"%obj
            names = dict(self.pool.get('hr.employee').name_get(cr, uid, obj['employee_ids']))
            print"obj['employee_ids']=%s"%obj['employee_ids']
            
            for employee_id in obj['employee_ids']:                      
                provision =self.pool.get('hr.employee').browse(cr ,uid, employee_id ,context=context).pago_provisiones
                print"provision=%s"%provision
                if provision == False:
                    journal=obj['journal_id'][0]#self.journal_id.id
                    partner=self.pool.get('hr.employee').browse(cr ,uid, employee_id ,context=context).address_home_id.id
                    account=self.pool.get('account.journal').browse(cr ,uid, journal ,context=context).default_credit_account_id.id
                    company=self.pool.get('hr.employee').browse(cr ,uid, employee_id ,context=context).company_id.id,
                    currency=self.pool.get('hr.employee').browse(cr ,uid, employee_id ,context=context).company_id.currency_id.id
                    
                    print"partner=%s"%partner
                    print"account=%s"%account
                    print"company=%s"%company
                    print"currency=%s"%currency
                    print"journal=%s"%journal            
                
                    vals = dict(
                                reference=obj['ref'],
                                partner_id=partner,
                                journal_id=journal,
                                amount=0.0,
                                currency_id=currency,
                                type='payment', 
                                date=obj['date'],
                                company_id=company,
                                account_id=account,
                                pre_line= True,
                                payment_option='without_writeoff',
                                pago_dc=obj['pago_dc'],
                                pago_dt=obj['pago_dt'],
                                narration=obj['ref'],
                                transfers=[]
                                )
                        
                 
                    #voucher =self.env['account.voucher'].create(vals)
                    voucher = voucher_model.create(cr, uid, vals, context=context)
                else:
                
                    continue

hr_payment_decimos_desde_employee_wizard()

     