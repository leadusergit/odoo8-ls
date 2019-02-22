# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Asset work
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
#creador  *EG

import time
import datetime
from openerp.osv import osv
from openerp.osv import fields
from mx import DateTime
# import netsvc
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime
import base64
import StringIO
import csv
# import ir
from openerp.tools.translate import _
from openerp import tools

class wizard_account_ats(osv.osv_memory):
    _name='wizard.account.ats'
    _description = "Anexo Transaccional Simplificado (ATS)"
    
    def _get_default_period(self, cr, uid, context={}):
        periods = self.pool.get('account.period').find(cr, uid)
        if periods:
            return periods[0]
        else:
            return False
    
    def _generate_item_invoice_line(self, anexo_document, invoice_ids, cr):
        
        ids = ','.join([str(x) for x in invoice_ids])
         
        sql = """
            select sum(t_b_excenta_iva) as excento,sum(t_bi_iva) as con_iva,sum(t_iva) as iva from account_invoice where id in (
        """ + ids + """)"""   
                       
        cr.execute(sql)
        res = cr.dictfetchall()
          
        item = []
        item.append(anexo_document['sequence'])
        item.append(anexo_document['name'])
        item.append(len(invoice_ids))
        item.append(res[0]['excento'])
        item.append(res[0]['con_iva'])
        item.append(res[0]['iva'])
        return item
    
    def generate_file(self, cr, uid, ids, context=None):
        anexo_line = self.pool.get('account.document.anexo.line')
        invoice_obj = self.pool.get('account.invoice')
        res = []
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        form = data['form']
        buf = StringIO.StringIO()
        writer = csv.writer(buf, delimiter=',') 
                
        period_id = form.get('period_id')
        anexo_document_ids = anexo_line.search(cr, uid, [('type', 'ilike', 'compras')])
        anexo_documents = anexo_line.browse(cr, uid, anexo_document_ids)
        
        item = ['CODIGO', 'TRANSACCION', 'NUM REG', 'BASE IMPONIBLE 0%', 'BASE IMPONIBLE 12%', 'VALOR IVA']
        writer.writerow(item)
        
        item = ['', '', '', 'COMPRAS', '', '']
        writer.writerow(item)
        
        itemTotales = []
        itemTotales.append('')
        itemTotales.append('TOTAL')
        
        totalNumReg = 0
        totalBeseCero = 0
        totalConBase = 0
        totalIva = 0
        
        for anexo_document in anexo_documents:
            
            tipo_factura = anexo_document.document_anexo_id.type_invoice
            tipo = anexo_document.document_anexo_id.type
            
            invoice_ids = invoice_obj.search(cr, uid, [('state', '=', 'open'), ('period_id', '=', period_id), ('tipo_factura', '=', tipo_factura), ('type', '=', tipo)])
            
            if invoice_ids:        
                item = self._generate_item_invoice_line(anexo_document, invoice_ids, cr)
                writer.writerow(item)
                
                totalNumReg += item[2]
                totalBeseCero += item[3] 
                totalConBase += item[4] 
                totalIva += item[5]
            
        itemTotales.append(totalNumReg)
        itemTotales.append(totalBeseCero)
        itemTotales.append(totalConBase)
        itemTotales.append(totalIva)
        writer.writerow(itemTotales)            
        
        
        totalNumReg = 0
        totalBeseCero = 0 
        totalConBase = 0 
        totalIva = 0
        
        anexo_document_ids = []
        
        anexo_document_ids = anexo_line.search(cr, uid, [('type', 'ilike', 'ventas')])
        
        anexo_documents = []
        
        itemTotales = []
        itemTotales.append('')
        itemTotales.append('TOTAL')
        
        anexo_documents = anexo_line.browse(cr, uid, anexo_document_ids)
        
        #print ' anexo_documents ', anexo_documents
        
        item = ['', '', '', 'VENTAS', '', '']
        writer.writerow(item)
        
        for anexo_document in anexo_documents:
            
            tipo_factura = anexo_document.document_anexo_id.type_invoice
            
            #print ' tipo_factura ', tipo_factura
            
            tipo = anexo_document.document_anexo_id.type
            
            #print ' tipo ', tipo
            
            invoice_ids = invoice_obj.search(cr, uid, [('state', '=', 'open'), 
                                                       ('period_id', '=', period_id), 
                                                       ('tipo_factura', '=', tipo_factura), 
                                                       ('type', '=', tipo)])
            if invoice_ids:        
    
                item = self._generate_item_invoice_line(anexo_document, invoice_ids, cr)
                ##print item
                writer.writerow(item)
                
                totalNumReg += item[2]
                totalBeseCero += item[3] 
                totalConBase += item[4] 
                totalIva += item[5]
            
        itemTotales.append(totalNumReg)
        itemTotales.append(totalBeseCero)
        itemTotales.append(totalConBase)
        itemTotales.append(totalIva)
        writer.writerow(itemTotales)                
            
        item = ['Cod.', '%', 'Concepto de Retencion', 'No. Reg', 'Base Imponible', 'Valor Retenido']
        writer.writerow(item)
        
        sql = """ 
            select tax.tax_code_id, tax.base_code_id,((tax.amount*100) * -1) as amount
                from account_invoice_line_tax line_tax,account_tax tax
                where 
                 line_tax.tax_id = tax.id
                 and tax.tax_code_id is not null
                 and invoice_line_id in(
                     select id
                       from account_invoice_line
                       where invoice_id in (
                         select id
                         from account_invoice
                         where type = 'in_invoice'
                         and tipo_factura = 'invoice'
                         and period_id = """ + str(period_id) + """
                       )
                )
        """
        cr.execute(sql)
        ##print "sql\n", sql
        res = cr.dictfetchall()
        ids1 = []
        for linea in res:
            ids1.append(linea['tax_code_id'])
            ids1.append(linea['base_code_id'])
                        
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'data':out, 'name':'ATS.xls'}, context=context)
        
    _columns = {
                'period_id': fields.many2one('account.period', 'Periodo'),
                'name':fields.char('Nombre', size=60),
                'data': fields.binary(string='Archivo'),
                }
    _defaults = {
                 'period_id':_get_default_period,
                 }
wizard_account_ats()