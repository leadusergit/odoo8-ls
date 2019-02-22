# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    Author: Israel Paredes Reyes <israelparedesreyes@gmail.com>
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


class wizard_provision_pay(models.TransientModel):

    _name = 'wizard.provision.pay'
            
    date_from=fields.Date('Fecha Inicio', default=time.strftime('%Y-%m-%d'),required=True)
    date_to=fields.Date('Fecha Fin', default=time.strftime('%Y-%m-%d'),required=True)
       

    @api.multi
    def run_sql(self):        
        self = self[0]
        buf = StringIO.StringIO()
        writer = csv.writer(buf, delimiter=';')
        self.env.cr.execute('''select sum(pl.amount),pl.employee_id,empleado.name_related
                                from hr_employee_provision_pay pp,hr_employee_provision_pay_line pl,hr_employee empleado
                                where pp.id=pl.ppay_id 
                                and pl.employee_id=empleado.id
                                and pl.period_start <=%s and pl.period_end <=%s
                                and pp.provision ='dc'
                                group by employee_id,empleado.name_related
                                order by 2''' % (self.date_from,self.date_to))            
        res = self.env.cr.dictfetchall()
        cadena= "".join(str(res))
        
        cadena1=cadena.replace("[{'name_related': u'",'')
        cadena2=cadena1.replace("{'name_related': u'",'\r\n')
        cadena3=cadena2.replace("'sum':",'')
        cadena4=cadena3.replace("}",'')
        cadena5=cadena4.replace("]",'')
        cadena6=cadena5.replace("'employee_id':",'-')
        cadena7=cadena6.replace("'",'')
        cadena8=cadena7.replace(cadena7,'Empleado,Monto'+ '\r\n' + cadena7)


        out = base64.encodestring(cadena8)
        print"out=%s"%out
        
        return self.env['base.file.report'].show(out, 'DecimoCuarto.csv')
    

   
   
   
class wizard_provision_paydt(models.TransientModel):

    _name = 'wizard.provision.paydt'
            
    date_from=fields.Date('Fecha Inicio', default=time.strftime('%Y-%m-%d'),required=True)
    date_to=fields.Date('Fecha Fin', default=time.strftime('%Y-%m-%d'),required=True)
       

    @api.multi
    def run_sql_dt(self):        
        self = self[0]
        buf = StringIO.StringIO()
        writer = csv.writer(buf, delimiter=';')
        self.env.cr.execute('''select sum(pl.amount),pl.employee_id,empleado.name_related
                                from hr_employee_provision_pay pp,hr_employee_provision_pay_line pl,hr_employee empleado
                                where pp.id=pl.ppay_id 
                                and pl.employee_id=empleado.id
                                and pl.period_start <=%s and pl.period_end <=%s
                                and pp.provision ='dt'
                                group by employee_id,empleado.name_related
                                order by 2''' % (self.date_from,self.date_to))            
        res = self.env.cr.dictfetchall()
        cadena= "".join(str(res))
        
        cadena1=cadena.replace("[{'name_related': u'",'')
        cadena2=cadena1.replace("{'name_related': u'",'\r\n')
        cadena3=cadena2.replace("'sum':",'')
        cadena4=cadena3.replace("}",'')
        cadena5=cadena4.replace("]",'')
        cadena6=cadena5.replace("'employee_id':",'-')
        cadena7=cadena6.replace("'",'')
        cadena8=cadena7.replace(cadena7,'Empleado,Monto'+ '\r\n' + cadena7)


        out = base64.encodestring(cadena8)
        print"out=%s"%out
        
        return self.env['base.file.report'].show(out, 'DecimoTercero.csv')
   