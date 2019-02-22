# -*- coding: utf-8 -*-
###################################################
#
#    Invoice Retention Module
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
from __future__ import absolute_import
from openerp.osv import osv, fields
from openerp import api
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools.translate import _
import pdb
import time
import datetime
import logging
import calendar
from lxml import etree

_logger = logging.getLogger(__name__)

class stock_move(osv.osv):
    
    _name = 'stock.move'
    _inherit = 'stock.move'
    
    _columns = {
        'price_unit': fields.float('Unit Price', digits=(16, 6))
        }
stock_move()

class product_template(osv.osv):
    _name = 'product.template'
    _inherit = 'product.template'
    
    _columns = {
        'standard_price': fields.float('Cost Price', required=True, digits=(16, 6), help="The cost of the product for accounting stock valuation. It can serves as a base price for supplier price."),
    }
product_template()

# aumente la tabla para registrar mensualmente el valor por mora de acuerdo al banco central EveM
class account_inv_fine(osv.osv):
    _name = 'account.inv.fine'
    _description = 'Fine of Invoice'
    
    def _read_code(self, cr, uid, ids, field_name, args, context):
         res = {}
         cod = ''
         for item in self.browse(cr, uid, ids):
             if item.name:
                 cod = item.name + '/' + str(time.strftime('%Y'))
                 res[item.id] = cod
         return res
    
    
    _columns = { 'name':fields.selection([('01', 'Enero'),
                                          ('02', 'Febrero'),
                                          ('03', 'Marzo'),
                                          ('04', 'Abril'),
                                          ('05', 'Mayo'),
                                          ('06', 'Junio'),
                                          ('07', 'Julio'),
                                          ('08', 'Agosto'),
                                          ('09', 'Septiembre'),
                                          ('10', 'Octubre'),
                                          ('11', 'Noviembre'),
                                          ('12', 'Diciembre')], 'Mes', size=60, required=True),
              'code':fields.function(_read_code, string='Codigo', type='char', size=60, method=True, store=True, readonly=True),
              'fine':fields.float('Multa', digits=(12, 4), help='Multa aplicada a las facturas en caso de mora', required=True),
              # 'invoice_ids':fields.one2many('account.invoice', 'fine_id', 'Factura'),
            }
    _default = {
              'code': lambda * a : str(time.strftime('%Y'))
    }
    _sql_constraints = [
        ('unique_code', 'unique(code)', 'El codigo debe ser unico, ya se creo una multa para este mes.'),
    ]
account_inv_fine()

class res_country(osv.osv):
    _inherit = 'res.country'
    _columns = {
        'ats_code': fields.char('Código S.R.I.', size=4, help='Código del país según S.R.I. para la generación del ATS')
    }
res_country()

class account_invoice_payment_method(osv.osv):
    _name = 'account.invoice.payment.method'
    _columns = {
        'name': fields.char('Descripción', size=512, required=True),
        'code': fields.char('Código', size=4, required=True, help='Código proporcionado por el S.R.I. para el nuevo ATS (Tabla 16)')}
account_invoice_payment_method()

class account_invoice_refund(osv.osv_memory):
    _inherit = 'account.invoice.refund'
    _defaults = {
        'period': lambda self, cr, uid, *a: self.onchange_date_invoice(cr, uid)['value']['period']
    }
    
    def onchange_date_invoice(self, cr, uid, ids=[], date=time.strftime('%Y-%m-%d')):
        res = self.pool.get('account.invoice').onchange_date_invoice(cr, uid, ids, date)
        res['value']['period'] = res['value'].pop('period_id')
        return res

account_invoice_refund()

class account_invoice(osv.osv):
    _name = "account.invoice"
    _inherit = "account.invoice"
    _description = "Invoice for Ecuador"
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(account_invoice, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form' and not view_id:#context.get('_terp_view_name') == 'Liquidaciones de compras':
            form_view = etree.XML(res['arch'])
            domain = "[('type','=','in_invoice'),('expiration_date','>=',date_invoice),('partner_id','=',company_id)]"
            ctx = "{'default_partner_id': company_id, 'default_type': 'in_invoice'}"
            form_view.find(".//field[@name='auth_inv_id']").set('domain', domain)
            form_view.find(".//field[@name='auth_inv_id']").set('context', ctx)
            res['arch'] = etree.tostring(form_view)
        return res
    
    def refund(self, cr, uid, ids, date=None, period_id=None, description=None, journal_id=None, context=None):
        new_ids = super(account_invoice, self).refund(cr, uid, ids, date, period_id, description, journal_id, context)
        for ind, refund_id in enumerate(new_ids):
            invoice_id = self.read(cr, uid, ids[ind], ['number','date_invoice'])
           ##self.write(cr, uid, refund_id, {'origin': 'Factura #%s (%s)'%(invoice_id['factura'] or 'S/N', invoice_id['id'])})
            """se copia el secuencial de la factura y la fecha ,estos datos son obligatorios como sustento en NC"""
            self.write(cr, uid, refund_id, {'origin': '%s[%s]'%(invoice_id['number'] or 'S/N', invoice_id['date_invoice'])})

        return new_ids
    
    def onchange_direccion(self, cr, uid, ids, type, partner_id, \
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        
        invoice_addr_id = False
        contact_addr_id = False
        partner_payment_term = False
        acc_id = False
        bank_id = False
        fiscal_position = False

        opt = [('uid', str(uid))]
        if partner_id:

            opt.insert(0, ('id', partner_id))
            res = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['contact', 'invoice'])
            contact_addr_id = res['contact']
            invoice_addr_id = res['invoice']
            p = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if company_id and p.property_account_receivable and p.property_account_payable and p.property_account_receivable.company_id \
               and p.property_account_payable.company_id:
                
                if p.property_account_receivable.company_id.id != company_id and p.property_account_payable.company_id.id != company_id:
                    property_obj = self.pool.get('ir.property')
                    rec_pro_id = property_obj.search(cr, uid, [('name', '=', 'property_account_receivable'), ('res_id', '=', 'res.partner,' + str(partner_id) + ''), ('company_id', '=', company_id)])
                    pay_pro_id = property_obj.search(cr, uid, [('name', '=', 'property_account_payable'), ('res_id', '=', 'res.partner,' + str(partner_id) + ''), ('company_id', '=', company_id)])
                    if not rec_pro_id:
                        rec_pro_id = property_obj.search(cr, uid, [('name', '=', 'property_account_receivable'), ('company_id', '=', company_id)])
                    if not pay_pro_id:
                        pay_pro_id = property_obj.search(cr, uid, [('name', '=', 'property_account_payable'), ('company_id', '=', company_id)])
                    rec_line_data = property_obj.read(cr, uid, rec_pro_id, ['name', 'value_reference', 'res_id'])
                    pay_line_data = property_obj.read(cr, uid, pay_pro_id, ['name', 'value_reference', 'res_id'])
                    rec_res_id = rec_line_data and rec_line_data[0].get('value_reference', False) and int(rec_line_data[0]['value_reference'].split(',')[1]) or False
                    pay_res_id = pay_line_data and pay_line_data[0].get('value_reference', False) and int(pay_line_data[0]['value_reference'].split(',')[1]) or False
                    if not rec_res_id and not pay_res_id:
                        raise osv.except_osv(_('Configuration Error !'),
                            _('Can not find account chart for this company, Please Create account.'))
                    account_obj = self.pool.get('account.account')
                    rec_obj_acc = account_obj.browse(cr, uid, [rec_res_id])
                    pay_obj_acc = account_obj.browse(cr, uid, [pay_res_id])
                    p.property_account_receivable = rec_obj_acc[0]
                    p.property_account_payable = pay_obj_acc[0]

            if type in ('out_invoice', 'out_refund'):
                acc_id = p.property_account_receivable.id
            else:
                acc_id = p.property_account_payable.id
            fiscal_position = p.property_account_position and p.property_account_position.id or False
            partner_payment_term = p.property_payment_term and p.property_payment_term.id or False
            if p.bank_ids:
                bank_id = p.bank_ids[0].id

        result = {'value': {
            'address_contact_id': contact_addr_id,
            'address_invoice_id': invoice_addr_id,
            'account_id': acc_id,
            'payment_term': partner_payment_term,
            'fiscal_position': fiscal_position
            }
        }
        
        if type in ('in_invoice', 'in_refund'):
            result['value']['partner_bank_id'] = bank_id

        if payment_term != partner_payment_term:
            if partner_payment_term:
                to_update = self.onchange_payment_term_date_invoice(
                    cr, uid, ids, partner_payment_term, date_invoice)
                result['value'].update(to_update['value'])
            else:
                result['value']['date_due'] = False

        if partner_bank_id != bank_id:
            to_update = self.onchange_partner_bank(cr, uid, ids, bank_id)
            result['value'].update(to_update['value'])
        
        invoice_addr_id = ''
        if partner_id:
            cr.execute("select street,street2 from res_partner where id=%i" % (partner_id))
            direcciones = cr.fetchall()
            
            dir1 = None
            dir2 = None
            
            if direcciones:
                dir1 = direcciones[0][0]
                dir2 = direcciones[0][1]
                    
            if not dir1 or not dir2:
                raise osv.except_osv('Aviso de Contabilidad',
                                                 'No se encuentra configurado la direccion')        
                
            direccion = dir1 + ' y ' + dir2             
            # v['direccion_factura'] = invoice_addr_id
            result['value']['direccion_factura'] = direccion
        # return {'value' : v}
        return result
              
        
    def _get_tipo_factura(self, cr, uid, context):
        if context is None:
            context = {}
        if context.has_key('tipo_factura'):
            return context.get('tipo_factura')
        else:
            return 'invoice'
        
    def fun_bot(self, cr, uid):
        
        return 0

    def _get_auth_retention(self, cr, uid, context):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        auths = user.company_id.partner_id.auth_ids
        tipo = 'retention'
        if 'type' in context.keys():
            if context['type'] == 'out_invoice':
                tipo = 'out_invoice'          
            elif context['type'] == 'out_refund':
                tipo = 'out_refund'          
            elif context['type'] == 'in_refund':
                return False
        for auth in auths:
            if auth.type == tipo and auth.active == True:
                return auth.id
    
    def automatic_retention_create(self, cr, uid, ids):
        inv = self.browse(cr, uid, ids)[0]
        ret_id = False
        aux_ret_id = False
        if inv.ret_sin_fact:
            raise osv.except_osv(_('Advertencia!'), _('No puede validar una factura cuando la opción "Permitir retención anticipada", está marcada.'))    
        if inv.type == 'in_invoice':
            if inv.gen_ret_mode:
                if not inv.ret_id or inv.ret_id.state == 'cancel':
                    num_comprobante = inv.auth_ret_id.sequence_id.number_next
                    num_completo = self.pool.get('ir.sequence').get_id(cr, uid, inv.auth_ret_id.sequence_id.id)
#                    #print "numero_completo", num_completo
                    ret_data = {'name' : num_completo, 'invoice_id': inv.id, 'autorization' : inv.auth_ret_id.id , 'type' : inv.auth_ret_id.type, 'num_comprobante': num_comprobante,
                                 'partner_id' : inv.partner_id.id, 'state':'paid', 'fecha': time.strftime('%Y-%m-%d')}
                    print"ret_data=%s"%ret_data
                    
                    ret_id = self.pool.get('account.invoice.retention').create(cr, uid, ret_data)
                    
                    print"ret_id=%s"%ret_id
                    
                    self.pool.get('account.invoice').write(cr, uid, [inv.id], {'ret_id':ret_id})            
                else:
                    if inv.ret_id.state == 'early':
                        for tax in inv.ret_id.tax_line:
                            inv_id = tax.invoice_id.id
                            if inv_id == False:
                                aux = 'delete from account_invoice_tax where ret_id in (' + ','.join(map(str, [inv.ret_id.id])) + ') and (invoice_id is null)'
                                #print "sql", aux
                                cr.execute('delete from account_invoice_tax where ret_id in (' + ','.join(map(str, [inv.ret_id.id])) + ') and (invoice_id is null)')
                    ret_data = {'autorization' : inv.auth_ret_id.id , 'partner_id' : inv.partner_id.id, 'state':'paid', 'move_ret_id':inv.move_id}
                    self.pool.get('account.invoice.retention').write(cr, uid, [inv.ret_id.id], ret_data)
        elif inv.type == 'out_invoice':
            if inv.ret_id:
                ret_data = {'partner_id' : inv.partner_id.id}
                self.pool.get('account.invoice.retention').write(cr, uid, [inv.ret_id.id], ret_data)            
        if inv.ret_id:
            aux_ret_id = inv.ret_id.id 
        elif ret_id:
            aux_ret_id = ret_id
        if aux_ret_id:
            for tax in inv.tax_line:
                if tax.tax_group in ['ret_vat', 'ret_ir']:
                    self.pool.get('account.invoice.tax').write(cr, uid, [tax.id], {'ret_id':aux_ret_id})
        return ret_id
    
    
    def obtain_lines_advances(self, cr, uid, inv, iml):
        
        expense = self.pool.get('hr.expense.expense')
        expense_expense_line = self.pool.get('hr.expense.expense.line')
        # id_liquidacion = expense.search(cr, uid, [('invoice_id', '=', inv.id)])
        id_liquidacion = False
        if not id_liquidacion:
            return
        
        ids_expense_expense_line = expense_expense_line.search(cr, uid, [('liquidation_id', '=', id_liquidacion[0])])
        ids_advance = expense_expense_line.read(cr, uid, ids_expense_expense_line, ['advance_id'])
        
        if not ids_advance:
            raise osv.except_osv(_('Error !'), _('La liquidación del anticipo no tiene anticipos asociados. La liquidación parece estar mal creada.'))
        
        for id_advance in ids_advance:
            # id_advance = expense.read(cr, uid, id_liquidacion, ['expense_id'])
#            #print 'id_advance ', str(id_advance)
            id_advance_lines = self.pool.get('hr.expense.line').search(cr, uid, [('expense_id', '=', id_advance['advance_id'][0])])
            advance_lines = self.pool.get('hr.expense.line').browse(cr, uid, id_advance_lines)
        
            for advance_line in advance_lines:
                
                if advance_line.product_id:
                    acc = advance_line.product_id.product_tmpl_id.property_account_expense.id
                    if not acc:
                        acc = advance_line.product_id.categ_id.property_account_expense_categ.id
                    tax_id = [x.id for x in advance_line.product_id.supplier_taxes_id]
                else:
                    acc = self.pool.get('ir.property').get(cr, uid, 'property_account_expense_categ', 'product.category')
                    if not acc:
                        raise osv.except_osv(_('Error !'), _('Please configure Default Expanse account for Product purchase, `property_account_expense_categ`'))
                
                mres = {
                    'type':'src',
                    'name': advance_line.name,
                    'price_unit':advance_line.unit_amount,
                    'quantity':advance_line.unit_quantity,
                    'price':(-1) * advance_line.total_amount,
                    'account_id':acc,
                    'product_id':advance_line.product_id and advance_line.product_id.id or False,
                    'uos_id':advance_line.uom_id.id,
                    'account_analytic_id':advance_line.analytic_account.id,
                    'taxes':False,
                }
                iml.append(mres)
                
    def obtain_line_analytics(self, cr, uid, inv, iml):
        """
        Se agrega lineas para dividir los asientos cuando existen detalles 
        con la cuenta analitica.
        """
        i = 0
        lista = []
        for aal in iml:
            if aal.has_key('analytic_line_id'):
                lista.append(aal['analytic_line_id'])
        analytic = list(set(lista))
        if inv.invoice_line:
            for l in inv.invoice_line:
                i = i + 1
                # if l.analytics_id:
                #    plan_id = l.analytics_id.id
                #    analytics = self.pool.get('account.analytic.plan.instance.line').search(cr, uid, [('plan_id', '=', plan_id)])
                #    for a in analytics:
                #        if a not in analytic:
                #            b = self.pool.get('account.analytic.plan.instance.line').browse(cr, uid, a)
#                            if not b.cuenta.id:
#                                raise osv.except_osv(_('Advertencia!'), _('Falta información en la cuenta de la Distribución Análitica: \n'+str(l.analytics_id.name))) 
                #            mres = {
                #                'type':'src',
                #                'name': l.name[:64],
                #                'price_unit': l.price_unit,
                #                'quantity': l.quantity,
                #                'price': l.price_subtotal * (b.rate / 100),
                #                #'account_id':b.cuenta.id or l.account_id.id,
                #                'account_id': l.account_id.id,
                #                'product_id':l.product_id.id,
                #                'uos_id':l.uos_id.id,
                #                'account_analytic_id':l.account_analytic_id.id,
                #                'taxes':l.invoice_line_tax_id,
                #                'analytics_id':l.analytics_id.id
                                
                #            }
                #            iml.append(mres)



    def _get_analytic_lines(self, cr, uid, ids):
        
        # #print ' en el get_analytics_line**********'
        
        inv = self.browse(cr, uid, ids)
        cur_obj = self.pool.get('res.currency')

        company_currency = inv.company_id.currency_id.id
        if inv.type in ('out_invoice', 'in_refund'):
            sign = 1
        else:
            sign = -1

        iml = self.pool.get('account.invoice.line').move_line_get(cr, uid, inv.id)
        #print"iml-lin417=%s"%iml
        
        # #print ' iml ', iml
        
        for il in iml:
            if il['account_analytic_id']:
                if inv.type in ('in_invoice', 'in_refund'):
                    ref = inv.reference
                else:
                    ref = inv.number
                if not inv.journal_id.analytic_journal_id:
                    raise osv.except_osv(_('No Analytic Journal !'), _("You have to define an analytic journal on the '%s' journal!") % (inv.journal_id.name,))
                il['analytic_lines'] = [(0, 0, {
                    'name': il['name'],
                    'date': inv['date_invoice'],
                    'account_id': il['account_analytic_id'],
                    'unit_amount': il['quantity'],
                    'amount': cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, il['price'], context={'date': inv.date_invoice}) * sign,
                    'product_id': il['product_id'],
                    'product_uom_id': il['uos_id'],
                    'general_account_id': il['account_id'],
                    'journal_id': inv.journal_id.analytic_journal_id.id,
                    'ref': ref,
                })]
        return iml


    def line_get_convert(self, cr, uid, x, part, date, context=None):         
             
            print"x=%s"%x
            account_obj = self.pool.get('account.account')
            cuenta_id = account_obj.search(cr, uid, [('partner_id','!=',None)]) #partner_id es nulo
            #lista_partner = account_obj.read(cr, uid, [x['account_id']], ['partner_id'], context=None)           
            print"cuenta_id=%s"%cuenta_id                                                                               
            if x['account_id'] in cuenta_id:# si cuenta de tabla esta en la lista buscar el partner de cuenta             
                partner_account = self.pool.get('account.account').browse(cr, uid,x['account_id'])
                print"partner_aux=%s"%partner_account.partner_id.id
                part = partner_account.partner_id.id

            
            return {
                'date_maturity': x.get('date_maturity', False),
                'partner_id':part ,
                'name': x['name'][:64],
                'date': date,
                'debit': x['price'] > 0 and x['price'],
                'credit': x['price'] < 0 and -x['price'],
                'account_id': x['account_id'],
                'analytic_lines': x.get('analytic_lines', []),
                'amount_currency': x['price'] > 0 and abs(x.get('amount_currency', False)) or -abs(x.get('amount_currency', False)),
                'currency_id': x.get('currency_id', False),
                'tax_code_id': x.get('tax_code_id', False),
                'tax_amount': x.get('tax_amount', False),
                'ref': x.get('ref', False),
                'quantity': x.get('quantity', 1.00),
                'product_id': x.get('product_id', False),
                'product_uom_id': x.get('uos_id', False),
                'analytic_account_id': x.get('account_analytic_id', False),
                # 'preproject_id':x.get('preproject_id', False),
            }
   
    def action_move_create(self, cr, uid, ids, *args):
        #print "2) action_move_create", ids
        # Actualiza Informacion de la Orden Venta en la Factura para el proceso de comisiones de vendedores
        # self.action_sale_cuota(cr, uid, ids)
        # Se Crea el Activo a partir de la Orden de Compra. Siempre y cuando se Escoja un Producto que este configurado como Activo
        self.action_asset_create(cr, uid, ids)
        #=======================================================================
        # Creacion de la tabla de Diferidos
        #=======================================================================
        self.action_generate_billing(cr, uid, ids)
        
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        rete_voucher_obj = self.pool.get('account.invoice.retention.voucher')
        context = {}
        
        for inv in self.browse(cr, uid, ids):
            or_amount = 0.0
            ir_amount = 0.0
            # Revision de Totales para la creacion de Notas de Credito de Facturas de Ventas
            if inv.type in ['out_refund']:
                # #print "o1", inv.origin
                if inv.origin:
                    # Buscar en el campo num_retention
                    foi = self.search(cr, uid, [('num_retention', 'ilike', inv.origin)])
                    # #print "foi", foi
                    if foi:
                        or_amount = self.browse(cr, uid, foi[0]).amount_total
                        # #print "or_amount", or_amount
                        if inv.amount_total > or_amount:
                            raise osv.except_osv('Total Incorrecto', 'Por favor Revise el total !\nEl Total a Pagar no debe ser mayor al de la factura de origen:' + inv.origin + '.')
            # Revision de Totales para la creacion de Notas de Credito de Facturas de Compras
            if inv.type in ['in_refund']:
                # #print "o2", inv.origin
                # Buscar en el campo number_inv_supplier
                if inv.origin:
                    a = True
                    for i in inv.origin:
                        if i not in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0'):
                            a = False
                             
                    if a and int(inv.origin):
                        ir = self.search(cr, uid, [('number_inv_supplier', '=', int(inv.origin))])
                        # #print "ir", ir
                        if ir:
                            # Valor sin retencion para facturas de proveedores
                            ir_amount = self.browse(cr, uid, ir[0]).amount_pay
                            # #print "ir_amount", ir_amount
                            if inv.amount_total > ir_amount:
                                raise osv.except_osv('Total Incorrecto', 'Por favor Revise el total !\nEl Total a Pagar no debe ser mayor al de la factura de origen:' + inv.origin + '.')
                    
            
            tipo_factura = inv.tipo_factura
            factura_tipo = inv.type
            number = False
            if inv.type == 'in_invoice' and inv.type in ['in_invoice', 'in_refund']:
                if inv.type == 'in_invoice' and inv.amount_untaxed >= 1000 and not len(inv.payment_method_ids):
                    raise osv.except_osv('ATS', u'El valor de la Base Imponible supera los $1000, por favor ingrese por lo menos un metodo de pago en la Pestaña de Información de Pago.')
                
            if inv.move_id:
                continue
            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice':time.strftime('%Y-%m-%d'),
                                               'date_from_deferred':time.strftime('%Y-%m-%d')})
            company_currency = inv.company_id.currency_id.id
                # create the analytical lines
            line_ids = self.read(cr, uid, [inv.id], ['invoice_line'])[0]['invoice_line']
            
            # one move line per invoice line
            # #print ' antes del envio '
            iml = self._get_analytic_lines(cr, uid, inv.id)
            #print ' iml account invoice ', iml

            if tipo_factura in ('purchase_liq', 'gas_no_dedu', 'doc_inst_est', 'invoice','gasto_financiero'):
                self.obtain_lines_advances(cr, uid, inv, iml)
                
            # check if taxes are all computed
            self.check_all_computed_taxes(cr, uid, inv, context)
            #print"inv.check_total=%s"%inv.check_total
            #print"inv.amount_pay=%s"%inv.amount_pay
            #print"inv.currency_id=%s"%(inv.currency_id.rounding / 2.0)

            if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_pay) >= (inv.currency_id.rounding / 2.0):
                raise osv.except_osv('Total incorrecto Verificar!', 'Por favor verificar el valor de la factura!\nEl valor real no es igual al calculado!')
            
            # one move line per tax line
            iml += ait_obj.move_line_get(cr, uid, inv.id)
            #print ' iml ***** AAAA **** ', iml
                        
            # delete tax line when ret_ir or ret_vat
            if not inv.gen_ret_mode or inv.type == 'out_invoice':
#                #print "entra_out_invoice"
                iml = [item for item in iml if not item.has_key('tax_group') or (item.has_key('tax_group') and not item['tax_group'] in ['ret_ir', 'ret_vat'])]
#                #print "iml", iml
            
            # Asignacion del campo ref en el move_line del numero de Factura para una mejor busqueda desde los extractos o desde la linea de asientos
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
            else:
                ref = inv.number
            if inv.type in ('in_invoice', 'in_refund'):
                if tipo_factura in ['invoice', 'purchase_liq', 'sales_note']:
                    ref = inv.number_inv_supplier and str(inv.number_inv_supplier).zfill(9)
                elif tipo_factura in ['anticipo', 'gas_no_dedu','gasto_financiero']:
                    ref = inv.code_advance_liq
                else:
                    ref = inv.number
#                     ref = self._convert_ref(inv.number)
            elif inv.type in ('out_invoice', 'out_refund'):
                
                if inv.auth_ret_id:
                    if inv.auth_ret_id.sequence_id:
                        if not inv.num_retention:
                            # #print "Asigno el Numero de Factura/Nota de Credito de Venta"
                            if inv.type == 'out_invoice' and inv.auth_ret_id.type not in ('out_invoice'):
                                    raise osv.except_osv('Aviso de Contabilidad',
                                                         'Debe seleccionar una autorizacion de tipo Factura Cliente')
                            number = self.pool.get('ir.sequence').get_id(cr, uid, inv.auth_ret_id.sequence_id.id)
                            ref = number
                        else:
                            ref = inv.num_retention
                if not inv.date_to_deferred:
                    inv.date_to_deferred = inv.date_invoice
#             else:
#                 ref = self._convert_ref(inv.number)
            # #print "referencia", ref
            
            diff_currency_p = inv.currency_id.id <> company_currency
            descuentos = []

            total = total_currency = band = descuento = 0
            
            if inv.type == 'out_invoice' and inv.invoice_line:
                for det in inv.invoice_line:
                    if det.discount != 0:
                        band = 1
            
            # Metodo que divide a las diferentes cuentas las valores del Diario Analitico            
            self.obtain_line_analytics(cr, uid, inv, iml)
            
            for i in iml:
                if inv.currency_id.id != company_currency:
                    i['currency_id'] = inv.currency_id.id
                    i['amount_currency'] = i['price']
                    i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id,
                                                 company_currency, i['price'],
                                                 context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')})
                else:
                    i['amount_currency'] = False
                    i['currency_id'] = False
#                 i['ref'] = ref
                
                if inv.type in ('out_invoice', 'in_refund'):
                    total += i['price']
                    total_currency += i['amount_currency'] or i['price']
                    i['price'] = -i['price']
                else:
                    total -= i['price']
                    total_currency -= i['amount_currency'] or i['price']
            
            acc_id = inv.account_id.id
            name = inv['name'] or '/'
            totlines = False
            # #print "payment_term", inv.payment_term            
            # if inv.payment_term:
                #   totlines = self.pool.get('account.payment.term').compute(cr, uid, inv.payment_term.id,
                #                                                            total, inv.date_invoice or False)

            if totlines and band == 0:
                # #print "Normal band 0 y Totlines"
                res_amount_currency = total_currency
                i = 0
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1])
                    else:
                        amount_currency = False
                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                        and  amount_currency or False,
                        'currency_id': diff_currency_p \
                        and inv.currency_id.id or False,
                        'ref': ref,
                        'inv_type':factura_tipo
                    })
            if not totlines and band == 0:
                # #print "Normal band 0 y not Totlines"
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity' : inv.date_due or False,
                    'amount_currency': diff_currency_p \
                    and total_currency or False,
                    'currency_id': diff_currency_p \
                    and inv.currency_id.id or False,
#                     'ref': ref,
                    'inv_type':factura_tipo
                })
            
            if totlines and band == 1: 
                # #print "Entro totlines band ==1"
                aux1 = 0
                for i in iml:
#                    #print "i", i
                    if i.has_key('discount') and i['discount'] != 0:
                        aux1 += (i['price_unit'] * i['quantity']) * i['discount'] / 100
                res_amount_currency = total_currency
                
                i = 0
                for t in totlines:
                    r = round(aux1, int(dp.get_precision('Account')))
                    resta = t[1] - r
#                    #print "resta", resta
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid,
                                                          company_currency, inv.currency_id.id, t[1])
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency
                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': resta,
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                        and  amount_currency or False,
                        'currency_id': diff_currency_p \
                        and inv.currency_id.id or False,
                        'ref': ref,
                        'inv_type':factura_tipo
                    })
            if not totlines and band == 1:
                # #print "Entro not totlines and band ==1"
                aux1 = 0
                for i in iml:
                    if i.has_key('discount') and i['discount'] != 0:
                        aux1 += (i['price_unit'] * i['quantity']) * i['discount'] / 100
                presicion = dp.get_precision('Account')(cr)
                r = round(aux1, presicion[1])
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total - r,
                    'account_id': acc_id,
                    'date_maturity' : inv.date_due or False,
                    'amount_currency': diff_currency_p \
                    and total_currency or False,
                    'currency_id': diff_currency_p \
                    and inv.currency_id.id or False,
                    'ref': ref,
                    'inv_type':factura_tipo
                })
            if band == 1:
                # #print "entra band = 1"
                for i in iml:
                    if i.has_key('discount'):
                        descuento = i['discount']
                        aux = i['discount']
                        if aux != 0:
                            descuento = (i['price_unit'] * i['quantity']) * i['discount'] / 100
                            price = round(descuento, int(dp.get_precision('Account')))
                            # #print "////////////PRECIO////// %s \n\n" % (price)
                            cuenta = i['discount_id']
                            iml.append({
                                    'type': 'dest',
                                    'name': name,
                                    'price': price,
                                    'account_id':cuenta ,
                                    'date_maturity': inv.date_due or False,
                                    'amount_currency': diff_currency_p \
                                    and  amount_currency or False,
                                    'currency_id': diff_currency_p \
                                    and inv.currency_id.id or False,
                                    'ref': ref,
                                    'inv_type':factura_tipo
                                })
                        
            date = inv.date_invoice or time.strftime('%Y-%m-%d')
            part = inv.partner_id.id
            print"partner-776=%s"%part  
                
            #print "IML \n %s \n" % iml
            line = map(lambda x:(0, 0, self.line_get_convert(cr, uid, x, part, date, context={})) , iml)  
            #print"partner_account=%s"%partner_account                              
            #print "LINES ////:\n %s \n\n\n" % line   
            print"inv.journal_id.group_invoice_lines=%s"%inv.journal_id.group_invoice_lines              
                    
            if inv.journal_id.group_invoice_lines:
                line2 = {}
                for x, y, l in line:
                    tmp = str(l['account_id'])
                    tmp += '-' + str(l.get('tax_code_id', "False"))
                    tmp += '-' + str(l.get('product_id', "False"))
                    tmp += '-' + str(l.get('analytic_account_id', "False"))
                    tmp += '-' + str(l.get('date_maturity', "False"))
                    
                    if tmp in line2:
                        am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
                        line2[tmp]['debit'] = (am > 0) and am or 0.0
                        line2[tmp]['credit'] = (am < 0) and -am or 0.0
                        line2[tmp]['tax_amount'] += l['tax_amount']
                        line2[tmp]['analytic_lines'] += l['analytic_lines']
                    else:
                        line2[tmp] = l
                line = []
                for key, val in line2.items():
                    line.append((0, 0, val))
                    
            journal_id = inv.journal_id.id  # self._get_journal(cr, uid, {'type': inv['type']})
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id)
            if journal.centralisation:
                raise osv.except_osv(_('UserError'),
                                     _('Cannot create invoice move on centralised journal'))     
            
            #dc#datos de registro en account_move_line
            print"line_id :\n %s \n\n\n"%line
            move = { 'line_id': line, 'journal_id': journal_id, 'date': date, 'ref': 'FACT. ' + (inv.factura or ''),
                    'other_info': inv.comment, 'no_comp': inv.number_inv_supplier or inv.factura}
            period_id = inv.period_id and inv.period_id.id or False
            if not period_id:
                period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', inv.date_invoice or time.strftime('%Y-%m-%d')),
                                                                              ('date_stop', '>=', inv.date_invoice or time.strftime('%Y-%m-%d'))])
                if period_ids:
                    period_id = period_ids[0]
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id
            # #print "Account Move values: %s" % move
            
            journal_code = inv.journal_id.code
            # NO CAMBIAR ESTAS LINEAS PARA QUE NO SE DANE LA SECUENCIA
#             if journal_code == 'VE':
#             # if journal.type == 'sale':
#                 move['tipo_comprobante'] = 'ComproDiario'
#             elif journal_code == 'CO':
#             # elif journal.type == 'purchase':
#                 move['tipo_comprobante'] = 'OPago'
#             elif journal_code == 'DD':
#                 move['tipo_comprobante'] = 'CajaChica'                    
#             elif journal_code == 'RCCH':
#                 move['tipo_comprobante'] = 'CajaChica'           
           
            move_id = self.pool.get('account.move').create(cr, uid, move, context=context)
            new_move_name = self.pool.get('account.move').browse(cr, uid, move_id).name
            ##print "new_move_name", new_move_name                  
            band = False
            number_retention = 0
            inv_data = {'move_id': move_id, 'period_id':period_id, 'move_name':new_move_name}
            for tax in inv.tax_line:
                if tax.tax_group in ['ret_vat', 'ret_ir']:
                    band = True
                    break
            ret_id = False
            if inv.amount_total != 0 and inv.tax_line:
                if inv.type == 'in_invoice':
                    #print 'inv.type838INVOICE=%s '%inv.type 
                    if band and tipo_factura != 'anticipo':
                        if not inv.auth_ret_id:
                            raise osv.except_osv('Aviso de Contabilidad',
                                             'Debe seleccionar una autorizacion de retenciones')
                        if inv.has_early_ret:
                            self._check_ret_anticipada_valida(cr, uid, ids, inv.ret_id.id)
                        ret_id = self.automatic_retention_create(cr, uid, ids)
                elif inv.type == 'out_invoice':
                    ret_id = self.automatic_retention_create(cr, uid, ids)
                    if inv.auth_ret_id:
                        if inv.auth_ret_id.sequence_id:
                            if not inv.num_retention:
                                if inv.auth_ret_id.type not in ('out_invoice'):
                                    raise osv.except_osv('Aviso de Contabilidad',
                                                     'Debe seleccionar una autorizacion de tipo Factura Cliente')
                                inv_data['num_retention'] = number
                                inv_data['factura'] = number
                elif inv.type == 'out_refund':
                    if inv.auth_ret_id:
                        if inv.auth_ret_id.sequence_id:
                            if not inv.num_retention:
#                            number = self.pool.get('ir.sequence').get_id(cr, uid, inv.auth_ret_id.sequence_id.id)
                                inv_data['num_retention'] = number
                                inv_data['factura'] = number
            else:
            # #print 'entra1'
                if inv.type == 'out_invoice':
                    ret_id = self.automatic_retention_create(cr, uid, ids)
                    if inv.auth_ret_id:
                        if inv.auth_ret_id.type not in ('out_invoice'):
                            raise osv.except_osv('Aviso de Contabilidad',
                                             'Debe seleccionar una autorizacion de tipo Factura Cliente')
                        if inv.auth_ret_id.sequence_id:
                            if not inv.num_retention:
                                inv_data['num_retention'] = number
                                inv_data['factura'] = number
                elif inv.type == 'out_refund':
                    if inv.auth_ret_id:
                        if inv.auth_ret_id.sequence_id:
                            if not inv.num_retention:
                                inv_data['num_retention'] = number
                                inv_data['factura'] = number
            
            
            self.write(cr, uid, [inv.id], inv_data)
            
            
            self.pool.get('account.move').post(cr, uid, [move_id], context={'invoice':inv})
            print 'move_id=%s '%move_id 
            # self.pool.get('account.move').post(cr, uid, [move_id], {'has_name': inv.number})
            if inv.gen_ret_mode:
                if band and tipo_factura != 'anticipo':
                    aux_ret_id = ret_id
                    if not ret_id:
                        aux_ret_id = inv.ret_id.id
                    self.pool.get('account.invoice.retention').write(cr, uid, aux_ret_id, {'move_ret_id':move_id})
                    
            # Actualizar la retencion en caso que tenga cuando vuelve de borrador a abierto
            if inv.ret_voucher and inv.ret_voucher_id and inv.ret_voucher_id.id:
                dir_com = ''
                if inv.partner_id.street and inv.partner_id.street2:
                    dir_com = inv.partner_id.street + ' Y ' + inv.partner_id.street2
                elif inv.partner_id.street:
                    dir_com = inv.partner_id.street
                    
                rete_voucher_obj.write(cr, uid, [inv.ret_voucher_id.id], {'partner':inv.partner_id.name, 'ruc':inv.partner_id.ident_num,
                                                                          'social_reason':inv.company_id.name, 'ruc_ci':inv.company_id.partner_id.ident_num,
                                                                          'address':dir_com, 'state':'draft', 'type_voucher_purchase':str(inv.tipo_factura),
                                                                          'num_voucher_purchase':inv.num_retention,
                                                                          'partner_id':inv.partner_id.id , 'numero':str(number or inv.num_retention).zfill(9)})
                for item in inv.ret_voucher_id.ret_voucher_line_ids:
                    b_i_iva = inv.t_bi_iva * 0.12
                    b_i_ir = inv.amount_untaxed
                    if period_id:
                        obj_period = self.pool.get('account.period').browse(cr, uid, period_id)
                        anio_fis = obj_period.fiscalyear_id.id
                                            
                    self.pool.get('account.invoice.retention.voucher.line').write(cr, uid, item.id, {'tax_base':b_i_ir,
                                                                                                    'fiscal_year_id':anio_fis,
                                                                                                    'ret_voucher_id':inv.ret_voucher_id.id,
                                                                                             })
                
        self._log_event(cr, uid, ids)
        return True


    def check_all_computed_taxes(self, cr, uid, inv, context):
        """
        check if taxes are all computed
        """
        ait_obj = self.pool.get('account.invoice.tax')
        
        context.update({'lang': inv.partner_id.lang})
        compute_taxes = ait_obj.compute(cr, uid, inv.id, context=context)
        #print ' compute_taxes **** ', str(compute_taxes)
        # #print ' inv.tax_line ', str(inv.tax_line)
            
        if not inv.tax_line:
            for tax in compute_taxes.values():
                ait_obj.create(cr, uid, tax)
        else:
            tax_key = []
            for tax in inv.tax_line:
                if tax.manual:
                    continue
                key = (tax.tax_code_id.id, tax.base_code_id.id, tax.account_id.id, tax.account_analytic_id.id)
                tax_key.append(key)
                if not key in compute_taxes:
                    raise osv.except_osv(_('Warning !'), _('Global taxes defined, but are not in invoice lines !'))
                base = compute_taxes[key]['base']
                if abs(base - tax.base) > inv.company_id.currency_id.rounding:
                    raise osv.except_osv(_('Warning !'), _('Tax base different !\nClick on compute to update tax base'))
            for key in compute_taxes:
                if not key in tax_key:
                    raise osv.except_osv(_('Warning !'), _('Taxes missing !'))
        

    def action_cancel(self, cr, uid, ids, *args):
        diferido_obj = self.pool.get('account.order.billing')
        for inv in self.browse(cr, uid, ids):
            if inv.ret_id.state in ['paid']:
                # cr.execute("select a.factura,a.type from account_invoice as a left join account_move m on m.id=a.move_id left join account_invoice_retention r on (select move_ret_id from account_invoice_retention where num_comprobante='%s')=a.move_id where a.factura=m.ref and a.partner_id=m.partner_id and r.move_ret_id=m.id" % (obj.num_comprobante,))
                # resultado = cr.fetchall()
                tipo = inv.type
                # if resultado:
                #    tipo=resultado[0][1]
                self.write(cr, uid, [inv.id], {'ret_id':False})
                self.pool.get('account.invoice.retention').act_cancel(cr, uid, [inv.ret_id.id], {'fact_ids':ids, 'tipo_fact':tipo})

            if inv.type in ('out_invoice', 'in_invoice'):
                #===============================================================
                # Borro el diferido de la factura cancelada
                #===============================================================
                diferido = diferido_obj.search(cr, uid, [('invoice_id', '=', inv.id)])
                if diferido:
                    diferido_obj.unlink(cr, uid, diferido)
                    
            if inv.type in ('out_invoice'):
                if inv.ret_voucher and inv.ret_voucher_id and inv.ret_voucher_id.id:
                    cancel = self.pool.get('account.invoice.retention.voucher').action_cancel_retention(cr, uid, [inv.ret_voucher_id.id], context={})
                    if cancel:
                        self.pool.get('account.invoice.retention.voucher').write(cr, uid, [inv.ret_voucher_id.id], {'state':'cancel'})
                    
        res = super(account_invoice, self).action_cancel(cr, uid, ids, *args) 
        return True
    
    def action_cancel_draft(self, cr, uid, ids, *args):
        diferido_obj = self.pool.get('account.order.billing')
        for inv in self.browse(cr, uid, ids):
            if inv.type in ('out_invoice', 'in_invoice'):
                diferido = diferido_obj.search(cr, uid, [('invoice_id', '=', inv.id)])
                if diferido:
                    diferido_obj.unlink(cr, uid, diferido)
            if inv.type in ('out_invoice'):
                if inv.ret_voucher and inv.ret_voucher_id and inv.ret_voucher_id.id:
                    self.pool.get('account.invoice.retention.voucher').action_cancel_retention(cr, uid, [inv.ret_voucher_id.id], context={})
                
        res = super(account_invoice, self).action_cancel_draft(cr, uid, ids, *args)
        self.write(cr, uid, ids, {'internal_number': False})
        return True

    
    #=======================================================================
    # Aumente funcion boton generar comprobante de retencion *EM
    # Generacion de las Retenciones en las Facturas de Clientes *EG
    #=======================================================================
    def action_generate_voucher(self, cr, uid, ids, *args):
        #print "action_generate_voucher", ids
        
        for inv in self.browse(cr, uid, ids):
            if inv.ret_voucher:
                raise osv.except_osv(('Informacion !'), ('Ya se genero el comprobante de retencion anteriormente.'))
            elif inv.state in ['draft', 'proforma2', 'cancel', 'proforma']:
                raise osv.except_osv(('Informacion !'), ('No se generan retenciones de facturas en estado: borrador,proformas o canceladas.'))
            else:
                if inv.tax_line:
                    num = ''
                    nom_com = ''
                    dir_com = ''
                    ruc = ''
                    ruc_emi = ''
                    nom_cli = ''
                    if inv.num_retention:
                        num = str(inv.num_retention).zfill(9)
                    if inv.partner_id.name:
                        nom_cli = inv.partner_id.name
                    if inv.partner_id.ident_num:
                        ruc_emi = inv.partner_id.ident_num
    
                    if inv.company_id.name:
                        nom_com = inv.company_id.name
                    
                    if inv.partner_id.street and inv.partner_id.street2:
                        dir_com = inv.partner_id.street + ' Y ' + inv.partner_id.street2
                    elif inv.partner_id.street:
                        dir_com = inv.partner_id.street
    
                    if inv.company_id.partner_id.ident_num:
                        ruc = inv.company_id.partner_id.ident_num
                        
                    id_voucher = self.pool.get('account.invoice.retention.voucher').create(cr, uid, {'partner':nom_cli,
                                                                                                     'invoice_id':inv.id,
                                                                                                     'ruc':ruc_emi,
                                                                                                     'social_reason':nom_com,
                                                                                                     'ruc_ci':ruc,
                                                                                                     'address':dir_com,
                                                                                                     'state':'draft',
                                                                                                     'type_voucher_purchase':str(inv.tipo_factura),
                                                                                                     'number':num,
                                                                                                     'num_voucher_purchase':inv.number,
                                                                                                     'partner_id':inv.partner_id.id,
                                                                                                     'numero':num})
                    b_i_iva = inv.t_bi_iva * 0.12
                    b_i_ir = inv.amount_untaxed
                    perc_iva = 70
                    perc_ir = 8
                    anio_fis = inv.period_id.fiscalyear_id.id
                    
                    #'''Retencion de los productos de ventas nombre del impuesto para la retencion'''
                    #id1 = self.pool.get('account.tax').search(cr, uid, [('name', '=', 'Retención Ventas: Aplicables el 2%')])
    
                    #if not id1:
                    #    raise osv.except_osv(('Aviso'), (' No se han podido obtener los parametros para la RETENCION DE RENTA A TERCEROS por favor revise la lista de impuestos.'))
    
                    #self.pool.get('account.invoice.retention.voucher.line').create(cr, uid, {'tax_base':b_i_ir,
                    #                                                                         'tax_id':int(id1[0]),
                    #                                                                         'fiscal_year_id':anio_fis,
                    #                                                                         'ret_voucher_id':id_voucher})
                    self.write(cr, uid, [inv.id], {'ret_voucher':True, 'ret_voucher_id':id_voucher})
    
        return {
            'type': 'ir.actions.act_window',
            'name': 'Retención de cliente',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': id_voucher,
            'res_model': 'account.invoice.retention.voucher',
            'target': 'current'
        }

    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, context=None):
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id)
        res1 = self.pool.get('account.authorisation').search(cr, uid, [('partner_id', '=', partner_id), ('active', '=', True), ('type', '=', type)])
        user = self.pool.get('res.users').browse(cr, uid, uid)
        payment = self.pool.get('res.partner').browse(cr, uid, partner_id)
        
        if  payment.payment_type:
            if payment.payment_type == 'CTA':
                res['value']['partner_payment'] = 'Cash Management Cuenta Bancaria'
            if payment.payment_type == 'CHQ':
                res['value']['partner_payment'] = 'Cash Management Cheque Gerencia'
            if payment.payment_type == 'EFE':
                res['value']['partner_payment'] = 'Cash Management Efectivo'
            if payment.payment_type == 'CHQINDV':
                res['value']['partner_payment'] = 'Cheque'
            if payment.payment_type == 'CARD':
                res['value']['partner_payment'] = 'Tarjeta de Credito'
            if payment.payment_type == 'CANJE':
                res['value']['partner_payment'] = 'Canje'
             
        if type == 'in_invoice':        
            for auth in user.company_id.partner_id.auth_ids:
                if auth.type == 'retention' and auth.active == True:
                    res['value']['auth_ret_id'] = auth.id        
        if res1:
            res['value']['auth_inv_id'] = res1[0]
        else:
            res['value']['auth_inv_id'] = False
            
        return res

    def _check_inv_auth(self, cr, uid, ids):
        def get_date(date=time.strftime('%Y-%m-%d'), format='%Y-%m-%d'):
            return datetime.datetime.strptime(date, format)
        for inv in self.browse(cr, uid, ids):
            if inv.type == 'in_invoice' and inv.type in ['in_invoice', 'in_refund']:
                if inv.type == 'in_invoice' and inv.amount_untaxed >= 1000 and not len(inv.payment_method_ids):
                    raise osv.except_osv('ATS', 'El valor de la Base Imponible supera los $1000, por favor ingrese por lo menos un metodo de pago.')
                if inv.auth_inv_id.expiration_date and get_date(inv.auth_inv_id.expiration_date) < get_date(inv.date_invoice):
                    raise osv.except_osv('AUTORIZACION','La autorizacion' + inv.auth_inv_id.name + ' de la factura ' + str(inv.number_inv_supplier) + ' del proveedor ' + inv.partner_id.name + ' no esta activa para la fecha ' + inv.date_invoice)
                if inv.auth_inv_id.doc_type != 'custom':
                    continue
                value = int(inv.number_inv_supplier)
                start = int(inv.auth_inv_id.num_start)
                end = int(inv.auth_inv_id.num_end)
                if value < start or value > end:
                    raise osv.except_osv('AUTORIZACION', 'La autorizacion ' + inv.auth_inv_id.name + ' de la factura ' + str(inv.number_inv_supplier) + 
                                         ' del proveedor ' + inv.partner_id.name + ' no concuerda con el numero de inicio ' + str(inv.auth_inv_id.num_start) + 
                                         ' y el numero de fin ' + str(inv.auth_inv_id.num_end) + ' de la autorizacion')
        return True
    
    def _check_ret_pendiente(self, cr, uid, ids, name, args, context):
        res = {}
        objs = self.browse(cr, uid, ids)
        for item in objs:
            if item.requiere_retencion:
                if not item.ret_id:
                    res[item.id] = 1
                elif not item.ret_id.state == 'paid':
                    res[item.id] = 1
                else: 
                    res[item.id] = 0
            else:     
                res[item.id] = 0
        return res
    
    def _check_ret_anticipada_valida(self, cr, uid, ids, ret_id_id):
        res = {}
        objs = self.browse(cr, uid, ids)
        ret_id = self.pool.get('account.invoice.retention').browse(cr, uid, ret_id_id)
        for item in objs:
            for tax_inv_line in item.tax_line:
                econtro = False
                if tax_inv_line.tax_group not in ['ret_vat', 'ret_ir']:
                    break
                for tax_ret_line in ret_id.tax_line:
                    if  not tax_ret_line.invoice_id: 
                        if tax_inv_line.tax_code_id == tax_ret_line.tax_code_id:
                            if not tax_inv_line.base_code_id: 
                                if not tax_ret_line.base_code_id:
                                    aux = True
                            if aux or tax_inv_line.base_code_id == tax_ret_line.base_code_id : 
                                if tax_inv_line.tax_amount == tax_ret_line.amount:
                                    
                                    if tax_inv_line.base_amount == tax_ret_line.base:
                                        encontro = True
                                        break
                if not encontro:
                    raise osv.except_osv('Aviso',
                                         'No puede relacionar la factura con esta retención ya que los \
                                         impuestos aplicados o sus valores difieren de los calculados en la factura')
        return True     
    
    def _get_ret_mode(self, cr, uid, context):
        if 'type' in context.keys():
            print"type-invoice=%s"%type
            if context['type'] == 'in_invoice':
                return 1
            elif context['type'] == 'out_invoice':
                return 0

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()
    
    def _get_invoice_retention(self, cr, uid, ids, context=None):
        # busca si la retención relacionada a la factura cambió de estado y de ser asi verifica si está o no pendiente su
        # retención.
        result = {}
        objs = self.browse(cr, uid, ids)
        for obj in objs:
            
            for retention in self.pool.get('account.invoice.retention').browse(cr, uid, ids, context=context):
                for inv_tax_line in retention.tax_line:
                    result[inv_tax_line.invoice_id.id] = {'requiere_retencion':0}
                    if inv_tax_line.invoice_id.requiere_retencion and not retention.state == 'paid':
                        result[inv_tax_line.invoice_id.id]['requiere_retencion'] = 1
                    else:
                        result[inv_tax_line.invoice_id.id]['requiere_retencion'] = 0
        return result
    
    def onchange_get_ret_mod(self, cr, uid, ids, gen_ret_mode):
        if not gen_ret_mode:
            return {'value': {'ret_sin_fact':False, 'has_early_ret':False}}


    def onchange_ret_sin_fact(self, cr, uid, ids, ret_sin_fact):
        if ret_sin_fact:
            return {'value': {'gen_ret_mode':True, 'has_early_ret':False}}

    def onchange_has_early_ret(self, cr, uid, ids, has_early_ret):
        if has_early_ret:
            return {'value': {'gen_ret_mode':True, 'ret_sin_fact':False}}

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        """
        Now amount_total 
        """
        res = {}
        name = isinstance(name, list) and name or self._columns.keys()
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = dict((aux, 0.0) for aux in name + ['amount_untaxed', 'amount_tax'])
            for line in invoice.invoice_line:
                if invoice.type in ('out_invoice', 'out_refund'):
                    res[invoice.id]['amount_untaxed'] += round(line.price_subtotal, 2)
                else:
                    res[invoice.id]['amount_untaxed'] += line.price_subtotal
                
            for line in invoice.invoice_line:
                price_unit = line.price_unit
                discount_porcentage = line.discount / 100
                discount = price_unit * discount_porcentage
                if invoice.type in ('out_invoice', 'out_refund'):
                    res[invoice.id]['amount_discount'] += round(discount * line.quantity, 2)
                    res[invoice.id]['amount_subtotal'] += round(price_unit * line.quantity, 2)
                else:
                    res[invoice.id]['amount_discount'] += discount * line.quantity
                    res[invoice.id]['amount_subtotal'] += price_unit * line.quantity
                
            for line in invoice.tax_line:
                if line.tax_group == 'vat':
                    res[invoice.id]['amount_tax'] += line.amount
                    res[invoice.id]['t_bi_iva'] += line.base
                    res[invoice.id]['t_iva'] += line.amount
                    res[invoice.id]['baseretencion'] += line.amount 
                elif line.tax_group == 'vat0':
                    res[invoice.id]['t_b_0_iva'] += line.base
                elif line.tax_group == 'excvat':
                    res[invoice.id]['t_b_excenta_iva'] += line.base
                elif line.tax_group == 'novat':
                    res[invoice.id]['t_b_no_iva'] += line.base
                    res[invoice.id]['t_b_excenta_iva'] += line.base
                elif line.tax_group == 'no_ret_ir':
                    res[invoice.id]['t_b_excenta_ret_ir'] += line.base
                elif line.tax_group == 'ret_vat' or line.tax_group == 'ret_ir':
                    res[invoice.id]['requiere_retencion'] = 1
                    res[invoice.id]['amount_tax_retention'] += line.amount
                    if line.tax_group == 'ret_vat':
                        res[invoice.id]['t_ret_iva'] += line.amount
                        res[invoice.id]['amount_ret_vat'] += line.amount
                    elif line.tax_group == 'ret_ir':
                        res[invoice.id]['t_bi_ir'] += line.base
                        res[invoice.id]['t_ret_ir'] += line.amount
                        res[invoice.id]['amount_ret_ir'] += line.amount
                        
            if invoice.type in ["out_invoice", "out_refund"]:
                res[invoice.id]['amount_total'] = round(res[invoice.id].get('amount_tax', 0.0), 2) + round(res[invoice.id].get('amount_untaxed', 0.0), 2)
            else:
                res[invoice.id]['amount_total'] = res[invoice.id].get('amount_tax', 0.0) + res[invoice.id].get('amount_untaxed', 0.0) + res[invoice.id]['amount_tax_retention']
            res[invoice.id]['amount_pay'] = res[invoice.id].get('amount_tax', 0.0) + res[invoice.id].get('amount_untaxed', 0.0)
        return res    

    def _get_date_start_period(self, cr, uid, ids, field_name, args, context):
        res = {}
        for item in self.browse(cr, uid, ids):
            select_po_id = "SELECT purchase_id FROM purchase_invoice_rel WHERE invoice_id = %s" % str(item.id)
            cr.execute(select_po_id)
            po_id = cr.fetchone()
            #print "PURCHASE ORDER: %s" % po_id
            purchase_order_ids = self.pool.get('purchase.order').search(cr, uid, [('id', '=', po_id)])
            if purchase_order_ids:
                purchase_order = self.pool.get('purchase.order').browse(cr, uid, purchase_order_ids)
                purchase_order_line = purchase_order[0].order_line
#                for line in purchase_order_line:
#                    if line.payment_order_id:
#                        res[item.id] = line.payment_order_id.period_start_date
#                    else:
#                        res[item.id] = ''
            else:
                res[item.id] = ''
        return res
    
    def _get_date_end_period(self, cr, uid, ids, field_name, args, context):
         res = {}
         for item in self.browse(cr, uid, ids):
            select_po_id = "SELECT purchase_id FROM purchase_invoice_rel WHERE invoice_id = %s" % str(item.id)
            cr.execute(select_po_id)
            po_id = cr.fetchone()
            purchase_order_ids = self.pool.get('purchase.order').search(cr, uid, [('id', '=', po_id)])
            if purchase_order_ids:
                purchase_order = self.pool.get('purchase.order').browse(cr, uid, purchase_order_ids)
                purchase_order_line = purchase_order[0].order_line
#                for line in purchase_order_line:
#                    if line.payment_order_id:
#                        res[item.id] = line.payment_order_id.period_end_date
#                    else:
#                        res[item.id] = ''
            else:
                res[item.id] = ''
         return res
        
    def _get_payment_order(self, cr, uid, ids, field_name, args, context):
        res = {}
        for item in self.browse(cr, uid, ids):
            select_po_id = "SELECT purchase_id FROM purchase_invoice_rel WHERE invoice_id = %s" % str(item.id)
            cr.execute(select_po_id)
            po_id = cr.fetchone()
            purchase_order_ids = self.pool.get('purchase.order').search(cr, uid, [('id', '=', po_id)])
            if purchase_order_ids:
                purchase_order = self.pool.get('purchase.order').browse(cr, uid, purchase_order_ids)
                purchase_order_line = purchase_order[0].order_line
#                for line in purchase_order_line:
#                    if line.payment_order_id:
#                        res[item.id] = line.payment_order_id.type_o
#                    else:
#                        res[item.id] = ''
            else:
                res[item.id] = ''
        return res
    
    def _zfill (self, cr, uid, ids, field_name, args, context):
        """Completa el Número de Factura a 9 Digitos"""
        res = {}
        numero = ''
        for item in self.browse(cr, uid, ids):
            nro_factura = item.number_inv_supplier if item.type in ['in_invoice', 'in_refund'] else item.num_retention
            res[item.id] = nro_factura and str(nro_factura).zfill(9) or ''
        return res
    
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default = default.copy()
        
        default.update({'state':'draft',
                        'number':False,
                        'move_id':False,
                        'period_id':False,
                        'move_name':False,
                        'number_inv_supplier':False,
                        'num_retention':False,
                        'factura':False,
                        'auth_inv_id':False,
                        #'sale_invoices_id':False,
                        #'rate_calculate':False,
                        # Cuando se duplica debe volver a crear el comprobante de retencion
                        'ret_voucher': False,
                        'ret_voucher_id':False,
                        # Cuando se duplica debe generar diferido
                        'generate_deferred': False,
                        'deferred_id':False
                         })
        
        if 'date_invoice' not in default:
            default['date_invoice'] = False
        if 'date_due' not in default:
            default['date_due'] = False
        
        return super(account_invoice, self).copy(cr, uid, id, default, context)
    
    #===========================================================================
    # def onchange_number_retention(self, cr, uid, ids, num_retencion):
    #     
    #     for invoice in self.browse(cr, uid, ids):
    #         if num_retencion:
    #             self.pool.get('account.invoice.retention').write(cr, uid, invoice.ret_id.id, {'num_comprobante': num_retencion, 'name':str(num_retencion).zfill(7)})
    #     return True
    #===========================================================================
    
    def onchange_seller(self, cr, uid, ids, seller_id):
        # #print "seller_id", seller_id
        res = {'value':{}}
        if seller_id:
            for invoice in self.browse(cr, uid, ids):
                vendedor = self.pool.get('res.users').browse(cr, uid, seller_id).name
                res['value']['saleer'] = vendedor
        return res
    
    def action_sale_cuota(self, cr, uid, invoice, context=None):
        # #print "action_sale_cuota", invoice
        for item in self.browse(cr, uid, invoice):
            cr.execute("""
                        SELECT id, type, cuota_id, date_invoice, date_due 
                           FROM account_invoice 
                       WHERE id = %s""", (item.id,))
            for (id, type, cuota_id, date_invoice, date_due) in cr.fetchall():
                if not cuota_id and type in ['out_invoice', 'out_refund']:
                    cr.execute("""
                                   SELECT order_id 
                                       FROM sale_order_invoice_rel 
                                   WHERE 
                                       invoice_id =%s
                               """, (id,))
                    for (order_id) in cr.fetchall():
                        if order_id: 
                            cr.execute("""
                                SELECT id as cuota
                                    FROM sale_payment_term_line 
                                WHERE begin_date >= %s
                                    AND
                                        due_date <=%s
                                    AND
                                        payment_term_line_id = %s""", (date_invoice, date_due, order_id))
                            for (cuota) in cr.fetchall():
                                if cuota:
                                    # #print "entra"
                                    cr.execute("""UPDATE
                                                       account_invoice SET cuota_id=%s
                                                  WHERE
                                                      id=%s""", (cuota, id))
        return True
    
    
    """
    Obtiene la orden de compra relacionada a la factura.
    """
    def _get_purchase_order (self, cr, invoice, uid):
        res = {}
        
        select_po_id = "SELECT purchase_id FROM purchase_invoice_rel WHERE invoice_id = %s" % str(invoice.id)
        cr.execute(select_po_id)
        po_id = cr.fetchone()
        #print "PURCHASE ORDER: %s" % po_id
        purchase_order_ids = self.pool.get('purchase.order').search(cr, uid, [('id', '=', po_id)])
        return purchase_order_ids
        
        
        
        
        # for item in self.browse(cr, uid, ids):
        #    select_po_id = "SELECT purchase_id FROM purchase_invoice_rel WHERE invoice_id = %s" % str(item.id)
        #    cr.execute(select_po_id)
        #    po_id = cr.fetchone()
        #    #print "PURCHASE ORDER: %s" % po_id
        #    purchase_order_ids = self.pool.get('purchase.order').search(cr, uid, [('id', '=', po_id)])
        #    return purchase_order_ids
            # if purchase_order_ids:
            #    purchase_order = self.pool.get('purchase.order').browse(cr, uid, purchase_order_ids)
            #    purchase_order_line = purchase_order[0].order_line
#                for line in purchase_order_line:
#                    if line.payment_order_id:
#                        res[item.id] = line.payment_order_id.period_start_date
#                    else:
#                        res[item.id] = ''
            # else:
            #    res[item.id] = ''
    
    
    
    def action_asset_create(self, cr, uid, ids, context=None):
        return True
        
        #print "action_asset_create", ids
        
        asset_obj = self.pool.get('account.asset.asset')
        asset_line_obj = self.pool.get('account.asset.method')
        asset_hist_obj = self.pool.get('account.asset.history')
        res = {}
         
        for invoice in self.browse(cr, uid, ids, context=None):
            if invoice.type == 'in_invoice':
                type = 'purchase'
            elif invoice.type == 'out_invoice':
                type = 'sale'
            # #print "invoice", invoice
            dict_asset = {}
            method_ids = []
            method = 0
            method_name = ''
            line_name = ''
            name_activo = ''
            asset_id = 0
            asset_list = []
            date = invoice.date_invoice
            
            validation = False
            
            
            for line in invoice.invoice_line:
                activo = False
                if asset_obj:
                    print"asset_obj=%s"%asset_obj
                    activos = asset_obj.search(cr, uid, [('invoice_line_id', '=', line.id)])
                else:
                    activos = True
                        
                if activos:
                    continue 
                
                if line.product_id.asset_ok:
                    method = line.product_id.asset_method_type_id.id
                    code = line.product_id.asset_method_type_id.code
                    method_name = line.product_id.asset_method_type_id.name
                    activo = True
                elif line.product_id.control_chained_ok:
                    validation = True
                    method = line.product_id.asset_method_type_bsc_id.id
                    code = line.product_id.asset_method_type_bsc_id.code
                    method_name = line.product_id.asset_method_type_bsc_id.name
                    activo = True
                    
             
                if activo and method:
                    
                    type_ids = self.pool.get('account.asset.method.defaults').search(cr, uid, [('method_type', '=', method)])
                    jornaul_ids = self.pool.get('account.journal').search(cr, uid, [('type', '=', 'general'),
                                                                                    ('name', 'ilike', 'activos fijos')])
                    if not jornaul_ids:
                        raise osv.except_osv(_('Alerta !'), _('¡Por favor! Cree un diario: \"Activos Fijos\"'))
                    else:
                        for j in self.pool.get('account.journal').browse(cr, uid, jornaul_ids):
                            journal = j.id
                            
                    # purchase_ids = self.pool.get('purchase.order').search(cr, uid, [('invoice_id', '=', invoice.id)])
                    purchase_ids = self._get_purchase_order(cr, invoice, uid)
                    if purchase_ids:
                        for purchase in self.pool.get('purchase.order').browse(cr, uid, purchase_ids):
                            purchase_order_id = purchase.id
                            date = purchase.date_order or False
                    else:
                        purchase_order_id = False
                            
                    if type_ids:
                        for m in self.pool.get('account.asset.method.defaults').browse(cr, uid, type_ids):
                            # if not m.asset_category.parent_id:#Tomo siempre el padre
                            category_id = m.asset_category and m.asset_category.id or False  
                            account_asset_id = m.account_asset_id and m.account_asset_id.id or False
                            account_expense_id = m.account_expense_id and m.account_expense_id.id or False
                            account_actif_id = m.account_expense_id and m.account_actif_id.id or False
                            period_id = asset_line_obj._get_next_period(cr, uid, context={})
                            life = m.method_delay or 0
                            #=============================================
                            # Se crea el detalle del activo fijo (asset_method)
                            #============================================
                            dict_asset_line = {
                                               'name':line_name,
                                               'asset_id':asset_id,
                                               'method_type':method,
                                               'account_asset_id':account_asset_id,
                                               'account_expense_id':account_expense_id,
                                               'account_actif_id':account_actif_id,
                                               'journal_id':journal or False,
                                               'period_id':period_id,
                                               'method':'linear',
                                               'value_total':line.price_subtotal,
                                               'life':life or False,
                                               'control_chained':validation,
                                               # state':'open'
                            }
                            linea = (0, 0, dict_asset_line)
                            method_ids.append(linea)
                            
                    if not type_ids:
                        raise osv.except_osv(_('Warning !'), _('¡Por favor! Configure los valores por defecto de este método en:\n'\
                                        'Gestion Financiera\Configuración\Activos\Valores por Defecto metodo del activo.\n'\
                                        'Para este método: ' + method_name.encode('utf-8') + '.'))
                    if line.description:
                        name_activo += line.name
                    
                    #===========================================================
                    # Creamos el activo en la tabla account.asset
                    #===========================================================
                    dict_asset = {
                                  'method_type':method,
                                  'name':str(line.product_id.name.encode('utf-8')) + ' / ' + name_activo,
                                  'purchase_order_id':purchase_order_id or False,
                                  'invoice_line_id':line.id,
                                  'amount_total':line.price_subtotal,
                                  'amount_residual':line.price_subtotal,
                                  'partner_id':invoice.partner_id.id,
                                  'category_id':category_id,
                                  'date':date or invoice.date_invoice,
                                  'invoice_id':invoice.id,
                                  'method_ids':method_ids,
                    }
                    
                    asset_id = asset_obj.create(cr, uid, dict_asset)
                    print"asset_id=%s"%asset_id
                    if asset_id:
                        ob_asset = asset_obj.browse(cr, uid, asset_id)
                        if not ob_asset.code:
                            raise osv.except_osv(_('Atencion !'), _('El modulo de Activos esta desactualizado por favor actualicelo para continuar.!'))
                        line_name += ob_asset.name + ' '
                        line_name += '(' + ob_asset.code + ') - '
                        line_name += code
                        
        return True
    
    def action_generate_billing(self, cr, uid, ids, context=None):
        # #print 'ids', ids
        res = {}
        if not context:
            context = {}
        context['invoice'] = True
        order_billing_obj = self.pool.get('account.order.billing')
        subtotal = 0.00
        band = False
        for item in self.browse(cr, uid, ids):
            for il in item.invoice_line:
                if il.product_id.deferred_ok:
                    band = True
                    break
            if item.type in ('out_invoice', 'out_refund') and band:
                o = False
                billing = []
                date_from = False
                date_to = False
                if item.type == 'out_invoice':
                    sql = "SELECT order_id FROM sale_order_invoice_rel "\
                        "WHERE invoice_id =" + str(item.id)
                
                    cr.execute(sql)
                    order = [x[0] for x in cr.fetchall()]
                
                    if order:
                        o = self.pool.get('sale.order').browse(cr, uid, order)[0]
                
                billing = order_billing_obj.search(cr, uid, [('invoice_id', '=', item.id)])
                
                # if item.type=='out_refund':Preguntar la nota de credito hasta cuando se genera el diferido
                #========================================================================================
                # El diferido se lo realiza por el valor total de los productos diferidos de la Factura 
                #========================================================================================
                for il in item.invoice_line:
                    if il.product_id.deferred_ok:
                        subtotal += il.price_subtotal
                
                if self.is_date(item.date_invoice):
                    date_from = item.date_invoice
                else:
                    date_from = time.strftime('%Y-%m-%d')
                
                if not item.date_to_deferred:
                    raise osv.except_osv(_('Aviso !'), _('Necesita Poner una Fecha fin del diferido en la Pestaña Ingresos Diferidos para continuar!'))
                
                if o and o.lease_end_date and self.is_date(o.lease_end_date):
                    date_to = o.lease_end_date
                
                if not date_to:
                    date_to = item.date_to_deferred
                
                val = {
                       'name':o and o.name or item.origin or '/',
                       'type':'sale',
                       'date_order':o and o.date_order or item.date_invoice or time.strftime('%Y-%m-%d'),
                       'sin_impuesto':subtotal,
                       'sale_order_id':o and o.id or False,
                       'lease_start_date':item.date_invoice or item.date_from_deferred or time.strftime('%Y-%m-%d'),
                       'lease_end_date':item.date_to_deferred,
                       'number_contract':o and o.number_contract or '',
                       'value_contract':o and o.value_contract or 0.00,
                       'invoice_id':item.id,
                       'num_invoice':item.num_retention,
                       'partner_id':item.partner_id.id,
                       'origin':item.origin or '',
                       'invoice_type':item.type,
                       # 'invoice_ids':[(0,0,int(item.id))],
                       }
                if not billing:
                    order_bill = order_billing_obj.create(cr, uid, val, context=context)
                    order_billing_obj.action_deferred(cr, uid, [int(order_bill)], context=context)
                else:
                    order_billing_obj.unlink(cr, uid, billing)
                    order_bill = order_billing_obj.create(cr, uid, val, context=context)
                    order_billing_obj.action_deferred(cr, uid, [int(order_bill)], context=context)
                
                self.write(cr, uid, ids, {'generate_deferred':True, 'deferred_id':order_bill,
                                          'date_from_deferred':item.date_invoice,
                                          'date_to_deferred':item.date_to_deferred,
                                          })
            #===================================================================
            # Diferido de los Gastos
            #===================================================================
            elif item.type in ('in_invoice', 'in_refund'):
                billing = []
                po = False
                band = False
                select_po_id = "SELECT purchase_id FROM purchase_invoice_rel WHERE invoice_id = %s" % str(item.id)
                cr.execute(select_po_id)
                po_id = cr.fetchone()

                purchase = False
                if po_id:
                    sql = "SELECT id FROM purchase_order "\
                            "WHERE id = %s" % str(po_id[0])
                    #print "sql", sql
                    cr.execute(sql)
                    purchase = [x[0] for x in cr.fetchall()]

                if purchase:
                    po = self.pool.get('purchase.order').browse(cr, uid, purchase)[0]
                    billing = order_billing_obj.search(cr, uid, [('purchase_order_id', '=', purchase[0])])
                    #print "orden billing", billing

#                 if purchase and len(purchase) > 1:
                    #print 'mas de 2', len(purchase)

                if not item.from_invoice:  # Diferido por linea de Factura
                    for il in item.invoice_line:  # Ve los productos diferidosy genera el documento y luego la tabla del diferido
                        if il.product_id.deferred_ok:
                            band = True  # Tiene productos Diferidos
                            break
                    if not item.date_deferred and band:
                        raise osv.except_osv(_('Aviso!'), _('Necesita Poner una Fecha fin del diferido en la Pestaña Gastos Diferidos para continuar!'))
                    if band:
                        for il in item.invoice_line:  # Diferido por linea de Factura
                            
                            if il.product_id.deferred_ok:
                                
                                val = {
                                       'name':po and po.name or item.name or str(item.number_inv_supplier) or '/',
                                       'type':'purchase',
                                       'date_order':po and po.date_order or item.date_invoice or time.strftime('%Y-%m-%d'),
                                       'proveedor':item.partner_id and item.partner_id.name,
                                       'sin_impuesto':il.price_subtotal,
                                       'purchase_order_id':po and po.id or False,
                                       'lease_start_date':item.date_invoice,
                                       'lease_end_date':item.date_deferred,
                                       'invoice_id':item.id,
                                       'invoice_line':il.id,
                                       'partner_id':item.partner_id and item.partner_id.id,
                                       'origin':il.origin,
                                       'invoice_type':item.type
                                       }
                                if not billing:
                                    order_bill = order_billing_obj.create(cr, uid, val)
                                    order_billing_obj.action_deferred(cr, uid, [int(order_bill)], context=context)
                                else:
                                    #print "no debe entrar por que ya borre si cambia a borrador la factura"
                                    order_billing_obj.unlink(cr, uid, billing)
                                    order_bill = order_billing_obj.create(cr, uid, val)
                                    order_billing_obj.action_deferred(cr, uid, [int(order_bill)], context=context)
                if item.from_invoice:  # A partir del monto de la Factura
                    if not item.date_deferred:
                        raise osv.except_osv(_('Aviso !'), _('Necesita Poner una Fecha fin del diferido en la Pestaña Gastos Diferidos para continuar!'))
                    subtotal = item.amount_untaxed
                    val = {
                           'name':po and po.name or item.name or str(item.number_inv_supplier) or '/',
                           'type':'purchase',
                           'date_order':po and po.date_order or item.date_invoice or time.strftime('%Y-%m-%d'),
                           'proveedor':item.partner_id and item.partner_id.name,
                           'sin_impuesto':subtotal,
                           'purchase_order_id':po and po.id or False,
                           'lease_start_date':item.date_invoice,
                           'lease_end_date':item.date_deferred,
                           'invoice_id':item.id,
                           'partner_id':item.partner_id and item.partner_id.id,
                           'origin':item.origin or '',
                           'invoice_type':item.type
                           }
                    if not billing:
                        order_bill = order_billing_obj.create(cr, uid, val)
                        order_billing_obj.action_deferred(cr, uid, [int(order_bill)], context=context)
                    else:
                        #print "no debe entrar diferido desde factura"
                        order_billing_obj.unlink(cr, uid, billing)
                        order_bill = order_billing_obj.create(cr, uid, val)
                        order_billing_obj.action_deferred(cr, uid, [int(order_bill)], context=context)
                        
        return True
    
    def _format_date(self, date_from):
        if date_from:
            campos = date_from.split('-')
            date_to = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date_to
    
    def is_date(self, name):
        # #print 'name', name
        if name:
            campos = name.split('-')
            if len(campos) == 3:
                return True
    
    def _get_start(self, primera_fecha):
        # #print "_get_start", primera_fecha
        current_date = self._format_date(primera_fecha)
        carry, new_month = divmod(current_date.month - 1 + 1, 12)
        new_month += 1
        dp = calendar.monthrange(current_date.year, new_month)
        current_date = current_date.replace(year=current_date.year + carry, month=new_month, day=dp[1])
        return current_date.strftime('%Y-%m-%d')
    
    def onchange_is_deferred(self, cr, uid, ids, is_deferred):
        #print "onchange_is_deferred", is_deferred
        res = {'value':{}}
        if not is_deferred:
            res['value']['from_invoice'] = False
        return res
    
    def onchange_date_invoice(self, cr, uid, ids, date_invoice):
        #print "onchange_date_invoice", date_invoice
        res = {'value':{}}
        res['value']['date_from_deferred'] = date_invoice
        period_id = self.pool.get('account.period').find(cr, uid, date_invoice)
        res['value']['period_id'] = date_invoice and period_id and period_id[0] or False
        return res
    
    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line.price_subtotal',
        'move_id.line_id.account_id.type',
        'move_id.line_id.amount_residual',
        'move_id.line_id.amount_residual_currency',
        'move_id.line_id.currency_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids.invoice.type',
    )
    def _compute_residual(inv):
        cur_obj = inv.env['res.currency']
        amount_pay = 0.00
        if inv.reconciled: 
            inv.residual = 0.0
            return
        inv_total = inv.amount_total
        if inv.type in ('out_invoice', 'in_refund'):
            for lines in inv.payment_ids:
                "Payments IDS %s" % lines
                inv_total += round(lines.debit or 0.00, 2) - round (lines.credit or 0.00, 2)
                print" inv_total=%s"% inv_total
        else:
            for lines in inv.move_id.line_id:
                inv_total -= (lines.debit or 0.00) - (lines.credit or 0.00)
        
        result = inv_total
           
        if inv.type in ('in_invoice', 'in_refund'): 
            inv.residual = inv.currency_id.round(result)
            print" inv.residual=%s"% inv.residual
        else:
            inv.residual = result
    
    _columns = {
#         'residual': fields.function(_amount_residual, method=True, digits_compute=dp.get_precision('Account'), string='Residual',
#             store={
#                  'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['origin','invoice_line', 'move_id'], 50),
#                  },
#             help="Remaining amount due."),
        'amount_untaxed': fields.function(_amount_all, method=True, digits=(16, 2), string='Untaxed',
                                          store={
                                              'account.invoice': (lambda self, cr, uid, ids, c={}: ids, None, 20),
                                              'account.invoice.tax': (_get_invoice_tax, None, 20),
                                              'account.invoice.line': (_get_invoice_line, None, 20),
                                              },
                                          multi='all'),
        'amount_tax': fields.function(_amount_all, method=True, digits=(16, 2), string='Tax',
                                      store={
                                          'account.invoice': (lambda self, cr, uid, ids, c={}: ids, None, 20),
                                          'account.invoice.tax': (_get_invoice_tax, None, 20),
                                          'account.invoice.line': (_get_invoice_line, None, 20),
                                          },
                                      multi='all'),
        'amount_total': fields.function(_amount_all, method=True, digits=(16, 2), string='Total a Pagar',
                                        store={
                                            'account.invoice': (lambda self, cr, uid, ids, c={}: ids, None, 20),
                                            'account.invoice.tax': (_get_invoice_tax, None, 20),
                                            'account.invoice.line': (_get_invoice_line, None, 20),
                                            },
                                        multi='all'),
        'amount_ret_ir': fields.function(_amount_all, method=True, readonly=True , digits=(16, 2), string='Monto Ret. IR', help='Monto de retención de IR aplicada por el cliente',
                                                 store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                                          'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                                          'account.invoice.line' : (_get_invoice_line, None, 20),
                                                          }, multi='all'),
        'amount_ret_vat': fields.function(_amount_all, method=True, readonly=True , digits=(16, 2), string='Monto Ret. IVA', help='Monto de retención de IVA aplicada por el cliente',
                                                 store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                                          'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                                          'account.invoice.line' : (_get_invoice_line, None, 20),
                                                          }, multi='all'),
        'amount_tax_retention' : fields.function(_amount_all, method=True, digits=(16, 2), string='Total Retención', help='Total de retención realmente aplicado.',
                                                 store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                                          'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                                          'account.invoice.line' : (_get_invoice_line, None, 20),
                                                          }, multi='all'),
        'amount_pay' : fields.function(_amount_all, method=True, digits=(16, 2), string='Total',
                                       store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                                'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                                'account.invoice.line' : (_get_invoice_line, None, 20),
                                                }, multi='all'),
        'amount_discount': fields.function(_amount_all, method=True, digits=(16, 2), string='Descuento',
                                          store={
                                              'account.invoice': (lambda self, cr, uid, ids, c={}: ids, None, 20),
                                              'account.invoice.tax': (_get_invoice_tax, None, 20),
                                              'account.invoice.line': (_get_invoice_line, None, 20),
                                              },
                                          multi='all'),
        'amount_subtotal': fields.function(_amount_all, method=True, digits=(16, 2), string='Subtotal',
                                          store={
                                              'account.invoice': (lambda self, cr, uid, ids, c={}: ids, None, 20),
                                              'account.invoice.tax': (_get_invoice_tax, None, 20),
                                              'account.invoice.line': (_get_invoice_line, None, 20),
                                              },
                                          multi='all'),
        'baseretencion' : fields.function(_amount_all, method=True, digits=(16, 2), string='B.R.I%',
                                  store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                           'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                           'account.invoice.line' : (_get_invoice_line, None, 20),
                                           }, multi='all'),
                
        #'num_retencion':fields.char('Número Retención', size=100),
        'num_retencion':fields.related('ret_id', 'num_comprobante', string='Número Retención', type='char', size=30),
        'num_retention' : fields.char('Num. Retencion', size=32, readonly=True, states={'draft': [('readonly', False)]}),
        'number_inv_supplier' : fields.integer('Número de Factura', help='Número de Factura de Proveedor'),
#         'nro_completo':fields.function(_zfill, string='Nro. Factura', type='char', method=True, store=False, size=11),
        'factura': fields.function(_zfill, method=True, type='char', size=16, string='Nro. Factura',
                                   store={_name: (lambda self, cr, uid, ids, *a: ids, None, 10)}),
#         'factura':fields.char('Nro.Factura', size=15, select=True),
        
        'auth_inv_id' : fields.many2one('account.authorisation', 'Aut. de Factura', help='Autorizacion del SRI para la factura del proveedor',
                                        readonly=True, states={'draft': [('readonly', False)]}),
                
        'auth_ret_id' : fields.many2one('account.authorisation', 'Aut. de Retencion', help='a)Factura de Compra: Autorizacion del SRI para retencion de la empresa.\nb)Factura de Venta: Autorización del SRI para facturas de venta de la empresa',
                                        readonly=True, states={'draft': [('readonly', False)],
                                                               'proforma2': [('readonly', False)]}),
                
        'type_document': fields.char('Tipo de Comp. de Venta', size=40, readonly=True, states={'draft': [('readonly', False)]}),
        
        'partner_payment':fields.char('Pago', size=100, readonly=True,
                                      help='Tipo de Pago del Proveedor: Cuenta Bancaria, Cheque Empresa, Efectivo, Tarjeta de Credito, Canje.\n'\
                                      'Opcion que se configura en el campo Empresa pestaña de Contabilidad - Forma de Pago'),
                
        'invoice_payment':fields.selection((('s/f', ''),
                                            ('DINERS', 'T.C. Diners Club'),
                                            ('AMERICAN', 'T.C. American Express'),
                                            ('CANJE', 'Canje')), 'Pagar con'),
        
        
        't_bi_iva' : fields.function(_amount_all, method=True, digits=(16, 2), string='B.I. IVA',
                                     store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                              'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                              'account.invoice.line' : (_get_invoice_line, None, 20),
                                              }, multi='all'),
        't_iva' : fields.function(_amount_all, method=True, digits=(16, 2), string='IVA',
                                  store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                           'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                           'account.invoice.line' : (_get_invoice_line, None, 20),
                                           }, multi='all'),
        't_b_excenta_iva' : fields.function(_amount_all, method=True, digits=(16, 2), string='B.I. Excenta de IVA',
                                            store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                                     'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                                     'account.invoice.line' : (_get_invoice_line, None, 20),
                                                     }, multi='all'),
        't_b_0_iva' : fields.function(_amount_all, method=True, digits=(16, 2), string='B.I. 0% IVA',
                                            store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                                     'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                                     'account.invoice.line' : (_get_invoice_line, None, 20),
                                                     }, multi='all'),
        't_b_no_iva' : fields.function(_amount_all, method=True, digits=(16, 2), string='B.I. No IVA',
                                            store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                                     'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                                     'account.invoice.line' : (_get_invoice_line, None, 20),
                                                     }, multi='all'),
        't_ret_iva' : fields.function(_amount_all, method=True, digits=(16, 2), string='Ret. IVA',
                                      store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                               'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                               'account.invoice.line' : (_get_invoice_line, None, 20),
                                               }, multi='all'),
        't_bi_ir' : fields.function(_amount_all, method=True, digits=(16, 2), string='B.I. de Ret. IR',
                                    store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                             'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                             'account.invoice.line' : (_get_invoice_line, None, 20),
                                             }, multi='all'),
        't_ret_ir' : fields.function(_amount_all, method=True, digits=(16, 2), string='Ret. IR',
                                     store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                              'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                              'account.invoice.line' : (_get_invoice_line, None, 20),
                                              }, multi='all'),
        't_b_excenta_ret_ir' : fields.function(_amount_all, method=True, digits=(16, 2), string='B. Excenta de Ret. IR',
                                               store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                                        'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                                        'account.invoice.line' : (_get_invoice_line, None, 20),
                                                        }, multi='all'),
                
        'tipo_factura':fields.selection((('invoice', 'Factura'),
                                         ('purchase_liq', 'Liquidación de Compra'),
                                         ('sales_note', 'Nota de Venta'),
                                         ('anticipo', 'Anticipo'),
                                         ('ticket_aereo', 'Ticket aereo'),
                                         ('alicuota', 'Alícuotas'),
                                         ('gas_no_dedu', 'Gastos No Deduci'),
                                         ('reembolso', 'Reembolso de gasto'),
                                         ('gasto_viaje', 'Gasto de Viaje'),
                                         ('gasto_deducble', 'Gasto deducible sin Factura'),
                                         ('doc_inst_est', 'Doc Emitido Estado'),
                                         ('gasto_financiero', 'Gastos Financieros')), 'Comprobante', select=True),
        # 'num_ret_cliente':fields.char('Num. Interno de Ret.', size=32, select=True, readonly=True, help='Número interno de registro de la retención de cliente'),
        # debe cambiarse por una relacion al objeto retencion       
        'ret_id': fields.many2one('account.invoice.retention', 'Num. Interno de Ret', states={'proforma': [('readonly', True)],
                                                                                              'proforma2': [('readonly', True)],
                                                                                              'open': [('readonly', False)],
                                                                                              'paid': [('readonly', True)],
                                                                                              'cancel': [('readonly', True)]},
                                  help='Número interno de registro de la retención de cliente'),
        # 'move_ret_id': fields.many2one('account.move', 'Asiento de Ret.', readonly=True, help="Enlace al asiento de Retención generado."),
        'gen_ret_mode':fields.boolean('Una retención por factura', readonly=True , states={'draft': [('readonly', True)]},
                                      help='Si selecciona la casilla, la retención será generada automáticamente y vinculada con la factura seleccionada, usando para ello los valores mostrado en Información, la retención se vincula con una sola factura. \n (Recomendado: seleccionar para facturas de compra)\nCaso contario, si no selecciona la casilla, el sistema le permitirá asociar más de una factura a la retención generada.'),
        'ret_sin_fact':fields.boolean('Retención a partir de factura borrador', readonly=True , states={'draft': [('readonly', True)]},
                                      help='Si selecciona la casilla, el sistema le permitirá generar una retención aun cuando la factura este en estado borrador. \nEste método es más útil cuando se tiene una copia de la factura con la cual emitir la retención.'),

        'has_early_ret':fields.boolean('Retención anticipada', readonly=True , states={'draft': [('readonly', True)]},
                                      help='Si selecciona la casilla, el sistema le permitirá relacionar esta factura con una retención previamente registrada (Anticipada)'),

        
        'requiere_retencion' : fields.function(_amount_all, string='Requiere retención', readonly=True, method=True, type='boolean',
                                               store={'account.invoice' : (lambda self, cr, uid, ids, c={}:ids, None, 20),
                                                        'account.invoice.tax' : (_get_invoice_tax, None, 20),
                                                        'account.invoice.line' : (_get_invoice_line, None, 20),
                                                        }, multi='all', help="Es verdadero cuando la factura posee un impuesto de tipo retención."),
        'retencion_pendiente' : fields.function(_check_ret_pendiente, string='Retención Pendiente', readonly=True , method=True, type='boolean',
                                                help="Es verdadero cuando la factura requiere una retención pero ésta aun no ha sido creada o ejecutada.", store={'account.invoice.retention':(_get_invoice_retention, None, 20)}),
        'start_date_period' : fields.function(_get_date_start_period, string="Fecha de Inicio", method=True, type='date', help="Fecha de inicio del periodo de pago de la factura", store=False),
        'end_date_period' : fields.function(_get_date_end_period, string="Fecha de Fin", method=True, type='date', help="Fecha de fin del periodo de pago de la factura", store=False),
        'type_payment_order':fields.function(_get_payment_order, string="Tipo Orden Pago", method=True, type='char', help="Tipo de Orden de pago", store=False),
        # Aumento el campo de relacion con el comprobante de retencion *EM
        'ret_voucher_id':fields.many2one('account.invoice.retention.voucher', 'Retencion Cliente', readonly=True),
        'ret_voucher':fields.boolean('Comprobante de Retencion'),
        'code_advance_liq':fields.char('Doc. Origen', size=32, help='Codigo del documento', required=False, readonly=True),
        # 'fine_id':fields.many2one('account.inv.fine', 'Interes de Mora', help='Multa aplicada en caso de mora'),
        'days_later':fields.integer('Dias Plazo', help='Numero de dias de plazo registrado en Ventas'),
        'order_total_billing':fields.float('Total Orden Facturación', help='Total de Orden de facturacion'),
        'trade_reference':fields.char('Referencia Comercial', size=100),
        'opc_billing':fields.char('OPC', size=15),
        'number_contract_billing':fields.char('Contrato', size=20),
        'value_payment':fields.float('Valor Forma Pago %', help='Valor en porcentaje de la Forma de pago'),
        'value_payment_text':fields.char('Desc Form Pago', help='Descripcion de la forma de pago. Se imprime en la Factura', size=128),
        'saleer':fields.char('Vendedor', size=100, readonly=True, states={'draft':[('readonly', False)]}),
        'saleer_id':fields.many2one('res.users', 'Vendedor', select=True, readonly=True,
                                    states={'draft':[('readonly', False)]}, domain=[('groups_id', 'in', [21, 20])]),
        'mount':fields.float('Monto', digits=(12, 2)),
        
        # 'sitio': fields.char('Sitio', size=100),
        # 'cuota_id':fields.many2one('sale.payment.term.line','Cuota'),
        
        'account_deferred':fields.many2one('account.account', 'Cuenta Diferido', domain=[('parent_id', '=', 1266)]),  # Cuenta de Gastos Diferidos
        
        'is_deferred':fields.boolean('Gasto Diferido', help='Si marca esta opcion debe ingresar la fecha fin del diferido. Caso contrario se crea un documento en borrador y '\
                                     'luego tendra que crear la tabla de diferido. Todo este caso se da si existen productos diferidos en la factura'),
        'from_invoice':fields.boolean('A partir de la Factura', help='Marque esta opcion si desea generar el diferido a partir del total de la Factura. '\
                                      'Si no marca el sistema al momento de validar la factura busca los productos diferidos de la factura y crea el diferido'),
        
        'date_deferred':fields.date('Fecha Fin Diferido', help='Ponga aqui la fecha final del diferido. Tenga encuenta que la fecha Incial'\
                                                                ' del diferido es la Fecha de la Factura.'),
        
        'deferred_id':fields.many2one('account.order.billing', 'Diferidos', help='Diferido de Venta', readonly=True),
        
        'date_from_deferred':fields.date('Inicio Diferido', readonly=True, states={'draft':[('readonly', False)],
                                                                                  'open':[('readonly', False)],
                                                                                  'paid':[('readonly', False)],
                                                                                  'proforma2':[('readonly', False)]},
                                         help='Fecha Incio del Diferido, es la fecha de la factura'),
        'date_to_deferred':fields.date('Fin Diferido', readonly=True, states={'draft':[('readonly', False)],
                                                                                        'open':[('readonly', False)],
                                                                                        'paid':[('readonly', False)],
                                                                                        'proforma2':[('readonly', False)]},
                                       help='Fecha fin de contrato'),
        'generate_deferred': fields.boolean('Diferido Pendiente', readonly=True, states={'draft':[('readonly', False)],
                                                                                         'open':[('readonly', False)],
                                                                                         'paid':[('readonly', False)],
                                                                                         'proforma2':[('readonly', False)]}, select=True,
                                            help='Se genero el diferido de Venta'),
        
        'create_date': fields.datetime('Date Created', readonly=True, select=True),
        
        'comment': fields.text('Additional Information', readonly=True, states={'draft':[('readonly', False)]}),
               
        'state': fields.selection([
            ('draft', 'Draft'),
            ('proforma', 'Pro-forma'),
            ('proforma2', 'Pro-forma'),
            ('open', 'Open'),
            ('paid', 'Paid'),
            ('cancel', 'Anulado')
            ], 'State', select=True, readonly=True,
            help=' * The \'Draft\' state is used when a user is encoding a new and unconfirmed Invoice. \
            \n* The \'Pro-forma\' when invoice is in Pro-forma state,invoice does not have an invoice number. \
            \n* The \'Open\' state is used when user create invoice,a invoice number is generated.Its in open state till user does not pay invoice. \
            \n* The \'Paid\' state is set automatically when invoice is paid.\
            \n* The \'Cancelled\' state is used when user cancel invoice.'),

        'cod_sustento':fields.selection([
        	    ('00', ' Casos especiales cuyo sustento no aplica en las opciones anteriores.'),
        	    ('01', ' Crédito Tributario para declaración de IVA (servicios y bienes distintos de inventarios y activos fijos)'),
        	    ('02', ' Costo o Gasto para declaración de IR (servicios y bienes distintos de inventarios y activos fijos)'),
        	    ('03', 'Activo Fijo - Crédito Tributario para declaración de IVA'),
        	    ('04', 'Activo Fijo - Costo o Gasto para declaración de IR'),
        	    ('05', 'Liquidación Gastos de Viaje, hospedaje y alimentación Gastos IR (a nombre de empleados y no de la empresa)'),
        	    ('06', 'Inventario - Crédito Tributario para declaración de IVA'),
        	    ('07', 'Inventario - Costo o Gasto para declaración de IR'),
        	    ('08', 'Valor pagado para solicitar Reembolso de Gasto (intermediario)'),
        	    ('09', ' Reembolso por Siniestros'),
                ('10', ' Distribución de Dividendos, Beneficios o Utilidades'),
        	], 'Codigo Sustento'),
        
        'direccion_factura':fields.char('Direccion de facturacion', size=100),
        #NUEVO ATS (INFORMACION DE PAGO)
        'payment_mode': fields.selection([('local', 'Local'), ('ext', 'Exterior')], 'Detalle de pago', required=True),
        'payment_country_id': fields.many2one('res.country', 'País al que se efectuó el pago'),
        'double_taxation': fields.boolean('¿Aplica convenio de doble tributación?'),
        'payment_retention': fields.boolean('¿Pago sujeto a retención en aplicación de la norma legal?'),
        'payment_method_ids':fields.many2many('account.invoice.payment.method', 'invoice_method_rel', 'invoice_id', 'method_id', 'Formas de pago'),
        'detalle_reembolso_ids':fields.one2many('account.invoice.reembolso.line', 'invoice_id', 'Detalle de reembolso')
    }
    _defaults = {
        'type_document':lambda * a:'Factura',
        'auth_ret_id': _get_auth_retention,
        # 'tipo_factura': lambda * b:'invoice',
        'tipo_factura': _get_tipo_factura,
        'gen_ret_mode' :1,# _get_ret_mode,#linea modificada para generar retencion con fac desde pedido compra
        'ret_sin_fact': lambda * c:0,
        'ret_voucher': lambda * c:0,
#         'nro_completo':lambda * c:0,
        'is_deferred':lambda * c:False,
        'generate_deferred':lambda * c:False,
        'payment_mode': lambda *a: 'local',
        'saleer_id': lambda self, cr, uid, context: uid,
        #'requiere_retencion':1
    }
    
    def _check_num_retention(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids):
            if obj.num_retention:
                if self.search(cr, uid, [('id', '!=', obj.id), ('num_retention', '=', obj.num_retention)]):
                    return False
        return True

    _constraints = [
        (_check_inv_auth, 'El numero de factura ingresado no concuerda con los valores la autorizacion del proveedor', ['number_inv_supplier']),
        (_check_num_retention, u'El número de la factura debe ser único', ['Preimpreso'])
    ]

    _sql_constraints = [
        ('unique_num', 'unique(number_inv_supplier, partner_id)', 'El numero de factura es unico.'),
    ]
account_invoice()

class account_invoice_reembolso_line(osv.osv):
    _name = 'account.invoice.reembolso.line'
    _columns = {
        'invoice_id': fields.many2one('account.invoice', 'Factura', required=True, ondelete='cascade'),
        'partner_id': fields.many2one('res.partner', 'Proveedor', required=True, domain=[('supplier', '=', True)]),
        'tipo_comprobante': fields.selection([('01', 'Factura.'),
                                              ('02', 'Nota de venta.'),
                                              ('03', 'Liquidación de compras de bienes o prestación de servicios'),
                                              ('04', 'Nota de crédito.'),
                                              ('05', 'Nota de débito.'),
                                              ('08', 'Boletos o entradas a espectáculos públicos.'),
                                              ('09', 'Tickets o valets emitidos por máquinas registradoras.'),
                                              ('11', 'Pasajes emititdos por empresas de aviación.'),
                                              ('12', 'Documentos emititdo por insitutiones financieras.'),
                                              ('15', 'Comprobante de venta emitido en el exterior.'),
                                              ('19', 'Documentos de pago de cuotas o aportes.'),
                                              ('20', 'Documentos por servicios administrativos emitidos por instituciones del estado.'),
                                              ('21', 'Carta de Porte Aereo'),
                                              ('41', 'Carta de deporte aereo.'),
                                              ('42', 'Documento agente de retención presuntiva.'),
                                              ('43', 'Liquidación para explotación y exploración de hidrocarburos.'),
                                              ('45', 'Liquidación de medicina prepagada.'),
                                              ('47', 'Nota de crédito por reembolso emitida por intermediarios.'),
                                              ('48', 'Nota de débito por reembolso emitido por intermediario.'),
                                              ('294', 'Liquidación de compras de bienes muebles usados'),
                                              ], 'Tipo de comprobante', required=True),
        'nro_autorizacion': fields.char('Número de autorización', size=64),
        'establecimiento': fields.char('Número de establecimiento', size=8),
        'pto_emision': fields.char('Punto de establecimiento', size=8),
        'number': fields.char('Número de comprobante', size=64),
        'date': fields.date('Fecha'),
        'base_imponible': fields.float('Base imponible', digits=(16,2)),
        'base_gravada': fields.float('Base gravada', digits=(16,2)),
        'base_no_gravada': fields.float('Base no gravada', digits=(16,2)),
        'monto_iva': fields.float('Monto I.V.A.', digits=(16,2)),
        'monto_ice': fields.float('Monto I.C.E.', digits=(16,2)),
    }
    
account_invoice_reembolso_line()

class account_invoice_line(osv.osv):
    
    _name = "account.invoice.line"
    _inherit = "account.invoice.line"
    _description = "Invoice line"
    
    def move_line_get(self, cr, uid, invoice_id, context=None):
        #print ' ************ move_line_get account_invoice_retentin    *********'
        res = []
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        if context is None:
            context = {}
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        company_currency = inv.company_id.currency_id.id

        for line in inv.invoice_line:
            # #print '  line ', line
            mres = self.move_line_get_item(cr, uid, line, context)
            #print ' mres mres ', mres
            if not mres:
                continue
            res.append(mres)
            tax_code_found = False
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id,
                    (line.price_unit * (1.0 - (line['discount'] or 0.0) / 100.0)),
                    line.quantity, line.product_id,
                    inv.partner_id)['taxes']:

                if inv.type in ('out_invoice', 'in_invoice'):
                    tax_code_id = tax['base_code_id']
                    tax_amount = line.price_subtotal * tax['base_sign']
                else:
                    tax_code_id = tax['ref_base_code_id']
                    tax_amount = line.price_subtotal * tax['ref_base_sign']

                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(self.move_line_get_item(cr, uid, line, context))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True

                res[-1]['tax_code_id'] = tax_code_id
                res[-1]['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, tax_amount, context={'date': inv.date_invoice})
                # #print ' res ****** ', res
        return res

    
    def move_line_get_item(self, cr, uid, line, context=None):
        
        #print ' move_line_get_item ******* ****'
        
        #logger = netsvc.Logger()
        price = line.price_subtotal
        account_id = line.account_id.id
        discount = False
        discount_id = False
        aapil = False
        inv = self.pool.get('account.invoice').read(cr, uid, line.invoice_id.id , ['type'])
        _logger.info('move_line_get_item %s' % (inv))
#         if inv['type'] in ('out_invoice', 'out_refund'):
#             if line.discount != 0:
#                 price = round (line.price_unit * line.quantity, 2)
#                 discount = round(line.discount, 2)
#                 account_id = line.account_id.id
#                 if line.discount_id and line.discount_id.account_id:
#                     discount_id = line.discount_id.account_id.id
#                 else:
#                     cuenta = self.pool.get('account.account').search(cr, uid, [('name', 'ilike', 'OTROS DESCUENTOS POR PAGAR')])
#                     if cuenta:
#                         discount_id = cuenta[0] 
#                     if not cuenta:
#                       raise osv.except_osv(_('Advertencia!'), _('Falta información en la cuenta para Descuento para continuar \n'))
#                 aapil = False
        # if inv['type'] in ['in_invoice', 'in_refund']:
            #===================================================================
            # if inv['from_invoice']:#Identifica si se va enviar la factura como diferido
            #    logger.notifyChannel('init', netsvc.LOG_INFO, 'Entra para cambiar cuenta del diferido del asiento')
            #    account_id = inv['account_deferred'][0]#Cambio la cuenta para realizar el asiento de la factura.
            #    aapil = False
            #    discount = False
            #    discount_id = False
            # else:
            #===================================================================
            # if line.analytics_id:
            #    o = self.pool.get('account.analytic.plan.instance').browse(cr, uid, line.analytics_id.id)
            #    if o:
            #        for l in o.account_ids:
            #            price = round (line.price_subtotal * l.rate / 100, 2)
                        # account_id = l.cuenta.id or line.account_id.id
            #            account_id = line.account_id.id
            #            aapil = l.id
            #            discount = False
            #            discount_id = False
            #            break
        
        # #print ' line.preproject.id ', line.preproject_id
        
        return {
            'type':'src',
            'name': line.name[:64],
            'price_unit':line.price_unit,
            'quantity':line.quantity,
            'price':price,
            'account_id':account_id,
            'product_id':line.product_id.id,
            'uos_id':line.uos_id.id,
            'account_analytic_id':line.account_analytic_id.id,
            'taxes':line.invoice_line_tax_id,
            'discount':discount,
            # 'discount_id':discount_id,
            'analytic_line_id':aapil,
            # 'preproject_id':line.preproject_id.id,
            # 'funds_certificate_id':line.funds_certificate_id.id,
        }

    _columns = {
        'account_analytic_id':  fields.many2one('account.analytic.account', 'Analytic Account', required=False),
        'description':fields.text('Descripcion2', required=False, select=True, readonly=True, states={'draft':[('readonly', False)]}, help="Descripcion de contratos de sitios.\n"\
                                  "Use este campo tambien para describir el Activo Fijo cuando sea necesario."),
        # 'discount_id':fields.many2one('sale.discount', 'Tipo de Descuento'),
        # 'preproject_id': fields.many2one('projectf.preproject', 'Proyecto Principal'),
    }    
account_invoice_line()
