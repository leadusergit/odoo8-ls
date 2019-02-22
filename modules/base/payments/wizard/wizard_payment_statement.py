# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Asset work
#    Copyright (C) 2010-2010 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
#creador  *EG

import time
import datetime
from openerp.osv import osv
from openerp.osv import fields
from mx import DateTime
import openerp.netsvc
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime
import openerp.tools
from openerp.tools.translate import _
from openerp.tools import config
import calendar
from lxml import etree

class wizard_payment_statement(osv.osv_memory):
    _name = "wizard.payment.statement"
    _description = 'Cambios sobre el Extracto Bancario'
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_cancel_check(self, cr, uid, statement_lines):
        #print 'act_cancel_check', statement_lines
        res = []
        unlink_ids = []
        
        '1) Rompo la concilacion ojo esto no borra los asientos del pago'
        
        for line in self.pool.get('account.bank.statement.line').browse(cr, uid, statement_lines):
            if line.reconcile_id: #El reconcile de la linea tiene la cuenta y esta cuenta tiene la concilacion total o parcial
                for x in line.reconcile_id.line_ids:
                    res.append(x.id)
            #print "res_move_line", res
            if res:
                recs = self.pool.get('account.move.line').read(cr, uid, res, ['reconcile_id', 'reconcile_partial_id'])
                
                full_recs = filter(lambda x: x['reconcile_id'], recs)
                rec_ids = [rec['reconcile_id'][0] for rec in full_recs]
                
                part_recs = filter(lambda x: x['reconcile_partial_id'], recs)
                part_rec_ids = [rec['reconcile_partial_id'][0] for rec in part_recs]
            
                unlink_ids += rec_ids
                unlink_ids += part_rec_ids
            
            if len(unlink_ids):
                #print "entra", unlink_ids
                self.pool.get('account.move.reconcile').unlink(cr, uid, unlink_ids)
        #Termino de romper la concilacion la concilacion
        
        '2) Debo registrar la devolucion del cheque'
        return True
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        ##print "fields_view_get ***", context 
        res = super(wizard_payment_statement, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if context and 'statement_lines' in context:
            view_obj = etree.XML(res['arch'])
            child = view_obj.getchildren()[0]
            domain = '[("id", "in", ' + str(context['statement_lines']) + ')]'
            field = etree.Element('field', attrib={'domain': domain , 'name':'statement_lines', 'colspan':'4', 'height':'300', 'width':'800', 'nolabel':"1"})
            child.addprevious(field)
            res['arch'] = etree.tostring(view_obj)
        return res
    
    def get_option(self, cr, uid, ids, context=None):
        ##print 'get_option', ids
        statement_obj = self.pool.get('account.bank.statement')
        this = self.browse(cr, uid, ids[0])
        tipo = this.type
        ##print 'tipo', tipo
        obj_model = self.pool.get('ir.model.data')
        if tipo == "cancel_check":
            for item in statement_obj.browse(cr, uid, context.get('active_ids', [])):
                model_data_ids = obj_model.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'wizard_payment_statement_search')])
                context.update({'statement_lines': map(lambda x : x.id , item.line_ids)})
                context.update({'date': this.date})
            
        else: #cuando se trata de transferencia
            model_data_ids = obj_model.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'payment_bank_statment_update_date')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        #print 'resource_id', resource_id 
        return {'name': ('Seleccionar Lineas Extracto'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wizard.payment.statement',
                'views': [(resource_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
        }
    
    def _check_inv_auth(self, cr, uid, in_invoice):
        #print "_check_inv_auth", in_invoice
        for inv in self.pool.get('account.invoice').browse(cr, uid, in_invoice):
            if inv.type in ['in_invoice', 'in_refund']:
                if inv.auth_inv_id.doc_type != 'custom':
                    continue
                if inv.auth_inv_id.num_start <= int(inv.number_inv_supplier) <= inv.auth_inv_id.num_end:
                    return True
                else:
                    raise osv.except_osv(('¡Error!'), ('¡El numero de la factura esta incorrecto!\n') + 
                        ('El numero de la factura (%s) que se espera debe estar en el rango (%s) y (%s)') % (inv.number_inv_supplier, inv.auth_inv_id.num_start, inv.auth_inv_id.num_end))            
            elif inv.type in ['out_invoice', 'out_refund']:
                return True
    
    def _is_number(self, ref):
        if ref:
            numero = True
            for x in ref:
                if x not in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0'):
                    numero = False
                    break
        return numero
        
    
    
    def cancel_check_2(self, cr, uid, ids, context=None):
        res_currency_obj = self.pool.get('res.currency')
        res_users_obj = self.pool.get('res.users')
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')
        account_bank_statement_line_obj = self.pool.get('account.bank.statement.line')
        account_bank_statement_line_rel_obj = self.pool.get('account.bank.statement.line.rel')
        account_invoice_obj = self.pool.get('account.invoice')
        statement_reconcile_obj = self.pool.get('account.bank.statement.reconcile')
        account_period_obj = self.pool.get('account.period')
        
        company_currency_id = res_users_obj.browse(cr, uid, uid, context=context).company_id.currency_id.id
        
        res = {}
        statement_obj = self.pool.get('account.bank.statement')
        
        ref = ''
        if context is None:
            context = {}
            
        data = self.browse(cr, uid, ids)[0]
        line_ids = data.statement_lines
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}
        
        invoices_id = []
        
        account_move_line_ids = []
        date_move = context.get('date')
        period_id = account_period_obj.find(cr, uid, dt=context.get('date'))
        move_lines = []
        
        for line in line_ids:
            ultima_line = line
            move_id = line.statement_id.move_id.id
            if line.invoice_id:
                invoices_id.append(line.invoice_id)
            if line.out_invoice_id:
                invoices_id.append(line.out_invoice_id)
            
            #print ' move_id ', move_id
            #print ' statement_line_id ', line.id    
            account_move_line_ids += account_move_line_obj.search(cr, uid, [('move_id', '=', move_id), ('statement_line_id', '=', line.id)])
                
        #print ' account_move_line_ids ', account_move_line_ids
        
        account_move_obj.button_cancel(cr, uid, [move_id], context)
        account_move_line_obj._remove_move_reconcile(cr, uid, account_move_line_ids, context=None)
        context['invoice_ids'] = invoices_id
        account_invoice_obj.change_state_paid_to_open(cr, uid, ids, context)
        
        #if ultima_line.statement_id.journal_id.type == 'bank':
            
        journal_data = ultima_line.statement_id.journal_id
        cuenta_banco_id = journal_data.default_debit_account_id.id
        statement_data = ultima_line.statement_id
        
        move_lines_data = account_move_line_obj.browse(cr, uid, account_move_line_ids)
        for move_line_data in move_lines_data:
            if move_line_data.account_id.id == cuenta_banco_id:
                continue
            
            if move_line_data.debit:
                
                amount = move_line_data.debit
                
                move_line_credit = {
                    'name': move_line_data.name,
                    'date': date_move,
                    'period_id': period_id[0],
                    'ref': 'Dev. Valores' + ref,
                    #'move_id': move_id,
                    'partner_id': ((move_line_data.partner_id) and move_line_data.partner_id.id) or False,
                    'account_id': (move_line_data.account_id) and move_line_data.account_id.id,
                    'credit': ((amount > 0) and amount) or 0.0,
                    'debit': ((amount < 0) and -amount) or 0.0,
                    'statement_id': statement_data.id,
                    'journal_id': journal_data.id,
                    'currency_id': statement_data.currency.id,
                     #*Em
                    'invoice_id':move_line_data.invoice_id,
                    'date_maturity':move_line_data.date_maturity,
                    'employee_id':move_line_data.employee_id,
                    'type_hr':move_line_data.type_hr,
                    'payment_form':move_line_data.payment_form or False,
                    'type_move':'ANU'
                }
                
                
                move_lines.append((0, 0, move_line_credit))
               
                amount = (-1) * move_line_data.debit
                
                move_line_debit = {
                    'name': move_line_data.name,
                    'date': date_move,
                    'period_id': period_id[0],
                    'ref': 'Dev. Valores' + ref,
                    #'move_id': move_id,
                    'partner_id': ((move_line_data.partner_id) and move_line_data.partner_id.id) or False,
                    'account_id': cuenta_banco_id,
                    'credit': ((amount > 0) and amount) or 0.0,
                    'debit': ((amount < 0) and -amount) or 0.0,
                    'statement_id': statement_data.id,
                    'journal_id': journal_data.id,
                    'currency_id': statement_data.currency.id,
                     #*Em
                    'invoice_id':move_line_data.invoice_id,
                    'date_maturity':move_line_data.date_maturity,
                    'employee_id':move_line_data.employee_id,
                    'type_hr':move_line_data.type_hr,
                    'payment_form':move_line_data.payment_form or False,
                    'type_move':'ANU'
                }
                
                move_lines.append((0, 0, move_line_debit))
                
                
            else:
                amount = (-1) * move_line_data.credit
                move_line_debit = {
                    'name': move_line_data.name,
                    'date': date_move,
                    'period_id': period_id[0],
                    'ref': 'Dev. Valores' + ref,
                    #'move_id': move_id,
                    'partner_id': ((move_line_data.partner_id) and move_line_data.partner_id.id) or False,
                    'account_id': (move_line_data.account_id) and move_line_data.account_id.id,
                    'credit': ((amount > 0) and amount) or 0.0,
                    'debit': ((amount < 0) and -amount) or 0.0,
                    'statement_id': statement_data.id,
                    'journal_id': journal_data.id,
                    'currency_id': statement_data.currency.id,
                    'invoice_id':move_line_data.invoice_id,
                    'date_maturity':move_line_data.date_maturity,
                    'employee_id':((move_line_data.employee_id) and move_line_data.employee_id.id) or False,
                    'type_hr':move_line_data.type_hr or False,
                    'payment_form':move_line_data.payment_form or False,
                    'type_move':'ANU'
                }
            
                move_lines.append((0, 0, move_line_debit))
                
                amount = move_line_data.credit
                move_line_credit = {
                    'name': move_line_data.name,
                    'date': date_move,
                    'period_id': period_id[0],
                    'ref': 'Dev. Valores' + ref,
                    #'move_id': move_id,
                    'partner_id': ((move_line_data.partner_id) and move_line_data.partner_id.id) or False,
                    'account_id': cuenta_banco_id,
                    'credit': ((amount > 0) and amount) or 0.0,
                    'debit': ((amount < 0) and -amount) or 0.0,
                    'statement_id': statement_data.id,
                    'journal_id': journal_data.id,
                    'currency_id': statement_data.currency.id,
                     #*Em
                    'invoice_id':move_line_data.invoice_id,
                    'date_maturity':move_line_data.date_maturity,
                    'employee_id':((move_line_data.employee_id) and move_line_data.employee_id.id) or False,
                    'type_hr':move_line_data.type_hr or False,
                    'payment_form':move_line_data.payment_form or False,
                    'type_move':'ANU'
                }
                move_lines.append((0, 0, move_line_credit))
            
        
        #print ' move_lines ', move_lines
#         for move_line in move_lines:
            #print ' move_line ', move_line
            
        i = 0
        vals_move = {
            'bandera':i,
            'tipo':"extracto",
            'journal_id': statement_data.journal_id.id,
            'period_id': period_id[0],
            'date': date_move,
            'name':statement_data.no_comp_rel,
            'ref':'Dev. Valores N.C.' + statement_data.no_comp_rel,
            'tipo_comprobante':statement_data.tipo_comprobante,
            'line_id':move_lines,
        }
        move_dev_id = account_move_obj.create(cr, uid, vals_move, context=context)
        #print ' post **** '
        account_move_obj.post(cr, uid, [move_dev_id], context=None)
        account_move_obj.post(cr, uid, [move_id], context=None)
        
        for line in line_ids:
            account_bank_statement_line_obj.write(cr, uid, line.id, {'state':'draft'})
        
        return {'type':'ir.actions.act_window_close' }  
            
                  
    
    def cancel_check(self, cr, uid, ids, context=None):
        #Tengo que hacer un formulariio donde marque las lineas que quiere anular
        #print "entra al cancel", ids
        #print 'context', context
        res_currency_obj = self.pool.get('res.currency')
        res_users_obj = self.pool.get('res.users')
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')
        account_bank_statement_line_obj = self.pool.get('account.bank.statement.line')
        account_bank_statement_line_rel_obj = self.pool.get('account.bank.statement.line.rel')
        invoice_obj = self.pool.get('account.invoice')
        statement_reconcile_obj = self.pool.get('account.bank.statement.reconcile')
        account_period_obj = self.pool.get('account.period')
        
        company_currency_id = res_users_obj.browse(cr, uid, uid, context=context).company_id.currency_id.id
        
        
        res = {}
        statement_obj = self.pool.get('account.bank.statement')
        
        ref = ''
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, [], context=context)[0]
        line_ids = data['statement_lines']
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}
        #Borro la concilacion y los pagos parciales
        if self.act_cancel_check(cr, uid, line_ids):
            for move in account_bank_statement_line_obj.browse(cr, uid, line_ids):
                date_move = context.get('date')
                period_id = account_period_obj.find(cr, uid, dt=context.get('date'))
                #print  'date_move', date_move
                #print  'period_id', period_id
                amount = -move.amount
                #print 'amount', amount
                in_invoice = move.invoice_id
                out_invoice = move.out_invoice_id
                tipo = ''
                if move.payment_form in ['DINERS', 'AMERICAN']:
                    tipo = str(move.payment_form)
                torec = []
                apunte = False
                if move.apunte:
                    apunte = True
                    
                if out_invoice and not move.apunte:#Facturas de Cliente si es move.apunte es saldo inicial o no es factura
                        out_invoices = invoice_obj.search(cr, uid, [('id', '=', move.out_invoice_id),
                                                                    ('state', 'in', ['open', 'paid']),
                                                                    ])#Veo si existe todavia la factura en cas de ser borrada
                        
                        if not out_invoices:#LA FACTURA ESTA EN BORRADOR se Esta cargando el numero de factura de saldo inicial aqui
                            if move.ref:
                                if self._is_number(move.ref):
                                    entero = int(move.ref)
                                    raise osv.except_osv(_('¡Aviso!'), ('Cargue la linea de ref: %s nuevamente la factura debe estar en borrador o se borro la factura') % (str(entero)))
                                else:
                                    raise osv.except_osv(_('¡Aviso!'), ('Cargue la linea de ref: %s nuevamente') % (str(move.ref).encode('UTF-8')))
                            
                            elif move.name:
                                raise osv.except_osv(_('¡Aviso!'), ('La linea de nombre %s cargue nuevamente o quite para continuar') % (str(move.name).encode('UTF-8')))
                        
                        ref = tools.ustr('Anulación de Cobro:') + move.ref 
                            
                        invoices_pay = account_bank_statement_line_obj.search(cr, uid, [('out_invoice_id', '=', out_invoice),
                                                                                        ('state', '=', 'confirm'),
                                                                                        ('apunte', '=', False)])
                        #print 'out_invoices_pay', invoices_pay
                        
                        
                        if len(invoices_pay) >= 1: #DEbo volver a draft en el boton cancelar
                            
                            for i in invoices_pay:
                                sql = 'select statement_id from account_bank_statement_line_move_rel where move_id=' + str(i)
                                
                                cr.execute(sql)
                                res = map(lambda x: x[0], cr.fetchall())
                                
                                movimiento = account_bank_statement_line_obj.read(cr, uid, i, ['amount'])
                                #print "movimiento", movimiento
                                
                                for x in account_move_obj.browse(cr, uid, res):
                                    
                                    for z in x.line_id:
                                        
                                        if movimiento['amount'] > 0:
                                            if z.credit > 0:
                                                torec.append(z.id)
                                        elif movimiento['amount'] < 0:
                                            if z.debit > 0:
                                                torec.append(z.id)
                                    
                'Saldos iniciales'
                if out_invoice and move.apunte:
                    args = [('out_invoice_id', '=', out_invoice), ('state', '=', 'confirm'), ('apunte', '=', True)]
                    if move.partner_id and move.partner_id.id:
                        args.append(('partner_id', '=', move.partner_id.id))
                    ##print 'args', args 
                    invoices_pay = account_bank_statement_line_obj.search(cr, uid, args)
                    #print 'lineas de iniciales', invoices_pay
                    
                    if len(invoices_pay) >= 1: #DEbo volver a draft en el boton cancelar
                        
                        for i in invoices_pay:
                            sql = 'select statement_id from account_bank_statement_line_move_rel where move_id=' + str(i)
                            
                            cr.execute(sql)
                            res = map(lambda x: x[0], cr.fetchall())
                            
                            movimiento = account_bank_statement_line_obj.read(cr, uid, i, ['amount'])
                            #print "movimiento pagos iniciales", movimiento
                            
                            
                            for x in account_move_obj.browse(cr, uid, res):
                                
                                for z in x.line_id:
                                    
                                    if movimiento['amount'] > 0:#
                                        if z.credit > 0:
                                            torec.append(z.id)
                                    elif movimiento['amount'] < 0:
                                        if z.debit > 0:
                                            torec.append(z.id)
                                            
                    
                'Facturas de Proveedor'                
                if in_invoice and not move.apunte:
                    ref = tools.ustr('Anulación de Pago:') + move.ref
                    in_invoices = invoice_obj.search(cr, uid, [('id', '=', move.invoice_id),
                                                               ('state', 'in', ['open', 'paid']),
                                                               ])
                    if not in_invoices:
                        if move.ref:
                            if self._is_number(move.ref):
                                entero = int(move.ref)
                                raise osv.except_osv(_('¡Aviso!'), ('Cargue la linea de ref: %s nuevamente la factura debe estar en borrador o se borro la factura') % (str(entero)))
                            else:
                                raise osv.except_osv(_('¡Aviso!'), ('Cargue la linea de ref: %s nuevamente') % (str(move.ref).encode('UTF-8')))
                        
                        elif move.name:
                            raise osv.except_osv(_('¡Aviso!'), ('La linea de nombre %s cargue nuevamente o quite para continuar') % (str(move.name).encode('UTF-8')))
                    else:
                        self._check_inv_auth(cr, uid, in_invoices)
                        tipo = invoice_obj.browse(cr, uid, in_invoice).invoice_payment
                    
                    
                    invoices_pay = account_bank_statement_line_obj.search(cr, uid, [('invoice_id', '=', in_invoice),
                                                                                    ('state', '=', 'confirm'),
                                                                                    ('apunte', '=', False)])
                    #print 'invoices_pay proveedor', invoices_pay
                    
                    if len(invoices_pay) >= 1: #DEbo volver a draft en el boton cancelar
                        
                        for i in invoices_pay:
                            sql = 'select statement_id from account_bank_statement_line_move_rel where move_id=' + str(i)
                            
                            cr.execute(sql)
                            res = map(lambda x: x[0], cr.fetchall())
                            movimiento = account_bank_statement_line_obj.read(cr, uid, i, ['amount'])
                            #print "movimiento pagos", movimiento
                            for x in account_move_obj.browse(cr, uid, res):
                                for z in x.line_id:
                                    ##print '', z
                                    if movimiento['amount'] > 0:
                                        if z.credit > 0:
                                            torec.append(z.id)
                                            account_move_line_obj.write(cr, uid, z.id, {'type_move':'ANU'})
                                    elif movimiento['amount'] < 0:
                                        if z.debit > 0:
                                            torec.append(z.id)
                                            account_move_line_obj.write(cr, uid, z.id, {'type_move':'ANU'})
                            
                    if move.payment_form in ['DINERS', 'AMERICAN']:
                        tipo = str(move.payment_form)
                        #print "tipo", tipo
                    
                move_id = account_move_obj.create(cr, uid, {
                                                            'journal_id': move.statement_id.journal_id.id,
                                                            'period_id': period_id[0],
                                                            'date': date_move,
                                                            'name':move.statement_id.num_deposit or move.statement_id.name or '/',
                                                            'ref':'Anulacion ' + str(move.ref),
                                                            'tipo_comprobante':'ComproDiario',
                                                            })
                #print 'dentro del wizard', move_id
                
                account_bank_statement_line_obj.write(cr, uid, [move.id], {'move_ids': [(4, move_id, False)]})
                
                if amount <= 0:
                    """Codigo para identificar si el pago es por tarjeta """
                    if tipo in ['DINERS' , 'AMERICAN' , 'CANJE']:
                        if tipo == 'DINERS':
                            account_id = 1752
                        if tipo == 'AMERICAN':
                            account_id = 1753
                        if tipo == 'CANJE':
                            account_id = 1229
                    else:
                        account_id = move.statement_id.journal_id.default_credit_account_id.id
                        tipo = ''
                else:
                    if tipo in ['DINERS' , 'AMERICAN' , 'CANJE']:
                        if tipo == 'DINERS':
                            account_id = 1752
                        if tipo == 'AMERICAN':
                            account_id = 1753
                        if tipo == 'CANJE':
                            account_id = 1229
                    else:
                        account_id = move.statement_id.journal_id.default_debit_account_id.id
                        tipo = ''
                if move.invoice_id:
                    val = {
                        'name': move.name,
                        'date': date_move,
                        'period_id': period_id[0],
                        'ref': ref,
                        'move_id': move_id,
                        'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                        'account_id': (move.account_id) and move.account_id.id,
                        'credit': ((amount > 0) and amount) or 0.0,
                        'debit': ((amount < 0) and -amount) or 0.0,
                        'statement_id': move.statement_id.id,
                        'journal_id': move.statement_id.journal_id.id,
                        
                        'currency_id': move.statement_id.currency.id,
                         #*Em
                        'invoice_id':move.invoice_id,
                        'date_maturity':move.date_maturity,
                        'employee_id':move.employee_id,
                        'type_hr':move.type_hr,
                        'payment_form':move.payment_form or False,
                        'type_move':'ANU'
                        }
                else:
                    val = {
                    'name': move.name,
                    'date': date_move,
                    'period_id': period_id[0],
                    'ref': ref,
                    'move_id': move_id,
                    'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                    'account_id': (move.account_id) and move.account_id.id,
                    'credit': ((amount > 0) and amount) or 0.0,
                    'debit': ((amount < 0) and -amount) or 0.0,
                    'statement_id': move.statement_id.id,
                    'journal_id': move.statement_id.journal_id.id,
                    'currency_id': move.statement_id.currency.id,
                    'date_maturity':move.date_maturity,
                    'employee_id':move.employee_id,
                    'type_hr':move.type_hr,
                    'payment_form':move.payment_form or False,
                    'out_invoice_id':move.out_invoice_id,
                    'apunte':apunte,
                    'type_move':'ANU'
                    }

                
                """Creacion de Move.Lines la linea del pago del Diario del Extracto Bancario"""
                    
                torec.append(account_move_line_obj.create(cr, uid, val))
                
                if (in_invoice or out_invoice or not out_invoice) and tipo in ['DINERS', 'AMERICAN', 'CANJE']:
                        """Creacion del Debit con codigo de cuenta Dinners"""
                        #print "debit", tipo
                        val = {
                        'name': move.name,
                        'date': date_move,
                        'period_id': period_id[0],
                        'ref': ref,
                        'move_id': move_id,
                        'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                        'account_id': account_id,
                        'credit': ((amount > 0) and amount) or 0.0,
                        'debit': ((amount < 0) and -amount) or 0.0,
                        'statement_id': move.statement_id.id,
                        'journal_id': move.statement_id.journal_id.id,
                        'currency_id': move.statement_id.currency.id,
                         #*Em
                        'invoice_id':move.invoice_id,
                        'date_maturity':move.date_maturity,
                        'card':True,
                        'payment_form':move.payment_form or False,
                        'out_invoice_id':move.out_invoice_id,
                        'apunte':apunte,
                        'type_move':'ANU'
                        }
                        account_move_line_obj.create(cr, uid, val)   
    
                if move.reconcile_id and move.reconcile_id.line_new_ids:
                    for newline in move.reconcile_id.line_new_ids:#Lineas de Ajuste en la parte concilacion
                        if move.invoice_id:
                            account_move_line_obj.create(cr, uid, {
                                'name': newline.name or move.name,
                                'date': date_move,
                                'period_id': period_id[0], 'ref': ref,
                                'move_id': move_id,
                                'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                                'account_id': (newline.account_id) and newline.account_id.id,
                                'debit': newline.amount > 0 and newline.amount or 0.0,
                                'credit': newline.amount < 0 and -newline.amount or 0.0,
                                'statement_id': move.statement_id.id,
                                'journal_id': move.statement_id.journal_id.id,
                                'invoice_id':move.invoice_id,
                                'date_maturity':move.date_maturity,
                                'employee_id':move.employee_id,
                                'type_hr':move.type_hr,
                                'type_move':'ANU'
                            })
                        else:
                            account_move_line_obj.create(cr, uid, {
                                'name': newline.name or move.name,
                                'ref': ref,
                                'date': date_move,
                                'period_id': period_id[0],
                                'move_id': move_id,
                                'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                                'account_id': (newline.account_id) and newline.account_id.id,
                                'debit': newline.amount > 0 and newline.amount or 0.0,
                                'credit': newline.amount < 0 and -newline.amount or 0.0,
                                'statement_id': move.statement_id.id,
                                'journal_id': move.statement_id.journal_id.id,
                                'date_maturity':move.date_maturity,
                                'employee_id':move.employee_id,
                                'type_hr':move.type_hr,
                                'type_move':'ANU'
                            })
    
                """Creacion de linea Credit"""
                if move.invoice_id:
                    account_move_line_obj.create(cr, uid, {
                            'name': move.name,
                            'date': date_move,
                            'period_id': period_id[0],
                            'ref': ref,
                            'move_id': move_id,
                            'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                            'account_id': account_id,
                            'credit': ((amount < 0) and -amount) or 0.0,
                            'debit': ((amount > 0) and amount) or 0.0,
                            'statement_id': move.statement_id.id,
                            'journal_id': move.statement_id.journal_id.id,
                            
                            'currency_id': move.statement_id.currency.id,
                            'invoice_id':move.invoice_id,
                            'date_maturity':move.date_maturity,
                            'employee_id':move.employee_id,
                            'type_hr':move.type_hr,
                            'type_move':'ANU'
                            })
                else:
                    account_move_line_obj.create(cr, uid, {
                            'name': move.name,
                            'ref': ref,
                            'date': date_move,
                            'period_id': period_id[0],
                            'move_id': move_id,
                            'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                            'account_id': account_id,
                            'credit': ((amount < 0) and -amount) or 0.0,
                            'debit': ((amount > 0) and amount) or 0.0,
                            'statement_id': move.statement_id.id,
                            'journal_id': move.statement_id.journal_id.id,
                            'currency_id': move.statement_id.currency.id,
                            'date_maturity':move.date_maturity,
                            'employee_id':move.employee_id,
                            'type_hr':move.type_hr,
                            'out_invoice_id':move.out_invoice_id,
                            'apunte':apunte,
                            'type_move':'ANU'
                            })
                """ 
                Movimiento Credit adicional para 
                Pago con Tarjeta Dinners con Cuenta De Banco por Pagar
                """
                if (in_invoice or out_invoice or not out_invoice) and tipo in ['DINERS', 'AMERICAN', 'CANJE']:
                    account_move_line_obj.create(cr, uid, {
                    'name': move.name,
                    'date': date_move,
                    'period_id': period_id[0],
                    'ref': ref,
                    'move_id': move_id,
                    'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                    'account_id': move.statement_id.journal_id.default_credit_account_id.id,
                    'credit': ((amount < 0) and -amount) or 0.0,
                    'debit': ((amount > 0) and amount) or 0.0,
                    'statement_id': move.statement_id.id,
                    'journal_id': move.statement_id.journal_id.id,
                    'currency_id': move.statement_id.currency.id,
                    'invoice_id':move.invoice_id,
                    'date_maturity':move.date_maturity,
                    'type_hr':move.type_hr,
                    'card':True,
                    'payment_form':move.payment_form or False,
                    'out_invoice_id':move.out_invoice_id,
                    'apunte':apunte,
                    'type_move':'ANU'
                    })
                            
                for line in account_move_line_obj.browse(cr, uid, [x.id for x in account_move_obj.browse(cr, uid, move_id).line_id]):
                    #print 'line adentro del wizard', line
                    if line.state <> 'valid':
                        raise osv.except_osv(_('¡ Error !'),
                                ('Línea de asiento contable "%s" no es válida') % line.name)
                self.pool.get('account.bank.statement.line').write(cr, uid, move.id, {'state':'confirm'})
                
                if move.reconcile_id:
                    if not move.reconcile_id.line_ids:#Se modifico la linea de asiento de la factura
                        if in_invoice and not move.apunte:
                            invoices = invoice_obj.search(cr, uid, [('id', '=', in_invoice), ('state', 'in', ['open', 'paid']), ])
                        if out_invoice and not move.apunte:
                            invoices = invoice_obj.search(cr, uid, [('id', '=', out_invoice), ('state', 'in', ['open', 'paid']), ])
                        
                        if invoices:
                            cr.execute('select \
                                    l.id \
                                from account_move_line l \
                                    left join account_invoice i on (i.move_id=l.move_id) \
                                where i.id in (' + ','.join(map(str, invoices)) + ') and l.account_id=i.account_id')
                            res = map(lambda x: x[0], cr.fetchall())
                            statement_reconcile_obj.write(cr, uid, move.reconcile_id.id, {'line_ids':[(6, 0, res)]}, context=context)
                            torec += map(lambda x: x, res)
                        #Aqui no busco la linea del saldo inicial por que se supone que ese no se puede cambiar a borrador y no se borra el asiento
                    else:
                        #Toma la linea de la cuenta que voy a pagar osea aqui tomo el move_line de la factura o saldo inicial etc.
                        torec += map(lambda x: x.id, move.reconcile_id.line_ids)
                        
                    #Factura de Cliente : move.apunte false, True es saldo inicial
                    if move.out_invoice_id and (not move.apunte):
                        rtotal = 0.0 
                        id_factura = invoice_obj.search(cr, uid, [('id', '=', move.out_invoice_id), ('type', '=', 'out_invoice')])
                        ##print "factura de cliente", id_factura
                        if id_factura:
                            cr.execute ("""
                                    SELECT i.id AS invoice,  i.amount_total AS tinvoice, r.id AS retencion, r.total AS tretencion, r.move_id as move
                                        FROM account_invoice AS i
                                    INNER JOIN account_invoice_retention_voucher AS r
                                        ON (i.ret_voucher_id = r.id)
                                    WHERE r.state = %s
                                        AND i.id = %s
                                    """, ('valid', str(move.out_invoice_id),))
                            
                            res = cr.dictfetchall()
                            ##print "res", res
                            if res:
                                rtotal = res[0]['tretencion']
                                retencion = res[0]['move']
                                movert = account_move_line_obj.search(cr, uid, [('move_id', '=', retencion),
                                                                               ('credit', '!=', 0.0)])
                                context['retencion'] = True
                                torec.append(movert[0]) 
                                
                    account_move_line_obj.reconcile_partial(cr, uid, torec, 'statement', context)
                    
                    #Cambio el estado para saber que se valido esa linea de extracto
                    self.pool.get('account.bank.statement.line').write(cr, uid, move.id, {'state':'confirm'})
                    
                    #DEbo marcar el que escogi para anular el pago
                    anu = "select statement_id from account_bank_statement_line_move_rel where move_id=" + str(move.id)
                    cr.execute(anu)
                    res_anu = map(lambda x: x[0], cr.fetchall())
                    if res_anu:
                        for x in account_move_obj.browse(cr, uid, res_anu):
                            for y in x.line_id:
                                account_move_line_obj.write(cr, uid, [y.id], {'type_move':'ANU'})
                    
                    if move.statement_id.journal_id.entry_posted:
                        account_move_obj.write(cr, uid, [move_id], {'state':'posted'})
        
        return {'type':'ir.actions.act_window_close' }
    
    _columns = {
                'name':fields.char('Label', size=64, required=False, readonly=False),
                'state':fields.selection([('draft', 'Draft'),
                                          ('done', 'Done'), ], 'Estado', select=True, readonly=True),
                'date':fields.date('Fecha'),
                'type':fields.selection([('cancel_check', 'Registrar Devolucion Valores'),
#                                         ('update_date','Actualizar fecha de Pago'),
#                                         ('update_account','Actualizar Cuenta de Pago'),
#                                         ('update_amount','Actualizar Monto de Pago'),
#                                         ('update_journal','Actualizar Diario de Extracto Bancario'),
                                         ], 'Opciones',
                                        help='Se creo esta opción para que el usuario puede modificar'\
                                             ' el extracto bancario sin necesidad de oprimir el boton cancelar ni desconciliar el extracto bancario.'),
                
                'account_id':fields.many2one('account.account', 'Cuenta', required=False),
                'journal_id':fields.many2one('account.journal', 'Diario', required=False),
                'amount':fields.float('Monto', digits=(16, 2)),
                'statement_lines':fields.many2many('account.bank.statement.line', 'statement_line_rel', 'wizard_id', 'stl_id', 'Pagos/Cobros')
                }
    _defaults = {  
        'type': lambda * a: 'cancel_check',
        'date': lambda * a: time.strftime('%Y-%m-%d')
        }
    
    
wizard_payment_statement()


#===============================================================================
# Creo un nuevo wizard que me deje creer anular solo los que quiero
#===============================================================================

class wizard_payment_statement_cancel_check(osv.osv_memory):
    _name = "wizard.payment.statement.cancel.check"
    _description = 'Incompleto'
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
        #print "fields_view_get", context 
        res = super(wizard_payment_statement_cancel_check, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar)
        if context and 'statement_lines' in context:
            view_obj = etree.XML(res['arch'])
            child = view_obj.getchildren()[0]
            domain = '[("id", "in", ' + str(context['statement_lines']) + ')]'
            field = etree.Element('field', attrib={'domain': domain , 'name':'statement_lines', 'colspan':'4', 'height':'300', 'width':'800', 'nolabel':"1"})
            child.addprevious(field)
            res['arch'] = etree.tostring(view_obj)
        return res
    
    
    
    def cancel_check(self, cr, uid, ids, context=None):
        #Tengo que hacer un formulariio donde marque las lineas que quiere anular
        #print "ids", ids
        return True
    
    _columns = {
                'statement_lines':fields.many2many('account.bank.statement.line', 'statement_line_rel', 'wizard_id', 'stl_id', 'Pagos/Cobros')
                }
    
wizard_payment_statement_cancel_check()
