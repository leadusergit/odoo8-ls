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
import StringIO
import xlwt
import csv
import re
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

from xlwt import Workbook
from openerp.addons.base_ec.tools.xls_tools import *

def style(bold=False, font_name='Calibri', size=10, font_color='black',
          rotation=0, align='left', vertical='center', wrap=False,
          border=False, color=None, format=None):
        return get_style(bold, font_name, size, font_color, rotation, align, vertical, wrap, border, color, format)


class wizard_report_spi(models.TransientModel):

    _name = 'wizard.report.spi'

    date_from=fields.Date('Fecha Inicio', default=time.strftime('%Y-%m-%d'),required=True)
    date_to=fields.Date('Fecha Fin', default=time.strftime('%Y-%m-%d'),required=True)
    payslip_ids=fields.Many2many('hr.payslip', required=True, domain=[('state', '=', 'done')],
                                   default=lambda self: self._context.get('active_ids', []))
    
    
    @api.multi
    def run_sql(self):
        self = self[0]
        buf = StringIO.StringIO()
        writer = csv.writer(buf, delimiter=';')
        
        qry = '''select hr_employee.identification_id CedulaRuc,hr_employee.name_related Nombre,rpb.bank_bic InstitucionFinanciera,
                 rpb.acc_number CuentaBeneficiario,rpb.acc_type TipoCuenta,psl.amount Valor,20103 Concepto ,ps.date_to Detalle
                 from hr_payslip ps,hr_payslip_line psl,hr_employee,res_partner_bank rpb
                 where ps.id=psl.slip_id 
                 and hr_employee.id=psl.employee_id
                 and hr_employee.bank_account_id=rpb.id
                 and psl.salary_rule_id=4
                 and psl.create_date::date between %s and %s order by 2'''
        
        self._cr.execute(qry,(self.date_from,self.date_to))
        res = self._cr.dictfetchall()
        print"res=%s"%res
        cadena= "".join(str(res)) #(" ".join(map(str, res)))#

        cadena1=cadena.replace("COR",'1')
        cadena2=cadena1.replace("AHO",'2')
        cadena3=cadena2.replace("[{",'')
        cadena4=cadena3.replace("}]",'')
        cadena5=cadena4.replace("u'",'')
        cadena6=cadena5.replace("'",'')
        cadena7=cadena6.replace("{",'\r\n')
        cadena8=cadena7.replace("}",'')
        cadena9=cadena8.replace("cedularuc:",'')
        cadena10=cadena9.replace("nombre:",'')
        cadena11=cadena10.replace("institucionfinanciera:",'')
        cadena12=cadena11.replace("cuentabeneficiario:",'')
        cadena13=cadena12.replace("tipocuenta:",'')
        cadena14=cadena13.replace("valor:",'')
        cadena15=cadena14.replace("concepto:",'')
        cadena16=cadena15.replace("detalle:",'')
        cadena17=cadena16.replace(cadena16,'Tipo Cuenta,Concepto,Institucion Financiera,Cuenta Beneficiario,Valor,Nombre,Cedula/Ruc,Detalle' + '\r\n' + cadena16)

        print"cadena17=%s"%cadena17

        out = base64.encodestring(cadena17)
        print"out=%s"%out
        
        return self.env['base.file.report'].show(out, 'spi.csv')

