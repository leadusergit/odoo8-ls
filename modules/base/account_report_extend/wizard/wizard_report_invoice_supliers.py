# -*- encoding: utf-8 -*-
##############################################################################
#
#    Tax reporte
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
#creador  *Vll

from openerp.osv import fields, osv
import time
import xlwt #as pycel
import xlsxwriter
from lxml  import etree
import cStringIO
import StringIO
import base64
import datetime
import openerp.tools
import re
from xml.dom.minidom import parse, parseString
from openerp.addons.web.controllers.main import ExcelExport
from openerp.addons.web.controllers.main import Export
#from django.http import HttpResponse

import locale


class wizard_report_invoice_supplier(osv.osv_memory):
    
    _name = "wizard.report.invoice.supplier"
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    
    def generate_report(self, cr, uid, ids, context=None):
            
        #print ' ids NNNN *****', ids
        
        
        style_cabecera = xlwt.easyxf('font: colour black, bold True;'
                                        'align: vertical center, horizontal center;'
                                        )

        linea_center = xlwt.easyxf('font: colour black;'
                                   'align: vertical center, horizontal center;'
                                   )
        print "linea_center=%s"%linea_center
        linea_left = xlwt.easyxf('font: colour black;'
                                   'align: vertical center, horizontal left;'
                                   )
        
        print "linea_left=%s"% linea_left
        wb = xlwt.Workbook(encoding="utf-8")
        print " wb=%s"%wb
        ws = wb.add_sheet("Facturas de Proveedores")
        print "  ws=%s"% ws
        ws.show_grid = False
        
        form = self.browse(cr, uid, ids)[0]
	args = []
	states = []
	if form.date_finish:
            args.append(('date_invoice', '<=', form.date_finish))        
	if form.date_start:
            args.append(('date_invoice', '>=', form.date_start))
        if form.draft==True:
            states.append('draft')
        if form.open==True:
            states.append('open')
        if form.paid==True:
            states.append('paid')
        if form.cancel==True:
            states.append('cancel')
        if states:
            args.append(('state', 'in', states))
	print 'Argumentos', args
	
	date_ini = form.date_start
        date_fin = form.date_finish
	estado_factura = form.estado_factura
	
        
	invoice_obj = self.pool.get('account.invoice')
        invoice_ids = invoice_obj.search(cr, uid, args, order='date_invoice')
	print 'Ids',invoice_ids
	#invoice_ids = invoice_obj.search(cr, uid, [('date_invoice', '<=', date_fin), ('date_invoice', '>=', date_ini), ('state', '=', estado_factura), ('type', '=', 'in_invoice')], order='date_invoice')
	##print 'Ids',invoice_ids	        

        invoices_data = invoice_obj.browse(cr, uid, invoice_ids)
	print 'datos',invoices_data 	
        
#        ws.write(1, 2, "Nro.Comp :", style_cabecera)
        ws.write(1, 5, "Empresa Provincial de Vivienda COVIPROV", style_cabecera)
        ws.write(2, 5, "FACTURAS DE PROVEEDORES", style_cabecera)
        ws.write(3, 5, "DESDE:" + date_ini, style_cabecera)
        ws.write(4, 5, "HASTA:" + date_fin, style_cabecera)
         
        ws.write(7, 1, "FECHA FACTURA", style_cabecera)
        ws.write(7, 2, "FECHA VENCIMIENTO", style_cabecera)
        ws.write(7, 3, "FACTURA", style_cabecera)
        ws.write(7, 4, "ESTADO", style_cabecera)
        ws.write(7, 5, "VALOR SIN IMPUESTO", style_cabecera)
        ws.write(7, 6, "VALOR IMPUESTO", style_cabecera)
        ws.write(7, 7, "TOTAL A PAGAR", style_cabecera)
        ws.write(7, 8, "SALDO", style_cabecera)
        ws.write(7, 9, "ORIGEN", style_cabecera)
        ws.write(7, 10, "PROVEEDOR", style_cabecera)
        ws.write(7, 11, "TIPO FACTURA", style_cabecera)
        ws.write(7, 12, "INFO ADICIONAL", style_cabecera)
        
        x = 4
        y = 8
        
        total_sin_impuesto = 0.0
        total_impuesto = 0.0
        total = 0.0
        total_residual = 0.0
        
        
        for invoice_data in invoices_data:
                print"invoice_data -128=%s"%invoice_data 

                y += 1
                x = 1 
                ws.write(y, x, invoice_data.date_invoice, linea_center)
                x += 1
                #print " y:%s x:%s" % (y, x)
                ws.write(y, x, invoice_data.date_due or 'No hay', linea_center)
                x += 1
                ws.write(y, x, invoice_data.factura, linea_center)
                x += 1
                state = invoice_data.state
                print" state=%s"%state
                estado = ''
                if state == 'open':
                    estado = 'ABR'
                #else:
                if state == 'paid':
                    estado = 'PAG'
                    #estado = 'PAGADO'
                    print"estado=%s"%estado
                    
                ws.write(y, x, estado, linea_center)
                x += 1
                total_sin_impuesto += invoice_data.amount_untaxed
                print"total_sin_impuesto=%s"%total_sin_impuesto
                ws.write(y, x, invoice_data.amount_untaxed, linea_center)
                x += 1
                total_impuesto += invoice_data.amount_tax
                print"total_impuesto=%s"%total_impuesto
                ws.write(y, x, invoice_data.amount_tax, linea_center)
                x += 1
                total += invoice_data.amount_total
                print"total=%s"%total
                ws.write(y, x, invoice_data.amount_total, linea_center)
                x += 1
                total_residual += invoice_data.residual
                print" total_residual=%s"% total_residual
                ws.write(y, x, invoice_data.residual, linea_center)
                x += 1
                origin = invoice_data.origin
                print"origin=%s"%origin
                
                if origin:
                    origen = invoice_data.origin
                    print"origen1=%s"%origen
                else:
                    origen = ''
                ws.write(y, x, origen, linea_left)
                x += 1
                ws.write(y, x, invoice_data.partner_id.name, linea_center)
                print"ws.write=%s"% invoice_data.partner_id.name
                x += 1
		ws.write(y, x, invoice_data.tipo_factura, linea_center)
                x += 1                
		if invoice_data.comment:
                    #print"invoice_data.comment=%s"%invoice_data.comment
                    ws.write(y, x, invoice_data.comment, linea_center)
                else:
                    ws.write(y, x, 'NINGUNA', linea_center)
                
                cont = 0
		
        
        
        y += 1
        ws.write(y, 5, total_sin_impuesto, style_cabecera)
        ws.write(y, 6, total_impuesto, style_cabecera)
        ws.write(y, 7, total, style_cabecera)
        ws.write(y, 8, total_residual, style_cabecera)
        
        
        ws.col(0).width = 550
        ws.col(1).width = 4550
        ws.col(2).width = 4550
        ws.col(3).width = 4500
        ws.col(6).height = 4000
        ws.col(7).height = 4000
                       
        """buf = cStringIO.StringIO() 
        print"buf=%s"%buf  
        wb.save(buf)
        print" wb.save(buf)=%s"% wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        print" out=%s"%out
        buf.close()"""             
        buf = StringIO.StringIO()        
        wb.save('report_invoice.xls')
        #print" wb.save(buf)=%s"%wb.save('report_invoice.xls')
        #print"buf.getvalue()=%s"%buf.getvalue()  
        out =buf.getvalue()#buf.read()
        #buf.close()
        print" out=%s"%out
        return self.write(cr, uid, ids, {'data':out, 'name':'reporte_invoice.xls', 'state':'res'})
        #return out
     
    _columns = {
        'date_start':fields.date('Fecha Desde'),
        'date_finish':fields.date('Fecha Hasta'),
        'data': fields.binary(string='Archivo'),
        'name':fields.char('Nombre', size=60),
	'draft':fields.boolean('Borrador'),
	'open':fields.boolean('Abierta'),
	'paid':fields.boolean('Pagada'),
	'cancel':fields.boolean('Anulada'),
        'estado_factura':fields.selection([
            ('draft', 'Borrador'),
            ('open', 'Abierta'),
            ('paid', 'Pagada'),
            ('cancel', 'Anulada')], 'Estado Factura'),
        
        'state':fields.selection([('ini', 'Inicial'),
                                   ('res', 'Resultado'),
                                  ], 'Estado'),
    }
    
    _defaults = {
    'date_start': lambda * a: time.strftime('%Y-%m-%d'),
    'date_finish': lambda * a: time.strftime('%Y-%m-%d'),
    'state':lambda * a:'ini'
    }            
          


wizard_report_invoice_supplier()
