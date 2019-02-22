# -*- coding: utf-8 -*-

import time
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp.exceptions import ValidationError

class AccountAtsSustento(models.Model):
    _name = 'account.ats.sustento'
    _description = 'Sustento del Comprobante'
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        reads = self.browse(cr, uid, ids, context=context)
        for record in reads:
            name = '%s - %s' % (record.code, record.type)
            res.append((record.id, name))
        return res

    _rec_name = 'type'
  
    code = fields.Char('Código', size=2, required=True)
    type = fields.Char('Tipo de Sustento', size=250, required=True)
    
class account_tax(models.Model):
    _inherit = 'account.tax'
    
    cod_sustento = fields.Many2one('account.ats.sustento', string='Cod.Sustento Tributario',select=True)

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    tax_id = fields.Many2one('account.tax', string='Cod.Impuesto Retencion',select=True)
  
    
"""class account_invoice(models.Model):
    _inherit = 'account.invoice'
    cod_sustento = fields.Many2one('account.ats.sustento', string='Sustento',select=True, readonly=True, states={'draft': [('readonly', False)]})

"""   

class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'
    
    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
            company_id=None):
        
        context = self._context
        company_id = company_id if company_id is not None else context.get('company_id', False)
        self = self.with_context(company_id=company_id, force_company=company_id)
        print"partner_id ACCOUNTINVOICE-AAHER=%s"%partner_id
        if not partner_id:
            #raise except_orm(_('No Partner Defined!'), _("You must first select a partner!"))
             raise ValidationError(u'Debe seleccionar una empresa')

        if not product:
            if type in ('in_invoice', 'in_refund'):
                return {'value': {}, 'domain': {'uos_id': []}}
            else:
                return {'value': {'price_unit': 0.0}, 'domain': {'uos_id': []}}

        values = {}

        part = self.env['res.partner'].browse(partner_id)
        fpos = self.env['account.fiscal.position'].browse(fposition_id)
       
        if part.lang:
            self = self.with_context(lang=part.lang)
        product = self.env['product.product'].browse(product)

        values['name'] = product.partner_ref
        if type in ('out_invoice', 'out_refund'):
            account = product.property_account_income or product.categ_id.property_account_income_categ
        else:
            account = product.property_account_expense or product.categ_id.property_account_expense_categ
        account = fpos.map_account(account)
        if account:
            values['account_id'] = account.id

        if type in ('out_invoice', 'out_refund'):
            taxes = product.taxes_id or account.tax_ids            
            if product.description_sale:
                values['name'] += '\n' + product.description_sale
        else:
            #taxes = (product.supplier_taxes_id or account.tax_ids) and part.tax_id
            taxes = product.supplier_taxes_id or account.tax_ids
            print"taxes ACCOUNTINVOICE-AAHER=%s"%taxes
            if product.description_purchase:
                values['name'] += '\n' + product.description_purchase 
                      
        taxes = fpos.map_tax(taxes)
        values['invoice_line_tax_id'] = taxes.ids
        
        """Si el partner tiene configurado el codigo impuesto de retencion se añade el codigo
           en la linea de impuestos del producto"""
        taxp=fpos.map_tax(part.tax_id)
        if taxp:
            values['invoice_line_tax_id'].append(taxp.id)
            print"values['invoice_line_tax_id']=%s"%values['invoice_line_tax_id']
                     
        if type in ('in_invoice', 'in_refund'):
            values['price_unit'] = price_unit or product.standard_price
        else:
            values['price_unit'] = product.lst_price

        values['uos_id'] = product.uom_id.id
        if uom_id:
            uom = self.env['product.uom'].browse(uom_id)
            if product.uom_id.category_id.id == uom.category_id.id:
                values['uos_id'] = uom_id

        domain = {'uos_id': [('category_id', '=', product.uom_id.category_id.id)]}
        company = self.env['res.company'].browse(company_id)
        currency = self.env['res.currency'].browse(currency_id)

        if company and currency:
            if company.currency_id != currency:
                if type in ('in_invoice', 'in_refund'):
                    values['price_unit'] = product.standard_price
                values['price_unit'] = values['price_unit'] * currency.rate

            if values['uos_id'] and values['uos_id'] != product.uom_id.id:
                values['price_unit'] = self.env['product.uom']._compute_price(
                    product.uom_id.id, values['price_unit'], values['uos_id'])

        return {'value': values, 'domain': domain}



class account_invoice(models.Model):
    _inherit = 'account.invoice'

    _defaults = {
        'cod_sustento' : '00',
        'comment':' '
    }
    @api.multi
    def button_reset_taxes(self):
        """limpia el campo"""
        self.comment = '' 
        account_invoice_tax = self.env['account.invoice.tax']
        ctx = dict(self._context)
        for invoice in self:
            self._cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False", (invoice.id,))
            self.invalidate_cache()
            partner = invoice.partner_id
            
            type=invoice.type
            print"type=%s"%type
            if type in ('out_invoice', 'out_refund'):
               self.cod_sustento= None
            #if type in ('in_invoice', 'in_refund'):
            """impuestos de producto"""
            
            print"mod account_inv_codsutento"            
            for x in invoice.invoice_line:
                taxes=x.invoice_line_tax_id 
                print"button_reset_taxesHER=%s"%taxes
                for taxprod in taxes:   
                    """imprime el codigo y descripcion de los impuestos en el campo comment"""
                    self.comment += u'[%s]%s\n'%(taxprod.description,taxprod.name) 
                                  
                    codsust=self.env['account.tax'].browse(taxprod.id)
                    codsust_tax=codsust.cod_sustento.id
                    print"codsust_tax=%s"%codsust_tax
                    """se actualiza el campo cod_sustento con el codigo atado al impuesto del producto
                    por defecto se le carga el valor 00"""
                    if codsust_tax:
                        sustento=self.env['account.ats.sustento'].browse(codsust_tax)
                        aux=sustento.code
                        print"//aux//=%s"%aux
                        self.cod_sustento=str(aux)
            
            if partner.lang:
                ctx['lang'] = partner.lang
            for taxe in account_invoice_tax.compute(invoice.with_context(ctx)).values():
                account_invoice_tax.create(taxe)
        # dummy write on self to trigger recomputations
        return self.with_context(ctx).write({'invoice_line': []})

    