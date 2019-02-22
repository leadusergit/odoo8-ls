# -*- coding: utf-8 -*-
##############################################################################
#
#    Gnuthink Software Labs
#    Copyright (C) 2004-2009 
#    $Id$
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

__author__ = 'mario.chogllo@gnuthink.com (Mario Chogllo)'

import time
import datetime
#from datetime import *
from openerp.osv import osv
from openerp.osv import fields
from mx import DateTime
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime
from xml.dom.minidom import Document
import StringIO
import csv
from time import strftime
import base64
from xlwt import Workbook
from openerp.addons.base_ec.tools.xls_tools import *

def style(bold=False, font_name='Calibri', size=10, font_color='black',
          rotation=0, align='left', vertical='center', wrap=False,
          border=False, color=None, format=None):
    return get_style(bold, font_name, size, font_color, rotation, align, vertical, wrap, border, color, format)

class account_tax_fechas(osv.osv_memory):
    _name = "account.tax.fechas"
        
    _columns = {
        'inicio':fields.date('Inicio', required=True),
        'fin':fields.date('Fin', required=True),
        'company_id':fields.many2one('res.company','Compañia')
        }    
    
    _defaults = {
        'inicio': lambda *a: time.strftime('%Y-%m-%d'),
        'fin': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid,context=context).company_id.id,
    }

    def llamar_reporte(self, cr, uid, ids, context={}):
        facturas_ids = []
        #print 'ids', ids
        for actual in self.browse(cr, uid, ids, context):
            ds = mx.DateTime.strptime(actual.inicio, '%Y-%m-%d')	
            #print 'actual.company_id', actual.company_id
            #print 'actual.company_id_[0]', actual.company_id.id
            facturas_ids = self.pool.get('account.invoice').search(cr, uid,[('date_invoice', '<=', actual.fin),
                                                                        ('date_invoice','>=',actual.inicio),
                                                                        ('company_id','=',actual.company_id and actual.company_id.id),
                                                                        ('state','not in',['cancel'])])
            header_id=self.pool.get('account.tax.header').create(cr, uid, {
                    'inicio':actual.inicio,
                    'fin':actual.fin,
                    })
        tipos = {}
        for factura in facturas_ids:
            #print 'facturas_ids',factura
            fact = self.pool.get('account.invoice').browse(cr, uid, factura)
            
            invoice_tax_ids=self.pool.get('account.invoice.tax').search(cr, uid,
                                                                         [('invoice_id','=',factura)],
#                                                                           ('tax_group','in',['ret_vat','ret_ir','no_ret_ir'])],
                                                                        order='name')
            for linea in self.pool.get('account.invoice.tax').browse(cr, uid, invoice_tax_ids):
                if not (linea.name in tipos.keys()):
                    tipo_id = self.pool.get('account.tax.type').create(cr, uid, {
                            'header_id': header_id,
                            'name': linea.name,
                            'code': linea.tax_code_id.code,
                            'formulario': linea.tax_code_id.formulario
                            
                            })
                    tipos[linea.name]=linea.name
                else:
                    tipo_id = self.pool.get('account.tax.type').search(cr, uid, [('name','=',linea.name),('header_id','=',header_id)])[0]
                
                doc= fact.tipo_factura
                if doc=='invoice':
                    doctipo='Factura'+ str(fact.number_inv_supplier)
                if doc=='purchase_liq':
                    doctipo='L.Compra'+ str(fact.number_inv_supplier)
                if doc=='sales_note':
                    doctipo='N.Venta'+ str(fact.number_inv_supplier)
                if doc=='doc_inst_est':
                    doctipo='D.E.Estado'+ str(fact.number_inv_supplier)
                if doc=='gas_no_dedu':
                    doctipo='G.no dedu'+ str(fact.number_inv_supplier)
                if doc=='gasto_financiero':
                    doctipo='G.Finan' + str(fact.number_inv_supplier)
                if doc=='anticipo':
                    doctipo='Anticipo' + str(fact.number_inv_supplier)
                if doc=='alicuota':
                    doctipo='Alicuota' + str(fact.number_inv_supplier)
                    
                    
                line_id=self.pool.get('account.tax.report.linea').create(cr, uid, {
                        'type_id':tipo_id,
                        'tax_invoice_id':linea.id,
                        'impuesto':linea.name,
                        'fecha':fact.date_invoice,
                        'documento':doctipo,
                        'tipodoc':doctipo,
                        'nombre':fact.partner_id.name,
                        'ruc':fact.partner_id.ident_num,
                        'b_imponible':linea.base,
                        'porcentaje':linea.percent,
                        'valor':linea.amount,
                        })
                tipo=self.pool.get('account.tax.type').browse(cr, uid, tipo_id)
                self.pool.get('account.tax.type').write(cr, uid, tipo_id, {
                        'b_total':tipo.b_total+linea.base,
                        'v_total':tipo.v_total+linea.amount,
                        })
        return {
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'account.tax.header',
            'type': 'ir.actions.act_window',
            'res_id' : header_id,
        } 

account_tax_fechas()

class account_tax_header(osv.osv):
    _name = "account.tax.header"
      
    _columns = {
        'inicio':fields.date('Inicio', required=True, readonly=True),
        'fin':fields.date('Fin', required=True, readonly=True),
	    'tax_ids':fields.one2many('account.tax.type', 'header_id', 'Tipos de impuestos', required=True, readonly=True),
        }

    _defaults = {
    }
    
    def print_xls(self, cr, uid, ids, context=None):
        def evalobj(obj, field):
            for attr in field.split('.'):
                if hasattr(obj, attr):
                    obj = getattr(obj, attr)
                else:
                    break
            return obj
        book = Workbook()
        obj = self.browse(cr, uid, ids[0])
        formtaxes = {}
        for tax in obj.tax_ids:
            formtaxes[tax.formulario] = formtaxes.get(tax.formulario, []) + [tax]
        FIELDS = [
            (u'Fecha', 'fecha', 'std'),
            (u'Asiento', 'tax_invoice_id.ret_id.move_ret_id.name', 'std'),
            (u'Documento', 'documento', 'std'),
            #(u'Contribuyente', 'tax_invoice_id.invoice_id.partner_id.name' or 'nombre', 'std'),
            #(u'R.U.C.', 'tax_invoice_id.invoice_id.partner_id.ident_num' or 'ruc', 'std'),
            (u'Contribuyente','nombre', 'std'),
            (u'R.U.C.', 'ruc', 'std'),
            (u'No. Retención', 'tax_invoice_id.ret_id.name', 'std'),
            (u'B. Imponible', 'b_imponible', 'num'),
            (u'Porcentaje', 'porcentaje', '%'),
            (u'Valor', 'valor', 'num')
        ]
        FIELDS_RES = [
            (u'Tipo', 'name', 'std'),
            (u'Total B. Imponible', 'b_total', 'num'),
            (u'Total Valor', 'v_total', 'num'),
            (u'Movimientos', 'lineas_ids', 'std')
        ]
        STYLES = {
            'std': style(),
            'bold': style(True, size=12),
            'title': style(True, font_color='white', color='periwinkle', align='center'),
            '%': style(format='0.00%'),
            'num': style(format='[$$-300A]#,##0.00;[$$-300A]-#,##0.00', align='right'),
            'numbold': style(True, format='[$$-300A]#,##0.00;[$$-300A]-#,##0.00', align='right')
        }
        for formulario, taxes in formtaxes.iteritems():
            sheet = book.add_sheet(formulario and str(formulario) or 'Des')
            row = 5
            for tax in taxes:
                sheet.write(row, 0, 'Impuesto: %s'%tax.name, STYLES['bold'])
                for col, field in enumerate(FIELDS, 0):
                    sheet.write(row+1, col, field[0], STYLES['title'])
                for aux, detail in enumerate(tax.lineas_ids, 0):
                    for col, (field, attr, sty) in enumerate(FIELDS, 0):
                        sheet.write(aux+row+2, col, evalobj(detail, attr) or '', STYLES[sty])
                row += len(tax.lineas_ids) + 3
            #=======================================================================
            # Resumen Tributario
            sheet.write(row, 0, 'RESUMEN TRIBUTARIO', STYLES['bold'])
            for col, field in enumerate(FIELDS_RES, 0):
                sheet.write(row+2, col, field[0], STYLES['title'])
            for aux, tax in enumerate(taxes, 0):
                for col, (field, attr, sty) in enumerate(FIELDS_RES):
                    value = evalobj(tax, attr)
                    value = '(%s Registros)'%len(value) if field == u'Movimientos' else value
                    sheet.write(aux+row+3, col, value or '', STYLES[sty])
            #=======================================================================
        buf = StringIO.StringIO()
        book.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return self.pool.get('base.file.report').show(cr, uid, out, 'Impuestos.xls')

account_tax_header()

class account_tax_type(osv.osv):
    _name = "account.tax.type"
    _columns = {
        'header_id': fields.many2one('account.tax.header','Reporte impuestos', readonly=True),
        'name':fields.char("Tipo", size=100),
        'lineas_ids':fields.one2many('account.tax.report.linea', 'type_id', 'Movimiento', required=False, readonly=True),
        'b_total':fields.float('Total B. Imp'),
        'v_total':fields.float('Total Valor'),
        'code':fields.char('Codigo'),
        'formulario':fields.integer('formulario'),
        }
account_tax_type()

class account_tax_report_linea(osv.osv):
    _name = "account.tax.report.linea"
    _order = 'impuesto'
    _columns = {
        'impuesto':fields.char('RETENCION', size=32),
        'fecha': fields.date('Fecha'),
        'documento':fields.char('Documento',size=16),
        'nombre':fields.char('Nombre',size=32),
        'ruc':fields.char('RUC',size=14),
        'b_imponible':fields.float('B. Imponible'),
        'porcentaje':fields.float('Porcentaje', digits=(8,16)),
        'valor':fields.float('Valor'),
        'type_id': fields.many2one('account.tax.type','Tipo', readonly=True),
        'tax_invoice_id': fields.many2one('account.invoice.tax', required=True, readonly=True, ondelete='cascade')
        }
    
account_tax_report_linea()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
