# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _

class wizard_account_deferred(osv.osv_memory):
    _name = "wizard.account.deferred"
    _description = "Generate deferred Sales and Purchase Invoices"
    
    def _get_default_period(self, cr, uid, context={}):
        periods = self.pool.get('account.period').find(cr, uid)
        if periods:
            return periods[0]
        else:
            return False
        
    def action_posted (self, cr, uid, ids, context=None):
        #print "action_posted",context
        account_invoice = self.pool.get('account.invoice')
        sale = self.pool.get('sale.order')
        purchase = self.pool.get('purchase.order')
        wiz_id = context.get('active_ids', [])
        obj_product = self.pool.get('product.template')
        obj_product_product = self.pool.get('product.product')
        obj_account_deferred = self.pool.get('account.deferred')
        obj_account_billing = self.pool.get('account.order.billing')
        if not wiz_id:
            return {'type': 'ir.actions.act_window_close'}
        if wiz_id:
            form = self.read(cr, uid, ids)[0]
            period_id = form.get('period_id', False)
            invoice_type = form.get('invoice_type', False)
            context['period_id'] = period_id
            type = form.get('type', False)
            action = form.get('action', 'posted')
            ##print action
            if invoice_type:
                if type=='sale':
                    if invoice_type=='invoice':
                        invoice_type = 'out_invoice'
                    else:
                        invoice_type = 'out_refund'
                if type=='purchase':
                    if invoice_type=='invoice':
                        invoice_type = 'in_invoice'
                    else:
                        invoice_type = 'in_refund'
                if action == 'posted':
                    where = " and ad.state ='draft' "
                else:
                     where = " and ad.state ='posted' "
                sql = "select ob.id from account_order_billing as ob "\
                      "join account_deferred as ad on(ob.id=ad.order_billing_id) "\
                      "where ob.invoice_type='"+str(invoice_type)+"' and ob.type='"+str(type)+"'"+where+""\
                      "and ad.period_id ="+str(period_id)
                ##print sql
                cr.execute(sql)
                diferidos = [x[0] for x in cr.fetchall()]
                order = list(set(diferidos))
                if not order:
                    raise osv.except_osv(_('Aviso!'), _('No se encontraron registros!')) 
                for item in order:
                    if invoice_type in ('in_invoice','out_invoice'):
                        if action=='posted':
                            obj_account_billing.action_posted(cr, uid,[item], context)
                        elif action=='unreconcile':
                            obj_account_billing.action_cancel(cr, uid,[item], context)
                    elif invoice_type in ('in_refund','out_refund'):
                        if action=='posted':
                            obj_account_billing.action_posted_refund(cr, uid,[item], context)
                        elif action=='unreconcile':
                            obj_account_billing.action_cancel(cr, uid,[item], context)
                
        result = {'type': 'ir.actions.act_window_close'}
        return result
    
    _columns = {
        'period_id': fields.many2one('account.period', 'Periodo', help='Periodo contable'),
        'type': fields.selection([('sale','Ventas'),
                                  ('purchase','Compras')
                                  ], 'Diferido', help='Ventas: Ingresos Diferidos, Compras: Gastos Diferidos'),
        'invoice_type': fields.selection([('invoice','Factura'),
                                          ('refund','Nota Credito')
                                          ], 'Facturas/Notas Credito', help='Origen de Documento del Diferido,\n'\
                                         'Depende del tipo para que cambie el asiento contable que se realiza mediante este wizard'),
        'action':fields.selection([('posted','Contabilizar'),
                                   ('unreconcile','Cancelar Asientos')
                                   ], 'Contabilizar/Borrar Asientos',help='Contabiliza o Borrar los asientos dependiendo del Periodo que elija!'),
    }
    
    _defaults = {
        'type': lambda *a: 'sale',
        'invoice_type': lambda *a: 'invoice',
        'period_id':_get_default_period,
        'action': lambda *a: 'posted',
    }

wizard_account_deferred()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: