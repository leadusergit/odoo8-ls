# -*- coding: utf-8 -*-

import time
import datetime
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging
import openerp.addons.decimal_precision as dp
from openerp.addons.hr_nomina import payroll_tools
    
class account_voucher(osv.osv):

    _inherit = "account.voucher"
   
    _columns = {                
        'pago_dt': fields.boolean('Pago Decimo Tercero', default= False,readonly=False, states={'done': [('readonly', True)]}),
        'pago_dc': fields.boolean('Pago Decimo Cuarto', default= False, readonly=False, states={'done': [('readonly', True)]}),
        'pagod_ref': fields.many2one('hr.employee.provision.pay','ID Rol Decimos',help='Referencia al documento de decimos desde el cual se generaron los vouchers')

    }


    def onchange_partner_id3(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):
       
        print"date=%s"%date
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
#        ctx.update({'date': date,'codigo':'dc' })
        ctx.update({'date': date })  
                  
        vals6 = self.recompute_voucher_lines3(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=ctx)
        vals7 = self.recompute_payment_rate(cr, uid, ids, vals6, currency_id, date, ttype, journal_id, amount, context=context)      

        for key in vals6.keys():
            res[key].update(vals6[key])
        for key in vals7.keys():
            res[key].update(vals7[key])               
        
        if ttype == 'sale':
            del(res['value']['line_dr_ids'])
            del(res['value']['pre_line'])
            del(res['value']['pago_dc'])
            del(res['value']['pago_dt'])
            del(res['value']['payment_rate'])
        elif ttype == 'purchase':
            del(res['value']['line_cr_ids'])
            del(res['value']['pre_line'])
            del(res['value']['pago_dc'])
            del(res['value']['pago_dt'])
            del(res['value']['payment_rate'])
            
            
            print"res=%s"%res
        return res
        
    
    def recompute_voucher_lines3(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
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

        dc=self.pool['account.voucher'].browse(cr ,uid, ids,context=context).pago_dc
        dt=self.pool['account.voucher'].browse(cr ,uid, ids,context=context).pago_dt
        print"dc,dt=%s"%dc,dt       
               
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
            ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
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
        id_emp = employee_pool.search(cr, uid, [('address_home_id', '=', partner_id)])    
        provisiones=self.pool.get('hr.employee').browse(cr ,uid, id_emp ,context=context).pago_provisiones
        """"""   
        for line in account_move_lines:
            valores=line.name                     
            if dc ==True and 'Cuarto' in valores and 'Retenido' in valores:#and str(line.date)[:4]== int(str(date)[:4])-1 :# and int(str(line.date)[5:7]) <= 8: #1
                print"valores=%s"%valores 
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
            
            elif dt == True and 'Tercero' in valores and 'Retenido' in valores:#and str(line.date)[:4]== int(str(date)[:4])-1 :# and int(str(line.date)[5:7]) <= 8: #1
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
            
        
        return default  
    
  
    def onchange_line_ids3(self, cr, uid, ids, line_dr_ids, line_cr_ids, amount, voucher_currency, type, context=None):
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
    
    
    
    def onchange_amount3(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id,  context=None):
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
        res = self.recompute_voucher_lines3(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=ctx)
        vals = self.onchange_rate(cr, uid, ids, rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
        for key in vals.keys():
            res[key].update(vals[key])
        return res
    
    
    def onchange_journal3(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, pago_dc ,context=None):
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
            res = self.onchange_partner_id3(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context)
            for key in res.keys():
                vals[key].update(res[key])
        return vals