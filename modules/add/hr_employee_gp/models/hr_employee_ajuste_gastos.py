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
import time, openerp.modules as addons
from openerp.osv import osv, fields
from openerp.addons.hr_nomina.payroll_tools import *
from openerp import api
import unicodedata

class hr_employee_expenses_adjustments(osv.osv):
    _name = "hr.employee.expenses.adjustments"
    _description = u'Ajuste Gastos personales de los empleados'
    
    _columns = {                
        'employee_id':fields.many2one('hr.employee','Empleado'),
        'fiscalyear_id':fields.many2one('hr.fiscalyear','Año Fiscal'),
        'period_end_id':fields.many2one('hr.contract.period','Periodo Final'),
        'period_start_id':fields.many2one('hr.contract.period','Periodo Inicial'),
        'aporte_iess_otro_empleador':fields.float('Aporte Iess'),
        'company_id':fields.many2one('res.company','Empresa'),
        'ingresos':fields.float('Ingresos'),
        'gasto_recaudado':fields.float('Valor Retencion Asumido'),
        
    }