# -*- coding: utf-8 -*-
##############################################################################
#
#    Payments Ecuador
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
import time
import openerp.netsvc
from openerp.osv import osv, fields
from openerp.tools.misc import currency
from openerp.tools.translate import _
from datetime import datetime
import openerp.tools
from re import match
from openerp.tools.misc import frozendict
#Aumento libreria
from openerp.addons.decimal_precision import decimal_precision as dp


class payment_cheque(osv.osv):
    _name = 'payment.cheque'
    _description = 'Payment by Cheque.'
    _order = "id Desc"
    
    def print_expense(self, cr, uid, ids, context=None):
        data = {'form': {}}
        cheque = self.browse(cr, uid, ids[0])
        data['form']['type'] = cheque.type
        data['form']['banco'] = cheque.bank_account_id.bank.name
        data['form']['cuenta'] = cheque.bank_account_id.acc_number
        data['form']['beneficiario'] = cheque.name
        data['form']['doc'] = cheque.type == 'in' and 'Comp. de depósito' or 'Cheque'
        data['form']['doc_num'] = cheque.num_cheque
        data['ids'] = [cheque.move.id]
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.move.inex',
                'datas': data}
    
    def amount_debit(self, cr, uid, ids, field_name, args, context):
        res = {}
        debit = 0.00
        for item in self.browse(cr, uid, ids):
            for line in item.cheque_det_ids:
                debit += line.debit
            res[item.id] = str(round(debit, 2))
        return res
    
    def amount_credit(self, cr, uid, ids, field_name, args, context):
        res = {}
        credit = 0.00
        for item in self.browse(cr, uid, ids):
            for line in item.cheque_det_ids:
                credit += line.credit
            res[item.id] = str(round(credit, 2))
        return res 
       
    def amount_cheque(self, cr, uid, ids, field_name, args, context):
        res = {}
        account_bank = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', 1496)])
        neto = 0.00
        for item in self.browse(cr, uid, ids):
            for line in item.cheque_det_ids:
                if line.line_id and line.line_id.account_id.id in account_bank:
                   neto += round(line.line_id.credit or 0.00, 2) - round(line.line_id.debit or 0.00, 2)
                else:
                    continue
            if neto:
                res[item.id] = abs(round(neto, 2))
            else:
                res[item.id] = round(item.amount, 2)
        return res
    
    def _get_type_move(self, cr, uid, ids, field_name, args, context):
        res = {}
        for item in self.browse(cr, uid, ids):
            if item.state == 'printed':
                for x in item.cheque_det_ids:
                    if x.line_id:
                        sql = "update account_move_line set type_move ='CHQ Nro:" + str(item.num_cheque or '') + "' "\
                              "where id=" + str(x.line_id.id)
                        ##print "actualizar",sql
                        cr.execute(sql)
                res[item.id] = 'CHQ'
            else:
                res[item.id] = 'S/CHQ'
        return res
                        
    def change_state(self, cr, uid, ids, context=None):
        context = context or {}
        return self.write(cr, uid, ids, {'state': context.get('new_state', 'draft')})
    
    def save_and_close(self, cr, uid, ids, context=None):
        'Esta función solo se invocará desde la creación del cheque directamente en el account.voucher'
        self.write(cr, uid, ids, {'state': 'done'})
        return {'type': 'ir.actions.act_window_close'}
        return {
            'name': 'Pago con cheque',
            'res_id': ids,
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'payment.cheque',
            'type': 'ir.actions.act_window',
            'multi': False
        }
    
    def onchange_bank_account_id(self, cr, uid, ids, type, bank_account_id):
        res = {'value': {'bank': None, 'num_cheque': None}}
        if bank_account_id:
            bank_id = self.pool.get('res.partner.bank').browse(cr, uid, bank_account_id).bank
            cr.execute('SELECT max(num_cheque::integer) FROM payment_cheque WHERE bank_account_id=%s and type=%s', (bank_account_id, type))
            number = int(cr.fetchone()[0] or 0) + 1
            res['value']['bank'] = bank_id.name
            res['value']['num_cheque'] = str(number).zfill(4)
        return res
    
    def onchange_parnter_id(self, cr, uid, ids, partner_id):
        res = {'value': {'name': False}}
        if partner_id:
            partner = self.pool.get('res.partner').read(cr, uid, partner_id, ['name'])
            res['value']['name'] = partner['name']
        return res
    
    def onchange_move(self, cr, uid, ids, move_id):
        res = {'value': {'amount': 0.0}}
        if move_id:
            move = self.pool.get('account.move').read(cr, uid, move_id, ['amount'])
            res['value']['amount'] = move['amount']
        return res
    
    def _get_date_maturity(self, cr, uid, ids, field, args, context):
        cheques_ids = self.read(cr, uid, ids, ['payment_date'])
        res = {}
        for cheque_id in cheques_ids:
            payment_date = datetime.strptime(cheque_id['payment_date'], '%Y-%m-%d')
            new_year = int(payment_date.strftime('%Y')) + 1
            res[cheque_id['id']] = payment_date.strftime(str(new_year)+'-%m-%d')
        return res
    
    _columns = { 
        'type': fields.selection([('in', 'Ingreso'), ('out', 'Egreso')], 'Tipo', required=True),
        'name': fields.char('Beneficiario', size=100, required=True, readonly=True, states={'draft': [('readonly', False)],
                                                                                            'done': [('readonly', False)]}),
        'num_cheque':fields.char('No. Cheque', size=60, required=True, readonly=True, states={'draft':[('readonly', False)],
                                                                                              'done':[('readonly', False)]}),
        'bank_account_id': fields.many2one('res.partner.bank', 'Cuenta bancaria', required=True, domain=[('partner_id.is_provider', '=', True)],
                                           readonly=True, states={'draft':[('readonly', False)], 'done':[('readonly', False)]}),
        'amount': fields.float('Valor', digits=(12, 2), readonly=True, states={'draft': [('readonly', False)]}),
        'origin': fields.char('Origen', size=128, help='Documento el cual originó este cheque'),
        'observation':fields.text('Observacion', size=1000),
        'state': fields.selection([('draft', 'Borrador'),
                                   ('done', 'Listo'),
                                   ('printed', 'Impreso'),
                                   ('cancel', 'Anulado')], 'Estado', readonly=True),
        'cheque_det_ids':fields.one2many('payment.cheque.detail', 'cheque_id', 'Detalle Asientos'),
        'date_maturity':fields.function(_get_date_maturity, method=True, string='Fecha de Vencimiento', type='date',
                                        store={_name: (lambda self, cr, uid, ids, ctx: ids, ['payment_date'], 10)}),
        'date_invoice':fields.date('Fecha de Factura'),
        'invoice_num': fields.char('No. Factura', size=60),
        'payment_date':fields.date('Fecha Emision Cheque', readonly=True, states={'draft': [('readonly', False)], 'done':[('readonly', False)]}),
        'generation_date':fields.date('Fecha Generacion Cheque'),
        'num_exit_voucher':fields.char('No. Comprobante de Egreso', size=60),
        'move':fields.many2one('account.move', 'Asiento', required=True, domain=[('journal_id.type', '=', 'bank')],
                               readonly=True, states={'draft': [('readonly', False)]}),
        'bank':fields.related('bank_account_id', 'bank', 'name', string='Banco', type='char', size=60, readonly=True, store=True),
        'acc_num':fields.related('bank_account_id', 'acc_number', string='Cuenta contable', type='char', size=60, readonly=True, store=True),
        'ruc':fields.related('partner_id', 'ident_num', type='char', size=60, string='RUC', store=True),
        
        'total_debit':fields.float('Total debe', digits=(12, 2)),
        'total_credit':fields.float('Total haber', digits=(12, 2)),
        
        'debit':fields.function(amount_debit, string='Total Debito', type='char', size=100, method=True, store=False),
        'credit':fields.function(amount_credit, string='Total Credito', type='char', size=100, method=True, store=False),
        
        'partner_id':fields.many2one('res.partner', 'Empresa', required=True, domain=['|',('customer','=',True),('supplier','=',True)],
                                     readonly=True, states={'draft': [('readonly', False)]}),
        'employee_id':fields.integer('Empleado'),
        'card': fields.char('Tarjeta', size=80),
        'period_id': fields.many2one('account.period', 'Periodo', required=False, select=True),
        'type_hr':fields.char('Tipo TH', size=60, required=False, select=True),
        'change_partner':fields.boolean('Cambiar Beneficiario', readonly=True, states={'done':[('readonly', False)],
                                                                                       'printed':[('readonly', False)]}),
        'inv_type':fields.selection([('invoice', 'Factura'),
                                     ('purchase_liq', 'Liquidación de Compra'),
                                     ('anticipo', 'Anticipo'),
                                     ('liquidacion', 'Liquidacion de Viaje'),
                                     ('gas_no_dedu', 'Gasto no Deducible'),
                                     ('doc_inst_est', 'Doc. Emitido Estado'),
                                     ('apunte', 'Asiento por Apunte'),
                                     ('sales_note', 'Nota de Venta')], 'Tipo de Documento', size=60),
        'amount_cheque':fields.function(amount_cheque, string='Valor', method=True, store=False),
        'payment':fields.function(_get_type_move, string='Pago', type='char', size=60, method=True, store=False),
        'company_id': fields.related('move', 'company_id', string='Compañia', readonly=True,
                                     type='many2one', relation='res.company', store=True),
        #=========================================================================================
        'has_reverso':fields.boolean('Reverso',help="Este campo me indica si se realizo un asiento reverso desde los pagos de proveedor cuando se anulo el pago"),
        
    }
    
    _defaults = {
        'state': lambda * a : 'draft',
        'payment_date': lambda *a: time.strftime('%Y-%m-%d'),
        'generation_date': lambda *a: time.strftime('%Y-%m-%d'),
        'type': lambda self, *a: self.__get_defaults(*a).get('type', 'out'),
        'has_reverso': False,
        'name': lambda self, *a: self.__get_defaults(*a).get('name', ''),
        'amount': lambda self, *a: self.__get_defaults(*a).get('amount', 0.0),
        'move': lambda self, *a: self.__get_defaults(*a).get('move'),
        'partner_id': lambda self, *a: self.__get_defaults(*a).get('partner_id'),
        'period_id': lambda self, *a: self.__get_defaults(*a).get('period_id'),
        'origin': lambda self, *a: self.__get_defaults(*a).get('origin', ''),
        'num_exit_voucher': lambda self, *a: self.__get_defaults(*a).get('num_exit_voucher', ''),
        'cheque_det_ids': lambda self, *a: self.__get_defaults(*a).get('cheque_det_ids', ''),
    }
    
    def __get_defaults(self, cr, uid, context):
    #def view_init(self, cr , uid , fields_list, context=None):
        context = context or {}
        ctx = {}
        if context.get('active_id') and context.get('active_model', '') == 'account.voucher':
            voucher_id = self.pool.get('account.voucher').browse(cr, uid, context['active_id'])
            #print 'isinstance', isinstance(context, frozendict)
            ctx['type'] = 'in' if voucher_id.type == 'receipt' else 'out'
            ctx['name'] = voucher_id.partner_id.name
            ctx['amount'] = voucher_id.amount
            ctx['move'] = voucher_id.move_id.id
            ctx['partner_id'] = voucher_id.partner_id.id
            ctx['period_id'] = voucher_id.period_id.id
            ctx['origin'] = 'PAGO #%s (%s)'%(voucher_id.number, voucher_id.id)
            ctx['num_exit_voucher'] = 'PAGO #%s (%s)'%(voucher_id.number, voucher_id.id)
            ctx['cheque_det_ids'] = self.__load_details(cr, uid, voucher_id.move_id.id)
        return ctx
    
    def __load_details(self, cr, uid, move_id):
        move = self.pool.get('account.move').browse(cr, uid, move_id)
        res = []
        for move_line_id in move.line_id:
            res.append({
                'name': move_line_id.name,
                'account': move_line_id.account_id.name,
                'partner': move_line_id.partner_id.name,
                'debit': move_line_id.debit,
                'credit': move_line_id.credit,
                'invoice_num': move_line_id.invoice.number_inv_supplier,
                'date_invoice': move_line_id.invoice.date_invoice,
                'partner_id': move_line_id.partner_id.id,
                'line_id': move_line_id.id,
                'inv_type': move_line_id.invoice.tipo_factura,
                'fecha_transaccion': move_line_id.date,
            })
        return res
    
    def create(self, cr, uid, vals, context={}):
        if vals.has_key('move') and not vals.has_key('cheque_det_ids'):
            vals['cheque_det_ids'] = [(0, 0, aux) for aux in self.__load_details(cr, uid, vals['move'])]
        res_id = super(payment_cheque, self).create(cr, uid, vals, context)
        return res_id
    
    def write (self, cr, uid, ids, vals, context=None):
        items = self.browse(cr, uid, ids, context)
        
        if vals.has_key('num_cheque') and vals['num_cheque']:
            for item in items: 
                for x in item.cheque_det_ids:
                    if x.line_id:
                        sql = "update account_move_line set cheque = True, type_move ='CHQ Nro:" + str(vals['num_cheque'] or '') + "' "\
                                  "where id=" + str(x.line_id.id)
                        cr.execute(sql)
        if vals.has_key('move'):
            for item in items:
                self.pool.get('payment.cheque.detail').unlink(cr, uid, [aux.id for aux in item.cheque_det_ids])
            vals['cheque_det_ids'] = [(0, 0, aux) for aux in self.__load_details(cr, uid, vals['move'])]
        return super(payment_cheque, self).write(cr, uid, ids, vals, context=context)
    
    def copy(self, cr, uid, id, default=None, context=None):
        raise osv.except_osv(_('Atencion !'), _('No se puede duplicar este documento!!!'))
        return super(payment_cheque, self).copy(cr, uid, id, {}, context)
    
    def unlink(self, cr, uid, ids, context={}):
        for cheque in self.read(cr, uid, ids, ['state', 'num_cheque', 'cheque_det_ids']):
            if cheque['state'] not in ('draft', 'done'):
                raise osv.except_osv(('Aviso '),
                        ('Usted no puede eliminar el cheque "%s" mientras se encuentre en el estado "%s"!') % \
                                (cheque['num_cheque'], cheque['state']))
            if cheque['cheque_det_ids']:
                self.pool.get('payment.cheque.detail').unlink(cr, uid, cheque['cheque_det_ids'], context=context)
        return super(payment_cheque, self).unlink(cr, uid, ids, context)
    
    #Nota: Si los campos estan creados y recien se va aumentar el constrains se debe borrar el campo para q funcione. 
    #Respaldar en otra columna y luego se actualiza con la misma informacion.
    _sql_constraints = [('unique_cheque', 'unique(bank_account_id,num_cheque)', 'El Nro.cheque Unico para la misma cuenta')]
    
payment_cheque()


class payment_cheque_detail(osv.osv):
    _name = 'payment.cheque.detail'
    _description = 'Payment by Cheque Detail'
    
    _columns = { 
              'name':fields.char('Codigo', size=60, required=True),
              'account':fields.char('Cuenta', size=100),
              'partner':fields.char('Proveedores', size=100),
              'debit':fields.float('Debito', digits=(12, 2)),
              'credit':fields.float('Credito', digits=(12, 2)),
              'cheque_id':fields.many2one('payment.cheque', 'Cheque', ondelete="cascade"),
              'invoice_num':fields.char('Factura', size=100),
              'date_invoice':fields.date('Fecha Factura'),
              'partner_id':fields.many2one('res.partner', 'Partner'),
              'line_id':fields.many2one('account.move.line', 'Linea de Asiento', ondelete='set null'),
              'state': fields.selection([('draft', 'Borrador'),
                                         ('done', 'Listo'),
                                         ('printed', 'Impreso'),
                                         ('cancel', 'Anulado')], 'Estado'),
              'inv_type':fields.selection([('invoice', 'Factura'),
                                           ('purchase_liq', 'Liquidación de Compra'),
                                           ('anticipo', 'Anticipo'),
                                           ('liquidacion', 'Liquidacion de Viaje'),
                                           ('gas_no_dedu', 'Gasto no Deducible'),
                                           ('doc_inst_est', 'Doc. Emitido Estado'),
                                           ('apunte', 'Asiento por Apunte'),
                                           ('sales_note', 'Nota de Venta')], 'Tipo de Documento', size=60),
              'fecha_transaccion':fields.date('Fecha Transaccion'),
              
            }
    _default = {
                'state': lambda * a : 'draft',
                }
payment_cheque_detail()


class payment_transfer(osv.osv):
    _name = 'payment.transfer'
    _description = 'Payment by Transfer.'
    _order = "id Desc"
    
    def change_state(self, cr, uid, ids, context=None):
        context = context or {}
        new_state = context.get('new_state', 'draft')
        return self.write(cr, uid, ids, {'state': new_state}, context=context)
    
    def print_expense(self, cr, uid, ids, context=None):
        data = {'form': {}}
        transfe = self.browse(cr, uid, ids[0])
        data['form']['type'] = transfe.type
        data['form']['banco'] = transfe.bank_account_dest_id.bank.name
        data['form']['cuenta'] = transfe.bank_account_dest_id.acc_number
        data['form']['beneficiario'] = transfe.name
        data['form']['doc'] = 'Transferencia'
        data['form']['doc_num'] = transfe.num_exit_voucher
        data['ids'] = [transfe.move.id]
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.move.inex',
                'datas': data}
    
    def amount_debit(self, cr, uid, ids, field_name, args, context):
        res = {}
        debit = 0.00
        for item in self.browse(cr, uid, ids):
            
            for line in item.transfer_ids:
                debit += line.debit
            
            res[item.id] = str(round(debit, 2))
            
        return res
    
    def amount_credit(self, cr, uid, ids, field_name, args, context):
        res = {}
        credit = 0.00
        for item in self.browse(cr, uid, ids):
            for line in item.transfer_ids:
                credit += line.credit
            res[item.id] = str(round(credit, 2))
            
        return res    
    
    def amount_transfer(self, cr, uid, ids, field_name, args, context):
        res = {}
        account_bank = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', 1496)])
        neto = 0.00
        for item in self.browse(cr, uid, ids):
            for line in item.transfer_ids:
                if line.line_id and line.line_id.account_id.id in account_bank:
                   neto += round(line.line_id.credit or 0.00, 2) - round(line.line_id.debit or 0.00, 2)
                else:
                    continue
            if neto:
                res[item.id] = abs(round(neto, 2))
            else:
                res[item.id] = round(item.amount, 2)
        return res
    
    def _get_type_move(self, cr, uid, ids, field_name, args, context):
        res = {}
        for item in self.browse(cr, uid, ids):
            if item.state == 'printed':
                for x in item.transfer_ids:
                    if x.line_id:
                        sql = "update account_move_line set type_move ='TRANS' "\
                              "where id=" + str(x.line_id.id)
                        ##print "actualizar TRANSFERENCIA",sql
                        cr.execute(sql)
                        
                res[item.id] = 'TRANS'
            else:
                res[item.id] = 'S/TRANS'
        return res
    
    _columns = { 
              'type': fields.selection([('in', 'Ingreso'), ('out', 'Egreso')], 'Tipo', required=True),
              'name':fields.char('Nombre', size=200, required=True, readonly=True, states={'draft':[('readonly', False)]}),
              'amount':fields.float('Valor', digits=(12, 2), required=True, readonly=True, states={'draft':[('readonly', False)]}),
              'origin': fields.char('Origen', size=128, help='Documento el cual originó esta transferencia', readonly=True),
              'state': fields.selection([('draft', 'Borrador'),
                                         ('done', 'Listo'),
                                         ('printed', 'Impreso'),
                                         ('cancel', 'Anulada')], 'Estado', readonly=True),
              'bank_account_id': fields.many2one('res.partner.bank', 'Cuenta beneficiaria', readonly=True, states={'draft':[('readonly', False)]}),
              'bank_account_dest_id': fields.many2one('res.partner.bank', 'Cuenta bancaria', required=True, domain=[('partner_id.is_provider', '=', True)],
                                                      readonly=True, states={'draft':[('readonly', False)]}),
              'transfer_ids':fields.one2many('payment.transfer.line', 'transfer_id', 'Detalle Asientos'),
              'date_maturity':fields.function(lambda self, cr, uid, ids, *args: dict((o.id, o.payment_date) for o in self.browse(cr, uid, ids)),
                                              method=True, type='date', string='Fecha de Vencimiento',
                                              store={_name:(lambda self, cr, uid, ids, ctx: ids, ['payment_date'], 10)}),
              'invoice_num': fields.char('No. Factura', size=60),
              'date_invoice':fields.date('Fecha Factura'),
              'payment_date':fields.date('Fecha Transferencia', select=True),
              'date_generation':fields.date('Fecha', required=True, readonly=True, states={'draft':[('readonly', False)]}  ),
              'num_exit_voucher':fields.char('No. Documento', size=60, readonly=True, states={'done':[('readonly', False)]}),
#               'move':fields.integer('Asiento'),
              'move':fields.many2one('account.move', 'Asiento', required=True, readonly=True, states={'draft':[('readonly', False)]},
                                     domain=[('journal_id.type','=','bank'),('tipo_comprobante','=','Egreso'),('state','=','posted')]),
              'bank': fields.related('bank_account_id', 'bank', 'name', type='char', string='Banco', size=60, store=True, readonly=True),
              'acc_num':fields.related('bank_account_id', 'acc_number', type='char', string='No. Cuenta', size=60, store=True, readonly=True),
              'ruc': fields.related('partner_id', 'ident_num', type='char', string='RUC', size=60, store=True, readonly=True),
              'total_debit':fields.float('Total debe', digits=(12, 2)),
              'total_credit':fields.float('Total haber', digits=(12, 2)),
              
              'debit':fields.function(amount_debit, string='Total Debito', type='char', size=60, method=True, store=False),
              'credit':fields.function(amount_credit, string='Total Credito', type='char', size=60, method=True, store=False),
              
              'partner_id':fields.many2one('res.partner', 'Empresa',domain=['|',('customer','=',True),('supplier','=',True)], readonly=True, states={'draft':[('readonly', False)]}),
              'detalle':fields.text('Detalle', size=1000),
              'period_id': fields.many2one('account.period', 'Periodo', required=False, select=True),
              'type_hr':fields.char('Tipo TH', size=60, required=False, select=True),
              'change_partner':fields.boolean('Cambiar Beneficiario', readonly=True, states={'done':[('readonly', False)],
                                                                                             'printed':[('readonly', False)]}),
              'inv_type':fields.selection([('invoice', 'Factura'),
                                           ('purchase_liq', 'Liquidación de Compra'),
                                           ('anticipo', 'Anticipo'),
                                           ('liquidacion', 'Liquidacion de Viaje'),
                                           ('gas_no_dedu', 'Gasto no Deducible'),
                                           ('doc_inst_est', 'Doc. Emitido Estado'),
                                           ('apunte', 'Asiento por Apunte'),
                                           ('sales_note', 'Nota de Venta')], 'Tipo de Documento', size=60),
              'amount_transfer':fields.function(amount_transfer, string='Valor', method=True, store=False),
              'date_payment':fields.date('Fecha Pago', readonly=True, states={'done':[('readonly', False)]}),
              'payment':fields.function(_get_type_move, string='Pago', type='char', size=60, method=True, store=False),
              'company_id': fields.related('move', 'company_id', string='Compañia', readonly=True,
                                           type='many2one', relation='res.company', store=True)
            }
    
    def onchange_move(self, cr, uid, ids, move_id):
        res = {'value': {'amount': 0.0}}
        if move_id:
            move = self.pool.get('account.move').read(cr, uid, move_id, ['amount'])
            res['value']['amount'] = move['amount']
        return res
    
    def onchange_parnter_id(self, cr, uid, ids, partner_id):
        res = {'value': {'name': False}}
        if partner_id:
            partner = self.pool.get('res.partner').read(cr, uid, partner_id, ['name'])
            res['value']['name'] = partner['name']
        return res
    
    def __load_details(self, cr, uid, move_id):
        move = self.pool.get('account.move').browse(cr, uid, move_id)
        res = []
        for move_line_id in move.line_id:
            res.append({
                'name': move_line_id.name,
                'account': move_line_id.account_id.name,
                'partner': move_line_id.partner_id.name,
                'debit': move_line_id.debit,
                'credit': move_line_id.credit,
                'invoice_num': move_line_id.invoice.number_inv_supplier,
                'date_invoice': move_line_id.invoice.date_invoice,
                'partner_id': move_line_id.partner_id.id,
                'line_id': move_line_id.id,
                'inv_type': move_line_id.invoice.tipo_factura,
                'fecha_transaccion': move_line_id.date,
            })
        return res
    
    def create(self, cr, uid, vals, context={}):
        if vals.has_key('move') and not vals.has_key('transfer_ids'):
            vals['transfer_ids'] = [(0, 0, aux) for aux in self.__load_details(cr, uid, vals['move'])]
        res_id = super(payment_transfer, self).create(cr, uid, vals, context)
        return res_id
    
    def write (self, cr, uid, ids, vals, context=None):
        items = self.browse(cr, uid, ids, context)
        if vals.has_key('move'):
            for item in items:
                self.pool.get('payment.transfer.line').unlink(cr, uid, [aux.id for aux in item.transfer_ids])
            vals['transfer_ids'] = [(0, 0, aux) for aux in self.__load_details(cr, uid, vals['move'])]
        return super(payment_transfer, self).write(cr, uid, ids, vals, context=context)
    
    def copy(self, cr, uid, id, default=None, context=None):
        raise osv.except_osv(_('Atencion !'), _('No se puede duplicar este documento!!!'))
        return super(payment_transfer, self).copy(cr, uid, id, {}, context)
    
    def unlink(self, cr, uid, ids, context={}):
        ##print "unlik sale", ids
        toremove = []
        for transfer in self.browse(cr, uid, ids, context):
            if transfer['state'] not in ('draft', 'cancel'):
                raise osv.except_osv(('Aviso '),
                        ('Solo puede borrar el cheque %s si esta en estado borrador o cancelada!') % \
                                transfer['name'])
            line_ids = map(lambda x: x.id, transfer.transfer_ids)
            
            self.pool.get('payment.transfer.line').unlink(cr, uid, line_ids, context=context)
            toremove.append(transfer.id)
        result = super(payment_transfer, self).unlink(cr, uid, toremove, context)
        return result

    _defaults = {
        'state': lambda * a : 'draft',
        'date_generation': lambda *a: time.strftime("%Y-%m-%d"),
        'type': lambda *a: 'out'
      }
payment_transfer()


class payment_transfer_line(osv.osv):
    _name = 'payment.transfer.line'
    _description = 'Payment Line Transfer.'
    
    _columns = { 
              'name':fields.char('Codigo', size=60, required=True),
              'account':fields.char('Cuenta', size=100),
              'partner':fields.char('Proveedores', size=100),
              'credit':fields.float('Haber', digits=(12, 2)),
              'debit':fields.float('Debe', digits=(12, 2)),
              'transfer_id':fields.many2one('payment.transfer', 'Transferencia', ondelete="cascade"),
              'invoice_num':fields.char('Factura', size=100),
              'date_invoice':fields.date('Fecha Factura'),
              'partner_id':fields.many2one('res.partner', 'Partner', ondelete="cascade"),
              'line_id':fields.many2one('account.move.line', 'Linea de Asiento', ondelete='set null'),
              'state': fields.selection([('draft', 'Borrador'),
                                         ('done', 'Listo'),
                                         ('printed', 'Impreso'),
                                         ('cancel', 'Anulada')], 'Estado'),
             'inv_type':fields.selection([('invoice', 'Factura'),
                                           ('purchase_liq', 'Liquidación de Compra'),
                                           ('anticipo', 'Anticipo'),
                                           ('liquidacion', 'Liquidacion de Viaje'),
                                           ('gas_no_dedu', 'Gasto no Deducible'),
                                           ('doc_inst_est', 'Doc. Emitido Estado'),
                                           ('apunte', 'Asiento por Apunte'),
                                           ('sales_note', 'Nota de Venta')], 'Tipo de Documento', size=60),
             
            }
    _defaults = {
                 'state': lambda * a : 'draft',
                }
payment_transfer_line()


class payment_transfer_payment(osv.osv):
    _name = 'payment.transfer.payment'
    _description = 'Payments Cash Manangment or Cheque'
    _order = "id Desc"
    
    def buttom_charge(self, cr, uid, ids, context=None):
        """Load info about Invoices """
        #print 'Paso 1:Cargar', ids
        move_lines = self.pool.get('account.move.line')
        line = self.pool.get('invoice.line.transfer')
        obj_invoice = self.pool.get('account.invoice')
        transfer = self.browse(cr, uid, ids)[0]
        tipo_comp = transfer.tipo_com
        #print "tipo_comp", tipo_comp
        tarjeta = transfer.tarjeta
        #print "tarjeta", tarjeta
        caso = 0
        val = {}
        
        #FACTURAS
        if not tarjeta:
            #print "Sin tarjeta"
            if tipo_comp == 'apunte':
                caso = 1
                move_line = move_lines.search(cr, uid, [('has_transfer', '=', 0), ('cheque', '=', 0),
                                                        ('debit', '!=', 0.0), ('inv_type', 'like', tipo_comp),
                                                        ('statement_id', '<>', False), ('payment_form', '=', False)])
            else:
                caso = 2
                move_line = move_lines.search(cr, uid, [('has_transfer', '=', 0), ('cheque', '=', 0),
                                                        ('card', '!=', True), ('invoice_id', '!=', False),
                                                        ('debit', '!=', 0.0), ('inv_type', 'like', tipo_comp),
                                                        ('statement_id', '<>', False)])
            
        if tarjeta and tarjeta in ['DINERS', 'AMERICAN']:
            #print "Con tarjeta"
            if tipo_comp == 'apunte':
                caso = 3
                move_line = move_lines.search(cr, uid, [('has_transfer', '=', 0), ('cheque', '=', 0),
                                                        ('card', '=', True), ('debit', '!=', 0.0),
                                                        ('inv_type', 'like', tipo_comp), ('statement_id', '<>', False),
                                                        ('payment_form', 'like', tarjeta)])
            else:
                caso = 4
                move_line = move_lines.search(cr, uid, [('has_transfer', '=', 0), ('cheque', '=', 0),
                                                        ('card', '=', True), ('invoice_id', '!=', False),
                                                        ('debit', '!=', 0.0), ('inv_type', 'like', tipo_comp),
                                                        ('statement_id', '<>', False), ('payment_form', 'like', tarjeta)])
        
        #print 'caso', caso
        #print 'las facturas q pueden ser pagadas por transferencia y cheque:  ', move_line
        if not move_line:
            raise osv.except_osv("Información", 'No existen documentos que cancelar')
            return
        cad = ''
        band = 0
        
        for item in move_line:
            inv = self.pool.get('account.move.line').browse(cr, uid, item)
            lista = line.search(cr, uid, [('account_mov_id', '=', int(inv.id)), ('transfer_id', '=', int(transfer.id))])
            if not lista:
                val['transfer_id'] = int(",".join(map(str, ids)))
                val['origin'] = inv.inv_type         
                val['account_mov_id'] = inv.id
                val['amount_total'] = inv.debit
                val['has_transfer'] = inv.has_transfer
                val['card'] = inv.payment_form or False
                if inv.partner_id:
                    partner = self.pool.get('res.partner').browse(cr, uid, inv.partner_id.id)
                    val['name'] = partner.name
                    val['identification_number'] = partner.ident_num
                    val['identification_type'] = partner.ident_type
                    val['supplier_code'] = partner.ref
                    val['partner'] = partner.id
                    val['payment_type'] = partner.payment_type
                    if partner.payment_type:
                        if partner.payment_type == 'CTA':
                            if partner.bank_ids:
                                for cuentas in partner.bank_ids:
                                    if cuentas.has_payment:
                                        val['acc_type'] = cuentas.acc_type or False
                                        val['bank_code'] = cuentas.bank.code or False
                                        val['acc_number'] = cuentas.acc_number or False
                                        break
                                    else:
                                        cad = cad + str(partner.name) + '/'
                            else:
                                cad = cad + str(partner.name) + '/'
                            if not partner.ref:
                                raise osv.except_osv("Por favor ingrese! ", 'El codigo del proveedor: ' + partner.name)
                        else:
                            if partner.bank_ids:
                                for cuentas in partner.bank_ids:
                                    if cuentas.has_payment:
                                        val['acc_type'] = cuentas.acc_type or False
                                        val['bank_code'] = cuentas.bank.code or False
                                        val['acc_number'] = cuentas.acc_number or False
                    
                else:
                    if 'name' not in val:
                        val['name'] = inv.name or inv.ref or False
                    #raise osv.except_osv("Información", 'No existe Partner')
                val['date_payment'] = inv.statement_id and inv.statement_id.date 
                if inv.invoice_id:
                    invoice = obj_invoice.browse(cr, uid, inv.invoice_id)
                    if invoice:
                        if invoice.tipo_factura in ['invoice', 'purchase_liq', 'sales_note']:
                            val['invoice_num'] = str(invoice.auth_inv_id.serie_entidad) + '-' + str(invoice.auth_inv_id.serie_emision) + '-' + str(invoice.number_inv_supplier).zfill(13)
                            val['date_maturity'] = invoice.date_due or False
                            val['date_invoice'] = invoice.date_invoice or False
                        elif invoice.tipo_factura in ['anticipo', 'gas_no_dedu', 'doc_inst_est']:
                                if invoice.tipo_factura in ['anticipo']:
                                    val['invoice_num'] = invoice.code_advance_liq
                                else:
                                    val['invoice_num'] = invoice.number
                                val['date_maturity'] = invoice.date_due or False
                                val['date_invoice'] = invoice.date_invoice or False
                    else:
                        val['invoice_num'] = inv.ref or False
                        val['date_maturity'] = inv.date_maturity or inv.date or False
                else:
                    val['invoice_num'] = inv.ref or False
                    val['date_maturity'] = inv.date_maturity or inv.date
                
                line.create(cr, uid, val)
        return True
              
    
    def create_invoice_transfer_line(self, cr, uid, ids, st, ml, stl):
        cad = ''
        invoice_obj = self.pool.get('account.invoice')
        invoice_line_transfer_obj = self.pool.get('invoice.line.transfer')
        val = {}
        val['statement_line_id'] = stl.id 
        val['transfer_id'] = int(",".join(map(str, ids)))
        val['origin'] = ml.inv_type 
        val['account_mov_id'] = ml.id
        val['amount_total'] = ml.debit
        val['has_transfer'] = ml.has_transfer
        val['card'] = ml.payment_form or False
        val['date_payment'] = st.date
        if ml.partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, ml.partner_id.id)
            val['name'] = partner.name
            val['identification_number'] = partner.ident_num
            val['identification_type'] = partner.ident_type
            val['supplier_code'] = partner.ref
            val['partner'] = partner.id
            val['payment_type'] = partner.payment_type
            #print "partner.payment_type", partner.payment_type
            if partner.payment_type:
                if partner.payment_type == 'CTA':
                    if partner.bank_ids:
                        for cuentas in partner.bank_ids:
                            if cuentas.has_payment:
                                val['acc_type'] = cuentas.acc_type or False
                                val['bank_code'] = cuentas.bank.code or False
                                val['acc_number'] = cuentas.acc_number or False
                                break
                            else:
                                cad = cad + str(partner.name) + '/'
                    else:
                        cad = cad + str(partner.name) + '/'
                    if not partner.ref:
                        raise osv.except_osv("Por favor ingrese! ", 'El codigo del proveedor: ' + partner.name)
                else:
                    if partner.bank_ids:
                        for cuentas in partner.bank_ids:
                            if cuentas.has_payment:
                                val['acc_type'] = cuentas.acc_type or False
                                val['bank_code'] = cuentas.bank.code or False
                                val['acc_number'] = cuentas.acc_number or False
        else:
            if 'name' not in val:
                val['name'] = ml.name or ml.ref or 'BENEFICIARIO'

        if ml.invoice_id:
            invoice = invoice_obj.browse(cr, uid, ml.invoice_id)
            if invoice:
                if invoice.tipo_factura in ['invoice', 'purchase_liq', 'sales_note']:
                
                    val['invoice_num'] = str(invoice.auth_inv_id.serie_entidad) + '-' + \
                                         str(invoice.auth_inv_id.serie_emision) + '-' + \
                                         str(invoice.number_inv_supplier).zfill(13)
                    val['date_maturity'] = invoice.date_due
                    val['date_invoice'] = invoice.date_invoice
                elif invoice.tipo_factura in ['anticipo', 'gas_no_dedu', 'doc_inst_est']:
                    if invoice.tipo_factura in ['anticipo']:
                        val['invoice_num'] = invoice.code_advance_liq
                    else:
                        val['invoice_num'] = invoice.code_advance_liq
                    val['date_maturity'] = invoice.date_due
                    val['date_invoice'] = invoice.date_invoice
            else:
                val['invoice_num'] = ml.ref or False
                val['date_maturity'] = ml.date_maturity or ml.date or False
        else:
            val['invoice_num'] = ml.ref or False
            val['date_maturity'] = ml.date_maturity or ml.date
        ##print "Creacion de Lineas Invoice Linea Transfer ", val
        il = invoice_line_transfer_obj.create(cr, uid, val)
        return il
    
    def update_partner(self, cr, uid, lista, ml):
        account_move_line_obj = self.pool.get('account.move.line')
        invoice_line_transfer_obj = self.pool.get('invoice.line.transfer')
        
        cad2 = ''
        cad = ''
        val1 = {}
        
        if ml.partner_id:
            val1['payment_type'] = ml.partner_id.payment_type 
            if ml.partner_id.payment_type == 'CTA':
                if ml.partner_id.bank_ids:
                    for cuentas in ml.partner_id.bank_ids:
                        if cuentas.has_payment:
                            val1['acc_type'] = cuentas.acc_type or False
                            val1['bank_code'] = cuentas.bank.code or False
                            val1['acc_number'] = cuentas.acc_number or False
                            break
                        else:
                            cad2 = cad2 + str(ml.partner_id.name) + '/'
                else:
                    cad2 = cad2 + str(partner.name) + '/'
                if not ml.partner_id.ref:
                    raise osv.except_osv("Por favor ingrese! ", 'El codigo del proveedor: ' + ml.partner_id.name)
            else:
                if ml.partner_id.bank_ids:
                    for cuentas in ml.partner_id.bank_ids:
                        if cuentas.has_payment:
                            val1['acc_type'] = cuentas.acc_type or False
                            val1['bank_code'] = cuentas.bank.code or False
                            val1['acc_number'] = cuentas.acc_number or False
            if cad2 <> '':
                raise osv.except_osv("Por favor ingrese! ", 'La cuenta del proveedor: ' + ml.partner_id.name)
#                                                #print "val1", val1
            invoice_line_transfer_obj.write(cr, uid, lista[0], val1)
        
        
    def onchange_statement(self, cr, uid, ids, statement_id, name):
        dict = {'value':{}}
        val = {}
        ilt = []
        val1 = {}
        cad2 = ''
        cad = ''
        stl_list = []
        invoice_obj = self.pool.get('account.invoice')
        line_obj = self.pool.get('invoice.line.transfer')
        account_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        statement_obj = self.pool.get('account.bank.statement')
        
        if not name:
            dict['value']['warning'] = {'title': 'Aviso', 'message': u"Llena el campo nombre y oprima el boton guardar antes de seleccionar el Extracto.!!"}
            return dict
        
        for item in self.browse(cr, uid, ids):
            if item:
                if item.invoce_line_ids:
                    for x in item.invoce_line_ids:
                        ilt.append(x.id)
            if statement_id:
                for st in statement_obj.browse(cr, uid, [statement_id]):
                    for line in st.move_line_ids:
                        if line.state <> 'valid':
                            raise osv.except_osv(_('¡ Error !'), ('Las líneas de los asientos contables no están en estado válido.'))
                    
                    
                    lista = []
                    for stl in st.line_ids:
                        american = []
                        diners = []
                        res = []
                        stlids = []
                        if item.type in ('credit_card'):
                            if stl.payment_form == 'DINERS':
                                diners.append(stl.id)
                            elif stl.payment_form == 'AMERICAN':
                                american.append(stl.id)
                            #print 'diners', diners
                            if item.tarjeta == 'DINERS' and diners:
                                cr.execute("SELECT statement_id as move FROM account_bank_statement_line_move_rel \
                                        WHERE move_id in (" + ','.join(map(str, diners)) + ")" 
                                        )
                                res = cr.dictfetchall()
                            elif item.tarjeta == 'AMERICAN' and american:
                                cr.execute("SELECT statement_id as move FROM account_bank_statement_line_move_rel \
                                            WHERE move_id in (" + ','.join(map(str, american)) + ")" 
                                        )
                                res = cr.dictfetchall()
                        else:
                            stlids.append(stl.id)
                            if stlids:
                                #cr.execute("SELECT statement_id as move FROM account_bank_statement_line_move_rel \
                                #            WHERE move_id in (" + ','.join(map(str, stlids)) + ")" 
                                #            )
                                
                                query = "select move_id as move from account_bank_statement where id in (" + str(statement_id) + ")"
                                
                                ##print ' item.type ', item.type 
                                ##print ' query ', query
                                cr.execute(query)
                                res = cr.dictfetchall()
                                ##print ' res ', res
                    
                        if not res:
                            raise osv.except_osv("Advertencia", 'La información proporcionada es incompleta. - ' + '(' + str(statement_id) + ')')
                            
                        if res:
                            
                            #1332 Cuenta de proveedores para induvallas
                            ##66 Para covipro
                            ##print "stl_list", stl_list
                            account_ids = account_obj.search(cr, uid, [('parent_id', '=', 1332)])
                            
                            for mo in res:
                                ##print ' mo ', mo
                                ##print ' mo ', mo['move']
                                move = move_obj.browse(cr, uid, mo['move'])
                                if move:
                                    for ml in move.line_id:
                                        lista = []
                                        if item.type in ('transfer', 'check'):
                                            ##print ' ml.debit ', ml.debit
                                            ##print ' ml.debit ', ml.has_transfer
                                            ##print ' ml.cheque ', ml.cheque
                                            ##print ' stl.id ', stl.id
                                            ##print ' stl_list ', stl_list
                                            if ml.debit > 0.0 and (not ml.has_transfer) and (not ml.cheque) and (stl.id not in stl_list):
                                                stl_list.append(stl.id)
                                                lista = line_obj.search(cr, uid, [('account_mov_id', '=', ml.id),
                                                                                  ('transfer_id', '=', ids)])
                                                ##print ' lista *** ', lista
                                                if lista:
                                                    ilt.append(lista[0])
                                                    self.update_partner(cr, uid, lista, ml)
                                                if not lista:
                                                    il = self.create_invoice_transfer_line(cr, uid, ids, st, ml, stl)
                                                    ilt.append(il)
                                                    
                                        elif item.type in ('credit_card'):
                                            
                                            if ml.debit > 0.0 and (not ml.has_transfer) and (not ml.cheque) \
                                                and ml.account_id.id in account_ids and (stl.id not in stl_list):#Cuentas de proveedores
                                                stl_list.append(stl.id)
                                                
                                                lista = line_obj.search(cr, uid, [('account_mov_id', '=', ml.id),
                                                                                  ('transfer_id', '=', ids)])
                                                if lista:
                                                    ilt.append(lista[0])
                                                    self.update_partner(cr, uid, lista, ml)
                                                
                                                if not lista:
                                                    il = self.create_invoice_transfer_line(cr, uid, ids, st, ml, stl)
                                                    ilt.append(il)
                                                    
                                            elif ml.debit > 0.0 and (not ml.has_transfer) and (not ml.cheque)\
                                                and (stl.id not in stl_list):#Gastos Bancarios y otros
                                                stl_list.append(stl.id)
                                                lista = line_obj.search(cr, uid, [('account_mov_id', '=', ml.id),
                                                                                  ('transfer_id', '=', ids)])
                                                if lista:
                                                    ilt.append(lista[0])
                                                    self.update_partner(cr, uid, lista, ml)
                                                
                                                if not lista:
                                                    il = self.create_invoice_transfer_line(cr, uid, ids, st, ml, stl)
                                                    ilt.append(il)
            
            #print ' ilt ****** ', ilt
            dict['value']['invoce_line_ids'] = list(set(ilt))                            
        return dict    
    
    def write(self, cr, user, ids, vals, context=None): 
        #print 'Paso 2:Seleccionar, ids', ids
        #print 'Paso 2: context', context
        cad = ''
        id = super(payment_transfer_payment, self).write(cr, user, ids, vals, context=context)
        
        for payments_obj in self.browse(cr, user, ids):
            if not payments_obj.payment_date and payments_obj.state == 'draft':
                for line in payments_obj.invoce_line_ids:
                    if line.account_mov_id:
                        obj_ac_mov_l = self.pool.get('account.move.line').browse(cr, user, line.account_mov_id.id)
                        if obj_ac_mov_l.has_transfer and obj_ac_mov_l.cheque:
                            if line.has_transfer:
                                cad = cad + str(obj_ac_mov_l.inv_number) + ' de la fecha: ' + str(obj_ac_mov_l.date_maturity) + ' \n'
                            if line.cheque:
                                   cad = cad + str(obj_ac_mov_l.inv_number) + ' de la fecha: ' + str(obj_ac_mov_l.date_maturity) + ' \n'
                if cad:
                    raise osv.except_osv("Advertencia", 'Ya se genero el pago por cheque de: ' + cad + ' Por favor deshabilite para guardar.')
        return id
    
    def get_bank(self, cr, uid, diario, context):
        val = {}
        if diario == "Diario B.Guayaquil":
             #print "diario Guayaquil"
             val['bank'] = "Banco de Guayaquil"
             val['acc_num'] = "5805929"
             
        if diario == "Diario B.Pichincha":
             #print "Pichincha"
             val['bank'] = "Banco del Pichincha"
             val['acc_num'] = "3016897104"
        if diario == "Diario B.Produbanco":
             #print "produbanco"
             val['bank'] = "Produbanco"
             val['acc_num'] = "2005016130"
             
        if diario == "Diario B.Internacional":
             #print "internacional"
             val['bank'] = "Banco Internacional"
             val['acc_num'] = "0700075355"
             
        if diario == "Diario B.Pacifico":
             #print "pacifico"
             val['bank'] = "Banco del Pacifico"
             val['acc_num'] = "5163331"
             
        if diario == "Diario Banco Rumiñahui":
             #print "RUMINÑAHUI"
             val['bank'] = "Banco Rumiñahui"
             val['acc_num'] = "8016408104"
        #print 'val', val
        return val        
    
    def generate_payment_cheque(self, cr, uid, ids, context):
        #print "generate_payment_cheque", ids
        move_line = self.pool.get('account.move.line')
        cheque_line = self.pool.get('payment.cheque.detail')
        cheque = self.pool.get('payment.cheque')
        transfer_line = self.pool.get('invoice.line.transfer')
        
        val = {}
        cad = ''
        caso = 0
        
        sin_partner = []

        for item in self.browse(cr, uid, ids):
            
            transfer_id = item.id
            observacion = item.name
            tarjeta = item.tarjeta
            tipo = item.tipo_com
            
            if not tarjeta:
                caso = 1
                
                if item.group_by == 'by_partner':
                    cr.execute("""
                             select partner as codigo, sum(amount_total) as total from invoice_line_transfer
                             where cheque = %s 
                             and transfer_id=%s
                             and chq=%s 
                             and state=%s
                             and partner is not null
                             group by codigo
                             """, (True, transfer_id, True, 'draft'))
                else:
                    cr.execute("""
                             select transfer_id as none, sum(amount_total) as total from invoice_line_transfer
                             where cheque = %s 
                             and transfer_id=%s
                             and chq=%s 
                             and state=%s
                             group by transfer_id
                             """, (True, transfer_id, True, 'draft'))
                   
            if tarjeta and tarjeta in ['DINERS', 'AMERICAN']:
                caso = 2
                
                cr.execute("""
                         select transfer_id as card, sum(amount_total) as total from invoice_line_transfer
                         where cheque = %s 
                         and transfer_id=%s
                         and chq=%s 
                         and state=%s
                         and card='""" + str(tarjeta) + """'
                         group by transfer_id
                         """, (True, transfer_id, True, 'draft'))
                
            consulta = cr.dictfetchall()
            
            if item.group_by == 'by_partner':
                
                sql = "SELECT id as sin_partner, amount_total as total FROM invoice_line_transfer "\
                       "WHERE cheque = %s AND transfer_id=%s AND chq=%s AND state='%s' AND partner is null" % (True, transfer_id, True, 'draft')
                
                cr.execute(sql)
                sin_partner = cr.dictfetchall()
                
                union = consulta + sin_partner
                
            else:
                union = consulta
            
            #print ' union**** ', union
            if union:
                 for key in union:
                     #print ' key *** ', key
                     total = key['total']
                     #Pago agrupado por proveedor
                     if key.has_key('codigo'):
                         if key['codigo']:
                             partner = key['codigo']
                             partner_obj = self.pool.get('res.partner').browse(cr, uid, partner)
                             if partner_obj.ident_type in ('c', 'p', 'r'):
                                 if partner_obj.ident_num:
                                     val['name'] = partner_obj.name
                                     val['amount'] = total
                                     val['partner'] = partner_obj.name
                                     val['ruc'] = str(partner_obj.ident_num)
                                     val['partner_id'] = partner_obj.id
                                 else :
                                     cad = cad + str(partner_obj.name) + ' / '
                                 if cad <> '':
                                     raise osv.except_osv("Falta Informacion (TIPO  DE IDENTIFICACION O NUMERO DE IDENTIFICACION ", 'Proveedores:  ' + cad)
                                      
                             lineas = transfer_line.search(cr, uid, [('partner', '=', partner), ('transfer_id', '=', transfer_id),
                                                                     ('state', '=', 'draft'), ('chq', '=', True)])
                             
                             obj_trasfer = transfer_line.browse(cr, uid, lineas)
                     
                     #Pago de tarjeta de credito     
                     if key.has_key('card'):
                         if key['card']:
                             val['name'] = tarjeta
                             val['card'] = tarjeta
                             val['amount'] = total
                             val['partner'] = False
                             val['ruc'] = False
                             val['partner_id'] = False
                             
                             lineas = transfer_line.search(cr, uid, [('transfer_id', '=', transfer_id),
                                                                     ('state', '=', 'draft'),
                                                                     ('chq', '=', True),
                                                                     ('card', '=', tarjeta)])
                             obj_trasfer = transfer_line.browse(cr, uid, lineas)
                    
                     #Pago en un solo cheque
                     if key.has_key('none'):
                         if key['none']:
                             val['name'] = tools.ustr(item.payable_to)
                             val['amount'] = total
                             
                             lineas = transfer_line.search(cr, uid, [('transfer_id', '=', transfer_id),
                                                                     ('state', '=', 'draft'),
                                                                     ('chq', '=', True),
                                                                     ])
                             obj_trasfer = transfer_line.browse(cr, uid, lineas)
                     
                     #Pago de lineas seleccionadas pero q no tienen proveedor
                     if key.has_key('sin_partner'):
                         if key['sin_partner']:
                             
                             val['amount'] = key['total'] or 0.0
                             
                             lineas = transfer_line.search(cr, uid, [('id', '=', key['sin_partner'])])
                             
                             obj_trasfer = transfer_line.browse(cr, uid, lineas)
                     
                     ##print"Lineas que estan para el cheque o transferencia", obj_trasfer
                     if obj_trasfer:
                         #Marco las lineas que genero el cheque para que no se vuelvan a generar el cheque de estos movimientos    
                         for item in obj_trasfer:
                             if item.account_mov_id:
                                 #move_line.write(cr, uid, [item.account_mov_id.id], {'cheque':True})
                                 sql = "update account_move_line set cheque = True where id=" + str(item.account_mov_id.id)
                                 cr.execute(sql)
                                 transfer_line.write(cr, uid, [item.id], {'state':'valid',
                                                                          'generation_date':time.strftime('%Y-%m-%d'),
                                                                          'note':'Cheque'})
                             else:
                                 continue
                             
                             val['invoice_num'] = item.invoice_num or False
                             val['date_invoice'] = item.date_invoice or False
                             
                             move_line_id = item.account_mov_id.id
                             obj_move_line = move_line.browse(cr, uid, move_line_id)
                             
                             if 'name' not in val:
                                 val['name'] = obj_move_line.ref or obj_move_line.name or 'Sin Proveedor'
                                 
                             val['date_maturity'] = item.date_maturity or False
                             val['move'] = obj_move_line.move_id.id
                             
                             journal_id = obj_move_line.journal_id.id
                             ##print "journal_id", journal_id
                             journal_obj = self.pool.get('account.journal').browse(cr, uid, journal_id)
                             diario = tools.ustr(journal_obj.name)
                             
                             #Obtengo el nombre del Banco y el numero de cuenta 
                             dato_banco = self.get_bank(cr, uid, diario, context)
                             
                             val['bank'] = dato_banco.get('bank', '') 
                             val['acc_num'] = dato_banco.get('acc_num', '')
                             val['inv_type'] = obj_move_line.inv_type
                             val['num_exit_voucher'] = obj_move_line.statement_id.no_comp_rel
                             
                         
                         val['state'] = 'done'
                         val['generation_date'] = time.strftime('%Y-%m-%d')
                         
                         #seq = self.pool.get('ir.sequence').get(cr, uid, 'ret_voucher_seq')
                         #val['num_exit_voucher'] = seq
                         #val['num_exit_voucher'] = item.statement_line_id.no_comp_rel
                         
                         val['observation'] = tools.ustr(observacion)
                         
                         'Creacion de la Cabecera del cheque'
                         if 'move' in val:
                             id_cheque = cheque.create(cr, uid, val)
                             ##print "Create Cheque ", id_cheque
                         else:
                             continue
                         
                         t_debit = 0.00
                         t_credit = 0.00
                         g_debito = 0.00
                         g_credito = 0.0
                         
                         #Genero las Lineas del Cheque
                         for item in obj_trasfer:
                             if not item.account_mov_id:
                                 continue
                             invoice_num = item.invoice_num
                             move_line_id = item.account_mov_id.id
                             move_line_data = move_line.browse(cr, uid, move_line_id)
                             st_id = int(move_line_data.statement_id)
                             ##print 'st_id: ', st_id
                             m_id = int(move_line_data.move_id)
                             ##print 'm_id: ', m_id
                             id_fac = int(move_line_data.invoice_id)
                             ##print 'id_fac', id_fac
                             tipo_factura = move_line_data.inv_type
                             id_move = None
                             if caso == 1:
                                 if id_fac:
                                     id_move = move_line.search(cr, uid, [('invoice_id', '=', id_fac),
                                                                          ('statement_id', '=', st_id),
                                                                          ('move_id', '=', m_id)])
                                 else:
                                     id_move = move_line.search(cr, uid, [('statement_id', '=', st_id), ('move_id', '=', m_id)])
                             elif caso == 2:
                                 if id_fac:
                                     id_move = move_line.search(cr, uid, [('invoice_id', '=', id_fac),
                                                                          ('statement_id', '=', st_id),
                                                                          ('move_id', '=', m_id), ('card', '=', True)])
                                 elif tipo_factura == 'apunte':
                                     id_move = move_line.search(cr, uid, [('inv_type', '=', 'apunte'), ('card', '=', True),
                                                                          ('statement_id', '=', st_id), ('move_id', '=', m_id)])
                                 else:
                                     id_move = move_line.search(cr, uid, [('card', '=', True),
                                                                          ('statement_id', '=', st_id), ('move_id', '=', m_id)])
                             
                             if id_move:
                                 obj_move_line = move_line.browse(cr, uid, id_move)
                                 for obj in obj_move_line:
                                     #if obj.credit > 0 and obj.account_id.id in [1366, 1367, 1368, 1369, 4534]:
                                     cheque_line.create(cr, uid, {'name':str(obj.account_id.code),
                                                                 'account':obj.account_id.name,
                                                                 'partner':obj.partner_id and obj.partner_id.name or False,
                                                                 'credit':obj.credit,
                                                                 'debit':obj.debit,
                                                                 'cheque_id':id_cheque,
                                                                 'invoice_num':invoice_num,
                                                                 'partner_id':obj.partner_id and obj.partner_id.id or False,
                                                                 'line_id':obj.id,
                                                                 'state':'done',
                                                                 'inv_type': obj.inv_type#Aumento el tipo de documento del que proviene la Factura
                                                                 })
                         if id_cheque:
                             self.write(cr, uid, ids, {'state':'done'})
                         else:
                             raise osv.except_osv("Se ha borrado la linea del Pago")
        return True
    
    def save_and_close(self, cr, uid, ids, context=None):
        'Esta función solo se invocará desde la creación de la transferencia directamente en el account.voucher'
        self.write(cr, uid, ids, {'state': 'draft'})
#         return {'type': 'ir.actions.act_window_close'}
        model_data_obj = self.pool.get('ir.model.data')
        data_ids = model_data_obj.search(cr, uid, [('model', '=', 'ir.ui.view'), ('module', '=', 'payments'),
                                                   ('name', '=', 'view_payment_transfer_payment_form')])
        data_results = model_data_obj.read(cr, uid, data_ids, ['res_id'])[0]
        return {
            'name': 'Pago con transferencia',
            'res_id': ids,
            'view_mode': 'form',
            'view_id': [data_results['res_id']],
            'view_type': 'form',
            'res_model': 'payment.transfer.payment',
            'type': 'ir.actions.act_window',
        }
    
    def generate_voucher_payment_transfer(self, cr, uid, ids, context=None):
        transfers_ids = self.browse(cr, uid, ids)
        for payment_id in transfers_ids:
            for line in [aux for aux in payment_id.invoce_line_ids if aux.has_transfer]:
                expr = match('^PAGO #\d+ \((\d+)\)$', line.origin or '')
                voucher_id = self.pool.get('account.voucher').browse(cr, uid, int(expr.group(1)))
                vals = {
                    'name': line.name, 'amount': line.amount_total, 'date_generation': line.generation_date,
                    'date_maturity': line.date_maturity, 'invoice_num': line.invoice_num, 'state': 'done', 'bank_account_des_id': payment_id.bank_account_id.id,
                    'date_payment': line.date_payment, 'payment_date': line.date_payment, 'date_invoice': line.date_invoice,
                    'num_exit_voucher': line.origin, 'origin': line.origin, 'move': voucher_id.move_id.id, 'transfer_ids': [],
                    'bank_account_id': line.bank_account_id.id, 'partner_id': line.partner.id, 'total_debit': line.amount_total,
                    'total_credit': line.amount_total, 'detalle': line.origin, 'period_id': voucher_id.period_id.id,
                    'type_hr': None, 'change_partner': True, 'inv_type': None,
                }
                for movel_id in voucher_id.move_ids:
                    vals['transfer_ids'].append((0, 0, {
                            'name': movel_id.name,
                            'account': movel_id.account_id.name,
                            'partner': movel_id.partner_id.name,
                            'credit': movel_id.credit,
                            'debit': movel_id.debit,
                            'invoice_num': movel_id.invoice.number_inv_supplier,
                            'date_invoice': movel_id.invoice.date_invoice,
                            'partner_id': movel_id.partner_id.id,
                            'line_id': movel_id.id,
                            'state': 'done',
                            'inv_type': 'invoice'                                
                    }))
                self.pool.get('payment.transfer').create(cr, uid, vals)
            self.pool.get('invoice.line.transfer').write(cr, uid, [aux.id for aux in payment_id.invoce_line_ids], {'state': 'valid'})
        return self.write(cr, uid, ids, {'state':'done'})
    
    def generate_payment_transfer(self, cr, uid, ids, context=None):
        #print 'generate_payment_transfer ', ids
        return self.generate_voucher_payment_transfer(cr, uid, ids, context)
        val = {}
        cad = ''
        for item in self.browse(cr, uid, ids):
            transfer_id = item.id
            detalle = ''
            if item.group_by == 'by_partner':
                cr.execute("""
                            select partner as codigo, sum(amount_total) as total 
                            from invoice_line_transfer
                            where has_transfer = %s 
                            and transfer_id = %s 
                            and state = %s 
                            group by codigo
                            """, (True, transfer_id, 'draft',)
                            )
            else:
                cr.execute("""
                            select transfer_id as none, sum(amount_total) as total 
                            from invoice_line_transfer
                            where has_transfer = %s 
                            and transfer_id = %s 
                            and state = %s 
                            group by transfer_id
                            """, (True, transfer_id, 'draft',)
                            )
            consulta = cr.dictfetchall()
            #print "transferencia", consulta
            if consulta:
                 # "CONSULTA: ", consulta
                 for key in consulta:
                     facturas = []
                     total = key['total']
                     obj_trasfer = []
                     if key.has_key('codigo'):
                         if key['codigo']:
                             partner = key['codigo']
                             partner_obj = self.pool.get('res.partner').browse(cr, uid, partner)
                             if partner_obj.ident_num and partner_obj.ident_type:
                                 val['name'] = partner_obj.name
                                 val['amount'] = total
                                 val['partner'] = partner_obj.name
                                 val['ruc'] = str(partner_obj.ident_num)
                                 val['partner_id'] = partner_obj.id

                             lineas = self.pool.get('invoice.line.transfer').search(cr, uid, [('partner', '=', partner),
                                                                                              ('transfer_id', '=', transfer_id),
                                                                                              ('state', '=', 'draft'),
                                                                                              ('has_transfer', '=', True) ])
                             obj_trasfer = self.pool.get('invoice.line.transfer').browse(cr, uid, lineas)
                             
                     
                     if key.has_key('none'):
                         if key['none']:
                             if item.transfer_to == 'partner_to':
                                 if not item.supplier_to:
                                     raise osv.except_osv(_('¡ Aviso !'), ('Ingrese el nombre del proveedor al que va ir la transferencia.'))
                                 partner_obj = item.supplier_to
                                 val['name'] = partner_obj.name
                                 val['amount'] = total
                                 val['partner'] = partner_obj.name
                                 val['ruc'] = str(partner_obj.ident_num)
                                 val['partner_id'] = partner_obj.id
                             #---------- elif item.transfer_to == 'employee_to':
                                 #--------------------- if not item.employee_to:
                                     # raise osv.except_osv(_('¡ Aviso !'), ('Ingrese el nombre del empleado al que va ir la transferencia.'))
                                 #---------- val['name'] = item.employee_to.name
                                 #------------------------ val['amount'] = total
                                  
                             lineas = self.pool.get('invoice.line.transfer').search(cr, uid, [('transfer_id', '=', transfer_id),
                                                                                              ('state', '=', 'draft'),
                                                                                              ('has_transfer', '=', True) ])
                             obj_trasfer = self.pool.get('invoice.line.transfer').browse(cr, uid, lineas)
                             
                     #print 'obj_trasfer', obj_trasfer                
                     for line in obj_trasfer:
                         
                         #self.pool.get('account.move.line').write(cr,uid, [line.account_mov_id.id], {'has_transfer':True})
                         if line.account_mov_id:
                             sql = "update account_move_line set has_transfer = True where id=" + str(line.account_mov_id.id)
                             cr.execute(sql)
                         self.pool.get('invoice.line.transfer').write(cr, uid, [line.id], {'state':'valid',
                                                                                          'generation_date':time.strftime('%Y-%m-%d'),
                                                                                          'note':'Transferencia'})
                         
                         val['invoice_num'] = line.invoice_num or False
                         if line.origin:
                             if line.origin in ('purchase_liq'):
                                 detalle += ' REG. LIQ. Nro. ' + str(line.invoice_num)[14:] + ' '
                             
                             if line.origin in ('invoice'):
                                 detalle += ' REG. FACT. Nro. ' + val['invoice_num'][14:] + ' '
                             
                             if line.origin in ('anticipo'):
                                 if val.has_key('invoice_num') and val['invoice_num']:
                                     detalle += ' REG. ANT. Nro. ' + val['invoice_num'] + ' '
                                 else:
                                     detalle += ' '
                             
                             if line.origin in ('apunte'):
                                 if val.has_key('invoice_num') and val['invoice_num']:
                                     detalle += ' ' + val['invoice_num'] + ' '
                                 else:
                                     detalle += ' '
                         else:
                            detalle = item.name
                     
                         move_id = line.account_mov_id and line.account_mov_id.id
                         if move_id:
                             obj_move = self.pool.get('account.move.line').browse(cr, uid, move_id)
                             val['move'] = obj_move.move_id.id
                             val['inv_type'] = obj_move.inv_type or False
                            
                        #Estos datos me sirven como informacion en el caso que sea una sola factura que pago en la transferencia
                         val['date_maturity'] = line.date_maturity or False
                         val['date_invoice'] = line.date_invoice or False
                         val['date_payment'] = line.date_payment
                     
                     val['detalle'] = detalle    
                     val['state'] = 'done'
                     val['payment_date'] = time.strftime('%Y-%m-%d')
                     seq = self.pool.get('ir.sequence').get(cr, uid, 'ret_voucher_seq')
                     val['num_exit_voucher'] = seq
                     
                     id_transfer = self.pool.get('payment.transfer').create(cr, uid, val)
                         
                     for item in obj_trasfer:
                         invoice_num = str(item.invoice_num)
                         move_id = item.account_mov_id and item.account_mov_id.id
                         move = self.pool.get('account.move.line').browse(cr, uid, move_id)
                         st_id = int(move.statement_id)
                         ##print 'st_id: ', st_id
                         m_id = int(move.move_id)
                         ##print 'm_id: ', m_id
                         id_fac = int(move.invoice_id)
                         ##print 'id_fac',id_fac
                         id_move = None
                         if id_fac:
                             id_move = self.pool.get('account.move.line').search(cr, uid, [('invoice_id', '=', id_fac),
                                                                                           ('statement_id', '=', st_id),
                                                                                           ('move_id', '=', m_id)])
                         else:
                             id_move = self.pool.get('account.move.line').search(cr, uid, [('statement_id', '=', st_id),
                                                                                           ('move_id', '=', m_id)])
                         if id_move:
                             ##print 'id_move: ', id_move
                             obj_move_line = self.pool.get('account.move.line').browse(cr, uid, id_move)
                             ##print 'id_move2: ', obj_move_line
                             for obj in obj_move_line:
                                 transfer_ids = self.pool.get('payment.transfer.line').create(cr, uid,
                                                                                                {'name':str(obj.account_id.code),
                                                                                                 'account':obj.account_id.name,
                                                                                                 'partner':obj.partner_id.name,
                                                                                                 'credit':obj.credit,
                                                                                                 'debit':obj.debit,
                                                                                                 'transfer_id':id_transfer,
                                                                                                 'invoice_num':obj.inv_number or invoice_num or '',
                                                                                                 'partner_id':obj.partner_id and obj.partner_id.id or False,
                                                                                                 'line_id':obj.id,
                                                                                                 'state':'done',
                                                                                                 'inv_type': obj.inv_type
                                                                                                })
                     if id_transfer:
                         self.write(cr, uid, ids, {'state':'done'})
                     else:
                          raise osv.except_osv("Se ha borrado la linea del Pago")
                         
        return True
    
    def _read_amout(self, cr, uid, ids, field_name, args, context):
         res = {}
         for item in self.browse(cr, uid, ids):
             total = 0.0
             total2 = 0.0
             total3 = 0.0
             for il in item.invoce_line_ids:
                 if il.state == 'valid' and il.has_transfer:#Transferencia
                     total += il.amount_total
                 if il.state == 'valid' and il.cheque and il.chq and il.payment_type not in ['CARD']:#Cheque
                     total2 += il.amount_total
                 if il.state == 'valid' and il.cheque and il.chq and il.payment_type == 'CARD':#Cheque Tarjeta de Credito
                     total3 += il.amount_total
             if not total:
                 if not total3:
                     if total2:
                         cr.execute("""
                             UPDATE payment_transfer_payment
                                 SET type=%s 
                            WHERE id=%s""", ('check', item.id))
                 if not total2:
                     if total3:
                         cr.execute("""
                             UPDATE payment_transfer_payment
                                 SET type=%s 
                            WHERE id=%s""", ('credit_card', item.id))
             if not total2:
                if not total3:
                    if total:
                        cr.execute("""
                             UPDATE payment_transfer_payment
                                 SET type=%s 
                            WHERE id=%s""", ('transfer', item.id))
             if not total3:
                 if not total2:
                     if total:
                         cr.execute("""
                             UPDATE payment_transfer_payment
                                 SET type=%s 
                            WHERE id=%s""", ('transfer', item.id))
                                    
             cr.execute("""
                         UPDATE payment_transfer_payment
                         SET monto_transfer=%s,
                             monto_cheque=%s,
                             monto_card=%s 
                        WHERE id=%s""", (total, total2, total3, item.id))
             res[item.id] = str(total + total2 + total3)
         return res
     
    def _get_period(self, cr, uid, context):
        period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', time.strftime('%Y-%m-%d')),
                                                                   ('date_stop', '>=', time.strftime('%Y-%m-%d'))])
        if period_ids:
            return period_ids[0]
        
    def _get_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        type = context.get('type', 'transfer')
        return type
    
    def change_all_check(self, cr, uid, ids, context=None):
        context = context or {}
        transfers_ids = self.read(cr, uid, ids, ['type', 'invoce_line_ids'])
        for item in transfers_ids:
            context['field'] = 'has_transfer' if item['type'] == 'transfer' else 'chq'
            self.pool.get('invoice.line.transfer').change_check(cr, uid, item['invoce_line_ids'], context)
        return True
    
    def view_init(self, cr, uid, fields_list, context=None):
        context = context or {}
        if context.get('active_model') == 'account.voucher' and context.get('active_ids'):
            voucher_ids = self.pool.get('account.voucher').browse(cr, uid, context['active_ids'])
            context['default_invoce_line_ids'] = []
            for voucher_id in [aux for aux in voucher_ids if not aux.comprobante_id and aux.state == 'posted']:
                bank_account_id = self.pool.get('res.partner.bank').search(cr, uid, [('partner_id', '=', voucher_id.partner_id.id)], limit=1)
                context['default_invoce_line_ids'].append({
                    'name': voucher_id.partner_id.name,#fields.char('Nombre', size=20),
                    'date_maturity': time.strftime('%Y-%m-%d'),#fields.date('Fecha vencimiento', help="Fecha máxima de Pago"),
                    'amount_total': voucher_id.amount,
                    'bank_account_id': bool(bank_account_id) and bank_account_id[0],
                    'identification_number': voucher_id.partner_id.ident_num,
                    'identification_type': voucher_id.partner_id.ident_type,
                    'account_mov_id': None,#fields.many2one('account.move.line', 'Línea de Asiento', help='Linea de Movimiento', ondelete='set null'),
                    'invoice_num': None,#fields.char('Nro.Factura', size=60),
                    'supplier_code': voucher_id.partner_id.ref,#fields.char ('Codigo', size=20),
                    'partner': voucher_id.partner_id.id,
                    'has_transfer': False,#fields.boolean('Transferencia'),
                    'cheque': False,#fields.boolean('Cheque'),
                    'chq': False,#fields.boolean('Marcar'),
                    'note': 'PAGO #%s (%s)'%(voucher_id.number, voucher_id.id),#fields.char('Nota', size=60),
                    'payment_type': voucher_id.partner_id.payment_type,#fields.char('Forma de Pago', size=50, required=False),
                    'card': None,#fields.char('Tarjeta', readonly=False, size=50),
                    'origin': 'PAGO #%s (%s)'%(voucher_id.number, voucher_id.id),#fields.char('Origen', size=50), #Si es factura, liquidacion
                    'date_invoice': None,#fields.date('Fecha Factura'),
                    'date_payment': time.strftime('%Y-%m-%d'),#fields.date('Fecha Pago'),
                    'statement_line_id': None,#fields
#                     'state': 'draft'
                })
    
    _columns = {
              'name':fields.char('Nombre', size=1000, required=True, select=True),
              'bank_account_id': fields.many2one('res.partner.bank', 'Cuenta bancaria', required=True, domain=[('partner_id.is_provider', '=', True)],
                                                 readonly=True, states={'draft':[('readonly', False)], 'done':[('readonly', False)]}),
              'invoce_line_ids':fields.one2many('invoice.line.transfer', 'transfer_id', 'Línea de Pago'),
              'state': fields.selection([('draft', 'Borrador'),
                                         ('done', 'Listo'),
                                         ('printed', 'Impreso')], 'Estado', readonly=True),
              'tipo_com':fields.selection([('invoice', 'Factura'),
                                           ('purchase_liq', 'Liquidación de Compra'),
                                           ('anticipo', 'Anticipo'),
                                           ('liquidacion', 'Liquidacion de Viaje'),
                                           ('gas_no_dedu', 'Gasto no Deducible'),
                                           ('doc_inst_est', 'Doc. Emitido Estado'),
                                           ('apunte', 'Asiento por Apunte'),
                                           ('sales_note', 'Nota de Venta')], 'Tipo de Comprobante', size=60, help="Tipos de Comprobante que desee cargar\n"),
              'generation_date':fields.date('Fecha de Pago', select=True),
              'payment_date':fields.date('Fecha Emision Cash', select=True),
              'contador':fields.integer('Nro.de Pago'),
              'tarjeta': fields.selection([('DINERS', 'DINERS CLUB'),
                                           ('AMERICAN', 'AMERICAN EXPRESS')], 'Tarjeta'),
              'gasto_bancario':fields.char('Gasto Bancario', size=100, required=False),
              'monto':fields.function(_read_amout, string='Total', type='char', method=True, store=False, size=32),
              'period_id':fields.many2one('account.period', 'Periodo', help='Periodo de la Factura.'),
              'statement_id':fields.many2one('account.bank.statement', 'Extracto Bancario',
                                             help='Extracto Bancario Nota: El extracto se carga si '\
                                                  'llena y guarda primero los campos: Nombre y Tipo de Compronbate del Formulario'),
              'type':fields.selection([('transfer', 'Transferencia'),
                                       ('check', 'Cheque'),
                                       ('credit_card', 'Tarjeta de Credito')
                                      ], 'Tipo de Pago'),
              'monto_transfer':fields.char('Monto', size=50),
              'monto_cheque':fields.char('Monto', size=50),
              'monto_card':fields.char('Monto', size=50),
              'group_by':fields.selection([('by_partner', 'Proveedor'),
                                           ('by_none', 'Un solo Pago'),
                                          ], 'Agrupar por', help='Proveedor: Agrupa el pago por proveedor.\n Un solo Pago: Crea un solo pago a nombre de la persona que elija.'),
              'payable_to':fields.char('Pago a Nombre', size=100, help='Nombre de la persona que saldra el pago'), #Cheque
              'transfer_to':fields.selection([('partner_to', 'Proveedor')], 'Pago A un', help='Escoja aqui el nombre de persona que recibira el pago'), #Tranferencias a Nombre de
              #---- 'transfer_to':fields.selection([('partner_to', 'Proveedor'),
                                              #----- ('employee_to', 'Empleado')
                                              # ], 'Pago A un', help='Escoja aqui el nombre de persona que recibira el pago'), #Tranferencias a Nombre de
              'supplier_to':fields.many2one('res.partner', 'Proveedor', help='Nombre del proveedro que se realizar la Transfencia', ondelete="cascade"),
              #'employee_to':fields.many2one('hr.employee', 'Empleado', help='Nombre del Empleado que se realizar la Transfencia', ondelete="cascade"),
              }

    _defaults = {
               'type': _get_type,
               'generation_date':lambda * a: time.strftime('%Y-%m-%d'),
               'state':lambda * a: 'draft',
               'contador':lambda * a: 0,
               'tipo_com': lambda * a: 'invoice',
               'period_id':_get_period,
               'group_by':lambda * a: 'by_partner',
               'transfer_to':lambda * a: 'partner_to',
               }
payment_transfer_payment()


class account_bank_statement(osv.osv):
    _name = "account.bank.statement"
    _inherit = "account.bank.statement"
    
    #Los campos de la sequencia tenemos que poner en accoun_invoice_retencion en la clase account.py 
    
    def button_cancel(self, cr, uid, ids, context={}):
        #print 'Herencia del button cancel del statement'
        done = []
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')
        statement_line_obj = self.pool.get('account.bank.statement.line')
        account_invoice_obj = self.pool.get('account.invoice')
        
        for st in self.browse(cr, uid, ids, context):
            if st.state == 'draft':
                continue
            self.write(cr, uid, ids, {'move_id':None})
            move_id = []
            invoices_id = []
            ultima_line = None
            for line in st.line_ids:
                #ultima_line = line
                ultima_line = line.journal_entry_id.id
                statement_line_obj.write(cr, uid, line.id, {'state':'draft'}, context=context)
                if line.invoice_id:
                    invoices_id.append(line.invoice_id)
                
            #move_id.append(ultima_line.move_ids[0].id)
            move_id.append(ultima_line)
            print"ultima_line=%s"%ultima_line
            account_move_obj.button_cancel(cr, uid, move_id, context)
            account_move_line_ids = account_move_line_obj.search(cr, uid, [('move_id', 'in', move_id)])
            account_move_line_obj._remove_move_reconcile(cr, uid, account_move_line_ids, context=None)
            context['invoice_ids'] = invoices_id
            account_invoice_obj.change_state_paid_to_open(cr, uid, ids, context)
            account_move_obj.unlink(cr, uid, move_id, context)
            done.append(st.id)
        self.write(cr, uid, done, {'state':'draft'}, context=context)
        return True
    
    def _check_inv_auth(self, cr, uid, in_invoice):
        #print "_check_inv_auth", in_invoice
        for inv in self.pool.get('account.invoice').browse(cr, uid, in_invoice):
            if inv.type in ['in_invoice', 'in_refund']:
                if inv.auth_inv_id.doc_type != 'custom':
                    continue
                if inv.auth_inv_id.num_start <= int(inv.number_inv_supplier) <= inv.auth_inv_id.num_end:
                    return True
                elif inv.tipo_factura in ['anticipo']:
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
    
    def button_confirm_bank(self, cr, uid, ids, context={}):
        """Aumente el campo invoice_id y envio a escribir el invoice_id"""
        #print 'button_confirm', context 
        
        done = []
        res_currency_obj = self.pool.get('res.currency')
        res_users_obj = self.pool.get('res.users')
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')
        account_bank_statement_line_obj = self.pool.get('account.bank.statement.line')
        account_bank_statement_line_rel_obj = self.pool.get('account.bank.statement.line.rel')
        invoice_obj = self.pool.get('account.invoice')
        statement_reconcile_obj = self.pool.get('account.bank.statement.reconcile')
        
        company_currency_id = res_users_obj.browse(cr, uid, uid, context=context).company_id.currency_id.id
          
        for st in self.browse(cr, uid, ids, context):
            """Cabecera account_bank_statement"""
                            
            if not st.state == 'draft' and not context.get('moves_cancel_check', []):
                continue

            if st.state == 'draft':
                if not (abs(st.balance_end - st.balance_end_real) < 0.0001):
                    raise osv.except_osv(('¡ Error !'), ('¡El balance del extracto bancario es incorrecto!\n') + 
                        ('El balance previsto (%.2f) es diferente del calculado. (%.2f)') % (st.balance_end_real, st.balance_end))
            if (not st.journal_id.default_credit_account_id) \
                    or (not st.journal_id.default_debit_account_id):
                raise osv.except_osv(_('¡Error de configuración!'),
                        ('Compruebe que se ha definido una cuenta en el diario.'))
            
            
            #Entra si se anade lineas de asientos reales en el extracto bancario
            for line in st.move_line_ids:
                print "entro a move lines",line
                if line.state <> 'valid':
                    raise osv.except_osv(_('¡ Error !'),
                            ('Las líneas de los asientos contables no están en estado válido.'))
            # for bank.statement.lines
            # In line we get reconcile_id on bank.ste.rec.
            # in bank stat.rec we get line_new_ids on bank.stat.rec.line
            i = 0
            lineas_torec = []
            val_move_line = []
            
            
            """Se crea el asiento"""
            """Paso 1 Crear Cabecera Move """
            move_id = account_move_obj.create(cr, uid, {
                'bandera':i,
                'tipo':"extracto",
                'journal_id': st.journal_id.id,
                'period_id': st.period_id.id,
                'date': st.date,
                'name':st.num_deposit or st.name or '/',
                'ref':st.concepto,
                'tipo_comprobante':st.tipo_comprobante,
            }, context=context)
            
            #"""Paso 2  Actualizo Account.Statement.Move.Line Tabla intermedia """
            #account_bank_statement_line_obj.write(cr, uid, [move.id], {
            #                                                               'move_ids': [(4, move_id, False)]
            #                                                               })
            
            """Recorro las facturas importadas y esta creadas en Account.Statment.Line o lineas aumentadas manualmente"""
            for move in st.line_ids:
                invoices_pay = []
                context.update({'date':move.date})
                in_invoice = move.invoice_id
                out_invoice = move.out_invoice_id
                #print "in_invoice", in_invoice
                #print "out_invoice", out_invoice
                move_ref_id = move.move_ref_id
                tipo = ''
                apunte = False
                if move.apunte:
                    apunte = True
                torec = []
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
                    
                    #print 'como q no vale esta parte', out_invoice
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
                                    if z.type_move == 'ANU':
                                        continue
                                    if movimiento['amount'] > 0:
                                        if z.credit > 0:
                                            torec.append(z.id)
                                    elif movimiento['amount'] < 0:
                                        if z.debit > 0:
                                            torec.append(z.id)
                
                #Linea agregada en algun lado  o saldo inicial
                #if out_invoice and move.apunte:
                if move.apunte and not out_invoice and not in_invoice and move_ref_id and move.type != 'general':
                    #print 'Entro por aqui *****',
                    torec.append(move_ref_id)
                    #args = [('ref', '=', move.ref), ('state', '=', 'draft'), ('apunte', '=', True)]
                    #if move.partner_id and move.partner_id.id:
                    #    args.append(('partner_id', '=', move.partner_id.id))
                    ##print 'args', args 
                    #invoices_pay = account_bank_statement_line_obj.search(cr, uid, args)
                    ##print 'lineas de iniciales', invoices_pay 
                    #if len(invoices_pay) >= 1: #DEbo volver a draft en el boton cancelar
                    #    #print ' dentro del if *** '
                    #    for i in invoices_pay:
                    #        sql = 'select statement_id from account_bank_statement_line_move_rel where move_id=' + str(i)
                    #        
                    #        #print ' sql *** ', sql 
                    #        cr.execute(sql)
                    #        res = map(lambda x: x[0], cr.fetchall())
                            
                    #        #print ' res ***', res
                    #        movimiento = account_bank_statement_line_obj.read(cr, uid, i, ['amount'])
                    #        #print "movimiento pagos iniciales", movimiento
                            
                    #        for x in account_move_obj.browse(cr, uid, res):
                                
                    #            for z in x.line_id:
                    #                if z.type_move == 'ANU':
                    #                    continue
                    #                if movimiento['amount'] > 0:#
                    #                    if z.credit > 0:
                    #                        torec.append(z.id)
                    #                elif movimiento['amount'] < 0:
                    #                    if z.debit > 0:
                    #                        torec.append(z.id)
                    
                'Facturas de Proveedor'                
                if in_invoice and not move.apunte:
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
                            #print "res",
                            movimiento = account_bank_statement_line_obj.read(cr, uid, i, ['amount'])
                            #print "movimiento pagos", movimiento
                            for x in account_move_obj.browse(cr, uid, res):
                                for z in x.line_id:
                                    if z.type_move == 'ANU':
                                        continue
                                    if movimiento['amount'] > 0:
                                        if z.credit > 0:
                                            torec.append(z.id)
                                    elif movimiento['amount'] < 0:
                                        if z.debit > 0:
                                            torec.append(z.id)
                        
                if move.payment_form in ['DINERS', 'AMERICAN']:
                    tipo = str(move.payment_form)
                    #print "tipo", tipo
                
                """Paso 2  Actualizo Account.Statement.Move.Line Tabla intermedia """
                account_bank_statement_line_obj.write(cr, uid, [move.id], {
                                                                           'move_ids': [(4, move_id, False)]
                                                                           })
                #print 'move_id: ', move_id
                if not move.amount:
                    continue

                
                if move.amount >= 0:
                    """Codigo para identificar si el pago es por tarjeta """
                    if tipo in ['DINERS' , 'AMERICAN' , 'CANJE']:
                        if tipo == 'DINERS':
                            account_id = 1752
                        if tipo == 'AMERICAN':
                            account_id = 1753
                        if tipo == 'CANJE':
                            account_id = 1229
                    else:
                        account_id = st.journal_id.default_debit_account_id.id
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
                        account_id = st.journal_id.default_credit_account_id.id
                        tipo = ''
                acc_cur = ((move.amount <= 0) and st.journal_id.default_credit_account_id) or move.account_id
                
                amount = res_currency_obj.compute(cr, uid, st.currency.id,
                        company_currency_id, move.amount, context=context)
                
                #if move.reconcile_id and move.reconcile_id.line_new_ids:
                #    for newline in move.reconcile_id.line_new_ids:
                 #       amount += newline.amount
                """Creacion de linea de Debit o Credito en Caso de proveedores"""
                if move.invoice_id:
                    val = {
                    'name': move.name,
                    'date': st.date,
                    'ref': move.ref,
                    'move_id': move_id,
                    'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                    'account_id': (move.account_id) and move.account_id.id,
                    'credit': ((amount > 0) and amount) or 0.0,
                    'debit': ((amount < 0) and -amount) or 0.0,
                    'statement_id': st.id,
                    'journal_id': st.journal_id.id,
                    'period_id': st.period_id.id,
                    'currency_id': st.currency.id,
                    'invoice_id':move.invoice_id,
                    'date_maturity':move.date_maturity,
                    #'employee_id':move.employee_id.id,
                    'type_hr':move.type_hr,
                    'payment_form':move.payment_form or False,
                    'type_move':'EG',
                    'statement_line_id':move.id,
                    'analytic_account_id':move.analytic_account_id.id
                    }
                else:
                     
                    val = {
                        'name': move.name,
                        'date': st.date,
                        'ref': move.ref,
                        'move_id': move_id,
                        'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                        'account_id': (move.account_id) and move.account_id.id,
                        'credit': ((amount > 0) and amount) or 0.0,
                        'debit': ((amount < 0) and -amount) or 0.0,
                        'statement_id': st.id,
                        'journal_id': st.journal_id.id,
                        'period_id': st.period_id.id,
                        'currency_id': st.currency.id,
                        'date_maturity':move.date_maturity,
                        #'employee_id':move.employee_id.id,
                        'type_hr':move.type_hr,
                        'payment_form':move.payment_form or False,
                        'out_invoice_id':move.out_invoice_id,
                        'apunte':apunte,
                        'type_move':move.out_invoice_id and 'IN',
                        'statement_line_id':move.id,
                        'analytic_account_id':move.analytic_account_id.id
                    }
                    #print ' FACTURA DE CLIENTE ', val

                val.update(dict(key, eval(value)) for key, value in context.get('vals', {}))
                val_move_line.append(val)
                amount = res_currency_obj.compute(cr, uid, st.currency.id,
                        company_currency_id, move.amount, context=context)
                
                if st.currency.id <> company_currency_id:
                    amount_cur = res_currency_obj.compute(cr, uid, company_currency_id,
                                st.currency.id, amount, context=context,
                                account=acc_cur)
                    
                    val['amount_currency'] = -amount_cur

                if move.account_id and move.account_id.currency_id and move.account_id.currency_id.id <> company_currency_id:
                    val['currency_id'] = move.account_id.currency_id.id
                    if company_currency_id == move.account_id.currency_id.id:
                        amount_cur = move.amount
                    else:
                        amount_cur = res_currency_obj.compute(cr, uid, company_currency_id,
                                move.account_id.currency_id.id, amount, context=context,
                                account=acc_cur)
                    val['amount_currency'] = amount_cur
                    
                """Creacion de Move.Lines la linea del pago del Diario del Extracto Bancario"""
                ##print 'antes', torec
                #print 'creacion move line ***', val     
                torec.append(account_move_line_obj.create(cr, uid, val , context=context))
                if 'moves_cancel_check' in context:
                    ##print 'moves_cancel_check', context
                    for item in context.get('moves_cancel_check'):
                        torec.append(item)
                        
                torec = list(set(torec))
                
                #print 'despues ***', torec
                """
                Movimiento Adicional Para pagos de Tarjetas de Credito y Canje
                Se incluye el pago de asientos por apunte pagado con tarjeta de credito
                """
                if (in_invoice or out_invoice or not out_invoice) and tipo in ['DINERS', 'AMERICAN', 'CANJE']:
                    """Creacion del Debit con codigo de cuenta Dinners"""
                    #print "debit", tipo
                    val = {
                        'name': move.name,
                        'date': st.date,
                        'ref': move.ref,
                        'move_id': move_id,
                        'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                        'account_id': account_id,
                        'credit': ((amount > 0) and amount) or 0.0,
                        'debit': ((amount < 0) and -amount) or 0.0,
                        'statement_id': st.id,
                        'journal_id': st.journal_id.id,
                        'period_id': st.period_id.id,
                        'currency_id': st.currency.id,
                         #*Em
                        'invoice_id':move.invoice_id,
                        'date_maturity':move.date_maturity,
                        'card':True,
                        'payment_form':move.payment_form or False,
                        'out_invoice_id':move.out_invoice_id,
                        'apunte':apunte,
                        'type_move':move.out_invoice_id and 'IN' or move.invoice_id and 'EG' or 'TAR',
                        #TODO CAMBIAR AL PUBLIC
                        #'preproject_id':move.preproject_id.id or False,
                        'statement_line_id':move.id,
                        #TODO CAMBIAR AL PUBLIC
                        #'funds_certificate_id':move.funds_certificate_id.id,
                        #'numero_orden':move.numero_orden,
                        'analytic_account_id':move.analytic_account_id.id,
                    }
                    #print 'creacion valll ', val
                    #account_move_line_obj.create(cr, uid, val , context=context)
                    val_move_line.append(val)
                       
                
                #NO SE EJECUTA YA NO EXISTE ESTE OBJETO RECONCILE
                if move.reconcile_id and move.reconcile_id.line_new_ids:
                    for newline in move.reconcile_id.line_new_ids:#Lineas de Ajuste en la parte concilacion
                        if move.invoice_id:
                            account_move_line_obj.create(cr, uid, {
                                'name': newline.name or move.name,
                                'date': st.date,
                                'ref': move.ref,
                                'move_id': move_id,
                                'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                                'account_id': (newline.account_id) and newline.account_id.id,
                                'debit': newline.amount > 0 and newline.amount or 0.0,
                                'credit': newline.amount < 0 and -newline.amount or 0.0,
                                'statement_id': st.id,
                                'journal_id': st.journal_id.id,
                                'period_id': st.period_id.id,
                                'invoice_id':move.invoice_id,
                                'date_maturity':move.date_maturity,
                                #'employee_id':move.employee_id.id,
                                'type_hr':move.type_hr,
                                'type_move':'AJ',
                                'statement_line_id':move.id,
                                'analytic_account_id':move.analytic_account_id.id,
                            }, context=context)
                        else:
                            account_move_line_obj.create(cr, uid, {
                                'name': newline.name or move.name,
                                'date': st.date,
                                'ref': move.ref,
                                'move_id': move_id,
                                'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                                'account_id': (newline.account_id) and newline.account_id.id,
                                'debit': newline.amount > 0 and newline.amount or 0.0,
                                'credit': newline.amount < 0 and -newline.amount or 0.0,
                                'statement_id': st.id,
                                'journal_id': st.journal_id.id,
                                'period_id': st.period_id.id,
                                'date_maturity':move.date_maturity,
                                #'employee_id':move.employee_id.id,
                                'type_hr':move.type_hr,
                                'type_move':'AJ',
                                'statement_line_id':move.id,
                                'analytic_account_id':move.analytic_account_id.id,
                            }, context=context)

                # Fill the secondary amount/currency
                # if currency is not the same than the company
                amount_currency = False
                currency_id = False
                if st.currency.id <> company_currency_id:
                    amount_currency = move.amount
                    currency_id = st.currency.id
                """Creacion de linea Credit"""
                if move.invoice_id:
                    #print 'creacion move line aaa ', account_id
                    
                    val = {
                        'name': move.name,
                        'date': st.date,
                        'ref': move.ref,
                        'move_id': move_id,
                        'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                        'account_id': account_id,
                        'credit': ((amount < 0) and -amount) or 0.0,
                        'debit': ((amount > 0) and amount) or 0.0,
                        'statement_id': st.id,
                        'journal_id': st.journal_id.id,
                        'period_id': st.period_id.id,
                        'amount_currency': amount_currency,
                        'currency_id': currency_id,
                        'invoice_id':move.invoice_id,
                        'date_maturity':move.date_maturity,
                        #'employee_id':move.employee_id.id,
                        'type_hr':move.type_hr,
                        'type_move':'EG',
                        'statement_line_id':move.id,
                        'analytic_account_id':move.analytic_account_id.id,
                    }
                    val_move_line.append(val)   
                    #account_move_line_obj.create(cr, uid, val, context=context)
                    
                else:
                    #print 'crear move_line bbb move_id ', move_id
                    #print 'crear move_line bbb account_id ', account_id
                    val = {
                        'name': move.name,
                        'date': st.date,
                        'ref': move.ref,
                        'move_id': move_id,
                        'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                        'account_id': account_id,
                        'credit': ((amount < 0) and -amount) or 0.0,
                        'debit': ((amount > 0) and amount) or 0.0,
                        'statement_id': st.id,
                        'journal_id': st.journal_id.id,
                        'period_id': st.period_id.id,
                        'amount_currency': amount_currency,
                        'currency_id': currency_id,
                        'date_maturity':move.date_maturity,
                        #'employee_id':move.employee_id.id,
                        'type_hr':move.type_hr,
                        'out_invoice_id':move.out_invoice_id,
                        'apunte':apunte,
                        'type_move':'IN',
                        'statement_line_id':move.id,
                        'analytic_account_id':move.analytic_account_id.id,
                        } 
                    #account_move_line_obj.create(cr, uid, val, context=context)
                    val_move_line.append(val)
                    
                """ 
                Movimiento Credit adicional para 
                Pago con Tarjeta Dinners con Cuenta De Banco por Pagar
                """
                if (in_invoice or out_invoice or not out_invoice) and tipo in ['DINERS', 'AMERICAN', 'CANJE']:
                    #print 'Creacion move_line ccc ', move_id
                    #print 'Creacion move_line ccc ', st.journal_id.default_credit_account_id.id
                    
                    val = {
                        'name': move.name,
                        'date': st.date,
                        'ref': move.ref,
                        'move_id': move_id,
                        'partner_id': ((move.partner_id) and move.partner_id.id) or False,
                        'account_id': st.journal_id.default_credit_account_id.id,
                        'credit': ((amount < 0) and -amount) or 0.0,
                        'debit': ((amount > 0) and amount) or 0.0,
                        'statement_id': st.id,
                        'journal_id': st.journal_id.id,
                        'period_id': st.period_id.id,
                        'amount_currency': amount_currency,
                        'currency_id': currency_id,
                        'invoice_id':move.invoice_id,
                        'date_maturity':move.date_maturity,
                        'type_hr':move.type_hr,
                        'card':True,
                        'payment_form':move.payment_form or False,
                        'out_invoice_id':move.out_invoice_id,
                        'apunte':apunte,
                        'type_move':move.out_invoice_id and 'IN' or move.invoice_id and 'EG' or 'TAR',
                        'statement_line_id':move.id,
                        'analytic_account_id':move.analytic_account_id.id,
                    }
                    
                    #account_move_line_obj.create(cr, uid, val, context=context)
                    val_move_line.append(val)
                        
                #for line in account_move_line_obj.browse(cr, uid, [x.id for x in account_move_obj.browse(cr, uid, move_id, context=context).line_id],
                #                                         context=context):
                #    if line.state <> 'valid':
                #        raise osv.except_osv(_('¡ Error !'),
                #                ('Línea de asiento contable "%s" no es valida') % line.name)
                
#                    if move.reconcile_id:
#                        if not move.reconcile_id.line_ids:#Se modifico la linea de asiento de la factura
                invoices = ""
                if in_invoice and not move.apunte:
                    invoices = invoice_obj.search(cr, uid, [('id', '=', in_invoice), ('state', 'in', ['open', 'paid']), ])
                if out_invoice and not move.apunte:
                    invoices = invoice_obj.search(cr, uid, [('id', '=', out_invoice), ('state', 'in', ['open', 'paid']), ])
                
                if invoices:
                    #print 'invoices ', invoices 
                    cr.execute('select \
                            l.id \
                        from account_move_line l \
                            left join account_invoice i on (i.move_id=l.move_id) \
                        where i.id in (' + ','.join(map(str, invoices)) + ') and l.account_id=i.account_id')
                    res = map(lambda x: x[0], cr.fetchall())
                    #statement_reconcile_obj.write(cr, uid, move.reconcile_id.id, {'line_ids':[(6, 0, res)]}, context=context)
                    #print 'res ***', res
                    if len(res) > 1:
                       res = [move.move_ref_id]

                    torec += map(lambda x: x, res)
                    #print 'torec ***', torec 
                        #Aqui no busco la linea del saldo inicial por que se supone que ese no se puede cambiar a borrador y no se borra el asiento
#                        else:
#                            #Toma la linea de la cuenta que voy a pagar osea aqui tomo el move_line de la factura o saldo inicial etc.
#                            torec += map(lambda x: x.id, move.reconcile_id.line_ids)
                        
                    #Factura de Cliente : move.apunte false, True es saldo inicial
                    if move.out_invoice_id and (not move.apunte):
                        rtotal = 0.0 
                        id_factura = invoice_obj.search(cr, uid, [('id', '=', move.out_invoice_id), ('type', '=', 'out_invoice')])
                        #print "factura de cliente", id_factura
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
                            #print "res", res
                            if res:
                                rtotal = res[0]['tretencion']
                                retencion = res[0]['move']
                                movert = account_move_line_obj.search(cr, uid, [('move_id', '=', retencion),
                                                                               ('credit', '!=', 0.0)])
                                context['retencion'] = True
                                torec.append(movert[0]) 
                                
                    #Para reconciliar parcial o total las facturas
                    #lineas_torec.append((torec, move))
                #Cambio el estado para saber que se valido esa linea de extracto
                lineas_torec.append((torec, move))
            
            #print ' val_move_line ', val_move_line
            self.move_line_bank(cr, uid, ids, val_move_line, st, context)
            #print ' lineas ***', lineas_torec
            self.reconcile_total_patial(cr, uid, ids, lineas_torec, context=context)    
            account_move_obj.post(cr, uid, [move_id], context=None)
            i += 1
            self.write(cr, uid, [st.id], {'state':'confirm', 'move_id':move_id}, context=context)
        return True  
    
    """
    Metodo que agrupa en el extracto bancario las lineas de asiento del banco
    """
    def move_line_bank(self, cr, uid, ids, vals_move_line, st, context):
        
        account_move_line_obj = self.pool.get('account.move.line')
        #Las cuentas contables del plan de cuentas que son de bancos
        #cta_bank = [1366, 1367, 1368, 1369, 4534]
        cta_bank = [14,277,278]
        mount_debit = 0.0
        mount_credit = 0.0
        
        i = 0
        for move_line in vals_move_line:
            print move_line, vals_move_line
            if move_line['account_id'] in cta_bank:
                mount_debit += move_line['debit'] or 0.0 
                mount_credit += move_line['credit'] or 0.0
                i += 1        
        
        if i != 0:
            move_line['credit'] = mount_credit or 0.0
            move_line['debit'] = mount_debit or 0.0
            move_line['partner_id'] = False
            ##print ' move_line ', move_line
            account_move_line_obj.create(cr, uid, move_line, context=context)
            
        else:
            for move_line in vals_move_line:
                account_move_line_obj.create(cr, uid, move_line, context=context)
             

            
    def reconcile_total_patial(self, cr, uid, ids, data, context=None):
        
        account_move_line_obj = self.pool.get('account.move.line')
        for line_reconcile in data:
            torec = line_reconcile[0]
            if len(torec) < 2:
                continue
            move = line_reconcile[1]
            st = move.statement_id
            
            if abs(round(move.reconcile_amount, 2) - round(move.amount, 2)) < 0.01:
                #print "Pago Completo del Extracto Bancario"
                writeoff_acc_id = False
                #print " torec dentro del if torec:%s statement_line: %s " % (torec, move.id)
                account_move_line_obj.reconcile(cr, uid,
                                                        torec,
                                                        'statement',
                                                        writeoff_acc_id=writeoff_acc_id,
                                                        writeoff_period_id=st.period_id.id,
                                                        writeoff_journal_id=st.journal_id.id,
                                                        context=context)
            else:
                #Realizar pago Parcial
                #print 'Pago Parcial'
                account_move_line_obj.reconcile_partial(cr, uid, torec, 'statement', context)
                     
    
    _columns = {
            'concepto': fields.text('Concepto', required=True),
    }
        
account_bank_statement()

#Aumento tabla para guardar los tipos de movimientos
class account_code_move(osv.osv):
    _name = "account.code.move"
    _description = 'Codigos de Movimientos'
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['code', 'name'], context)
        res = []
        for record in reads:
            name = record['name']
            res.append((record['id'], name))
        return res
    
    _columns = {
            'name':fields.char('Nombre', size=250),
            'code':fields.char('Código', size=15),
            
    }
account_code_move()


class account_bank_statement_line(osv.osv):
    _name = "account.bank.statement.line"
    _inherit = "account.bank.statement.line"
    
    _columns = {
                'invoice_id': fields.integer('Factura Proveedor'),
                'out_invoice_id':fields.integer('Factura Cliente'),
                'date_maturity': fields.date('Fecha vencimiento'),
                #'employee_id':fields.many2one('hr.employee', 'Empleado', readonly=True),
                'type_hr':fields.char('TipoHR', size=8),
                'apunte':fields.boolean('Apunte'),
                #Este campo no se porque pusieron ????
                'reconcile_id': fields.many2one('account.move.reconcile', 'Reconcile', readonly=True, ondelete='set null', select=2),
                
                #Campos que marcan los anticipos y muestran la informacion 
                #correspondiente en cada vendedor y cliente
                'statement_type':fields.selection([('ant', 'ANT'),
                                                   ('nc', 'NDC'),
                                                   ('can', 'CAN'),
                                                   ('ci', 'CI'),
                                                   ], 'Cod.M', select=True, help='ANT: Anticipo Cliente, NDC:Nota de Credito, '\
                                                                                'CAN: Pago Factura '\
                                                                                'CI: Cierre de Anticipo'),
                'is_advance':fields.boolean('Anticipo', help='Marque este campo cuando vaya a registrar un anticipo de cliente'),
                'seller_id':fields.many2one('res.users', 'Vendedor(a)', help='Seleccione el Vendedor(a) al que pertenece el cliente del Anticipo'),
                 #Aumento este estado para saber incluir luego cuando desconciliar
                'state': fields.selection([('draft', 'Draft'),
                                           ('confirm', 'Confirm'),
                                           ('cancel', 'Cancel')
                                           ], 'State', states={'confirm': [('readonly', True)]}, readonly="1"),
                #En este campo guardo el valor que debe pagar la factura del cliente
                #Q pasa si pongo lineas normales.??
                'reconcile_amount': fields.float('Monto', digits_compute=dp.get_precision('Account')),
                #'reconcile_amount':fi
                        }
    _defaults = {
        'apunte': lambda * a : False,
        'is_advance': lambda * a : False,
        'state':lambda * a : 'draft',
      }
    
account_bank_statement_line()


class account_move_line(osv.osv):
    _name = 'account.move.line'
    _inherit = 'account.move.line'
    
    def _read_invoice_type(self, cr, uid, ids, field_name, args, context):
         res = {}
         obj_invoice = self.pool.get('account.invoice')
         for item in self.browse(cr, uid, ids):
             if item.invoice_id:
                 invoice_ids = obj_invoice.search(cr, uid, [('id', '=', item.invoice_id)])
                 if invoice_ids:
#                     tp = obj_invoice.browse(cr, uid, invoice_ids[0])
                     res[item.id] = obj_invoice.browse(cr, uid, invoice_ids[0]).tipo_factura
                 else:
                      res[item.id] = 'apunte'
             elif item.inv_type:
                 res[item.id] = item.inv_type
             elif item.apunte:
                 res[item.id] = 'apunte'
             else:
                 res[item.id] = False
         return res
    
    def _read_invoice_number(self, cr, uid, ids, field_name, args, context):
         res = {}
         obj_invoice = self.pool.get('account.invoice')
         for item in self.browse(cr, uid, ids):
             if item.invoice_id:
                 obj_fact = obj_invoice.search(cr, uid, [('id', '=', item.invoice_id)])
                 if obj_fact:
                     for invoice in obj_invoice.browse(cr, uid, obj_fact):
                         if invoice.number_inv_supplier and invoice.auth_inv_id:
                             num = ''
                             num = str(invoice.number_inv_supplier).zfill(13)
                             num = str(invoice.auth_inv_id.serie_entidad) + '-' + str(invoice.auth_inv_id.serie_emision) + '-' + num
                             res[item.id] = num
                         else:
                             res[item.id] = False
                 else:
                     res[item.id] = False
         return res
    

    _columns = {
                'invoice_id': fields.integer('Factura'),
                'transfer_line_ids':fields.one2many('invoice.line.transfer', 'account_mov_id', 'Invoice Line'),
                'has_transfer': fields.boolean('Transferencia'),
                'inv_type':fields.function(_read_invoice_type, string='Tipo de Factura', type='char', size=60, method=True, store=True),
                'inv_number': fields.function(_read_invoice_number, string='No. Factura', type='char', size=60, method=True, store=True),
                'cheque': fields.boolean('Cheque', help='Indica si este pago se lo realizo con cheque'),
                'card': fields.boolean('Tarjeta', help='Indica si el movimiento de la factura fue creada con Pago con Tarjeta de Credito'),
                #'type_hr':fields.char('TipoHR', size=8),
                'payment_form':fields.char('Tarjeta de Credito', size=50),
                'out_invoice_id':fields.integer('FCliente'),
                'apunte':fields.boolean('Apunte'),
                'statement_line_id':fields.many2one('account.bank.statement.line', 'Linea Extracto Ban', help='Linea del Extracto'),
                'statement_line_id':fields.integer('Linea Extracto Ban'),
              }
    
    _defaults = {
        'has_transfer': lambda * a : False,
        'cheque': lambda * a : False,
        'card': lambda * a : False,
        'apunte': lambda * a : False,
      }
account_move_line()


class invoice_line_transfer(osv.osv):
    _name = 'invoice.line.transfer'
    _description = 'Lineas de Asiento para Generar Cheque o Transferencia'
    _order = "note, invoice_num"
    
    def _update_number(self, cr, uid, ids, field_name, args, context):
         res = {}
         obj_invoice = self.pool.get('account.invoice')
         num = ''
         for item in self.browse(cr, uid, ids):
             if item.account_mov_id:
                 if item.account_mov_id.invoice_id:
                     invoices = obj_invoice.search(cr, uid, [('id', '=', item.account_mov_id.invoice_id)])
                     if invoices:
                         for inv in obj_invoice.browse(cr, uid, invoices):
                             if inv.number_inv_supplier and inv.auth_inv_id:
                                 num = ''
                                 num = str(inv.number_inv_supplier).zfill(13)
                                 num = str(inv.auth_inv_id.serie_entidad) + '-' + str(inv.auth_inv_id.serie_emision) + '-' + num
                                 cr.execute("""UPDATE invoice_line_transfer
                                             SET invoice_num = %s
                                             WHERE id =%s""", (num, item.id))
                                 res[item.id] = num
                             else:
                                 num = inv.code_advance_liq or inv.number or ''
                                 cr.execute("""UPDATE invoice_line_transfer
                                             SET invoice_num = %s
                                             WHERE id =%s""", (num, item.id))
                                 res[item.id] = inv.code_advance_liq or inv.number or ''
                     else:
                         cr.execute("""UPDATE invoice_line_transfer
                                             SET invoice_num = %s
                                             WHERE id =%s""", (num, item.id))
                         res[item.id] = num
                 else:
                     if item.account_mov_id.ref:
                         cr.execute("""UPDATE invoice_line_transfer
                                             SET invoice_num = %s
                                             WHERE id =%s""", (item.account_mov_id.ref, item.id))
                         res[item.id] = item.account_mov_id.ref
                     else:
                         cr.execute("""UPDATE invoice_line_transfer
                                             SET invoice_num = %s
                                             WHERE id =%s""", (num, item.id))
                         res[item.id] = num
             else:
                 cr.execute("""UPDATE invoice_line_transfer
                                             SET invoice_num = %s
                                             WHERE id =%s""", (num, item.id))
                 res[item.id] = False
         return res 
    
    def _on_create_write(self, cr, uid, id, context={}):
        ilt = self.browse(cr, uid, id, context)
        return map(lambda x: x.id, ilt.transfer_id.invoce_line_ids)
    
    def write(self, cr, uid, ids, vals, context=None):
         ##print "ILT Paso 3:Guardar los señalados", vals
         if vals.has_key('has_transfer'):
             if vals['has_transfer'] and 'note' not in vals:
                 ##print "has_transfer true", vals['has_transfer']
                 vals['cheque'] = False
                 vals['has_transfer'] = True
                 vals['note'] = 'Transferencia'
                 id = super(invoice_line_transfer, self).write(cr, uid, ids, vals, context=context)
             elif vals['has_transfer'] and vals['note'] == 'Transferencia':
                 vals['has_transfer'] = True
                 id = super(invoice_line_transfer, self).write(cr, uid, ids, vals, context=context)
             else:
                 vals['has_transfer'] = False
                 id = super(invoice_line_transfer, self).write(cr, uid, ids, vals, context=context)
         else:
              id = super(invoice_line_transfer, self).write(cr, uid, ids, vals, context=context)
         return id
    
    def change_check(self, cr, uid, ids, context=None):
        context = context or {}
        transfers_ids = self.browse(cr, uid, ids)
        ids = [aux.id for aux in transfers_ids if aux.bank_account_id]
        for obj in transfers_ids:
            if not obj.bank_account_id and len(transfers_ids) == 1:
                raise osv.except_osv('Error', u'Es obligatorio la colocación de una cuenta bancaria '
                                     u'para el pago por transferencia al proveedor %s'%obj.partner.name)
        return self.write(cr, uid, ids, {context.get('field', 'has_transfer'): context.get('value')})
    
    _columns = {
        'transfer_id':fields.many2one('payment.transfer.payment', 'Nro. de Transferencia', help='Transferencia', ondelete="cascade"),
        'name':fields.char('Nombre', size=20),
        'bank_account_id': fields.many2one('res.partner.bank', 'Cuenta bancaria', readonly=True,
                                           states={'draft':[('readonly', False)], 'done':[('readonly', False)]}),
        'generation_date':fields.date('Fecha Generacion', help="Fecha de Registro del Pago"),
        'date_maturity':fields.date('Fecha vencimiento', help="Fecha máxima de Pago"),
        'amount_total': fields.float('Total a pagar', help="Monto a Pagar"),
        'identification_number':fields.char('Nro.Identificacion', size=20, help='Numero de identificacion'),
        'identification_type':fields.selection((('c', 'Cédula'),
                                                ('r', 'RUC'),
                                                ('p', 'Pasaporte'),
                                                ('s', 'S/N')
                                                ), 'Tipo Identificacion',
                                               help='Tipo de identificacion (cedula,pasaporte o ruc)'),
        'acc_type':fields.related('bank_account_id', 'acc_type', string='Tipo de cuenta', type='char', size=3),
        'acc_number':fields.related('bank_account_id', 'acc_number', type='char', string='Nro.Cuenta', size=16, store=True),
        'bank_code':fields.related('bank_account_id', 'bank', 'bic', type='char', string='Banco', size=16, store=True),
        'account_mov_id':fields.many2one('account.move.line', 'Línea de Asiento', help='Linea de Movimiento', ondelete='set null'),
        'invoice_num':fields.char('Nro.Factura', size=60),
        'state':fields.selection((('draft', 'Borrador'),
                                  ('valid', 'Validado')), 'Estado'),
        'supplier_code':fields.char ('Codigo', size=20),
        'partner': fields.many2one('res.partner', 'Proveedor', required=True),
        'has_transfer': fields.boolean('Transferencia'),
        'cheque': fields.boolean('Cheque'),
        'chq': fields.boolean('Marcar'),
        'note':fields.char('Nota', size=60),
        'payment_type':fields.char('Forma de Pago', size=50, required=False),
        'card':fields.char('Tarjeta', readonly=False, size=50),
        'origin':fields.char('Origen', size=50), #Si es factura, liquidacion
        'factura':fields.function(_update_number, string='Factura', type='char', size=60, method=True, store=True),
        'date_invoice':fields.date('Fecha Factura'),
        'date_payment':fields.date('Fecha Pago'),
        'statement_line_id':fields.many2one('account.bank.statement.line', 'Linea Extracto', ondelete='set null')
     }
    _defaults = {
                 'state': lambda * a : 'draft',
                 'cheque':lambda * a : True,
                 'generation_date': lambda *a: time.strftime('%Y-%m-%d')
                 }
    
invoice_line_transfer()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
