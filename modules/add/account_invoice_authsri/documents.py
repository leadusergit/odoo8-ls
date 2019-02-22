# -*- coding: utf-8 -*-

import time
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp.exceptions import ValidationError

   
class account_tax(models.Model):
    _inherit = 'account.tax'
    
    auth_ret_id = fields.Many2one('account.authorisation', string='Nº Autorización',select=True)




class account_invoice_auth(models.Model):
    _inherit = 'account.invoice'


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
                    codsust_tax = codsust.cod_sustento.id                    
                    auth_id = codsust.auth_ret_id.id                    

                    """se actualiza el campo cod_sustento con el codigo atado al impuesto del producto
                    por defecto se le carga el valor 00"""
                    if codsust_tax:
                        sustento=self.env['account.ats.sustento'].browse(codsust_tax)
                        aux=sustento.code
                        self.cod_sustento = str(aux)
                        print"//AUXXXXXX//=%s"%aux
                        
                    """se actualiza el campo auth_ret_id con el id de autorizacion atado 
                        al impuesto del producto"""                                              
                    if auth_id:
                       acc_authorisation = self.env['account.authorisation'].browse(auth_id)
                       self.auth_ret_id = acc_authorisation.id
                       print"//AUTORIZACION//=%s"%acc_authorisation.id
                    else:
                       self.auth_ret_id = x.invoice_id.journal_id.auth_ret_id.id
            
            if partner.lang:
                ctx['lang'] = partner.lang
            for taxe in account_invoice_tax.compute(invoice.with_context(ctx)).values():
                account_invoice_tax.create(taxe)
        # dummy write on self to trigger recomputations
        return self.with_context(ctx).write({'invoice_line': []})

        
    