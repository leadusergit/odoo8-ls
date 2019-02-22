# -*- coding: utf-8 -*-
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

from openerp import api, tools
from openerp.osv import osv, fields
from psycopg2 import IntegrityError

    
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

     