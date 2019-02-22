# -*- coding: utf-8 -*-
###################################################
#
#    Account Invoice Retention Module
#    Copyright (C) 2012 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
#    $autor: Dairon Medina Caro <dairon.medina@gmail.com>
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
###################################################
import time
import logging
from openerp import api
from openerp.osv import fields, osv
from openerp.tools.translate import _
from dateutil import relativedelta
import datetime
import calendar

_logger = logging.getLogger(__name__)

class account_code(osv.osv):
    """
    A code for the tax object.
    This code is used for some tax declarations.
    """
    _name = 'account.code'
    _description = 'Account Code'
    _rec_name = 'code'
    _total = 0
    _dict_valores = []
    _columns = {
        'name': fields.char('Account Case Name', size=64, required=True),
        'code': fields.char('Case Code', size=64),
        'info': fields.text('Description'),
        'parent_id': fields.many2one('account.code', 'Parent Code', select=True),
        'child_ids': fields.one2many('account.code', 'parent_id', 'Child Codes'),
        'line_ids': fields.one2many('account.move.line', 'tax_code_id', 'Lines'),
        'account_id': fields.many2one('account.account', 'Account', required=False),
    }
    
    def _check_recursion(self, cr, uid, ids):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from account_code where id in (' + ','.join(map(str, ids)) + ')')
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True

    _order = 'code,name'
account_code()


class account_document_anexo(osv.osv):
    _name = 'account.document.anexo'
    _description = 'Account Document Anexo'
    _columns = {
        'name':fields.char('Documento', size=64, required=True),
        'description':fields.char('Descripcion', size=64, required=True),
        'type_invoice':fields.char('Tipo Factura', size=64, required=True),
        'type':fields.char('Tipo', size=64, required=True),
        'document_anexo_ids':fields.one2many('account.document.anexo.line', 'document_anexo_id', 'Documentos'),
    }
account_document_anexo()

class account_document_anexo_line(osv.osv):
    _name = 'account.document.anexo.line'
    _description = 'Account Document Anexo por Linea'
    _columns = {
        'name': fields.char('Descripcion', size=64, required=True),
        'sequence': fields.integer('Secuencia', size=64),
        'group_transaction':fields.char('Group', size=64),
        'type':fields.selection([('compras', 'Compras'), ('ventas', 'Ventas')], 'Grupo', required=True),
        'code':fields.char('Codigo', size=64),
        'document_anexo_id':fields.many2one('account.document.anexo', 'Documento', required=True),
    }
    _order = 'sequence' 
account_document_anexo_line()

class account_order_billing(osv.osv):
    _name = 'account.order.billing'
    _description = 'Ordenes de Facturacion Generadas'
    _order='number_invoice DESC'
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['origin', 'name','num_invoice'], context)
        res = []
        for record in reads:
            name = record['name']
            if name == '/':
                if record['num_invoice']:
                    name = record['num_invoice']
                elif record['num_invoice']:
                    name = record['num_invoice']
                else:
                    name = record['name']
            else:
                name = record['name']
            
            if not name:
                name = '/'
            res.append((record['id'], name))
        return res
    
    def _get_invoice (self, cr, uid, ids, field_name, args, context):
        res ={}
        for item in self.browse(cr, uid, ids):
            if item.invoice_id:
                res[item.id] = item.invoice_id.factura
                sql ='update account_order_billing set number_invoice = '+str(item.invoice_id.factura)+' where id='+str(item.id)
                cr.execute(sql)
            else:
                 res[item.id] = ''
        return res
    
    def write (self, cr, uid, ids, vals, context=None):
        #===============================================================================
        # Se vuele a borrador para volver a generar los diferidos
        #===============================================================================
        l = 0
        al = []
        if vals.has_key('deferred_ids'):
            if vals['deferred_ids']:
                l = len(vals['deferred_ids'])
                for line in vals['deferred_ids']:
                    if not line[2]:
                        al.append(line)
                if l == len(al):
                    vals['state']='draft'
        ##print "vals2", vals
        order = super(account_order_billing,self).write(cr, uid, ids, vals, context=context)
        return order
    
    def unlink(self, cr, uid, ids, context=None):
        account_move_obj = self.pool.get('account.move')
        unlink_ids = []
        for t in self.browse(cr, uid, ids):
            unlink_ids.append(t.id)
            for item in t.deferred_ids:
                if item.state =='posted':
                    account_move_obj.button_cancel(cr, uid, [item.move_id.id])
                    account_move_obj.unlink(cr, uid, [item.move_id.id])
        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        
        return True
    
    #Funcion Para Diferidos de Migracion  
    def _get_date_finish(self, cr, uid, ids, field_name, args, context):
        res = {}
        for item in self.browse(cr, uid, ids):
#            #print "item_numero", item.time_left
            if item.time_left > 0 and item.type=='migration':
                if item.lease_start_date:
#                    #print "time_left", item.time_left
                    begin_date = datetime.strptime(item.lease_start_date, '%Y-%m-%d')
                    if item.time_left == 1:
                        date_f = self._date_format(item.lease_start_date)
                        dp = calendar.monthrange(date_f.year,date_f.month)
                        finish_date =datetime.date(date_f.year,date_f.month, dp[1]).strftime('%Y-%m-%d') 
                    else:
                        finish_date = (begin_date + relativedelta(months=+(item.time_left-1))).strftime('%Y-%m-%d')
#                    #print "finish_date", finish_date
                    res[item.id] = finish_date
            else:
                res[item.id]=None
        return res
    
    def _get_type(self, cr, uid, context=None):
        ##print "_get_type", context
        if context is None:
            context = {}
        type = context.get('type', 'sale')
        return type
    
    _columns = { 
        'name':fields.char('Orden de Venta', size=500, required=True,
                           states={'generate': [('readonly', True)],'posted': [('readonly', True)]}),
        'num_invoice':fields.function(_get_invoice, string='Factura', type='char', method=True, store=False, size=20),
        'number_invoice':fields.char('Factura', size=500),
        'date_order':fields.date('Fecha Orden de Venta', required=True,
                                 states={'generate': [('readonly', True)],'posted': [('readonly', True)]}),
        'sin_impuesto':fields.float('Monto a Diferir', digits=(16, 2), required=True, states={'generate': [('readonly', True)]}),
        'deferred_ids':fields.one2many('account.deferred', 'order_billing_id', 'Diferidos'),
        'sale_order_id':fields.many2one('sale.order','Sale', required=False, ),
        'purchase_order_id':fields.many2one('purchase.order','Purchase Order', required=False,),
        'lease_start_date':fields.date('Fecha Inicio Diferido', required=False, help="Fecha de la emision de la Factura",
                                       states={'generate': [('readonly', True)],'posted': [('readonly', True)]}),
        'lease_end_date':fields.date('Fecha Fin Diferido', required=False,
                                     states={'generate': [('readonly', True)],'posted': [('readonly', True)]},
                                     help='Fecha Fin del Diferido: Ventas: Fecha fin del contrato. Compras: Fecha ingresada por el usuario desde la factura de compra.'),
        'number_contract':fields.char('Numero Contrato', size=10, required=False, help='Nro. de Contrato'),
        'value_contract':fields.float('Valor Contrato', digits=(12, 2), required=False),
        'type':fields.selection([('sale','Ingresos Diferidos'),
                                ('purchase','Gastos Diferidos'),
                                ('migration','Otros Gastos Diferidos'),
                                ],'Tipo', help='Ingresos Diferidos: Provienen de las facturas de ventas con productos de ventas configurados como diferidos.\n'\
                                               'Gastos Diferidos: Provienen de las Facturas de compras con productos de compra configurados como diferidos y tambien, '\
                                               'de las facturas de compras señaladas como gasto diferido', readonly=True),
        'state':fields.selection([('draft', 'Borrador'), #Venta
                                  ('generate', 'Generado'),
                                  ('posted', 'Contabilizado'),],'Estado', select=True, readonly=True),
        'partner_id':fields.many2one('res.partner', 'Empresa',
                                     states={'generate': [('readonly', True)],'posted': [('readonly', True)]}),
        'period_id':fields.many2one('account.period', 'Periodo a Diferir', help='Seleccione un periodo para contabilizar.'),
        'origin':fields.char('Origen', size=50, required=False, states={'generate': [('readonly', True)]}),
        'date_create':fields.date('Fecha Creacion'),#Diferido migracion *
        'amount_total':fields.float('Monto Total'),#Monto total del diferido *
        'amount_to_defered':fields.float('Monto #'), #monto por diferir*
        'time_left':fields.integer('Tiempo Restante', states={'generate': [('readonly', True)]}),#Por Diferir
        'date_finish':fields.function(_get_date_finish,string='Fecha fin Contrato', type='date', method=True, store=True),
        'product_id':fields.many2one('product.product', 'Producto', domain=[('deferred_ok','=',True)], states={'generate': [('readonly', True)]}),
        'invoice_id':fields.many2one('account.invoice','Factura'),
        'invoice_ids':fields.one2many('account.invoice','deferred_id','Facturas'),#Relacion que muestra 
        'invoice_line':fields.many2one('account.invoice.line','Linea Factura'),#Diferido por Linea de Factura de Compra
        'period_deferred':fields.many2one('account.period', 'Periodo'),
        'invoice_type':fields.char('Tipo Factura', size=100)
        #Este campo se usa cuando provienen de asientos por apuntes la tabla Gastos de Permiso Municipal
        #'move_id':many2one('account.move','Movimiento'),
        #'account_deferred_id':many2one('account.account', 'Cuenta Diferida'),
        #'account_expense_id':many2one('account.account', 'Cuenta de Gasto')
    }
    
    _defaults = {
        'state': lambda *a: 'draft',
        'type': _get_type,
    }
    
    def action_posted(self, cr, uid, ids, context):
        #print "contabilizar_diferidos", ids
        #print "context", context
        obj_product = self.pool.get('product.template')
        obj_product_product = self.pool.get('product.product')
        obj_account_deferred = self.pool.get('account.deferred')
        for ob in self.browse(cr, uid, ids):
            #Obtener el periodo
            if context.get('period_id', False):#Desde Wizard
                period_id = context.get('period_id', False)
                date = self.pool.get('account.period').browse(cr, uid,period_id).date_start
            else:    
                period_id = ob.period_id.id
                date = ob.period_id.date_start
                if not period_id:
                    raise osv.except_osv(_('Aviso'), _('Escriba el periodo del que desea generar el diferido.'))
            #Obtener el diario
            if ob.type in ('sale'):
                diario_id = self.pool.get('account.journal').search(cr, uid, [('type','=','sale')])
                if not diario_id:
                    raise osv.except_osv(_('Aviso'), _('No existe el diario de ventas creelo por favor!.'))
            elif ob.type in ('purchase', 'migration'):
                diario_id = self.pool.get('account.journal').search(cr, uid, [('type','=','purchase')])
                if not diario_id:
                    raise osv.except_osv(_('Aviso'), _('No existe el diario de compras creelo por favor!.'))
            #buscar las lineas de los diferidos que coinciden con el periodo.
            defered_ids = obj_account_deferred.search(cr, uid, [('period_id', '=', period_id), ('order_billing_id', '=', ob.id)])
            
            if defered_ids:
                for line in obj_account_deferred.browse(cr, uid, defered_ids):
                    mov_lines = []
                    if line.state == 'posted':
                        continue
                        raise osv.except_osv(_('Alerta'), _('El periodo que selecciono ya esta contabilizado.'))
                    if line.product_id:
                        product_product = obj_product_product.browse(cr, uid,line.product_id.id)
                        
                        producto_template = obj_product.read(cr, uid, [product_product.product_tmpl_id.id],
                                                             ['name','property_account_deferred_sale','property_account_income',
                                                              'property_account_expense','property_account_deferred_purchase'])[0]
                        #Obtener los datos del producto
                        name_producto = producto_template['name']
                    #Si es compra
                    if line.type_document in ('PO','MI'):
                        #=======================================================
                        # Cuenta 5 al debe de Diferido contra cuenta 1 al haber cuenta del producto
                        #=======================================================
                        d_amount_line_debit = line.amount
                        d_amount_line_credit = 0.00
                        h_amount_line_debit = 0.00
                        h_amount_line_credit = line.amount
                        if line.account_deferred:
                            diferido = (line.account_deferred.id,line.account_deferred.name)#Cuenta 1 de Gastos Diferidos
                            income = producto_template['property_account_expense']#Cuenta 5 
                        else:
                            income = producto_template['property_account_deferred_purchase']#Cuenta 5
                            diferido = producto_template['property_account_expense']#Cuenta 1
                        
                    else:
                        #=========================================================================
                        # Cuenta 2 de ingreso al debe contra cuenta 4 del diferido al haber para los diferidos de Ventas
                        #=========================================================================
                        diferido = producto_template['property_account_deferred_sale']#Cuenta 4
                        income = producto_template['property_account_income']#Cuenta 2
                        
                        d_amount_line_debit = line.amount
                        d_amount_line_credit =0.00 
                        h_amount_line_debit = 0.00
                        h_amount_line_credit = line['amount']
                    
                    if not diferido:
                        raise osv.except_osv(_('Error Configuracion'), _('El producto ' + name_producto + ' no tiene configurado la cuenta de diferidos '))
                       
                    if ob.type in ("sale"):
                        ref = "Ingreso Diferido de "+str(self._date_format(date).strftime('%B-%Y')).upper()+' '+name_producto
                        ref_line_debe = "Ingreso Diferido de " +str(self._date_format(date).strftime('%B %Y')).upper()+ ' '+ income[1][10:]
                        ref_line_haber = "Ingreso Diferido de "+str(self._date_format(date).strftime('%B %Y')).upper()+' ' + diferido[1][10:]
                    elif ob.type in ('purchase', 'migration'):
                        ref = "Reg. Gasto o Costo Diferidos "+str(self._date_format(date).strftime('%B-%Y')).upper()+ ' '  +name_producto
                        ref_line_debe = "Reg.Gasto o Costo Diferidos " +str(self._date_format(date).strftime('%B %Y')).upper()+ ' '+ income[1][10:]
                        ref_line_haber = "Reg.Gasto o Costo Diferidos "+str(self._date_format(date).strftime('%B %Y')).upper()+' ' + diferido[1][10:]
                    
                    vals = {'ref': ref, 'journal_id': diario_id[0], 'date': str(datetime.date.today()), 'period_id': period_id}
                    #linea del movimiento del debe
                    vals_debe = {'ref':name_producto,
                                 'name': ref_line_debe,
                                 'account_id': income[0],
                                 'period_id': period_id,
                                 'debit':d_amount_line_debit,
                                 'credit': d_amount_line_credit,
                                 'date': str(datetime.date.today()),
                                 'partner_id':ob.partner_id.id,
                                 'journal_id':diario_id[0]
                                 }
                    mov_line_debe = (0, 0, vals_debe)
                    mov_lines.append(mov_line_debe)
                    #linea del movimiento del haber
                    vals_haber = {'ref':name_producto, 
                                  'name': ref_line_haber,
                                  'account_id': diferido[0],
                                  'period_id': period_id,
                                  'debit': h_amount_line_debit,
                                  'credit': h_amount_line_credit,
                                  'date': str(datetime.date.today()),
                                  'partner_id':ob.partner_id.id,
                                  'journal_id':diario_id[0]
                                  }
                    ##print ' line haber ', vals_haber
                    mov_line_haber = (0, 0, vals_haber)
                    mov_lines.append(mov_line_haber)
                    vals['line_id'] = mov_lines
                    account_move_id = self.pool.get('account.move').create(cr, uid, vals)
                    self.pool.get('account.move').post(cr, uid, [account_move_id])
                    obj_account_deferred.write(cr,uid,line.id,{'state':'posted', 'move_id': account_move_id})
            b = False
            for line in ob.deferred_ids:
                if line.state =='draft':
                    b = True
            if not b:
                self.write(cr, uid, [ob.id], {'state':'posted'})
    
    def action_posted_refund(self, cr, uid, ids, context):
        if not context:
            context = {}
        deferred_obj = self.pool.get('account.deferred')
        obj_product_product = self.pool.get('product.product')
        obj_product = self.pool.get('product.template')
        
        for item in self.browse(cr, uid, ids,context):
            if context.get('period_id', False):#Desde Wizard
                period_id = context.get('period_id', False)
                date = self.pool.get('account.period').browse(cr, uid,period_id).date_start
            else:    
                period_id = item.period_id.id
                date = item.period_id.date_start
                if not period_id:
                    raise osv.except_osv(_('Aviso'), _('Escriba el periodo del que desea generar el diferido.'))
            
            if item.type in ('sale', 'migration'):
                diario_id = self.pool.get('account.journal').search(cr, uid, [('type','=','sale')])
                if not diario_id:
                    raise osv.except_osv(_('Aviso'), _('No existe el diario de ventas creelo por favor!.'))
            elif item.type == 'purchase':
                diario_id = self.pool.get('account.journal').search(cr, uid, [('type','=','purchase')])
                if not diario_id:
                    raise osv.except_osv(_('Aviso'), _('No existe el diario de compras creelo por favor!.'))
                
            if item.invoice_type in ('out_refund','in_refund'):
                
                defered_ids = deferred_obj.search(cr, uid, [('period_id', '=', period_id), ('order_billing_id', '=', item.id)])
                for line in deferred_obj.browse(cr, uid, defered_ids):
                    mov_lines = []
                    if line.product_id:
                        product_product = obj_product_product.browse(cr, uid,line.product_id.id)
                        ##print 'product_product', product_product
                        producto_template = obj_product.read(cr, uid, [product_product.product_tmpl_id.id],
                                                             ['name','property_account_deferred_sale','property_account_income',
                                                              'property_account_expense','property_account_deferred_purchase'])[0]
                        name_producto = producto_template['name']
                    if line.type_document == 'PO':
                        #=======================================================
                        # Cuenta 5 al debe de Diferido contra cuenta 1 al haber cuenta del producto
                        #=======================================================
                        d_amount_line_debit = line.amount
                        d_amount_line_credit = 0.00
                        h_amount_line_debit = 0.00
                        h_amount_line_credit = line.amount
                        if line.account_deferred:
                            diferido = (line.account_deferred.id,line.account_deferred.name)#Cuenta 1 de Gastos Diferidos
                            income = producto_template['property_account_expense']#Cuenta 5 
                        else:
                            income = producto_template['property_account_deferred_purchase']#Cuenta 5
                            diferido = producto_template['property_account_expense']#Cuenta 1
                        
                    else:
                        #=========================================================================
                        # Cuenta 2 de ingreso al debe contra cuenta 4 del diferido al haber para los diferidos de Ventas
                        #=========================================================================
                        
                        if not item.partner_id:
                            raise osv.except_osv(_('Aviso'), _('Seleccione el cliente antes de continuar!.'))
                        if not item.partner_id.property_account_payable:
                            raise osv.except_osv(_('Aviso'), _('Seleccione la cuenta en la ficha del cliente antes de continuar!.'))
                        
                        diferido = item.partner_id.property_account_receivable.id#Cuenta 1 Clientes Locales
                        income = producto_template['property_account_income']#Cuenta 2
                        
                        d_amount_line_debit = line.amount
                        d_amount_line_credit =0.00 
                        h_amount_line_debit = 0.00
                        h_amount_line_credit = line['amount']
                    if item.type =='sale':
                        ref = "Reg. Ingreso NC."+str(self._date_format(date).strftime('%B-%Y')).upper()+' '+line.nombre_producto
                        ref_line = 'Nota de Credito, #Factura:'+str(item.num_invoice)
                    if item.type =='purchase':
                        ref = "Reg. Costo o Gasto NC."+str(self._date_format(date).strftime('%B-%Y')).upper()+' '+line.nombre_producto
                    vals = {'ref': ref, 'journal_id': diario_id[0], 'date': str(datetime.date.today()), 'period_id': period_id}
                    
                    if item.invoice_id.tax_line:#Linea de Impuestos en las notas de Credito
                         for tax in item.invoice_id.tax_line:
                             h_amount_line_credit += tax.tax_amount
                             vals_debe = {'ref':line.nombre_producto,
                                          'name': ref_line,
                                         'account_id': tax.account_id.id,
                                         'period_id': period_id,
                                         'debit':tax.tax_amount,
                                         'credit': 0.00,
                                         'date': str(datetime.date.today()),
                                         'partner_id':item.partner_id.id,
                                         'journal_id':diario_id[0]
                                     }
                             mov_line_haber = (0, 0, vals_debe)
                             mov_lines.append(mov_line_haber)
                    
                    vals_debe = {'ref':line.nombre_producto,
                                 'name': ref_line,
                                 'account_id': income[0],
                                 'period_id': period_id,
                                 'debit':d_amount_line_debit,
                                 'credit': d_amount_line_credit,
                                 'date': str(datetime.date.today()),
                                 'partner_id':item.partner_id.id,
                                 'journal_id':diario_id[0]
                                 }
                    mov_line_debe = (0, 0, vals_debe)
                    mov_lines.append(mov_line_debe)
                    
                    vals_haber = {'ref':line.nombre_producto, 
                                  'name': ref_line,
                                  'account_id': diferido,
                                  'period_id': period_id,
                                  'debit': h_amount_line_debit,
                                  'credit': h_amount_line_credit,
                                  'date': str(datetime.date.today()),
                                  'partner_id':item.partner_id.id,
                                  'journal_id':diario_id[0]
                                  }
                    ##print ' line haber ', vals_haber
                    mov_line_haber = (0, 0, vals_haber)
                    mov_lines.append(mov_line_haber)
                    ##print 'mov_lines', mov_lines
                    vals['line_id'] = mov_lines
                    account_move_id = self.pool.get('account.move').create(cr, uid, vals)
                    self.pool.get('account.move').post(cr, uid, [account_move_id])
                    deferred_obj.write(cr,uid,line.id,{'state':'posted', 'move_id': account_move_id})
            b = False
            for line in item.deferred_ids:
                if line.state =='draft':
                    b = True
            if not b:
                self.write(cr, uid, [item.id], {'state':'posted'})
        return True
            
    def action_cancel(self, cr, uid, ids, context):
        #print 'action_cancel', context
        account_move_obj = self.pool.get('account.move')
        deferred = self.pool.get('account.deferred')
        for item in self.browse(cr, uid, ids, context):
            if context.get('period_id', False):#Desde Wizard
                period_id = context.get('period_id', False)
            else:    
                period_id = item.period_id.id
                if not period_id:
                    raise osv.except_osv(_('Aviso'), _('Escriba el periodo del que desea cancelar el asiento.!'))
            defered_ids = deferred.search(cr, uid, [('period_id', '=', period_id),
                                                    ('order_billing_id', '=', item.id),
                                                    ('state','=','posted')
                                                    ])
            if  defered_ids:
                for defered_id in defered_ids:
                    line = deferred.read(cr, uid, defered_id)
                    if line['move_id']:
                        account_move_obj.button_cancel(cr, uid, [line['move_id'][0]])
                        account_move_obj.unlink(cr, uid, [line['move_id'][0]])
                        deferred.write(cr, uid, line['id'],{'state':'draft'})
        return True
    
    def action_deferred(self, cr, uid, ids,context):
        #print "action_deferred", context
        amount_sale = 0.0
        amount_purchase = 0.0
        deferred = self.pool.get('account.deferred')
        sale_order = self.pool.get('sale.order')
        account_invoice = self.pool.get('account.invoice')
        for of in self.browse(cr, uid, ids, context):#Account Order Billing
            if of.type=="sale":
                diferred_id = False
                if of.sale_order_id:
                   s_o_d = sale_order.browse(cr, uid, of.sale_order_id.id)
                   if s_o_d.state in ('draft', 'cancel'):
                       raise osv.except_osv(_('Aviso'), _('La Orden de Venta .'+of.name+' no debe estar en estado: Cancelado o Presupuesto, para continuar!'))
                if not of.invoice_id:
                    #print 'no tiene factura'
                    continue
                #Diferidos por linea de Facturas si tiene productos diferidos
                
                for il in of.invoice_id.invoice_line:  
                    if not il.product_id.deferred_ok:
                        continue
                    ##print "of.lease_start_date", of.lease_start_date
                    fic = of.lease_start_date
                    if not of.lease_start_date and not(context.get('invoice', False)):
                        raise osv.except_osv(_('Error Configuracion'), _('Escriba la fecha de inicio del Diferido de la orden de venta: '+str(of.name)))
                    if not of.lease_start_date and context.get('invoice', False):
                        continue
                        
                    campos = map(lambda x: int(x), fic.split('-'))
                    date_fic = datetime.date(campos[0], campos[1], campos[2])
                    
                    ffc = of.lease_end_date
                    if not of.lease_end_date and not(context.get('invoice', False)):
                        raise osv.except_osv(_('Error Configuracion'), _('Escriba la fecha de fin del contrato de la orden de venta: '+str(of.name)))
                    if not of.lease_end_date and context.get('invoice', False):
                        continue
                    
                    if of.lease_start_date > of.lease_end_date:
                        raise osv.except_osv(_('Aviso'), _('La fecha fin del diferido debe ser menor que la fecha inicio del diferido')) 
                    
                    campos = map(lambda x: int(x), ffc.split('-'))
                    date_ffc = datetime.date(campos[0], campos[1], campos[2])
                    
                    diff = (date_ffc - date_fic).days
                    diff = diff + 1
                    
                    abd = float(il.price_subtotal / diff)
                    #amount_sale = il.price_subtotal
                    periodos = self._get_period(date_fic, date_ffc)
                    i = 1
                    for periodo in periodos:
                        #amount_sale -= periodo['number_days'] * abd
                        periodo['amount'] = periodo['number_days'] * abd
                        periodo['name'] = 'Periodo ' + str(i)
                        periodo['order_billing_id'] = of.id
                        periodo['period_id'] = self._get_period_account(periodo['fecha_inicio'], cr)
                        periodo['invoice_line'] = il.id
                        periodo['type_document'] = 'SO'
                        periodo['invoice_id'] = of.invoice_id.id 
                        periodo['product_id'] = il.product_id.id
                        periodo['monto_producto'] = il.price_subtotal
                        periodo['nombre_producto'] = il.product_id.name
                        periodo['origin'] = of.sale_order_id and of.sale_order_id.name or of.invoice_id.origin or '/'
                        periodo['invoice_type'] = of.invoice_type
                        diferred_id = deferred.create(cr, uid, periodo)
                        i = i + 1
                if diferred_id:
                    self.write(cr, uid, ids, {'state':'generate'})
                
                            
            elif of.type =='purchase':
                """Gasto"""
                deferred_id = False
                "A partir de la Linea de la factura se genera el diferido de compra si es diferido en wizard ya esta validada esta informacion"
                
                if not of.sin_impuesto:
                    raise osv.except_osv(_('Error Configuracion'), _('Escriba el valor a diferir.'))
                
                fic = of.lease_start_date
                if not of.lease_start_date and not(context.get('invoice', False)):#Cuando Genere el Diferido Directo de la parte de Diferidos
                    raise osv.except_osv(_('Error Configuracion'),
                                         _('Escriba la fecha de inicio del Diferido de la orden de compra: '+str(of.name)))
                if not of.lease_start_date and context.get('invoice', False):#Si es a partir de la factura solo crea la cabecera no la tabla del diferido
                    continue
            
                campos = map(lambda x: int(x), fic.split('-'))
                date_fic = datetime.date(campos[0], campos[1], campos[2])
     
                ffc = of.lease_end_date
                if not of.lease_end_date and not(context.get('invoice', False)):
                    raise osv.except_osv(_('Error Configuracion'),
                                         _('Escriba la fecha de fin del diferido orden de venta: '+str(of.name)))
                if not of.lease_end_date and context.get('invoice', False):
                    continue
                
                if of.lease_start_date > of.lease_end_date:
                        raise osv.except_osv(_('Aviso'), _('La fecha fin del diferido debe ser menor que la fecha inicio del diferido'))
                     
                campos = map(lambda x: int(x), ffc.split('-'))
                date_ffc = datetime.date(campos[0], campos[1], campos[2])
                diff = (date_ffc - date_fic).days
                diff = diff + 1
                abd = float(of.sin_impuesto / diff)
                periodos = self._get_period(date_fic, date_ffc)
                i = 1
                amount = 0.00
                product_name = ''
                line_id = False
                product_id = False
                
                if not of.invoice_id:
                    continue
                
                if of.invoice_id:#Siempre viene la factura 
                    invoice_id = of.invoice_id
                    if invoice_id.from_invoice:#Solo si es diferido a partir de la factura
                        amount = invoice_id.amount_untaxed
                        for il in invoice_id.invoice_line:#No se que producto escoger si son muchos items en la factura
                            product_id = il.product_id.id
                            product_name = il.product_id.name
                        #print "longitud", len(invoice_id.invoice_line)
                        if not invoice_id.account_deferred:
                            raise osv.except_osv(_('Aviso'), _('Ingrese la cuenta de diferido en la factura:'+str(invoice_id.number_inv_supplier)))
                    else:
                        if of.invoice_line:
                            line_id = of.invoice_line.id
                            amount = of.invoice_line.price_subtotal
                            product_name = of.invoice_line.product_id.name
                            product_id = of.invoice_line.product_id.id
                     
                for periodo in periodos:
                    #amount_purchase -= periodo['number_days'] * abd
                    periodo['amount'] = periodo['number_days'] * abd
                    periodo['name'] = 'Periodo ' + str(i)
                    periodo['order_billing_id'] = of.id
                    periodo['period_id'] = self._get_period_account(periodo['fecha_inicio'], cr)
                    periodo['invoice_line'] = line_id or False
                    periodo['product_id'] = product_id
                    periodo['account_deferred'] = invoice_id.from_invoice and invoice_id.account_deferred and \
                                                  invoice_id.account_deferred.id or False
                    periodo['type_document'] = 'PO'
                    periodo['invoice_id'] = invoice_id.id or False
                    periodo['monto_producto'] = amount
                    periodo['nombre_producto'] = product_name
                    periodo['origin'] = of.purchase_order_id and of.purchase_order_id.name or of.invoice_id.origin or '/'
                    periodo['invoice_type'] = of.invoice_type
                    deferred_id = deferred.create(cr, uid, periodo)
                    i = i + 1
                if deferred_id:
                    self.write(cr, uid, ids, {'state':'generate'})
                
            #Alterno Temporal Generacion de Diferidos
            elif of.type =='migration':
                if not of.time_left or of.time_left < 0 :
                    raise osv.except_osv(_('Error Configuracion'), _('Escriba el Tiempo Restante debe ser > 0 para continuar'))
                    
                if not of.sin_impuesto:
                    raise osv.except_osv(_('Error Configuracion'), _('Escriba el valor a diferir.'))
                
                fic = of.lease_start_date
                if not of.lease_start_date:
                    raise osv.except_osv(_('Error Configuracion'), _('Escriba la fecha de inicio del contrato.'))
                
                date_start = self._date_format(fic)
     
                ffc = of.date_finish
                if not of.date_finish:
                    raise osv.except_osv(_('Error Configuracion'), _('Escriba la fecha de fin del contrato.')) 
                
                abd = float(of.sin_impuesto / of.time_left)
                amount_purchase = of.sin_impuesto
                i = 1
                n = of.time_left
                while n > 0:
                    amount_purchase -= abd
                    if of.time_left==1 or i==1:
                        date_start_period =  date_start.strftime('%Y-%m-%d')
                        dp = calendar.monthrange(date_start.year,date_start.month)
                        date_finish_period = datetime.date(date_start.year,date_start.month, dp[1]).strftime('%Y-%m-%d')
                        date_start = date_start_period
                    else:
                        date_start_period = self._get_last_day_month(date_start)
                        dp = calendar.monthrange(self._date_format(date_start_period).year,
                                                 self._date_format(date_start_period).month)
                        date_finish_period = datetime.date(self._date_format(date_start_period).year,
                                                          self._date_format(date_start_period).month, dp[1]).strftime('%Y-%m-%d')
                        date_start =  date_start_period
                    
                    deferred.create(cr, uid,{
                                             'amount': abd,
                                             'number_days':(self._date_format(date_finish_period)-self._date_format(date_start_period)).days,
                                             'name': 'Periodo ' + str(i),
                                             'order_billing_id':of.id,
                                             'period_id': self._get_period_account(date_start_period, cr),
                                             'type_document': 'MI',
                                             'fecha_inicio':date_start_period,
                                             'fecha_fin':date_finish_period,
                                             'monto_producto':amount_purchase,
                                             'product_id':of.product_id.id,
                                             'nombre_producto':of.product_id.name,
                                             })
                    i = i + 1
                    n-= 1
                self.write(cr, uid, ids, {'state':'generate'})  
                    
    def _get_period_account(self, fecha_inicio, cr):
        query = "select id from account_period where '" + fecha_inicio + "' between date_start and date_stop"
        cr.execute(query)
        consulta = cr.dictfetchall()
        if consulta:
            return consulta[0]['id']
        else:
            raise osv.except_osv(_('Aviso'), _('La fecha: ' + str(fecha_inicio) + ' no pertenece a ningun periodo creado.! '))
        
    def _get_period(self, fecha_inicio, fecha_fin):
        
        res = []
        puntero = fecha_inicio
        valor = (puntero - fecha_fin).days
        
        while  valor <= 0:
            numero_dias = 0
            data = calendar.monthrange(puntero.year, puntero.month) 
            ##print ' data ', data
            date_period = datetime.date(puntero.year, puntero.month, data[1])
            ##print ' date_period ', date_period
            periodo = {}
            ##print ' (date_period - fecha_fin).days ', (date_period - fecha_fin).days
            if (date_period - fecha_fin).days <= 0:
                numero_dias = (date_period - puntero).days
                if numero_dias < 0:
                    numero_dias = (-1) * numero_dias
                numero_dias = numero_dias + 1     
                periodo['number_days'] = numero_dias 
                periodo['fecha_inicio'] = puntero.strftime('%Y-%m-%d')
                periodo['fecha_fin'] = date_period.strftime('%Y-%m-%d')
            else:
                numero_dias = (puntero - fecha_fin).days
                if numero_dias < 0:
                    numero_dias = (-1) * numero_dias
                numero_dias = numero_dias + 1   
                
                periodo['number_days'] = numero_dias
                periodo['fecha_inicio'] = puntero.strftime('%Y-%m-%d')
                periodo['fecha_fin'] = fecha_fin.strftime('%Y-%m-%d') 
                     
            res.append(periodo)
            puntero = date_period + datetime.timedelta(days=1)
            valor = (puntero - fecha_fin).days

        return res
    
    def _date_format(self, date):
        if date:
            campos = date.split('-')
            date = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date
    
    def _get_last_day_month(self, date):
        current_date = self._date_format(date)
        carry, new_month=divmod(current_date.month-1+1, 12)
        new_month+=1
#        dp = calendar.monthrange(current_date.year,new_month)
        current_date=current_date.replace(year=current_date.year+carry, month=new_month)
        return current_date.strftime('%Y-%m-%d')

account_order_billing()

#=========================================================================================
# Tabla que guarda las lineas del detalle de diferido  de los facturas de compras y ventas 
#=========================================================================================
class account_deferred(osv.osv):
    _name = 'account.deferred'
    _description = 'Diferidos de Compras y Ventas'
    
    def unlink(self, cr, uid, ids, context=None):
        account_def = self.read(cr, uid, ids, ['state','name','order_billing_id'])
        unlink_ids = []
        for t in account_def:
            if t['state'] and (t['state'] not in ('posted')):
                unlink_ids.append(t['id'])
            else:
                raise osv.except_osv(_('Alerta!'), _('No puede eliminar el diferido del (%s) mientras este contabilizado !') % (t['name']))
        result = super(account_deferred, self).unlink(cr, uid, unlink_ids, context)
        return result
    
    _columns = {
        'name':fields.char('Periodo', size=16, required=True, states={'posted': [('readonly', True)]}),
        'fecha_inicio':fields.date('Fecha Inicio', states={'posted': [('readonly', True)]}),
        'fecha_fin':fields.date('Fecha Fin', states={'posted': [('readonly', True)]}),
        'amount':fields.float('Valor Diferido', digits=(16, 2), states={'posted': [('readonly', True)]}),
        'number_days':fields.integer('#Dias', states={'posted': [('readonly', True)]}),
        'order_billing_id':fields.many2one('account.order.billing', 'Order', states={'posted': [('readonly', True)]}, ondelete="cascade",),
        'period_id':fields.many2one('account.period', 'Periodo', states={'posted': [('readonly', True)]}),
        'invoice_line':fields.many2one('account.invoice.line','Linea Factura', states={'posted': [('readonly', True)]}),
        'invoice_id':fields.many2one('account.invoice', 'Factura', readonly=True),
        'type_document':fields.char('Tipo Documento', size=3, states={'posted': [('readonly', True)]}),
        'monto_producto':fields.float('Monto', states={'posted': [('readonly', True)]}),
        'nombre_producto':fields.char('Producto', size=128, states={'posted': [('readonly', True)]}),
        'product_id':fields.many2one('product.product','Producto', states={'posted': [('readonly', True)]}),
        'state':fields.selection([('draft', 'Borrador'), 
                                  ('posted', 'Contabilizado'),
                                  ('cancel', 'Cancelado'),
                                  ], 'Estado', readonly=True),
        'move_id':fields.many2one('account.move', 'Movimiento', readonly=True),
        'origin':fields.char('Origen', size=16, states={'posted': [('readonly', True)]}),
        #Cuenta de Diferido de la Factura
        'account_deferred':fields.many2one('account.account', 'Cuenta Diferido'),
        'invoice_type':fields.char('Tipo Factura', size=100)
    }
    _defaults = {
        'state': lambda *a: 'draft',
    }
    
account_deferred()

#Depositos en Cheques del Cliente
class account_bank_statement(osv.osv):
    _name = "account.bank.statement"
    _inherit = "account.bank.statement"
    
    _columns = {
                'bank_deposits': fields.one2many('account.deposit.bank.statement.line', 'bank_deposit', 'Cheques del cliente'),
                'bank_transfers_ids': fields.one2many('account.deposit.bank.statement.line', 'bank_transfer_id', 'Transferencias cliente'),
                }
account_bank_statement()

class account_deposit_bank_statement_line(osv.osv):
    _name = "account.deposit.bank.statement.line"
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['number'], context)
        res = []
        for record in reads:
            name = record['number']
            if not name:
                name = '/'
            res.append((record['id'], name))
        return res
    
    def create(self, cr, uid,vals, context={}):
        if 'number' in vals:
            vals['name'] = vals.get('number')
        return super(account_deposit_bank_statement_line, self).create(cr, uid, vals, context)
    
    def write(self, cr, uid,ids,vals, context={}):
        if 'number' in vals:
            vals['name'] = vals.get('number')
        return super(account_deposit_bank_statement_line, self).write(cr, uid, ids, vals, context)
 
    _columns = {
                'name':fields.char('Cheque/Transferencia', size=100),
                'bank_deposit':fields.many2one('account.bank.statement', 'Cheques del cliente', ondelete='cascade'),
                'bank_transfer_id':fields.many2one('account.bank.statement', 'Transferencias del cliente', ondelete='cascade'),
                'bank':fields.char('Banco', size=50),
                'account':fields.char('Nro. Cuenta', size=20),
                'number':fields.char('Nro. Cheque', size=30),
                'partner_id':fields.many2one('res.partner', 'Cliente'),
                'amount':fields.float('Valor', digits=(16, 2)),
                #Aumento Fecha de Coboro del Cheque
                'date_income':fields.date('Fecha de Cheque', help="Ingrese la fecha de ingreso del cheque")
                
                }
    
    _defaults = {  
        'date_income': lambda *a: time.strftime('%Y-%m-%d')
        }

account_deposit_bank_statement_line()


class product_product(osv.osv):
    _inherit = "product.product"
    
    _columns = {
                'deferred_ok': fields.boolean('Es Diferido', help="Determina si el producto es parte del valor para la generación de los diferidos."),
    }
    
product_product()

# Conciliaciones Bancarias
class account_conciliation(osv.osv):
    _name = "account.conciliation"
    _description = "Concilacion Bancaria"
    _order="journal_id,period_id"
    
    def _default_journal_id(self, cr, uid, context={}):
        if context.get('journal_id', False):
            return context['journal_id']
        return False


    def _get_before_period(self, cr, uid, period_id):
        account_period = self.pool.get('account.period')
        periodo = account_period.read(cr, uid, period_id, ['code','date_start','date_stop'])
        date = periodo.get('date_start')
        date = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=1)
        periodo_anterior = account_period.find(cr, uid, dt=date, context={})
        return periodo_anterior[0]

    def _get_period(self, cr, uid, context={}):
        periods = self.pool.get('account.period').find(cr, uid)
        if periods:
            return periods[0]
        else:
            return False
        
    def _get_default_periods(self, cr, uid, context={}):
        periods = self.pool.get('account.period').find(cr, uid)
        if periods:
            return periods[0]
        else:
            return False
    
    def _get_periods(self, cr, uid, date_start, fiscalyear):
        ##print "fiscal", fiscalyear
        res = []
        if date_start:
            period_obj = self.pool.get('account.period')
            campos = date_start.split('-')
            ##print "campos", campos
            if fiscalyear == 2:
                if int(campos[1])>7:
                    cont = 7
                    var = int(campos[1])-1
                    #Acumular saldos de todos los periodos a partir del mes de Julio
                    while cont <= var:  
                        date_start = datetime.date(int(campos[0]), var, int(campos[2]))
                        #print "date_start", date_start
                        period_ids = period_obj.search(cr, uid, [('date_start','=',date_start)])
                        res.append(period_ids[0])
                        var-= 1
                    return res
                elif int(campos[1])==7:
                    return res
                else:
                    return res
            else:
                #Acumular saldos de todos los periodos a partir del mes de Julio
                if int(campos[1])>1:
                    cont = 1
                    var = int(campos[1])-1
                    while cont <= var:
                        date_start = datetime.date(int(campos[0]), var, int(campos[2]))
                        period_ids = period_obj.search(cr, uid, [('date_start','=',date_start)])
                        res.append(period_ids[0])
                        var-=1
                    return res
                else:
                    return res

    def before_balance(self, cr, uid, account_id, periodo):
        #print"periodo::",periodo
        
        saldo = 0.0
        group = "GROUP BY l.account_id"
        where = ""
        sql = "SELECT COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, COALESCE(SUM(l.credit), 0) as credit, COALESCE(SUM(l.debit), 0) as debit "\
                "FROM account_move_line l WHERE l.account_id ="+str(account_id)
        
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')
        fecha = time.strftime('%Y-%m-%d')
        period_ob = period_obj.browse(cr, uid, periodo)
        #nio = period_ob.dperiod_objate_start
        anio = period_ob.date_start
        #print"anio::",anio
        campos = anio.split('-')
        #print"anio", campos
        year = self.pool.get('account.fiscalyear').search(cr, uid,[('date_start','<=', period_ob.date_start),
                                                          ('date_stop','>=',period_ob.date_stop),
                                                          ('code','=',campos[0]),])
        fiscalyear_clause= year[0]
        #print"fiscalyear_clause:::",fiscalyear_clause
        periodos = self._get_periods(cr, uid, period_ob.date_start, period_ob.date_stop, fiscalyear_clause)
        #print"periodos::::",periodos
        if periodos:
            ids = ','.join([str(x) for x in periodos])
            where =" AND l.state<>'draft' AND l.period_id in (SELECT id from account_period WHERE fiscalyear_id in (%s) AND id in (%s)) " % (fiscalyear_clause, ids,)
        else:
            return 0.0
        sql = sql + where + group
        #print"sql::",sql
        cr.execute(sql)
        res = cr.dictfetchall()
        for r in res:
            saldo = round (r['balance'],2)
        return saldo  
    
    def onchange_journal_id(self, cr, uid, ids, journal_id, period_id):
        #logger = netsvc.Logger()
        balance_start = 0.0
        account_period = self.pool.get('account.period')
        if journal_id:
            sql ="select balance_end_real as balance_initial from account_conciliation where journal_id="+str(journal_id)+" "
            if period_id:
                periodo_anterior = self._get_before_period(cr, uid, period_id)
                #fecha = self.start_of_fiscal_year(cr, uid, period_id)
                sql += "and period_id = "+str(periodo_anterior)+" and state='confirm'"
                _logger.info('onchange_journal %s' % (sql))
                cr.execute(sql)
                res = cr.fetchone()
                if res:
                    balance_start = res[0]
        return {'value': {'balance_start': balance_start}}
    
    def abrir_conciliacion(self, cr, uid, ids, context=None):
        conciliations = self.browse(cr, uid, ids, context)
        for conciliation in conciliations:
            args = [('journal_id', '=', conciliation.journal_id.id), ('date_to', '>', conciliation.date_to), ('state', '=', 'confirm')]
            others = self.search(cr, uid, args)
            if others:
                raise osv.except_osv('ValidationError', u'Hay otras conciliaciones validadas posteriores a ésta. Intente abrir loas otras conciliaciones.')
        return self.write(cr, uid, ids, {'state': 'read'})
    
    # Metodo que generar los account_move_line que no han sido procesadas
    def cargar_conciliacion(self, cr, uid, ids, context=None):
        for conciliation in self.browse(cr, uid, ids, context):
            lines = [line for line in conciliation.conciliation_ids if line.conciliado]
            print"lines=%s"%lines
            
            # Elimino registros excepto los que ya han conciliado
            drop_lines = [line.id for line in conciliation.conciliation_ids if not line.conciliado]
            if drop_lines: self.pool['account.conciliation.line'].unlink(cr, uid, drop_lines, context=context)
            
            # Busco registros de movimientos contables sin conciliar excepto los ya cargados
            account_id = conciliation.journal_id.default_debit_account_id.id
            print"account_id=%s"%account_id
            args = [('account_id', '=', account_id), ('x_conciliado', '=', False),
                    ('move_id.state', '=', 'posted'), ('date', '<', conciliation.date_to)]
            if lines: args.append(('id', 'not in', [aux.aml_id.id for aux in lines]))
            move_ids = self.pool['account.move.line'].search(cr, uid, args)
            
            # Creo las líneas con los movimientos encontrados
            for move_line in self.pool['account.move.line'].browse(cr, uid, move_ids, context):
                cheque_id = self.pool['payment.cheque'].search(cr, uid, [('move', '=', move_line.move_id.id),
                                                                         ('state', 'in', ['done', 'printed'])], limit=1)
                cheque_id = self.pool['payment.cheque'].browse(cr, uid, cheque_id and cheque_id[0])
                print"move_line.statement_id=%s"%move_line.statement_id.id
                val = {
                   'conciliation_id':conciliation.id,'date': move_line.date,'ref': move_line.ref or move_line.move_id.ref,
                   'partner_id': move_line.partner_id.id,'name': 'IN' if move_line.debit > 0 else 'EG',
                   'debit': move_line.debit,'credit': move_line.credit,
                   'journal_id': move_line.journal_id.id,'moves':[(6, 0,[move_line.id])],
                   #'statement_id':move_line.statement_id and lineas.statement_id.id or False,
                   'statement_id':move_line.statement_id.id,
                   'period_id':move_line.period_id.id,
                   'state':'read','aml_id':move_line.id,'nro':cheque_id and cheque_id.num_cheque or '',
                   'beneficiario': cheque_id.name or ''
                }
                print"val-account_ind=%s"%val
                self.pool['account.conciliation.line'].create(cr, uid, val, context=context)
        self.write(cr, uid, ids, {'state': 'read'}) 
    
    # Afectacion al account.move.line con las conciliaciones realizadas
    def procesar_conciliacion(self, cr, uid, ids, context=None):
        #logger = netsvc.Logger()
        for item in self.browse(cr, uid, ids):
            for lineas in item.conciliation_ids:
                if lineas.conciliado:
                    accml_id = lineas.moves
                    if accml_id:
                        sql = "UPDATE account_move_line SET x_conciliado=True WHERE id in ("+','.join([str(x.id) for x in accml_id])+")"
                        _logger.info('sql procesar %s' % (sql))
                        cr.execute(sql)
                    if lineas.aml_id:
                        sql = "UPDATE account_move_line SET x_conciliado=True WHERE id="+str(lineas.aml_id.id)
                        _logger.info('sql procesar com aml_id %s' % (sql))
                        cr.execute(sql)
        self.write(cr, uid, ids, {'state':"confirm"})             
        return True   
    
    def calcular_conciliacion(self, cr, uid, ids, context=None):
        #logger = netsvc.Logger()#Imprime las variables en lugar de los #print
        total_debit = 0
        total_credit = 0
        dep_transito = 0
        cheques_no_cobrados = 0
        _total = 0.00
        ctx = context.copy()
        inicial = 0
        for item in self.browse(cr, uid, ids):
            ctx['periods'] = [item.period_id.id]
            account_id = item.journal_id.default_credit_account_id.id
            accounts  = self.pool.get('account.account').browse(cr, uid,account_id, ctx)
            periodo = item.period_id.id
            if not periodo:
                raise osv.except_osv(_('Aviso'), _('El periodo es obligatorio para saber que saldo anterior debo tomar.!')) 
            print "saldo actual del periodo", accounts.balance
            _logger.info('SALDO ACTUAL DEL PERIODO %s' % (accounts.balance))
            balance = self.before_balance(cr, uid, account_id, periodo)
            print "saldo anterior del periodo", balance
            _logger.info('SALDO ANTERIOR DEL PERIODO %s' % (balance))
            saldo_inicial = item.balance_start
            for lineas in item.conciliation_ids:
                if lineas.conciliado:
                    if lineas.credit > 0:
                        total_credit += lineas.credit
                    if lineas.debit > 0:
                        total_debit += lineas.debit
                else:
                    if lineas.credit > 0:
                        cheques_no_cobrados += lineas.credit
                    if lineas.debit > 0:
                        dep_transito += lineas.debit
                     
        self.write(cr, uid, ids, {'credit_sum':total_credit,
                                  'debit_sum':total_debit,
                                  'balance_end_real':balance + accounts.balance + cheques_no_cobrados - dep_transito,
                                  'balance_journal':balance + accounts.balance,
                                  'deposit_transit':dep_transito,
                                  'uncashed_checks':cheques_no_cobrados})             
        return True
    
    def create(self, cr, uid, vals, context={}):
        #print 'create', vals
        balance_start = 0.00
        if 'journal_id' in vals:
            journal_id = vals.get('journal_id', False)
            sql ="SELECT balance_end_real as balance_initial FROM account_conciliation where journal_id="+str(journal_id)+" "
            if 'period_id' in vals:
                period_id = vals.get('period_id',False)
                periodo_anterior = self._get_before_period(cr, uid, period_id)
                sql += "and period_id = "+str(periodo_anterior)+" and state='confirm'"
                cr.execute(sql)
                res = cr.fetchone()
                if res:
                    balance_start = res[0]
                vals['balance_start'] = balance_start
                
        conciliation_id = super(account_conciliation, self).create(cr, uid, vals, context)
        return conciliation_id
    
    def write (self, cr, uid, ids, vals, context=None):
        balance_start = 0.00
        if not context:
                context = {}
        if 'journal_id' in vals:
            journal_id = vals.get('journal_id', False)
            sql ="SELECT balance_end_real as balance_initial FROM account_conciliation where journal_id="+str(journal_id)+" "
            if 'period_id' in vals:
                period_id = vals.get('period_id',False)
                periodo_anterior = self._get_before_period(cr, uid, period_id)
                sql += "and period_id = "+str(periodo_anterior)+" and state='confirm'"
                cr.execute(sql)
                res = cr.fetchone()
                if res:
                    balance_start = res[0]
                vals['balance_start'] = balance_start
            else:
                for item in self.browse(cr, uid, ids):
                    period_id = item.period_id.id
                    periodo_anterior = self._get_before_period(cr, uid, period_id)
                    sql += "and period_id = "+str(periodo_anterior)
                    cr.execute(sql)
                    res = cr.fetchone()
                    if res:
                        balance_start = res[0]
                    vals['balance_start'] = balance_start
                
        else:
            for item in self.browse(cr, uid, ids):
                journal_id = item.journal_id.id
                period_id = item.period_id.id
                
                sql ="SELECT balance_end_real as balance_initial FROM account_conciliation where journal_id="+str(journal_id)+" "
                
                if 'period_id' in vals:
                    period_id = vals.get('period_id',False)
                    periodo_anterior = self._get_before_period(cr, uid, period_id)
                    sql += "and period_id = "+str(periodo_anterior)+" and state='confirm'"
                    cr.execute(sql)
                    res = cr.fetchone()
                    if res:
                        balance_start = res[0]
                    vals['balance_start'] = balance_start
                else:
                    periodo_anterior = self._get_before_period(cr, uid, period_id)
                    sql += "and period_id = "+str(periodo_anterior)+" and state='confirm'"
                    cr.execute(sql)
                    res = cr.fetchone()
                    if res:
                        balance_start = res[0]
                    vals['balance_start'] = balance_start

        return super(account_conciliation, self).write(cr, uid, ids, vals, context=context)
    
    def unlink(self, cr, uid, ids, context={}):
        toremove = []
        for item in self.browse(cr, uid, ids, context):
            if item.state == 'confirm':
                raise osv.except_osv(('Advertencia'),('No se puede borrar una concilacion confirmada!'))
            toremove.append(item.id)
        result = super(account_conciliation, self).unlink(cr, uid, toremove, context)
        return result
    
    def check_all(self, cr, uid, ids, context={}):
        tocheck = []
        for item in self.browse(cr, uid, ids, context):
            for x in item.conciliation_ids:
                tocheck.append(x.id)
        self.pool.get('account.conciliation.line').write(cr,uid,tocheck,{'conciliado':True})
        return True
    
    def uncheck_all(self, cr, uid, ids, context={}):
        tocheck = []
        for item in self.browse(cr, uid, ids, context):
            for x in item.conciliation_ids:
                tocheck.append(x.id)
        self.pool.get('account.conciliation.line').write(cr,uid,tocheck,{'conciliado':False})
        return True

    def _get_balance_start(self, cr, uid, ids, field, args, context):
        res = {}
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id] = 0.0
            previous_id = self.search(cr, uid, [('journal_id', '=', obj.journal_id.id), ('date_to', '<', obj.date_to)],
                                      order='date_to desc', limit=1)
            if previous_id:
                previous_id = self.browse(cr, uid, previous_id, context)
                res[obj.id] = previous_id.balance_end_real
        return res
    
    def _get_balance_journal(self, cr, uid, ids, field, args, context):
        res = {}
        context = context or {}
        for obj in self.browse(cr, uid, ids, context):
            ctx = context.copy()
            company_id = obj.journal_id.company_id.id
            ctx.update({'initial_bal': True, 'date_from': obj.date_to, 'date_to': True, 'company_id': company_id})
            account_id = obj.journal_id.default_debit_account_id.id
            account_id = self.pool['account.account'].browse(cr, uid, account_id, context=ctx)
            res[obj.id] = account_id.balance
        return res
    
    def _get_values(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id] = dict.fromkeys(fields, 0.0)
            values = [(aux.debit, aux.credit) for aux in obj.conciliation_ids if not aux.conciliado]
            res[obj.id]['deposit_transit'] = sum([aux[0] for aux in values])
            res[obj.id]['uncashed_checks'] = sum([aux[1] for aux in values])
        return res
    
    def _get_balance_end_real(self, cr, uid, ids, field, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context):
            values = [(aux.debit, aux.credit) for aux in obj.conciliation_ids if aux.conciliado]
            res[obj.id] = obj.balance_start + sum([aux[0] for aux in values]) - sum([aux[1] for aux in values])
        return res
    
    def _change_conciliation_ids(line_pool, cr, uid, line_ids, context=None):
        line_ids = line_pool.browse(cr, uid, line_ids, context)
        ids = dict.fromkeys([aux.conciliation_id.id for aux in line_ids])
        return ids.keys()
    
    def dummy_button(self, cr, uid, ids, context=None):
        return True
    
    _columns = {
        'name': fields.char('Nombre', size=64, states={'confirm': [('readonly', True)]}),
        'date': fields.date('Fecha de Registro', required=True,
                            states={'confirm': [('readonly', True)]}),
        'journal_id': fields.many2one('account.journal', 'Diario', required=True,
                                      states={'confirm': [('readonly', True)]}, domain=[('type', 'in', ['cash', 'bank'])]),
        'period_id': fields.many2one('account.period', 'Conciliar Periodo',required=True, 
                                     states={'confirm': [('readonly', True)]}),
        'balance_start': fields.function(_get_balance_start, method=True, string='Saldo anterior', type='float', digits=(16, 2),
                                         store={_name: (lambda self, cr, uid, ids, ctx=None: ids, ['date_to', 'conciliation_ids'], 10),
                                                'account.conciliation.line': (_change_conciliation_ids, [], 10)}),
#         'balance_start': fields.float('Saldo Anterior', digits=(16, 2),
#             states={'confirm':[('readonly', True)]}, help="Saldo en libros del mes anterior"),
        'balance_end_real': fields.function(_get_balance_end_real, method=True, string='(=)Saldo Final', type='float', digits=(16, 2),
                                            store={_name: (lambda self, cr, uid, ids, ctx=None: ids, ['balance_start', 'conciliation_ids'], 10),
                                                  'account.conciliation.line': (_change_conciliation_ids, ['debit', 'credit', 'conciliado'], 10)}),
#         'balance_end_real': fields.float('(=)Saldo Final', digits=(16, 2), states={'confirm':[('readonly', True)]}, help="Saldo de la concilacion\n"\
#                                          "Saldo Final = Saldo en Libros - Depositos en transito + Cheques girados y no cobrados"),
        'balance_journal': fields.function(_get_balance_journal, method=True, string='Saldo en Libros', type='float', digits=(16, 2),
                                           store={_name: (lambda self, cr, uid, ids, ctx=None: ids, ['date_to'], 10)}),
#         'balance_journal': fields.float('Saldo en Libros', digits=(16, 2), states={'confirm':[('readonly', True)]}),
        'line_ids': fields.one2many('account.bank.statement.line',
                                    'statement_id', 'Statement lines',states={'confirm':[('readonly', True)]}),
        'conciliation_ids': fields.one2many('account.conciliation.line', 'conciliation_id', 'Conciliacion'),
        'state': fields.selection([('draft', 'Draft'),
                                   ('read', 'Read'),
                                   ('confirm', 'Confirm')], 'Estado', select=True, readonly=True),
        'debit_sum': fields.float('Tot. Debito', digits=(16, 2)),
        'credit_sum': fields.float('Tot. Credito', digits=(16, 2)),
        'deposit_transit': fields.function(_get_values, method=True, string='(-)Deposito en Transito', type='float', digits=(16, 2), multi='bank',
                                           store={_name: (lambda self, cr, uid, ids, ctx=None: ids, ['conciliation_ids'], 10),
                                                  'account.conciliation.line': (_change_conciliation_ids, ['debit', 'credit', 'conciliado'], 10)}),
#         'deposit_transit': fields.float('(-)Deposito en Transito', digits=(16, 2)),
        'uncashed_checks': fields.function(_get_values, method=True, string='(+)Cheques girados y no cobrados', type='float', digits=(16, 2), multi='bank',
                                           store={_name: (lambda self, cr, uid, ids, ctx=None: ids, ['conciliation_ids'], 10),
                                                  'account.conciliation.line': (_change_conciliation_ids, ['debit', 'credit', 'conciliado'], 10)}),
#         'uncashed_checks': fields.float('(+)Cheques girados y no cobrados', digits=(16, 2)),
        'filters':fields.selection([('byperiod', 'Por Periodo'),
                                    ('bydate', 'Por Fechas')], 'Filtrar Movimientos', required=True, states={'confirm':[('readonly', True)]},
                                    help="Filtrar por un rango de Fechas/Periodo"),
        'date_from': fields.date('Desde', states={'confirm':[('readonly', True)]}),
        'date_to': fields.date('Hasta', states={'confirm':[('readonly', True)]}),
        'period_to': fields.many2one('account.period', 'Periodo', states={'confirm':[('readonly', True)]}),
        'date_start': fields.date('Fecha Inicio del Periodo', help="Fecha de Inicio de Periodo Fiscal Actual."),
        #Temporales para crear el constraint
        'journal_id1': fields.many2one('account.journal', 'Diario'),
        'period_id1': fields.many2one('account.period', 'Conciliar Periodo'),
        'notes': fields.text('Notas', states={'confirm':[('readonly', True)]}),
        'company_id': fields.related('journal_id', 'company_id', string='Compañia', type='many2one', relation='res.company',
                                     required=True, store=True)
    }
    _defaults = {
        'name': lambda self, cr, uid, context = None: \
                self.pool.get('ir.sequence').get(cr, uid, 'account.bank.statement'),
        'date': lambda * a: time.strftime('%Y-%m-%d'),
        'state': lambda * a: 'draft',
        'balance_start': lambda * a: 0.00,
        'journal_id': _default_journal_id,
        'period_id': _get_period,
        'filters': lambda *a:'bydate',
        'date_start':lambda *a: time.strftime('2011-07-01'),#Fecha Incio del Periodo
        'date_from':lambda *a: time.strftime('%Y-%m-01'),
        'date_to':lambda * a: time.strftime('%Y-%m-%d'),
        'period_to': _get_default_periods,
        'company_id': lambda self, cr, uid, ctx: self.pool['res.users'].browse(cr, uid, uid).company_id.id
    }
    
    _sql_constraints = [
        ('unique_conciliation', 'unique(journal_id,date_to)', u'Ya existe una conciliación a esa fecha.'),
    ]

account_conciliation()

class account_conciliation_line(osv.osv):
    _name = "account.conciliation.line"
    _description = "Account Conciliation Line"
    _order = "date"
    
    @api.one
    def un_check(self):
        self.conciliado = not self.conciliado
        return  True
    
    def _get_num_cheque(self, cr, uid, ids, field_name, args, context):
        res = {}
        #=======================================================================
        # for item in self.browse(cr, uid, ids):
        #     if item.statement_id:
        #         for line in item.statement_id.bank_deposits:
        #             if line.partner_id and item.partner_id:
        #                 a = line.partner_id.id
        #                 b = item.partner_id.id
        #                 if a == b:
        #                     res[item.id] = line.number
        #                 else:
        #                     res[item.id] = ''
        #             else:
        #                 res[item.id] = ''
        #     else:
        #         res[item.id] = ''
        #=======================================================================
                
        return res
    
    def _change_state(conciliation_pool, cr, uid, conciliation_ids, context=None):
        ids = conciliation_pool.pool['account.conciliation.line'].search(cr, uid, [('conciliation_id', 'in', conciliation_ids)])
        return ids

    _columns = {
        'name': fields.char('Nombre', size=64, readonly=True, states={'draft': [('readonly', False)]}),
        'debit': fields.float('Debito', digits=(16, 2), readonly=True, states={'draft': [('readonly', False)]} ),
        'credit': fields.float('Credito', digits=(16, 2), readonly=True, states={'draft': [('readonly', False)]} ),
        'conciliation_id':fields.many2one('account.conciliation', 'Conciliacion', ondelete="cascade",),
        'ref': fields.char('Ref.', size=64, readonly=True, states={'draft': [('readonly', False)]}),
        'date': fields.date('Fecha', readonly=True, states={'draft': [('readonly', False)]}),
        'partner_id': fields.many2one('res.partner', 'Partner Ref.',readonly=True, states={'draft': [('readonly', False)]}),
	    'numero_orden': fields.char('Numero Orden', size=8),
        'period_id': fields.many2one('account.period', 'Periodo', domain=[('state','=','draft')], readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.related('conciliation_id', 'state', selection=[('draft', 'Draft'),
                                                                       ('read', 'Read'),
                                                                       ('confirm', 'Confirm')],
                                string='Estado', readonly=True, type='selection',
                                store={_name: (lambda self, cr, uid, ids, ctx=None: ids, ['conciliation_id'], 10),
                                       'account.conciliation': (_change_state, ['state'], 10)}),
#         'state': fields.selection([('draft', 'Draft'),
#                                    ('read', 'Read'),
#                                    ('confirm', 'Confirm'),
#                                    ],'Estado', readonly=True),
        #'conciliado': fields.boolean('Conciliado', states={'confirm': [('readonly', True)]}),
        'conciliado': fields.related('aml_id', 'x_conciliado', string='Conciliado', type='boolean', states={'confirm': [('readonly', True)]}),
        'journal_id': fields.many2one('account.journal', 'Diario', select=1, readonly=True, states={'draft': [('readonly', False)]}),
        'statement_id': fields.many2one('account.bank.statement', 'Extracto Bancario'),
        #'nro_cheque':fields.function(_get_num_cheque, string='Cheque', type='char', method=True, store=False, size=20),
        'check':fields.boolean('Cheque Cobrado y Girado', readonly=True, states={'draft': [('readonly', False)]}),
        'nro':fields.char('Nro.Cheque Girado',size=64, readonly=True, states={'draft': [('readonly', False)]}),
        'moves':fields.many2many('account.move.line',
                                 'account_conciliation_line_rel',
                                 'acl_id',
                                 'aml_id', 'Lineas de Asiento'),
        'aml_id':fields.many2one('account.move.line','Move Line', required=True, ondelete='cascade'),#Sirve para filtrar las lineas sin extracto bancario
        'beneficiario': fields.char('Beneficiario')
    }
    _defaults = {
        'state': lambda * a: 'draft',
    }
    _sql_constraints = [
        ('uniq', 'unique(conciliation_id,aml_id)', 'Ya ha sido cargado el registro de conciliación!')        
    ]

account_conciliation_line()

class product_template(osv.osv):
    _inherit = "product.template"
    _columns = {
        'property_account_deferred_sale': fields.property(
#             'account.account',
            type='many2one',
            relation='account.account',
            string="Diferidos en Ventas",
            method=True,
            view_load=True,
            help="This account will be used by generation of deffered in sales orders."),
            
            
        'property_account_deferred_purchase': fields.property(
#             'account.account',
            type='many2one',
            relation='account.account',
            string="Diferidos en Compras",
            method=True,
            view_load=True,
            help="This account will be used by generation of defered in purchase orders."),

    }
product_template()


