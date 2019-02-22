# -*- coding: utf-8 -*-
from __future__ import absolute_import
from openerp.osv import osv, fields
from openerp import api
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools.translate import _
import openerp.netsvc
import pdb
import time
import datetime
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import logging
import calendar
from lxml import etree

_logger = logging.getLogger(__name__)

class PosOrderAdd(osv.osv):
    _inherit= 'pos.order'  
    
    _columns = {                
        'porcentaje_iva_aplicado': fields.selection([
                                            ('auto', 'Automatico'),
                                            ('iva12', 'IVA 12%'),    
                                            ('iva14', 'IVA 14%')], '%IVA aplicado', select=True,copy=True,required=True,readonly=False,states={'paid': [('readonly', True)]}),
    }
    
    _defaults = {
        'porcentaje_iva_aplicado':'auto'
    }
            
            
    def _amount_line_tax(self, cr, uid, line, context=None):
        print"line=%s"%line
        account_tax_obj = self.pool['account.tax']
        taxes_ids = [tax for tax in line.product_id.taxes_id if tax.company_id.id == line.order_id.company_id.id]
        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        taxes = account_tax_obj.compute_all(cr, uid, taxes_ids, price, line.qty, product=line.product_id, partner=line.order_id.partner_id or False,
                                            fecha_comprobante=line.order_id.date_order,valor_iva=line.order_id.porcentaje_iva_aplicado)['taxes']
        print"val pos-o heredado taxes=%s"%taxes
        val = 0.0
        for c in taxes:
            val += c.get('amount', 0.0)
        print"val pos-o heredado=%s"%val
        return val  
    
    
   
    
        
class pos_order_line(osv.osv):
    _inherit = 'pos.order.line'
    
    
    def _amount_line_all(self, cr, uid, ids, field_names, arg, context=None):
        res = dict([(i, {}) for i in ids])
        account_tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids, context=context):
            taxes_ids = [ tax for tax in line.product_id.taxes_id if tax.company_id.id == line.order_id.company_id.id ]
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            print"line.order_id.porcentaje_iva_aplicado=%s"%line.order_id.porcentaje_iva_aplicado
            taxes = account_tax_obj.compute_all(cr, uid, taxes_ids, price, line.qty, product=line.product_id, partner=line.order_id.partner_id or False,
                                                fecha_comprobante=line.order_id.date_order,valor_iva=line.order_id.porcentaje_iva_aplicado)
            
            cur = line.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal'] = taxes['total']
            res[line.id]['price_subtotal_incl'] = taxes['total_included']
        return res
    
    
    def onchange_qty(self, cr, uid, ids, product, discount, qty, price_unit, context=None):
        result = {}
        if not product:
            return result
        account_tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        prod = self.pool.get('product.product').browse(cr, uid, product, context=context)
        price = price_unit * (1 - (discount or 0.0) / 100.0)
        taxes = account_tax_obj.compute_all(cr, uid, prod.taxes_id, price, qty, product=prod, partner=False,fecha_comprobante=time.strftime("%y-%m-%d"),valor_iva='auto')
        print"taxes-qtyh=%s"%taxes
        result['price_subtotal'] = taxes['total']
        result['price_subtotal_incl'] = taxes['total_included']
        return {'value': result}
    
    
    _columns = {                
        'price_subtotal': fields.function(_amount_line_all, multi='pos_order_line_amount', digits_compute=dp.get_precision('Product Price'), string='Subtotal w/o Tax', store=True),
        'price_subtotal_incl': fields.function(_amount_line_all, multi='pos_order_line_amount', digits_compute=dp.get_precision('Account'), string='Subtotal', store=True),

    }
      
class PurchaseOrder(osv.osv):
    _inherit = 'purchase.order'  
        
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        """se añaden parametros para compute_all  order.date_order y order.porcentaje_iva_aplicado"""
        res = {}
        cur_obj=self.pool.get('res.currency')
        line_obj = self.pool['purchase.order.line']
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                            'amount_untaxed': 0.0,
                            'amount_tax': 0.0,
                            'amount_total': 0.0,
                            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                line_price = line_obj._calc_line_base_price(cr, uid, line, context=context)
                line_qty = line_obj._calc_line_quantity(cr, uid, line, context=context)
                for c in self.pool['account.tax'].compute_all(cr, uid, line.taxes_id, line_price, line_qty,
                                                                  line.product_id, order.partner_id,
                                                                  order.date_order,
                                                                  order.porcentaje_iva_aplicado)['taxes']:
                    val += c.get('amount', 0.0)
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
            print"po-res-purchase=%s"%res
            
        return res
            
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    
    _columns = {                
        'porcentaje_iva_aplicado': fields.selection([
                                            ('auto', 'Automatico'),
                                            ('iva12', 'IVA 12%'),    
                                            ('iva14', 'IVA 14%')], '%IVA aplicado', select=True,copy=True,required=True,readonly=False,states={'done': [('readonly', True)]}),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The total amount"),
        
    }
    
    _defaults = {
        'porcentaje_iva_aplicado':'auto'
    }
        
              

class PurchaseOrderLine(osv.osv):
    _inherit = 'purchase.order.line'
    
      
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            line_price = self._calc_line_base_price(cr, uid, line,
                                                    context=context)
            line_qty = self._calc_line_quantity(cr, uid, line,
                                                context=context)
            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line_price,
                                        line_qty, line.product_id,
                                        line.order_id.partner_id,line.order_id.date_order,
                                        line.order_id.porcentaje_iva_aplicado)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        print"res pol=%s"%res
        return res
    
    
    _columns = { 
            'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),

    }



class SaleOrder(osv.osv):
    _inherit = 'sale.order'
    __logger = logging.getLogger(_inherit) 
    
     
    _columns = {                
        'porcentaje_iva_aplicado': fields.selection([
                                            ('auto', 'Automatico'),
                                            ('iva12', 'IVA 12%'),
                                            ('iva14', 'IVA 14%')], '%IVA aplicado', select=True,copy=True,required=True,readonly=False,states={'open': [('readonly', True)]}),
    }
    
    _defaults = {
        'porcentaje_iva_aplicado':'auto'
    }
       
    
    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        line_obj = self.pool['sale.order.line']
        price = line_obj._calc_line_base_price(cr, uid, line, context=context)
        qty = line_obj._calc_line_quantity(cr, uid, line, context=context)
        for c in self.pool['account.tax'].compute_all(cr, uid,line.tax_id,price,qty, line.product_id,
                line.order_id.partner_id,line.order_id.date_order,line.order_id.porcentaje_iva_aplicado)['taxes']:
            #print"line.order_id.porcentaje_iva_aplicado=%s"%line.order_id.porcentaje_iva_aplicado
            #print"line.order_id.date_order=%s"%line.order_id.date_order
            val += c.get('amount', 0.0)
            print"amount so=%s"%c.get('amount', 0.0)
        return val


class SaleOrderLine(osv.osv):
    _inherit = 'sale.order.line' 
    __logger = logging.getLogger(_inherit)   
    
    
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = self._calc_line_base_price(cr, uid, line, context=context)
            qty = self._calc_line_quantity(cr, uid, line, context=context)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, qty,
                                        line.product_id,
                                        line.order_id.partner_id,
                                        line.order_id.date_order,
                                        line.order_id.porcentaje_iva_aplicado)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
            print"res sol=%s"%res
        return res
