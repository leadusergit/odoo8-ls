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
import time
import datetime
import base64
import xlwt
import csv
import re
import StringIO
from base64 import encodestring
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
from openerp.tools.translate import _
from openerp.osv import osv
from openerp import models, fields, api
from mx import DateTime
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime
from xml.dom.minidom import Document
from time import strftime
from xlwt import Workbook, Formula
from openerp.addons.base_ec.tools.xls_tools import *

def style(bold=False, font_name='Calibri', size=10, font_color='black',
          rotation=0, align='left', vertical='center', wrap=False,
          border=False, color=None, format=None):
        return get_style(bold, font_name, size, font_color, rotation, align, vertical, wrap, border, color, format)


class wizard_report_invoice_ret(models.TransientModel):

    _name = 'wizard.report.invoice.ret'

    date_from=fields.Date('Desde', default=time.strftime('%Y-%m-%d'),required=True)
    date_to=fields.Date('Hasta', default=time.strftime('%Y-%m-%d'),required=True)
    invoice_ids=fields.Many2many('account.invoice', required=True, domain=[('state', '=', 'open'),('type', '=', 'in_invoice')],
                                   default=lambda self: self._context.get('active_ids', []))
    
    
    @api.multi
    def run_sql(self):
        self = self[0]
#         buf = StringIO.StringIO()
#         writer = csv.writer(buf, delimiter=';')
        
        qry = '''select p.name a,ai.ident_partner_num c,ai.origin b,ai.date_invoice e,ai.t_iva d,
                 air.name g,air.fecha f,ait.base_amount i,ait.name h,ait.amount k,air.access_key j
                 from res_partner p,account_invoice ai,account_invoice_retention air,account_invoice_tax ait
                 where ai.partner_id=p.id 
                 and ai.partner_id=air.partner_id
                 and ai.id=air.invoice_id and ai.ret_id=air.id
                 and air.id=ait.ret_id and ai.id=ait.invoice_id
                 and ai.state in ('open','paid')
                 and ai.type='in_invoice'
                 and tipo_factura in ('invoice','sales_note','purchase_liq','gas_no_dedu','alicuota','ticket_aereo')
                 and ai.date_invoice::date between %s and %s
                 order by air.access_key asc'''

        
        self._cr.execute(qry,(self.date_from,self.date_to))

        res = self._cr.dictfetchall()

        cadena= "".join(str(res)) #(" ".join(map(str, res)))#

        cadena1=cadena.replace("[{",'')
        cadena2=cadena1.replace("}]",'')
        cadena3=cadena2.replace("u'",'')
        cadena4=cadena3.replace("'",'')
        cadena5=cadena4.replace("{",'\r\n')
        cadena6=cadena5.replace("}",'')
        cadena7=cadena6.replace("a:",'')
        cadena8=cadena7.replace("b:",'')
        cadena9=cadena8.replace("c:","'")
        cadena10=cadena9.replace("d:",'')
        cadena11=cadena10.replace("e:",'')
        cadena12=cadena11.replace("f:",'')
        cadena13=cadena12.replace("g:",'')
        cadena14=cadena13.replace("h:",'')
        cadena15=cadena14.replace("i:",'')
        cadena16=cadena15.replace("j:","'")
        cadena17=cadena16.replace("k:",'')
        cadena18=cadena17.replace(cadena17,'Proveedor,Ruc,DocReferencia,FechaFactura,Impuestos,NumRetencion,FechaRetencion,Base,DescImpuesto,Monto,ClaveAcceso' + '\r\n' + cadena17)
        
        out = base64.encodestring(cadena18)
        print"out=%s"%out
        
        return self.env['base.file.report'].show(out, 'ListaRetencionesProveedor.csv')
    
    @api.multi
    def run_sql_customer(self):
        self = self[0]
        #         buf = StringIO.StringIO()
        #writer = csv.writer(buf, delimiter=';')
        
        
        qry_c = '''select ai.internal_number a,rc.partner c,ai.ident_partner_num b,ai.date_invoice e,rcl.tax_base d,at.name g,rc.ret_ir f,rc.ret_vat i,rc.total h
                    from res_partner p,account_invoice ai,account_invoice_retention_voucher rc,account_invoice_retention_voucher_line rcl,account_tax at
                    where ai.partner_id=p.id 
                    and rc.invoice_id=ai.id
                    and rc.id=rcl.ret_voucher_id
                    and at.id=rcl.tax_id
                    and ai.state in ('open','paid')
                    and ai.date_invoice::date between %s and %s
                    order by ai.date_invoice asc'''
        
        self._cr.execute(qry_c,(self.date_from,self.date_to))

        res = self._cr.dictfetchall()
        print "/*/**/*/*/*/res/*/*/=%s"%res
        cadena= "".join(str(res)) #(" ".join(map(str, res)))#

        cadena1=cadena.replace("[{",'')
        cadena2=cadena1.replace("}]",'')
        cadena3=cadena2.replace("u'",'')
        cadena4=cadena3.replace("'",'')
        cadena5=cadena4.replace("{",'\r\n')
        cadena6=cadena5.replace("}",'')
        cadena7=cadena6.replace("a:","'")
        cadena8=cadena7.replace("b:","'")
        cadena9=cadena8.replace("c:",'')
        cadena10=cadena9.replace("d:",'')
        cadena11=cadena10.replace("e:",'')
        cadena12=cadena11.replace("f:",'')
        cadena13=cadena12.replace("g:",'')
        cadena14=cadena13.replace("h:",'')
        cadena15=cadena14.replace("i:",'')
        cadena16=cadena15.replace(cadena15,'NumFactura,Cliente,CI/Ruc,FechaFactura,Base,Impuesto,RIR,RIVA,Total' + '\r\n' + cadena15)
        
        out = base64.encodestring(cadena16)
        #         print"out=%s"%out
        
        return self.env['base.file.report'].show(out, 'ListaRetencionesCliente.csv')
