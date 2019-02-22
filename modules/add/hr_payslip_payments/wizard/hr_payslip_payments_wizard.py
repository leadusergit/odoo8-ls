# -*- coding: utf-8 -*-

import time
from openerp import netsvc

import datetime
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.addons.hr_nomina import payroll_tools
from openerp import models, fields, api
from openerp.exceptions import ValidationError
import logging
from docutils.nodes import line_block


class hr_payslip_paid_wizard(osv.osv_memory):
    """Validar pagos seleccionados en objeto account.voucher"""
    _name = "hr.payslip.paid.wizard"
    _description = "Pagar Payslips"

    def confirm_paid(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        proxy = self.pool['account.voucher']
        for recordp in proxy.browse(cr, uid, active_ids, context=context):
            if recordp.state not in ('draft'):
                raise osv.except_osv(_('Warning!'), _("Error Rol"))
            recordp.proforma_voucher()
            
        return {'type': 'ir.actions.act_window_close'}
    


class hr_payments_wizard(models.TransientModel):
    """Crea voucher desde hr.payslip para pago de nomina"""
    _name = 'hr.payments.wizard'

    journal_id=fields.Many2one('account.journal', 'Método de pago', required=True, domain=[('type', '=', 'bank')])
    date=fields.Date('Fecha', default=time.strftime('%Y-%m-%d'),required=True)
    period_id=fields.Many2one('account.period', 'Periodo', required=True)
    ref=fields.Char('Referencia', required=True)
    payslip_ids=fields.Many2many('hr.payslip', required=True, domain=[('state', '=', 'done')],
                                   default=lambda self: self._context.get('active_ids', []))
    paid_rol=fields.Boolean('Pago de Rol',default= True,readonly=False)

    
    @api.onchange('date')
    def onchange_date(self):
        period_id = self.env['account.period'].find(self.date)
        self.period_id = period_id

    @api.multi
    def pay(self):
        self = self[0]
        for payslip in self.payslip_ids:
            voucher_obj =self.env['account.voucher']
            print"self.payslip_ids=%s"%self.payslip_ids
            if payslip.state == 'done':
                partner=payslip.employee_id.address_home_id.id
                account=self.journal_id.default_credit_account_id.id
                company= payslip.company_id.id,
                currency=payslip.company_id.currency_id.id
                journal=self.journal_id.id
                move_id=payslip.move_id.id
                #period=self.period_id.id
                print"partner=%s"%partner
                print"account=%s"%account
                print"company=%s"%company
                print"currency=%s"%currency
                print"journal=%s"%journal
                print"move_id=%s"%move_id
               
                
                vals = dict(
                            reference=self.ref,
                            partner_id=partner,
                            journal_id=self.journal_id.id, 
                            amount=0.0,
                            currency_id=currency,
                            type='payment', 
                            date=self.date,
                            company_id=company,
                            account_id=account,
                            pre_line= True,
                            payment_option='without_writeoff',
                            paid_rol=True,
			    period_id=self.period_id.id,
                            narration=self.ref,
                            #line_ids=voucher_obj.onchange_partner_id1(partner_id=partner,journal_id=self.journal_id.id, amount=0, currency_id=currency, ttype='payment', date=self.date,context=None)
                            transfers=[])
  
                """vals1 = dict(amount=0.0,
                             reference=self.ref,
                             partner_id=partner,
                             journal_id=self.journal_id.id, 
                             type='payment', 
                             date=self.date,
                             company_id=company,
                             account_id=account,                         
                             transfers=[])"""
                
                vals1 = {'account_id':account,
                         'partner_id':partner,
                         'reference':self.ref,
                         'pre_line': True, 
                         'date':self.date,                        
                         'type':'payment'
                        }
     
                #line_ids = voucher_obj.onchange_partner_id1(partner_id=partner,journal_id=self.journal_id.id, amount=0, currency_id=currency, ttype='payment', date=self.date,context=None)
                #vals1.update(line_ids['value'])
                #line_ids['value'].update(vals1)
                #line_ids.update(vals1)
                #voucher =self.env['account.voucher'].create(line_ids)
                """se crea el encabezado del voucher de pago"""
                voucher =self.env['account.voucher'].create(vals)

                """se leen los registros del asiento contable y se busca el Salario Neto a recibir"""
                move_line_pool = self.env['account.move.line']
                account_move_lines = self.env['account.move.line'].search([("move_id", "=", move_id),("partner_id", "=", partner)])
                print" account_move_lines =%s"% account_move_lines
                
                for line in account_move_lines:
                    print"line=%s"% line
                    print"line.name =%s"%line.name 
                    print"line.credit =%s"%line.credit                           
                   
                    if 'Neto' in line.name or 'neto'in line.name or 'recibir'in line.name:

                        vals2=dict(amount= line.credit)
                        print"vals2=%s"%vals2

                        line_dr_ids = dict(reconcile= True,
                                            move_line_id = line.id,
                                            voucher_id =voucher.id, 
                                            amount_unreconciled= line.credit,
                                            amount=line.credit,
                                            amount_original=line.credit,
                                            account_id=line.account_id.id,
                                            type = 'dr')
                                       
                        print"line_dr_ids =%s"%line_dr_ids
                    
                #vals.update(line_dr_ids=line_dr_ids)
                #vals['transfers'].append(dict(line_ids=line_dr_ids))
                """se crea el detalle del voucher"""
                voucher_line =self.env['account.voucher.line'].create(line_dr_ids)
                """se actualiza el valor del monto en la cabecera del vocher"""
                voucher.update(vals2)
                #voucher.proforma_voucher()              

            
"""class account_voucher_nomina(osv.osv_memory):

    _name ='account.voucher.nomina'
    
    _columns = {
        #'partner_ids': fields.many2many('res.partner', 'partner_nomina_rel', 'ident_num', 'partner_id', 'Employees'),
        'employee_ids': fields.many2many('hr.employee', 'employee_nomina_rel', 'address_home_id', 'employee_id', 'Employees'),

    }
  
    def compute_sheet_nomina(self, cr, uid, ids, context=None):
        emp_pool = self.pool.get('hr.employee')
        #emp_pool = self.pool.get('res.partner')
        run_pool = self.pool.get('account.voucher')
        voucher_lines_pool = self.pool.get('account.voucher.line')

        line_ids= []
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        run_data = {}
        if context and context.get('active_id', False):
            run_data = run_pool.read(cr, uid, [context['active_id']], ['date','reference','journal_id','company_id'])[0]
        from_date =  run_data.get('date', False)
        reference = run_data.get('reference', False)
        journal = run_data.get('journal_id', False)
        company = run_data.get('company_id', False)

        print"time=%s"%from_date #time.strftime("%y-%m-%d")
        if not data['employee_ids']:
            raise osv.except_osv(_("Warning!"), _("You must select employee(s) to generate payslip(s)."))
        for emp in emp_pool.browse(cr, uid, data['employee_ids'], context=context):
            slip_data = run_pool.onchange_partner_id1(cr, uid, [],emp.address_home_id.id,19,0,3,'payment',from_date,context=None)
            res = {
                'partner_id': emp.address_home_id.id,
                'journal_id':19,#journal,
                'amount':0,
                'currency_id':3,
                'ttype':'payment',
                'date': from_date,
                'reference': reference,                
                'company_id':1, 
                'account_id':523,#emp.credit_account.id,
                'payment_option':'without_writeoff',
                #'line_ids': [(0, 0, x) for x in slip_data['value'].get('line_dr_ids','line_cr_ids')],

           }
            line_ids.append(run_pool.create(cr, uid, res, context=context))
        #run_pool.onchange_partner_id1(cr, uid, line_ids ,emp.address_home_id.id,19,0,3,'payment',from_date,context=None)

        return {'type': 'ir.actions.act_window_close'}


"""  

"""class hr_payment_decimos_wizard(models.TransientModel):
    
    _name = 'hr.payments.decimos.wizard'

    
    journal_id=fields.Many2one('account.journal', 'Método de pago', required=True, domain=[('type', '=', 'bank')])
    date=fields.Date('Fecha', default=time.strftime('%Y-%m-%d'),required=True)
    #period_id=fields.Many2one('account.period', 'Periodo', required=True)
    ref=fields.Char('Referencia', required=True)
    payslip_ids=fields.Many2many('hr.payslip', required=True, domain=[('state', '=', 'done')],
                                   default=lambda self: self._context.get('active_ids', []))
    #codigo=fields.Selection([
    #        ('dt', 'Décimo Tercero'),
    #        ('dc', 'Décimo Cuarto'),], 'Tipo de Nómina', select=True, readonly=False, copy=False)
    pago_dt=fields.Boolean('Pago Decimo Tercero', default= False, readonly=False,)
    pago_dc= fields.Boolean('Pago Decimo Cuarto', default= True , readonly=False)
      
    @api.onchange('date')
    def onchange_date(self):
        period_id = self.env['account.period'].find(self.date)
        self.period_id = period_id

    
    @api.multi
    def pay_decimos(self):
        self = self[0]
        for payslip in self.payslip_ids:
            voucher_obj =self.env['account.voucher']
            print"payslip.state=%s"%payslip.state
            if payslip.state == 'paid':
                partner=payslip.employee_id.address_home_id.id
                account=self.journal_id.default_credit_account_id.id
                company= payslip.company_id.id,
                currency=payslip.company_id.currency_id.id
                journal=self.journal_id.id
                move_id=payslip.move_id.id
                #codigo=self.codigo
                print"partner=%s"%partner
                print"account=%s"%account
                print"company=%s"%company
                print"currency=%s"%currency
                print"journal=%s"%journal
                print"move_id=%s"%move_id
                #print"codigo=%s"%codigo
              
                
                vals = dict(
                            reference=self.ref,
                            partner_id=partner,
                            journal_id=self.journal_id.id, 
                            amount=0.0,
                            currency_id=currency,
                            type='payment', 
                            date=self.date,
                            company_id=company,
                            account_id=account,
                            pre_line= True,
                            payment_option='without_writeoff',
                            #codigo= codigo,
                            pago_dc=self.pago_dc,
                            pago_dt=self.pago_dt,
                            transfers=[]
                            )
                        
                 
                voucher =self.env['account.voucher'].create(vals)

"""                         
            
