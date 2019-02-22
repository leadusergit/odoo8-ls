# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today OpenERP SA (<http://www.openerp.com>).
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

import logging
import psycopg2
import time
from datetime import datetime

from openerp import tools
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp
import openerp.addons.product.product

_logger = logging.getLogger(__name__)


"""class res_partner(osv.osv):
    _inherit = 'res.partner'
            
    _defaults = {
            'property_account_position':17,
    }"""
     
class pos_order(osv.osv):
    _inherit = 'pos.order'
    description = "Point of Sale"
    _order = "id desc"

    
    def action_invoice(self, cr, uid, ids, context=None):
        inv_ref = self.pool.get('account.invoice')
        inv_line_ref = self.pool.get('account.invoice.line')
        product_obj = self.pool.get('product.product')
        auth_obj = self.pool.get('account.authorisation')
        partner = self.pool.get('res.partner')
        inv_ids = []
        
        for order in self.pool.get('pos.order').browse(cr, uid, ids, context=context):
            if order.invoice_id:
                inv_ids.append(order.invoice_id.id)
                continue

            if not order.partner_id:
                raise osv.except_osv(_('Error!'), _('Please provide a partner for the sale.'))
            
            partner_id = partner.search(cr, uid, [('name','=',order.company_id.name)])
            user_id = order.user_id 
            print"partner_id=%s"%partner_id
            """auht_numero = auth_obj.search(cr, uid, [('partner_id','=',partner_id)])
            print"*/*//////AUTORIZACION auht_numero=%s"%auht_numero
            for n in auth_obj.browse(cr, uid, auht_numero, context=context):
                if n.expiration_date >=order.date_order:
                    auth_id= n.id 
                    print"///////NUMERO AUTORIZACION=%s"%auth_id"""

            auth_id=user_id.pos_config.journal_id.auth_id.id
            print"NUMERO AUTORIZACION auth_id=%s"%auth_id
                           
                
            acc = order.partner_id.property_account_receivable.id
            inv = {
                'date_invoice':order.date_order,
                'name': order.name,
                'origin': order.name,
                'account_id': acc,
                'journal_id': order.sale_journal.id or None,
                'type': 'out_invoice',
                'reference': order.name,
                'partner_id': order.partner_id.id,
                #'fiscal_position':fiscal,
                'num_retention':order.name,
                'payment_type':order.partner_id.payment_type_customer.id,
                'comment': order.note or '',
                'currency_id': order.pricelist_id.currency_id.id,
                'auth_ret_id':auth_id,
            # considering partner's sale pricelist's currency
            }
            inv.update(inv_ref.onchange_partner_id(cr, uid, [], 'out_invoice', order.partner_id.id)['value'])
            # FORWARDPORT TO SAAS-6 ONLY!
            if order.partner_id.property_account_position.id:
                fiscal=order.partner_id.property_account_position.id
            else:
                fiscal=17
                
            inv.update({'fiscal_position': fiscal})
            
            if not inv.get('account_id', None):
                inv['account_id'] = acc
            inv_id = inv_ref.create(cr, uid, inv, context=context)
            
            print"////CREA FACTURA inv_id=%s"%inv_id
            self.write(cr, uid, [order.id], {'invoice_id': inv_id, 'state': 'invoiced'}, context=context)
            inv_ids.append(inv_id)
            
            for line in order.lines:
                inv_line = {
                    'invoice_id': inv_id,
                    'product_id': line.product_id.id,
                    'quantity': line.qty,
                }
                inv_name = product_obj.name_get(cr, uid, [line.product_id.id], context=context)[0][1]
                inv_line.update(inv_line_ref.product_id_change(cr, uid, [],
                                                               line.product_id.id,
                                                               line.product_id.uom_id.id,
                                                               line.qty, partner_id = order.partner_id.id)['value'])
                if not inv_line.get('account_analytic_id', False):
                    inv_line['account_analytic_id'] = \
                        self._prepare_analytic_account(cr, uid, line,
                                                       context=context)
                inv_line['price_unit'] = line.price_unit
                inv_line['discount'] = line.discount
                inv_line['name'] = inv_name
                inv_line['invoice_line_tax_id'] = [(6, 0, inv_line['invoice_line_tax_id'])]
                inv_line_ref.create(cr, uid, inv_line, context=context)
            inv_ref.button_reset_taxes(cr, uid, [inv_id], context=context)
            self.signal_workflow(cr, uid, [order.id], 'invoice')
            inv_ref.signal_workflow(cr, uid, [inv_id], 'validate')
        if not inv_ids: return {}

        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
        res_id = res and res[1] or False
        return {
            'name': _('Customer Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': inv_ids and inv_ids[0] or False,
        }
        
        
        
        
        