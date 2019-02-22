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


class wizard_report_payslip(models.TransientModel):

    _name = 'wizard.report.payslip'

    date_from=fields.Date('Fecha Inicio', default=time.strftime('%Y-%m-%d'),required=True)
    date_to=fields.Date('Fecha Fin', default=time.strftime('%Y-%m-%d'),required=True)
    payslip_ids=fields.Many2many('hr.payslip', required=True, domain=[('state', '=', 'done')],
                                   default=lambda self: self._context.get('active_ids', []))
    
    
    @api.multi
    def run_sql(self):
        
        qry = '''select psl.name Descripcion,SUM(psl.amount) Suma
                 from hr_payslip ps,hr_payslip_line psl
                 where ps.id=psl.slip_id and psl.amount >0
                 and psl.write_date::date between %s and %s
                 group by psl.name
                 order by 1'''
        self._cr.execute(qry,(self.date_from,self.date_to))
        res = self._cr.dictfetchall()
        print"res=%s"%res
        
        
        #for key,val in res.items():
        #    print key, "=>", val
        
        #regex= r"\bSub[\w]*"

        cadena= "".join(str(res)) #(" ".join(map(str, res)))#
        #aux = re.findall(regex, str(res))#re.findall(r"\'([A-Za-z]+)\'", str(res))
        #cadena = " ".join(aux)   

        out = base64.encodestring(cadena)
        print"out=%s"%out
        
        return self.env['base.file.report'].show(out, 'payslip_totales.xls')

