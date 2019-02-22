# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution.
#    Module for basic payroll in Ecuador.
#    Copyright (C) 2010-2013 Israel Paredes Reyes. All Rights Reserved.
#    
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
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



class account_tax_fechas_add(osv.osv_memory):
    _inherit= "account.tax.fechas"
        


    def llamar_reporte1(self, cr, uid, ids, context={}):
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
            
            invoice_tax_ids=self.pool.get('account.invoice.retention.voucher').search(cr, uid,
                                                                         [('invoice_id','=',factura)])
            tax_line_ids=self.pool.get('account.invoice.retention.voucher.line').search(cr, uid,
                                                                         [('ret_voucher_id','=',invoice_tax_ids)])
            
            for linea in self.pool.get('account.invoice.retention.voucher.line').browse(cr, uid, tax_line_ids):
                if not (linea.tax_id.name in tipos.keys()):
                    tipo_id = self.pool.get('account.tax.type').create(cr, uid, {
                            'header_id': header_id,
                            'name': linea.tax_id.name,
                            'code': linea.tax_id.description,
                            #'formulario':'xxx'
                            
                            })
                    tipos[linea.tax_id.name]=linea.tax_id.name
                else:
                    tipo_id = self.pool.get('account.tax.type').search(cr, uid, [('name','=',linea.tax_id.name),('header_id','=',header_id)])[0]
                
                line_id=self.pool.get('account.tax.report.linea').create(cr, uid, {
                        'type_id':tipo_id,
                        #'tax_invoice_id':linea.tax_id.id,
                        'impuesto':linea.tax_id.name,
                        'fecha':linea.ret_voucher_id.invoice_id.date_invoice,
                        'documento':linea.ret_voucher_id.invoice_id.number,
                        'nombre':linea.ret_voucher_id.invoice_id.partner_id.name,
                        'ruc':linea.ret_voucher_id.invoice_id.partner_id.ident_num,
                        'b_imponible':linea.tax_base,
                        'porcentaje':linea.tax_id.amount,
                        'valor':linea.tax_base * linea.tax_id.amount,
                        })
                tipo=self.pool.get('account.tax.type').browse(cr, uid, tipo_id)
                self.pool.get('account.tax.type').write(cr, uid, tipo_id, {
                        'b_total':tipo.b_total+linea.tax_base,
                        'v_total':tipo.v_total+ (linea.tax_base * linea.tax_id.amount),
                        })
        return {
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'account.tax.header',
            'type': 'ir.actions.act_window',
            'res_id' : header_id,
        } 


