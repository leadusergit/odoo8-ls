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


class wizard_generate_expense(models.TransientModel):

    _name = 'wizard.generate.expense'

    periodo=fields.Many2one('hr.contract.period', string='Periodo',required=True)
    expense_ids=fields.Many2many('hr.expense', required=True, default=lambda self: self._context.get('active_ids', []))
    
    
    @api.multi
    def crear_expense(self):
        self = self[0]
        for expense in self.expense_ids:
            gasto_obj =self.env['hr.expense']
            empleado= expense.employee_id.id
            contrato= expense.contract_id.id
            company=  expense.company_id.id,
            periodo=  self.periodo.id
            expense_type=expense.expense_type_id.id

                
            vals = dict(expense_type_id= expense_type,
                        employee_id= empleado,
                        period_id= periodo, 
                        company_id= company,
                        contract_id= contrato,
                        value= expense.value,
                        name= expense.name,
                        transfers=[])
     
            gasto =self.env['hr.expense'].create(vals)

               

