# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author :  Edison Guachamin edison.guachamin@atikasoft.com.ec
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
from openerp.osv import osv, fields
from openerp import fields as fieldss
import time, datetime

class account_tax(osv.osv):
    _name = 'account.tax'
    _inherit = 'account.tax'
    _columns = {
              'ret_voucher_line_ids':fields.one2many('account.invoice.retention.voucher.line', 'tax_id', 'Lineas del Voucher'),
              }
account_tax()

class account_move(osv.osv):
    _name = 'account.move'
    _inherit = 'account.move'
    _columns = {
                'ret_voucher_ids':fields.one2many('account.invoice.retention.voucher', 'move_id', 'Voucher'),
                }
account_move()

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
    def account_move_get(self, cr, uid, voucher_id, context=None):
        move = super(account_voucher, self).account_move_get(cr, uid, voucher_id, context)
        move_id = self.browse(cr, uid, voucher_id, context=context)
        if move_id.type == 'receipt': move['tipo_comprobante'] = 'IngresoCaja'
        if move_id.type == 'payment': move['tipo_comprobante'] = 'Egreso'
        return move
    
    def cancel_voucher(self, cr, uid, ids, context=None):
        context = context or {}
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            # refresh to make sure you don't unlink an already removed move
            voucher.refresh()
            for line in voucher.move_ids:
                # refresh to make sure you don't unreconcile an already unreconciled entry
                line.refresh()
                if line.reconcile_id:
                    move_lines = [move_line.id for move_line in line.reconcile_id.line_id]
                    move_lines.remove(line.id)
                    reconcile_pool.unlink(cr, uid, [line.reconcile_id.id])
                    if len(move_lines) >= 2:
                        move_line_pool.reconcile_partial(cr, uid, move_lines, 'auto',context=context)

            if voucher.move_id and not context.get('reverse'):
                move_pool.button_cancel(cr, uid, [voucher.move_id.id])
                move_pool.unlink(cr, uid, [voucher.move_id.id])
        res = {
            'state':'cancel',
            'move_id':False,
        }
        self.write(cr, uid, ids, res)
        return True
    
#     def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
#         res = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=context)
#         def nro_factura(move_lines_ids):
#             for move_line in move_lines_ids:
#                 line_id = self.pool.get('account.move.line').browse(cr, uid, move_line['move_line_id'], context)
#                 move_line['nro_factura'] = line_id.invoice.factura
#         for field in ['line_ids', 'line_dr_ids', 'line_cr_ids']:
#             nro_factura(res['value'][field])
#         return res
        
account_voucher()

class account_voucher_line(osv.osv):
    _inherit = 'account.voucher.line'
    #===========================================================================
    # Columns
    nro_factura = fieldss.Char('Nro. Factura', related='move_line_id.invoice.factura')
    #===========================================================================
account_voucher_line()

class account_invoice_retention_voucher(osv.osv):
    _name = "account.invoice.retention.voucher"
    _description = 'Voucher retention'
    
    def unlink(self, cr, uid, ids, context=None):
        for ret_id in self.browse(cr, uid, ids, context):
            if ret_id.state != 'draft':
                raise osv.except_osv('ValidationError', u'No puede borrar retenciones de cliente que se encuentren en estado diferente a borrador.')
            ret_id.invoice_id.write({'ret_voucher': False})
        return super(account_invoice_retention_voucher, self).unlink(cr, uid, ids, context)
    
    #Quitar el metodo anterior    
    def _get_period(self, cr, uid, date):
        period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', date),
                                                                      ('date_stop', '>=', date)])
        if period_ids:
            for p in self.pool.get('account.period').browse(cr, uid, period_ids):
                return p.id
        else:
            raise osv.except_osv(('Aviso'), ('No existe un periodo Creado para esta fecha de creación. Creelo por favor!'))
      
    # Boton generar asientos del comprobante de retencion *EM, se modifico el funcionamiento anterior EG
    def action_move_lines_voucher(self, cr, uid, ids, context=None):
        #print 'action_move_lines_voucher', ids
        obj_move = self.pool.get('account.move')
        obj_move_line = self.pool.get('account.move.line')
        obj_voucher_line = self.pool.get('account.invoice.retention.voucher.line')
        obj_journal = self.pool.get('account.journal')
        obj_account = self.pool.get('account.account')
        torec = []
        inv_open = []
        cad = ''
        out_invoice = 0
        move_id = 0
        period_id = 0
        partner_id = 0
        journal = 0
        des = ''
        ref = ''
        a = []
        n = 0
        for com in self.browse(cr, uid, ids):
            band = False#Retenciones que no tiene facturas
            a.append('R.RENTA#' + str(com.number))
            for inv in com.invoice_ids:
                band = True
            for inv in com.invoice_ids:
                if inv.state in ('open'):
                    inv_open.append(inv.num_retention)
                    cad = cad + str(inv.num_retention) + ' / '
                    move_id_invoice = inv.move_id.id
                    period_id = self._get_period(cr, uid, com.broadcast_date)
                    partner_id = inv.partner_id.id 
                    print"***partner_id***=%s"%partner_id
                    journal = inv.journal_id.id
                    out_invoice = inv.id
                    #Descripcion de la Retencion R.RENTA#1236 FACT# 36963
                    ref = inv.num_retention
#                     n = int(inv.factura) or int(inv.num_retention)
                    n = inv.factura or inv.num_retention
                    a.append('FACT#' + str(n))
                    
            open = len(inv_open)

            if open == 1 and move_id_invoice and band and com.state in ('draft', 'new'):
                des = ' - '.join(a)
                id_v_lines = obj_voucher_line.search(cr, uid, [('ret_voucher_id', '=', com.id)])
                #identificar en cada plan de cuenta el numero de id de la cuenta de clientes
                account_ids = [com.partner_id.property_account_receivable.id, com.partner_id.property_account_payable.id]
#                 account_ids = obj_account.search(cr, uid, [('parent_id', 'in', (4544, 455120))])
                move_line_id = obj_move_line.search(cr, uid, [('move_id', '=', move_id_invoice),
                                                              ('account_id', 'in', account_ids),
                                                              ('credit', '=', 0.00)])                
                #print "Linea de Cuenta por cobrar de Cliente", move_line_id
                obj_cliente = self.pool.get('res.partner').browse(cr, uid, partner_id)                
                if move_line_id:
                    #obj_cliente = obj_move_line.browse(cr, uid, move_line_id)
                    journal_id = obj_journal.search(cr, uid, [('name', 'ilike', ('%retencion%'))])
                    
                    if not journal_id:
                        raise osv.except_osv(('Datos Incompletos'),
                                             ('No existe el diario de nombre RETENCIONES. Por favor crearlo'))
                    if id_v_lines:
                        move_id = obj_move.create(cr, uid, {'journal_id':journal_id[0],
                                                            'period_id':period_id,
                                                            'ref':com.num_voucher_purchase,
                                                            'no_comp':com.num_voucher_purchase,
                                                            'date':com.broadcast_date,
                                                            'tipo_comprobante':'ComproDiario'})

                        obj_v_lines = obj_voucher_line.browse(cr, uid, id_v_lines)
                        total = 0.0
                        account_id = False
                        
                        for line in obj_v_lines:
                            if line.tax_id.account_paid_id:
                                account_id = line.tax_id.account_paid_id.id
                            else:
                                raise osv.except_osv(('Error Uso'),
                                                     ('Configure la cuenta de impuestos de devoluciones de la cuenta de impuestos'))
                            total += line.ret_amount
                            """código añadido para obtener el partner configurado en la cuenta contable"""
                            account_obj = self.pool.get('account.account')
                            print"account_obj=%s"%account_obj
                            cuenta_id = account_obj.search(cr, uid, [('partner_id','!=',None)]) 
                            print"cuenta_id=%s"%cuenta_id
                            
                            if account_id in cuenta_id :
                                partner_account = self.pool.get('account.account').browse(cr, uid, account_id)
                                partner= partner_account.partner_id.id
                                print"partner_idif=%s"%partner
                            else:
                                partner=partner_id
                                                               
                            print"account_id=%s"%account_id                               
                            print"partner=%s"%partner
                            val = {
                                 'date':com.broadcast_date,
                                 'account_id':account_id,
                                 'partner_id':partner,#DC#partner_id,
                                 'period_id':period_id,
                                 'period_id':period_id,
                                 'journal_id':journal_id[0],
                                 'debit':line.ret_amount,
                                 'credit':0.0,
                                 'move_id':int(move_id) ,
                                 'name':line.tax_id.account_paid_id.name,
                                 'state':'valid',
                                 'ref': ref,
                                 'inv_type':'retencion'
                                 }
                            id_m_line = obj_move_line.create(cr, uid, val)
                        if total > 0:
                            val2 = {
                                 'date':com.broadcast_date,
                                 'account_id':obj_cliente.property_account_receivable.id,
                                 'partner_id':partner,#partner_id,
                                 'period_id':period_id,
                                 'journal_id':journal_id[0],
                                 'debit':0.0,
#                                 'name':obj_cliente.property_account_receivable.name,
                                 'name':des,
                                 'credit':total,
                                 'state':'valid',
                                 'move_id':int(move_id) ,
                                 'ref': ref,
                                 'inv_type':'retencion'
                                 }
                            id_n_l = obj_move_line.create(cr, uid, val2)
                            print"int(move_id)=%s"%int(move_id)
                            #===================================================
                            # Generacion de Pago parcial para la Retencion
                            #===================================================
                            
                            
                            partial = obj_move_line.search(cr, uid, [('move_id', '=', move_id_invoice),
                                                                     ('credit', '=', 0.00),
                                                                     ('reconcile_partial_id', '<>', False)])
                            #print "Agrego Retencion al Pago Parcial", partial
                            if partial:
                                torec.append(partial[0])
                                torec.append(id_n_l)
                                ##print "l", torec
                                context['retencion'] = True
                                obj_move_line.reconcile_partial(cr, uid, torec, 'statement', context)
                            else:
                                torec.append(move_line_id[0])
                                torec.append(id_n_l)
                                #print "Creo el pago parcial", torec
                                context['retencion'] = True
                                obj_move_line.reconcile_partial(cr, uid, torec, 'statement', context)
                        
                        if move_id:
                            self.pool.get('account.move').post(cr, uid, [move_id])
                        self.write(cr, uid, [com.id], {'state':'valid', 'move_id':move_id, 'total':total, 'nro_retencion':str(com.number)})
                else:
                    raise osv.except_osv(('Error Uso'), ('Revise la cuenta de cliente de la factura'))
            elif open == 0:
                raise osv.except_osv(('Error Uso'), ('Esta retencion no tiene factura en estado abierto'))
            else:
                raise osv.except_osv(('Error Uso'), ('Estas facturas tienen las misma retencion en estado abierto: ' + cad))

        return True
    
    def action_reconcile_retention(self, cr, uid, ids, context=None):
        #print 'action_reconcile_retention', ids
        obj_move = self.pool.get('account.move')
        obj_move_line = self.pool.get('account.move.line')
        obj_voucher_line = self.pool.get('account.invoice.retention.voucher.line')
        obj_journal = self.pool.get('account.journal')
        torec = []
        total = 0.0
        for com in self.browse(cr, uid, ids):
            #print "com", com
            period_id = self._get_period(cr, uid, com.broadcast_date)
            if not period_id:
                 raise osv.except_osv(('Aviso'), ('No existe el periodo para esta fecha. Cambiela por Favor.!'))
            journal_id = obj_journal.search(cr, uid, [('name', 'ilike', ('%retencion%'))])
            if not journal_id:
                raise osv.except_osv(('Datos Incompletos'), ('No existe el diario de nombre RETENCIONES. Por favor crearlo'))
            if not com.partner_id.id:
                raise osv.except_osv(('Aviso'), ('No existe el Cliente'))
        
            if com.ret_voucher_line_ids:
                move_id = obj_move.create(cr, uid, {'journal_id':journal_id[0],
                                                    'period_id':period_id,
                                                    'ref':com.num_voucher_purchase})
                account_id = False
                
                for line in com.ret_voucher_line_ids:
                    if line.tax_id.account_paid_id:
                        account_id = line.tax_id.account_paid_id.id
                    else:
                        raise osv.except_osv(('Error Uso'),
                                             ('Configure la cuenta de impuestos de devoluciones de la cuenta de impuestos'))
                    total += line.ret_amount
                    val = {
                         'date':com.broadcast_date,
                         'account_id':account_id,
                         'partner_id':com.partner_id.id or False,
                         'period_id':period_id,
                         'journal_id':journal_id[0],
                         'debit':line.ret_amount,
                         'credit':0.0,
                         'move_id':int(move_id),
                         'name':line.tax_id.account_paid_id.name,
                         'state':'valid',
                         'ref': com.name,
                         'inv_type':'retencion'
                         }
                    id_m_line = obj_move_line.create(cr, uid, val)
            else:
                raise osv.except_osv(('Aviso'), ('Ingrese el detalle de la Retencion para continuar'))
                
            if total > 0:
                val2 = { 'date':com.broadcast_date,
                         'account_id':com.partner_id.property_account_receivable.id,
                         'partner_id':com.partner_id.id,
                         'period_id':period_id,
                         'journal_id':journal_id[0],
                         'debit':0.0,
                         'name':'R.RENTA#' + str(com.number) + 'FACT#' + str(com.name),
                         'credit':total,
                         'state':'valid',
                         'move_id':int(move_id),
                         'ref': com.name,
                         'inv_type':'retencion'}
                id_n_l = obj_move_line.create(cr, uid, val2)
                #===================================================
                # Generacion de Pago parcial para la Retencion
                #===================================================
                partial = obj_move_line.search(cr, uid, [('id', '=', com.line_id.id),
                                                         ('reconcile_partial_id', '<>', False)])
                #print "Saldo Inicial Tiene Pagos Parciales", partial
                if partial:
                    torec.append(partial[0])
                    torec.append(id_n_l)
                    context['retencion'] = True
                    obj_move_line.reconcile_partial(cr, uid, torec, 'statement', context)
                else:
                    if not com.line_id.reconcile_id:#Si no esta conciliada la linea
                        torec.append(com.line_id.id)
                        torec.append(id_n_l)
                        ##print "Creo el pago parcial en el asiento por apunte", torec
                        context['retencion'] = True
                        obj_move_line.reconcile_partial(cr, uid, torec, 'statement', context)
            if move_id:
                self.pool.get('account.move').post(cr, uid, [move_id])
            self.write(cr, uid, [com.id], {'state':'valid', 'move_id':move_id, 'total':total, 'nro_retencion':str(com.number)})
        return True
    
    def on_change_move_line(self, cr, uid, ids, line_id):
        res = {'value':{}}
        partner_obj = self.pool.get('res.partner')
        move_line_obj = self.pool.get('account.move.line')
        users_obj = self.pool.get('res.users')
        authoriza_obj = self.pool.get('account.authorisation')
        address = self.pool.get('res.partner.address')
        #print "line_id", line_id
        if line_id:
            users = users_obj.browse(cr, uid, uid)
            res['value']['social_reason'] = users.company_id.name
            company = partner_obj.browse(cr, uid, users.id)
            res['value']['ruc_ci'] = company.ident_num
            move_line = move_line_obj.browse(cr, uid, line_id)
            res['value']['partner_id'] = move_line.partner_id.id
            res['value']['partner'] = move_line.partner_id.name
            res['value']['ruc'] = move_line.partner_id.ident_num
            res_address_ob = self.pool.get('res.partner.address').search(cr, uid, [('partner_id', '=', move_line.partner_id.id)])
            if res_address_ob:
                res['value']['address'] = address.browse(cr, uid, res_address_ob[0]).street
            res['value']['name'] = move_line.ref
            res['value']['amount_reconcile'] = move_line.debit
        return res
    
    def create(self, cr, uid, vals, context=None):
        ##print "create", vals
        partner_obj = self.pool.get('res.partner')
        move_line_obj = self.pool.get('account.move.line')
        users_obj = self.pool.get('res.users')
        address = self.pool.get('res.partner.address')
        if vals.has_key('line_id'):
            if vals['line_id']:
                line_id = vals['line_id'] 
                users = users_obj.browse(cr, uid, uid)
                vals['social_reason'] = users.company_id.name
                company = partner_obj.browse(cr, uid, users.id)
                vals['ruc_ci'] = company.ident_num
                move_line = move_line_obj.browse(cr, uid, line_id)
                vals['partner_id'] = move_line.partner_id.id
                vals['partner'] = move_line.partner_id.name
                vals['ruc'] = move_line.partner_id.ident_num
                res_address_ob = self.pool.get('res.partner.address').search(cr, uid, [('partner_id', '=', move_line.partner_id.id)])
                if res_address_ob:
                    vals['address'] = address.browse(cr, uid, res_address_ob[0]).street
                vals['name'] = move_line.ref
                vals['amount_reconcile'] = move_line.debit or move_line.credit
        voucher_id = super(account_invoice_retention_voucher, self).create(cr, uid, vals, context=context)
        return voucher_id 
    
    def write (self, cr, uid, ids, vals, context=None):
#        #print "write", vals
        partner_obj = self.pool.get('res.partner')
        move_line_obj = self.pool.get('account.move.line')
        users_obj = self.pool.get('res.users')
        address = self.pool.get('res.partner.address')
        if vals.has_key('line_id'):
            if vals['line_id']:
                line_id = vals['line_id']
                #print ' line_id *** ', line_id 
                users = users_obj.browse(cr, uid, uid)
                vals['social_reason'] = users.company_id.name
                company = partner_obj.browse(cr, uid, users.id)
                vals['ruc_ci'] = company.ident_num
                move_line = move_line_obj.browse(cr, uid, line_id)
                vals['partner_id'] = move_line.partner_id.id
                vals['partner'] = move_line.partner_id.name
                vals['ruc'] = move_line.partner_id.ident_num
                res_address_ob = self.pool.get('res.partner.address').search(cr, uid, [('partner_id', '=', move_line.partner_id.id)])
                if res_address_ob:
                    vals['address'] = address.browse(cr, uid, res_address_ob[0]).street
                vals['name'] = move_line.ref
                vals['amount_reconcile'] = move_line.debit or move_line.credit
                #print ' vals *** ', vals
        voucher = super(account_invoice_retention_voucher, self).write(cr, uid, ids, vals, context=context)
        return voucher
    
    def action_cancel_retention(self, cr, uid, ids, context):
        #print "action_cancel_retention", ids
        account_move_obj = self.pool.get('account.move')
        for item in self.browse(cr, uid, ids, context):
            if item.state in ('valid'):
                account_move_obj.button_cancel(cr, uid, [item.move_id.id])
                account_move_obj.unlink(cr, uid, [item.move_id.id])
                if item.line_id:
                    self.pool.get('account.invoice.retention.voucher').write(cr, uid, item.id, {'state':'new'})
                else:
                    self.pool.get('account.invoice.retention.voucher').write(cr, uid, item.id, {'state':'draft'})
        return True
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['number', 'nro_retencion'], context)
        res = []
        for record in reads:
            name = record['nro_retencion']
            if not name:
                name = record['number']
            res.append((record['id'], name))
        return res
    
    _order = "id DESC"
    
    def change_lines(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.retention.voucher.line').browse(cr, uid, ids, context=context):
            result[line.ret_voucher_id.id] = True
        return result.keys()
    
    def change_tax(self, cr, uid, ids, context=None):
        result = {}
        cr.execute('SELECT distinct(ret_voucher_id) FROM account_invoice_retention_voucher_line '
                   'WHERE tax_id = ANY(%s)', (ids,))
        return [aux[0] for aux in cr.fetchall()]
    
    def _get_amounts(self, cr, uid, ids, fields, args, context=None):
        fields = isinstance(fields, list) and fields or [fields]
        res = dict([(id, dict([(field, 0.0) for field in fields])) for id in ids])
        retention_ids = self.browse(cr, uid, ids, context=context)
        for retention in retention_ids:
            for line in retention.ret_voucher_line_ids:
                if line.tax_id.tax_group in fields:
                    res[retention.id][line.tax_id.tax_group] += line.ret_amount
        return res
    
    _columns = {
        'name' : fields.char('Origen', size=100, readonly=True, help="Factura de Cliente del Saldo Inicial"),
        'invoice_id': fields.many2one('account.invoice', 'Factura', required=True),
        'state':fields.selection([('draft', 'Borrador'),
                                  ('new', 'Nueva'), #Estado Creado por la migracion de datos que no tengo Facturas antiguas en el OpenErp.Usado solo para registar la retencion temporalemente. 
                                  ('valid', 'Validada'),
                                  ('cancel', 'Anulada'), #Este estado cuando dejen Anulada la retencion
                                  ], "Estado", select=True, readonly=True),
        'number':fields.char('No.Comprobante Retencion', size=64, readonly=False, states={'valid':[('readonly', True)],
                                                                                    'cancel':[('readonly', True)]}),
        'ruc':fields.char('R.U.C', size=15, help='Ruc del emisor del comprobante de retencion', readonly=False, states={'valid':[('readonly', True)],
                                                                                                                        'cancel':[('readonly', True)]}),
        'ath_sri':fields.char('Aut. SRI.', size=64, readonly=False, states={'valid':[('readonly', True)],
                                                                               'cancel':[('readonly', True)]}),
        'broadcast_date':fields.date('Fecha Emision', readonly=False, states={'valid':[('readonly', True)],
                                                                              'cancel':[('readonly', True)]}, help="El sistema toma esta fecha para registrar el asiento en el periodo que corresponde esta fecha. Ejemplo: 2011-07-01-->Periodo Julio"),
        'social_reason': fields.char('Sr(es).', size=100, readonly=False, states={'valid': [('readonly', True)]}),
        'ruc_ci': fields.char('R.U.C/C.I.', size=15, help='Numero de RUC o CI del beneficiario', readonly=False, states={'valid':[('readonly', True)],
                                                                                                                         'cancel':[('readonly', True)]}),
        'address': fields.char('Direccion', size=150, readonly=False, states={'valid':[('readonly', True)],
                                                                              'cancel':[('readonly', True)]}),
        'type_voucher_purchase':fields.selection((('invoice', 'Factura'),
                                                  ('purchase_liq', 'Liquidación de Compra'),
                                                  ('sales_note', 'Nota de Venta')),
                                                 'Tipo de comprobante de Venta', readonly=False, states={'valid':[('readonly', True)],
                                                                              'cancel':[('readonly', True)]}),
        'num_voucher_purchase':fields.char('Nro.Comprobante de Venta', size=60, readonly=False, states={'valid':[('readonly', True)],
                                                                              'cancel':[('readonly', True)]}),
        'invoice_ids':fields.one2many('account.invoice', 'ret_voucher_id', 'Factura', readonly=False, states={'valid':[('readonly', True)],
                                                                              'cancel':[('readonly', True)]}),
        'ret_voucher_line_ids':fields.one2many('account.invoice.retention.voucher.line', 'ret_voucher_id', 'Detalle', readonly=False, states={'valid':[('readonly', True)],
                                                                                                                                              'cancel':[('readonly', True)]}),
        'move_id':fields.many2one('account.move', 'Asiento',select=True),
        'total':fields.float('Total', digits=(12, 2)),
        'partner':fields.char('Cliente', size=60),
        'num_daily_voucher':fields.char('Nro.Comprobante Diario', size=60),
        #'preimpreso':fields.function(_get_invoice_number, string='#Preimpreso', type='char', size=20, method=True, store=False),
        'numero':fields.char('#Preimpreso', size=60, help='Número Preimpreso de la Factura'),
        'partner_id':fields.many2one('res.partner', 'Empresa'),
        'nro_retencion':fields.char('Nro.Retencion', size=60, help='Número de la Retencion'),
        'line_id':fields.many2one('account.move.line', 'Saldo Inicial', domain=[('journal_id', '=', 19),
                                                                                ('reconcile_id', '=', False),
                                                                                ('account_id.reconcile', '=', True),
                                                                                ('account_id.type', 'in', ['receivable']),
                                                                                ('state', '=', 'valid'),
                                                                                ('debit', '>', 0.0)]),
        'amount_reconcile':fields.float('Saldo Inicial', digits=(12, 2)),
        'ret_ir': fields.function(_get_amounts, method=True, string='Valor Ret. Renta', type='float', multi='amounts',
                                    store={_name: (lambda self, cr, uid, ids, *a: ids, None, 10),
                                           'account.invoice.retention.voucher.line': (change_lines, ['tax_base', 'tax_id'], 10),
                                           'account.tax': (change_tax, ['amount', 'tax_group'], 10)}),
        'ret_vat': fields.function(_get_amounts, method=True, string='Valor Ret. Iva', type='float', multi='amounts',
                                   store={_name: (lambda self, cr, uid, ids, *a: ids, None, 10),
                                          'account.invoice.retention.voucher.line': (change_lines, ['tax_base', 'tax_id'], 10),
                                          'account.tax': (change_tax, ['amount', 'tax_group'], 10)})
    }
    _defaults = {
              'broadcast_date':lambda * a: time.strftime("%Y-%m-%d"),
              'state':lambda * a:"new", #State temporal por migracion de Datos.
    }
account_invoice_retention_voucher()


class account_invoice_retention_voucher_line(osv.osv):
    _name = "account.invoice.retention.voucher.line"
    _description = 'Lines of the voucher retention'   
    
    def _compute_per_tax(self, cr, uid, ids, field_name, args, context):
         res = dict.fromkeys(ids, 0.0)
         for item in self.browse(cr, uid, ids):
             if item.tax_id.amount:
                 ##print 'item.tax_id.amount: ', item.tax_id.amount
                 res[item.id] = abs((item.tax_id.amount) * 100)
         return res
    
    def _compute_amount(self, cr, uid, ids, field_name, args, context):
         res = dict.fromkeys(ids, 0.0)
         for item in self.browse(cr, uid, ids):
             if item.tax_base and item.perc_tax:
                 res[item.id] = round((float(item.tax_base * item.perc_tax) / 100), 2)
         return res
    
    
    _columns = {
        'name' : fields.char('Descripcion', size=60),
        'ret_voucher_id':fields.many2one('account.invoice.retention.voucher', 'Comprobante de Retencion'),
        'fiscal_year_id':fields.many2one('account.fiscalyear', 'Ejercicio Fiscal'),
        'tax_base': fields.float('Base Imponible', digits=(12, 2)),
        'tax_id':fields.many2one('account.tax', 'Impuesto'),
        'perc_tax': fields.function(_compute_per_tax, string='% de retención', digits=(12, 2), method=True, type='float'),
        'ret_amount':fields.function(_compute_amount, string='Valor Retenido', digits=(12, 2), method=True, type='float'),
    }
account_invoice_retention_voucher_line()
