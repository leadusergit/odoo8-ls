# -*- coding: utf-8 -*-
import logging
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time
import openerp
from openerp import SUPERUSER_ID, api , workflow
from openerp import tools
from openerp.osv import fields, osv, expression
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools.safe_eval import safe_eval as eval
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class AccountInvoice(osv.osv):
    _inherit = 'account.invoice'
    
    _columns = {                
        'porcentaje_iva_aplicado': fields.selection([
                                            ('auto', 'Automatico'),
                                            ('iva12', 'IVA 12%'),
                                            ('iva14', 'IVA 14%')], '%IVA aplicado', select=True,copy=True,required=True,readonly=False,states={'open': [('readonly', True)]}),
    }
    
    _defaults = {
        'porcentaje_iva_aplicado':'auto'
    }
     

AccountInvoice()


class AccountInvoiceLine(osv.osv):
    _inherit = 'account.invoice.line' 
    __logger = logging.getLogger(_inherit) 
    
    
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_id', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id','invoice_id.date_invoice','invoice_id.porcentaje_iva_aplicado')
    def _compute_price(self):
        """incicializa variables price, partner,quantity,product,fecha"""
        #print"_compute_price invtaxiva34"
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_id.compute_all(price, self.quantity, product=self.product_id, 
                                                     partner=self.invoice_id.partner_id,fecha_comprobante=self.invoice_id.date_invoice,
                                                     valor_iva=self.invoice_id.porcentaje_iva_aplicado)

        self.price_subtotal = taxes['total']
        if self.invoice_id:
            self.price_subtotal = self.invoice_id.currency_id.round(self.price_subtotal)

AccountInvoiceLine()

class AccountTax(osv.osv):
    _inherit = 'account.tax' 
    __logger = logging.getLogger(_inherit) 
         
 
    def _applicable(self, cr, uid, taxes, price_unit, product=None, partner=None,fecha_comprobante=None,valor_iva=None):
        #print" product2007=%s"%product
        #print" _applicable --partner=%s"%partner
        res = []
        for tax in taxes:
            #print" tax.applicable_type2011=%s"%tax.applicable_type
            if tax.applicable_type=='code':
                localdict = {'price_unit':price_unit, 'product':product, 'partner':partner,'fecha_comprobante':fecha_comprobante,'valor_iva':valor_iva}
                eval(tax.python_applicable, localdict, mode="exec", nocopy=True)
                if localdict.get('result', False):
                    res.append(tax)
                    #print" res.append(tax)2017=%s"%res                   
            else:
                res.append(tax)
                #print" res.append(tax)2020=%s"%res  
       
        return res
    
    def _unit_compute(self, cr, uid, taxes, price_unit, product=None, partner=None, quantity=0,fecha_comprobante=None,valor_iva=None):       
        #print" partner42=%s"%partner
        #print" price_unit=%s"%price_unit
        #print" product=%s"%product
        #print" quantity=%s"%quantity               
        taxes = self._applicable(cr, uid, taxes, price_unit ,product, partner,fecha_comprobante,valor_iva)
        res = []
        #print" res=%s"%res
        cur_price_unit=price_unit       
        for tax in taxes:
            # we compute the amount for the current tax object and append it to the result
            data = {'id':tax.id,
                    'name': tax.name,
                    'account_collected_id':tax.account_collected_id.id,
                    'account_paid_id':tax.account_paid_id.id,
                    'account_analytic_collected_id': tax.account_analytic_collected_id.id,
                    'account_analytic_paid_id': tax.account_analytic_paid_id.id,
                    'base_code_id': tax.base_code_id.id,
                    'ref_base_code_id': tax.ref_base_code_id.id,
                    'sequence': tax.sequence,
                    'base_sign': tax.base_sign,
                    'tax_sign': tax.tax_sign,
                    'ref_base_sign': tax.ref_base_sign,
                    'ref_tax_sign': tax.ref_tax_sign,
                    'price_unit': cur_price_unit,
                    'tax_code_id': tax.tax_code_id.id,
                    'ref_tax_code_id': tax.ref_tax_code_id.id,
            }
            res.append(data)
            if tax.type=='percent':
                amount = cur_price_unit * tax.amount
                data['amount'] = amount
            elif tax.type=='fixed':
                data['amount'] = tax.amount
                data['tax_amount']=quantity
               # data['amount'] = quantity
            elif tax.type=='code':
                if not valor_iva:
                    valor_iva='auto'
                
                #str(datetime.now())
                localdict = {'price_unit':cur_price_unit, 'product':product, 'partner':partner, 'quantity': quantity,'fecha_comprobante':fecha_comprobante,'valor_iva':valor_iva}
                print"localdic_unit_compute h=%s"%localdict             
                eval(tax.python_compute, localdict, mode="exec", nocopy=True)
                amount = localdict['result']
                print" amount=%s"% amount
                data['amount'] = amount
            elif tax.type=='balance':
                data['amount'] = cur_price_unit - reduce(lambda x,y: y.get('amount',0.0)+x, res, 0.0)
                data['balance'] = cur_price_unit

            amount2 = data.get('amount', 0.0)
            if tax.child_ids:
                if tax.child_depend:
                    latest = res.pop()
                amount = amount2
                child_tax = self._unit_compute(cr, uid, tax.child_ids, amount, product, partner, quantity,fecha_comprobante,valor_iva)
                res.extend(child_tax)
                for child in child_tax:
                    amount2 += child.get('amount', 0.0)
                if tax.child_depend:
                    for r in res:
                        for name in ('base','ref_base'):
                            if latest[name+'_code_id'] and latest[name+'_sign'] and not r[name+'_code_id']:
                                r[name+'_code_id'] = latest[name+'_code_id']
                                r[name+'_sign'] = latest[name+'_sign']
                                r['price_unit'] = latest['price_unit']
                                latest[name+'_code_id'] = False
                        for name in ('tax','ref_tax'):
                            if latest[name+'_code_id'] and latest[name+'_sign'] and not r[name+'_code_id']:
                                r[name+'_code_id'] = latest[name+'_code_id']
                                r[name+'_sign'] = latest[name+'_sign']
                                r['amount'] = data['amount']
                                latest[name+'_code_id'] = False
            if tax.include_base_amount:
                cur_price_unit+=amount2
        return res
    
   
    
    @api.v7
    def compute_all(self, cr, uid, taxes, price_unit, quantity, product=None, partner=None,fecha_comprobante=None,valor_iva=None,force_excluded=False):
        """
        :param force_excluded: boolean used to say that we don't want to consider the value of field price_include of
            tax. It's used in encoding by line where you don't matter if you encoded a tax with that boolean to True or
            False
        RETURN: {
                'total': 0.0,                # Total without taxes
                'total_included: 0.0,        # Total with taxes
                'taxes': []                  # List of taxes, see compute for the format
            }
        """

        # By default, for each tax, tax amount will first be computed
        # and rounded at the 'Account' decimal precision for each
        # PO/SO/invoice line and then these rounded amounts will be
        # summed, leading to the total amount for that tax. But, if the
        # company has tax_calculation_rounding_method = round_globally,
        # we still follow the same method, but we use a much larger
        # precision when we round the tax amount for each line (we use
        # the 'Account' decimal precision + 5), and that way it's like
        # rounding after the sum of the tax amounts of each line
        #print"compute_all v7 h= %s"%fecha_comprobante
        
        print"compute_all v7 herencia= %s"%fecha_comprobante
        print"compute_all v7 herencia= %s"%valor_iva
            
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        tax_compute_precision = precision
        if taxes and taxes[0].company_id.tax_calculation_rounding_method == 'round_globally':
            tax_compute_precision += 5
        totalin = totalex = round(price_unit * quantity, precision)
        tin = []
        tex = []
        for tax in taxes:
            if not tax.price_include or force_excluded:
                tex.append(tax)
            else:
                tin.append(tax)
        tin = self.compute_inv(cr, uid, tin, price_unit, quantity, product=product, partner=partner, fecha_comprobante=fecha_comprobante,valor_iva=valor_iva,precision=tax_compute_precision)
        for r in tin:
            totalex -= r.get('amount', 0.0)
        totlex_qty = 0.0
        try:
            totlex_qty = totalex/quantity
        except:
            pass
        tex = self._compute(cr, uid, tex, totlex_qty, quantity, product=product, partner=partner,fecha_comprobante=fecha_comprobante,valor_iva=valor_iva,precision=tax_compute_precision)
        for r in tex:
            totalin += r.get('amount', 0.0)
        return {
            'total': totalex,
            'total_included': totalin,
            'taxes': tin + tex
        }

    @api.v8
    def compute_all(self, price_unit, quantity, product=None, partner=None,fecha_comprobante=None,valor_iva=None,force_excluded=False):
        #print"price_unit2160 =%s"%price_unit
        #print"product2160 =%s"%product
        #print"partner2160 =%s"%partner
        return self._model.compute_all(self._cr, self._uid, self, price_unit, quantity,product=product, 
                                       partner=partner,fecha_comprobante=fecha_comprobante,valor_iva=valor_iva,force_excluded=force_excluded)
        
    
    def _compute(self, cr, uid, taxes, price_unit, quantity, product=None, partner=None,fecha_comprobante=None,valor_iva=None,precision=None):
        """
        Compute tax values for given PRICE_UNIT, QUANTITY and a buyer/seller ADDRESS_ID.

        RETURN:
            [ tax ]
            tax = {'name':'', 'amount':0.0, 'account_collected_id':1, 'account_paid_id':2}
            one tax for each tax id in IDS and their children
        """      
        """pasa parametros para método  _unit_compute"""
        res = self._unit_compute(cr, uid, taxes, price_unit, product, partner, quantity,fecha_comprobante,valor_iva)
        #print"///_compute air128=%s"%res
        total = 0.0
        precision_pool = self.pool.get('decimal.precision')
        for r in res:
            if r.get('balance', False):
                r['amount'] = round(r.get('balance', 0.0) * quantity, precision_pool.precision_get(cr, uid, 'Account')) - total
            else:
                r['amount'] = r.get('amount', 0.0) * quantity
                total += r['amount']
        return res
    
    
    def _unit_compute_inv(self, cr, uid, taxes, price_unit, product=None, partner=None,fecha_comprobante=None,valor_iva=None):
        taxes = self._applicable(cr, uid, taxes, price_unit,  product, partner,fecha_comprobante,valor_iva)
        res = []
        taxes.reverse()
        cur_price_unit = price_unit
        tax_parent_tot = 0.0
        for tax in taxes:
            if (tax.type=='percent') and not tax.include_base_amount:
                tax_parent_tot += tax.amount

        for tax in taxes:
            if (tax.type=='fixed') and not tax.include_base_amount:
                cur_price_unit -= tax.amount

        for tax in taxes:
            if tax.type=='percent':
                if tax.include_base_amount:
                    amount = cur_price_unit - (cur_price_unit / (1 + tax.amount))
                else:
                    amount = (cur_price_unit / (1 + tax_parent_tot)) * tax.amount

            elif tax.type=='fixed':
                amount = tax.amount

            elif tax.type=='code':
                localdict = {'price_unit':cur_price_unit, 'product':product, 'partner':partner,'fecha_comprobante':fecha_comprobante,'valor_iva':valor_iva}
                eval(tax.python_compute_inv, localdict, mode="exec", nocopy=True)
                amount = localdict['result']
            elif tax.type=='balance':
                amount = cur_price_unit - reduce(lambda x,y: y.get('amount',0.0)+x, res, 0.0)

            if tax.include_base_amount:
                cur_price_unit -= amount
                todo = 0
            else:
                todo = 1
            res.append({
                'id': tax.id,
                'todo': todo,
                'name': tax.name,
                'amount': amount,
                'account_collected_id': tax.account_collected_id.id,
                'account_paid_id': tax.account_paid_id.id,
                'account_analytic_collected_id': tax.account_analytic_collected_id.id,
                'account_analytic_paid_id': tax.account_analytic_paid_id.id,
                'base_code_id': tax.base_code_id.id,
                'ref_base_code_id': tax.ref_base_code_id.id,
                'sequence': tax.sequence,
                'base_sign': tax.base_sign,
                'tax_sign': tax.tax_sign,
                'ref_base_sign': tax.ref_base_sign,
                'ref_tax_sign': tax.ref_tax_sign,
                'price_unit': cur_price_unit,
                'tax_code_id': tax.tax_code_id.id,
                'ref_tax_code_id': tax.ref_tax_code_id.id,
            })
            if tax.child_ids:
                if tax.child_depend:
                    del res[-1]
                    amount = price_unit

            parent_tax = self._unit_compute_inv(cr, uid, tax.child_ids, amount, product, partner,fecha_comprobante,valor_iva)
            res.extend(parent_tax)

        total = 0.0
        for r in res:
            if r['todo']:
                total += r['amount']
        for r in res:
            r['price_unit'] -= total
            r['todo'] = 0
        return res

    def compute_inv(self, cr, uid, taxes, price_unit, quantity, product=None, partner=None,fecha_comprobante=None,valor_iva=None, precision=None):
        """
        Compute tax values for given PRICE_UNIT, QUANTITY and a buyer/seller ADDRESS_ID.
        Price Unit is a Tax included price

        RETURN:
            [ tax ]
            tax = {'name':'', 'amount':0.0, 'account_collected_id':1, 'account_paid_id':2}
            one tax for each tax id in IDS and their children
        """
        if not precision:
            precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        res = self._unit_compute_inv(cr, uid, taxes, price_unit, product, partner=None,fecha_comprobante=None,valor_iva=None)
        total = 0.0
        for r in res:
            if r.get('balance',False):
                r['amount'] = round(r['balance'] * quantity, precision) - total
            else:
                r['amount'] = round(r['amount'] * quantity, precision)
                total += r['amount']
        return res

AccountTax()

