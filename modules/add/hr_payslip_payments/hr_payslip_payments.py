# -*- coding: utf-8 -*-

import time
from openerp import netsvc

import datetime
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.addons.report.models import abstract_report 
from openerp.addons.hr_nomina import payroll_tools
import time, logging, openerp.modules as addons
from openerp.tools import config, email_send
from mako.template import Template
from openerp.report import report_sxw
import logging

_logger = logging.getLogger(__name__)
   
class res_partner(osv.osv):
    
    _inherit = 'res.partner'
    
    _columns = {                
        'nomina':fields.boolean('Nómina',help="Parte de la Nomina"),
        
    }

    
class account_voucher(osv.osv):

    _inherit = "account.voucher"
     
    _columns = {                
        'paid_rol': fields.boolean('Pago de Rol',default= False,readonly=False,states={'done': [('readonly', True)]}),
    }

    def onchange_partner_id1(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):
        print"partner_id=%s"%partner_id
        print"ttype=%s"%ttype
        print"currency_id=%s"%currency_id
        
                
        """Se obtiene el valor del campo nomina del objeto res.partner"""
        employee_pool = self.pool.get('hr.employee')
        id_emp =  employee_pool.search(cr, uid, [('address_home_id', '=', partner_id)])    
        nomina=self.pool.get('hr.employee').browse(cr ,uid, id_emp ,context=context).address_home_id.nomina
        #company=self.pool.get('res.partner').browse(cr ,uid, id_emp ,context=context).is_company
        print" nomina=%s"% nomina   
        #print" company=%s"%company       
            
        if not journal_id:
            return {}
        if context is None:
            context = {}
        #TODO: comment me and use me directly in the sales/purchases views
        res = self.basic_onchange_partner(cr, uid, ids, partner_id, journal_id, ttype, context=context)
        if ttype in ['sale', 'purchase']:
            return res
        ctx = context.copy()
        # not passing the payment_rate currency and the payment_rate in the context but it's ok because they are reset in recompute_payment_rate
        ctx.update({'date': date})

        """Se obtiene el mes en el que se realiza el pago para filtrar los registros del periodo"""
        fecha= str(date)  
        print"fecha=%s"%fecha          
        mes = fecha[5:7]
        print"mes=%s" %mes
        fecha1= time.strftime("%y-%m-%d")
        print"fecha1=%s"%fecha1  
        mes1 = fecha1[3:5]
        print"mes1=%s" %mes1
  

        if  nomina== True :#and mes==mes1:                       
            #print"if nomina"                           
            vals1 = self.recompute_voucher_lines1(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=ctx)
            vals3 = self.recompute_payment_rate(cr, uid, ids, vals1, currency_id, date, ttype, journal_id, amount, context=context)      

            for key in vals1.keys():
                res[key].update(vals1[key])
            for key in vals3.keys():
                res[key].update(vals3[key])               
        """else:
            print"elif" 
            vals = self.recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=ctx)
            vals2 = self.recompute_payment_rate(cr, uid, ids, vals, currency_id, date, ttype, journal_id, amount, context=context)
            for key in vals.keys():
                res[key].update(vals[key])
            for key in vals2.keys():
                res[key].update(vals2[key])"""
      
        
        if ttype == 'sale':
            del(res['value']['line_dr_ids'])
            del(res['value']['pre_line'])
            del(res['value']['payment_rate'])
        elif ttype == 'purchase':
            del(res['value']['line_cr_ids'])
            del(res['value']['pre_line'])
            del(res['value']['payment_rate'])
        return res
    
    
    def recompute_voucher_lines1(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """
        Returns a dict that contains new values and context
        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone
        @return: Returns a dict which contains new values, and context
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
            return False

        if context is None:
            context = {}
        context_multi_currency = context.copy()

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')
        employee_pool = self.pool.get('hr.employee')

        #set default values
        default = {
            'value': {'line_dr_ids': [], 'line_cr_ids': [], 'pre_line': False},
        }
             
        
        paid_rol =self.pool['account.voucher'].browse(cr ,uid, ids,context=context).paid_rol

        # drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])])
        for line in line_pool.browse(cr, uid, line_ids, context=context):
            if line.type == 'cr':
                default['value']['line_cr_ids'].append((2, line.id))
            else:
                default['value']['line_dr_ids'].append((2, line.id))

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id

        total_credit = 0.0
        total_debit = 0.0
        account_type = None
        if context.get('account_id'):
            print"context['account_id']=%s"%context['account_id']
            account_type = self.pool['account.account'].browse(cr, uid, context['account_id'], context=context).type
        if ttype == 'payment':
            if not account_type:
                account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
            if not account_type:
                account_type = 'receivable'

        if not context.get('move_line_ids', False):
            ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id),('date', '<=', date)], context=context)
            #ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)

            #print"ids=%s"%ids
        else:
            ids = context['move_line_ids']
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_lines_found = []

        #order the lines by most old first
        ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)
        print"account_move_lines=%s"%account_move_lines
        
        #account_move_lines1=move_line_pool.browse(cr, uid, account_move_lines, context=context)
        #ids1 = move_line_pool.search(cr, uid, [('name','=','Décimo Tercero Ventas'),('partner_id', '=', partner_id)], context=context)
        #print"ids1=%s"%ids1

        #compute the total debit/credit and look for a matching open amount or invoice
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue

            if invoice_id:
                if line.invoice.id == invoice_id:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_lines_found.append(line.id)
            elif currency_id == company_currency:
                #otherwise treatments is the same but with other field names
                if line.amount_residual == price:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_lines_found.append(line.id)
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_lines_found.append(line.id)
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0

        remaining_amount = price
        #voucher line creation
        """"""
        #id_emp =  employee_pool.search(cr, uid, [('address_home_id', '=', partner_id)])
        #for emp in employee_pool.browse(cr, uid, id_emp , context=context):
          #prov= emp.pago_provisiones
          #fr=emp.maintain_reserve_funds

        id_emp = employee_pool.search(cr, uid, [('address_home_id', '=', partner_id)])    
        prov=self.pool.get('hr.employee').browse(cr ,uid, id_emp ,context=context).pago_provisiones
        fr=self.pool.get('hr.employee').browse(cr ,uid, id_emp ,context=context).maintain_reserve_funds
        print"prov=%s"%prov 
        print"fr=%s"%fr
        """"""   
        for line in account_move_lines:
            valores=line.name
            print"valores=%s"%valores          
            if str(date)[5:7] == str(line.date)[5:7] and prov==False and fr==True and('Cuarto')not in valores and ('Tercero')not in valores and 'Decimo'not in valores and ('Fondos')not in valores and ('Reserva')not in valores: #1
                print"str(date)=%s"%str(date)
                print"str(line.date)=%s"%str(line.date)

                if _remove_noise_in_o2m():
                    continue

                if line.currency_id and currency_id == line.currency_id.id:
                    amount_original = abs(line.amount_currency)
                    amount_unreconciled = abs(line.amount_residual_currency)
                else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                    amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
                    amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=context_multi_currency)
                    line_currency_id = line.currency_id and line.currency_id.id or company_currency
                    rs = {
                          'name':line.move_id.name,
                          'type': line.credit and 'dr' or 'cr',
                          'move_line_id':line.id,
                          'account_id':line.account_id.id,
                          'amount_original': amount_original,
                          'amount': (line.id in move_lines_found) and min(abs(remaining_amount), amount_unreconciled) or 0.0,
                          'date_original':line.date,
                          'date_due':line.date_maturity,
                          'amount_unreconciled': amount_unreconciled,
                          'currency_id': line_currency_id,
                          }
                    remaining_amount -= rs['amount']
                
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
                if not move_lines_found:
                    if currency_id == line_currency_id:
                        if line.credit:
                            amount = min(amount_unreconciled, abs(total_debit))
                            rs['amount'] = amount
                            total_debit -= amount
                        else:
                            amount = min(amount_unreconciled, abs(total_credit))
                            rs['amount'] = amount
                            total_credit -= amount

                if rs['amount_unreconciled'] == rs['amount']:
                    rs['reconcile'] = True

                if rs['type'] == 'cr':
                    default['value']['line_cr_ids'].append(rs)
                else:
                    default['value']['line_dr_ids'].append(rs)

                if len(default['value']['line_cr_ids']) > 0:
                    default['value']['pre_line'] = 1
                elif len(default['value']['line_dr_ids']) > 0:
                    default['value']['pre_line'] = 1
                    
                default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
                
        
            elif str(date)[5:7] == str(line.date)[5:7] and prov==True and fr==False: #2
                print"str(date)1=%s"%str(date)
                print"str(line.date)1=%s"%str(line.date)
                if _remove_noise_in_o2m():
                    continue                

                if line.currency_id and currency_id == line.currency_id.id:
                    amount_original = abs(line.amount_currency)
                    amount_unreconciled = abs(line.amount_residual_currency)
                else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                    amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
                    amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=context_multi_currency)
                    line_currency_id = line.currency_id and line.currency_id.id or company_currency
                    rs = {
                          'name':line.move_id.name,
                          'type': line.credit and 'dr' or 'cr',
                          'move_line_id':line.id,
                          'account_id':line.account_id.id,
                          'amount_original': amount_original,
                          'amount': (line.id in move_lines_found) and min(abs(remaining_amount), amount_unreconciled) or 0.0,
                          'date_original':line.date,
                          'date_due':line.date_maturity,
                          'amount_unreconciled': amount_unreconciled,
                          'currency_id': line_currency_id,
                          }
                    remaining_amount -= rs['amount']
           
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
                if not move_lines_found:
                    if currency_id == line_currency_id:
                        if line.credit:
                            amount = min(amount_unreconciled, abs(total_debit))
                            rs['amount'] = amount
                            total_debit -= amount
                        else:
                            amount = min(amount_unreconciled, abs(total_credit))
                            rs['amount'] = amount
                            total_credit -= amount

                if rs['amount_unreconciled'] == rs['amount']:
                    rs['reconcile'] = True

                if rs['type'] == 'cr':
                    default['value']['line_cr_ids'].append(rs)
                else:
                    default['value']['line_dr_ids'].append(rs)

                if len(default['value']['line_cr_ids']) > 0:
                    default['value']['pre_line'] = 1
                elif len(default['value']['line_dr_ids']) > 0:
                    default['value']['pre_line'] = 1
                default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
            
            elif str(date)[5:7] == str(line.date)[5:7] and prov==False and fr==False and 'Tercero'not in valores and 'Cuarto'not in valores and 'Decimo'not in valores: #3
                print"str(date)2=%s"%str(date)
                print"str(line.date)2=%s"%str(line.date)
                if _remove_noise_in_o2m():
                    continue                

                if line.currency_id and currency_id == line.currency_id.id:
                    amount_original = abs(line.amount_currency)
                    amount_unreconciled = abs(line.amount_residual_currency)
                else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                    amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
                    amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=context_multi_currency)
                    print"amount_unreconciled=%s"%amount_unreconciled
                    line_currency_id = line.currency_id and line.currency_id.id or company_currency
                    rs = {
                          'name':line.move_id.name,
                          'type': line.credit and 'dr' or 'cr',
                          'move_line_id':line.id,
                          'account_id':line.account_id.id,
                          'amount_original': amount_original,
                          'amount': (line.id in move_lines_found) and min(abs(remaining_amount), amount_unreconciled) or 0.0,
                          'date_original':line.date,
                          'date_due':line.date_maturity,
                          'amount_unreconciled': amount_unreconciled,
                          'currency_id': line_currency_id,
                          }
                    remaining_amount -= rs['amount']
                    print"remaining_amount=%s"%remaining_amount
           
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
                if not move_lines_found:
                    if currency_id == line_currency_id:
                        if line.credit:
                            amount = min(amount_unreconciled, abs(total_debit))
                            rs['amount'] = amount
                            total_debit -= amount
                        else:
                            amount = min(amount_unreconciled, abs(total_credit))
                            rs['amount'] = amount
                            total_credit -= amount

                if rs['amount_unreconciled'] == rs['amount']:
                    rs['reconcile'] = True

                if rs['type'] == 'cr':
                    default['value']['line_cr_ids'].append(rs)
                else:
                    default['value']['line_dr_ids'].append(rs)

                if len(default['value']['line_cr_ids']) > 0:
                    default['value']['pre_line'] = 1
                elif len(default['value']['line_dr_ids']) > 0:
                    default['value']['pre_line'] = 1
                default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
           

            elif str(date)[5:7] == str(line.date)[5:7] and prov==True and fr==True and ('Fondos')not in valores and ('Reserva')not in valores: #4
                print"str(date)3=%s"%str(date)
                print"str(line.date)3=%s"%str(line.date)
                if _remove_noise_in_o2m():
                    continue                

                if line.currency_id and currency_id == line.currency_id.id:
                    amount_original = abs(line.amount_currency)
                    amount_unreconciled = abs(line.amount_residual_currency)
                else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                    amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
                    amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=context_multi_currency)
                    line_currency_id = line.currency_id and line.currency_id.id or company_currency
                    rs = {
                          'name':line.move_id.name,
                          'type': line.credit and 'dr' or 'cr',
                          'move_line_id':line.id,
                          'account_id':line.account_id.id,
                          'amount_original': amount_original,
                          'amount': (line.id in move_lines_found) and min(abs(remaining_amount), amount_unreconciled) or 0.0,
                          'date_original':line.date,
                          'date_due':line.date_maturity,
                          'amount_unreconciled': amount_unreconciled,
                          'currency_id': line_currency_id,
                          }
                    remaining_amount -=  rs['amount']
           
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
                if not move_lines_found:
                    if currency_id == line_currency_id:
                        if line.credit:
                            amount = min(amount_unreconciled, abs(total_debit))
                            rs['amount'] = amount
                            total_debit -= amount
                        else:
                            amount = min(amount_unreconciled, abs(total_credit))
                            rs['amount'] = amount
                            total_credit -= amount

                if rs['amount_unreconciled'] == rs['amount']:
                    rs['reconcile'] = True

                if rs['type'] == 'cr':
                    default['value']['line_cr_ids'].append(rs)
                else:
                    default['value']['line_dr_ids'].append(rs)

                if len(default['value']['line_cr_ids']) > 0:
                    default['value']['pre_line'] = 1
                elif len(default['value']['line_dr_ids']) > 0:
                    default['value']['pre_line'] = 1
                default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
        
  
        return default

   
    def onchange_line_ids1(self, cr, uid, ids, line_dr_ids, line_cr_ids, amount, voucher_currency, type, context=None):
        #print "line_dr_ids av202=%s"%line_dr_ids
        context = context or {}
        if not line_dr_ids and not line_cr_ids:
            return {'value':{'writeoff_amount': 0.0}}
        # resolve lists of commands into lists of dicts
        line_dr_ids = self.resolve_2many_commands(cr, uid, 'line_dr_ids', line_dr_ids, ['amount'], context)
        line_cr_ids = self.resolve_2many_commands(cr, uid, 'line_cr_ids', line_cr_ids, ['amount'], context)
        #compute the field is_multi_currency that is used to hide/display options linked to secondary currency on the voucher
        is_multi_currency = False
        #loop on the voucher lines to see if one of these has a secondary currency. If yes, we need to see the options
        for voucher_line in line_dr_ids+line_cr_ids:
            line_id = voucher_line.get('id') and self.pool.get('account.voucher.line').browse(cr, uid, voucher_line['id'], context=context).move_line_id.id or voucher_line.get('move_line_id')
            if line_id and self.pool.get('account.move.line').browse(cr, uid, line_id, context=context).currency_id:
                is_multi_currency = True
                break
        return {'value': {'writeoff_amount': self._compute_writeoff_amount(cr, uid, line_dr_ids, line_cr_ids, amount, type),'amount':-1*(self._compute_writeoff_amount(cr, uid, line_dr_ids, line_cr_ids,0, type)), 'is_multi_currency': is_multi_currency}}

    
    
    def onchange_amount1(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({'date': date})
        
        #read the voucher rate with the right date in the context
        currency_id = currency_id or self.pool.get('res.company').browse(cr, uid, company_id, context=ctx).currency_id.id
        voucher_rate = self.pool.get('res.currency').read(cr, uid, [currency_id], ['rate'], context=ctx)[0]['rate']
        ctx.update({
                    'voucher_special_currency': payment_rate_currency_id,
                    'voucher_special_currency_rate': rate * voucher_rate})
        res = self.recompute_voucher_lines1(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=ctx)
        vals = self.onchange_rate(cr, uid, ids, rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
        for key in vals.keys():
            res[key].update(vals[key])
        return res
 
 
    def onchange_journal1(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        if context is None:
            context = {}
        if not journal_id:
            return False
        journal_pool = self.pool.get('account.journal')
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        if ttype in ('sale', 'receipt'):
            account_id = journal.default_debit_account_id
        elif ttype in ('purchase', 'payment'):
            account_id = journal.default_credit_account_id
            print"account_id534=%s"%account_id
        else:
            account_id = journal.default_credit_account_id or journal.default_debit_account_id
        tax_id = False
        if account_id and account_id.tax_ids:
            tax_id = account_id.tax_ids[0].id

        vals = {'value':{} }
        if ttype in ('sale', 'purchase'):
            vals = self.onchange_price(cr, uid, ids, line_ids, tax_id, partner_id, context)
            vals['value'].update({'tax_id':tax_id,'amount': amount})
        currency_id = False
        if journal.currency:
            currency_id = journal.currency.id
        else:
            currency_id = journal.company_id.currency_id.id

        period_ids = self.pool['account.period'].find(cr, uid, dt=date, context=dict(context, company_id=company_id))
        vals['value'].update({
            'currency_id': currency_id,
            'payment_rate_currency_id': currency_id,
            'period_id': period_ids and period_ids[0] or False
        })
        #in case we want to register the payment directly from an invoice, it's confusing to allow to switch the journal 
        #without seeing that the amount is expressed in the journal currency, and not in the invoice currency. So to avoid
        #this common mistake, we simply reset the amount to 0 if the currency is not the invoice currency.
        if context.get('payment_expected_currency') and currency_id != context.get('payment_expected_currency'):
            vals['value']['amount'] = 0
            amount = 0
        if partner_id:
            res = self.onchange_partner_id1(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context)
            for key in res.keys():
                vals[key].update(res[key])
        return vals
 

class hr_payslip(osv.osv):

    _inherit = "hr.payslip"
    
    _columns={
        'send_mail': fields.boolean('Mensaje enviado', readonly=True),
    }
    
      
    def send_email(self, cr, uid, ids, context):
        """Metodo enviar roles por email"""
        print"config.get('smtp_server') =%s"%config.get('smtp_server')
        if not config.get('smtp_server'):
            _logger.warning('"smtp_server" needs to be set to send mails to users')
            return False
        print"config.get('email_from') =%s"%config.get('email_from')
        if not config.get('email_from'):
            _logger.warning('"email_from" needs to be set to send welcome mails to users')
            return False
        template = addons.get_module_resource('hr_payslip_payments', 'report', 'payroll.mako')
        template = Template(filename=template)
        #template= self.pool['report']._get_report_from_name(cr, uid,'hr_payroll.report_payslip').associated_view(cr, uid,ids,'hr_payroll.report_payslip','hr_payroll.report_payslip')
      
        for payslip in self.browse(cr, uid, ids):
            """Obtiene direccion de correo del empleado"""
            email = payslip.employee_id.work_email
            print"email =%s"%email 
            if not email:
                _logger.warning(u'%s no tiene configurado ningún email' % payslip.employee_id.name)
                continue
            names = dict(self.name_get(cr, uid, ids, context))
            if not email_send(email_from=['email_from'], email_to=[email],subject="Rol de pagos"
                              , body=template.render(o=payslip, name=names[payslip.id].upper())
                              , subtype='html'):
                              #body=template
                              #.render(o=payslip), name=names[payslip.id].upper()),
                              #subtype='html'):
                _logger.error(u'El mensaje para %s no ha sido enviado.' % payslip.employee_id.name)
                continue
            _logger.info(u'El mensaje para %s ha sido enviado con éxito.' % payslip.employee_id.name)
        return True
    
    
    def view_payslip(self, cr, uid, ids, context=None):
        """Metodo link a vista de pago rol objeto account.voucher"""
        if context is None:
            context = dict(context or {})
            
        active_ids = context.get('active_ids', []) or []        
        mod_obj = self.pool.get('ir.model.data')
        employee_pool = self.pool.get('hr.employee')
        voucher_id = []
        
        #compute the number of invoices to display       
        partner=self.pool.get('hr.payslip').browse(cr ,uid, ids ,context=context).employee_id.address_home_id.id
        currency=self.pool.get('hr.payslip').browse(cr ,uid, ids ,context=context).company_id.currency_id.id
        name=self.pool.get('hr.payslip').browse(cr ,uid, ids ,context=context).name
        print"_currency=%s"%currency
        print"_partner=%s"%partner
        res = mod_obj.get_object_reference(cr, uid, 'hr_payslip_payments', 'view_vendor_payment_nomina_form')
        #res = mod_obj.get_object_reference(cr, uid, 'account_voucher', 'view_vendor_payment_form')      
        res_id = res and res[1] or False                
        #self.pool.get('account.voucher').onchange_partner_id1(cr, uid, ids,partner_id=partner,journal_id=8, amount=0, currency_id=currency, ttype='payment', date=time.strftime("%y-%m-%d"),context=None)
        #self.pool.get('account.voucher').onchange_partner_id1(cr, uid, ids,partner,8, 0, currency,'payment', time.strftime("%y-%m-%d"),context=None)
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'hr_payslip_payments', 'view_vendor_payment_nomina_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'account_voucher', 'view_voucher_tree')
        tree_id = tree_res and tree_res[1] or False

        return {
                'name': 'Pago Rol',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'view_id': [res_id],
                'view_name':'view_vendor_payment_nomina_form',
                'res_model': 'account.voucher',
                'context': {'partner_id':partner,'reference':name,
                            'currency_id':currency,'type':'payment'},
                #'nodestroy': True,
                #'target': 'current',
                'views': [(form_id, 'form'), (tree_id, 'tree')],
                ##'res_id': res_id ,
                'type': 'ir.actions.act_window',
        }
    
