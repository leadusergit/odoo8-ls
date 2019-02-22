# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution.
#    Account module for basic payroll in Ecuador.
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

from openerp.osv import osv, fields

class hr_department(osv.osv):
    _inherit = 'hr.department'
    _columns = {'analytic_id': fields.many2one('account.analytic.account', 'Centro de costos')}
hr_department()

class hr_employee_ec(osv.osv):
    _name = "hr.employee"
    _inherit = "hr.employee"
    _columns = {
        'debit_account': fields.many2one('account.account', 'Cuenta contable al debe'),
        'credit_account': fields.property(
            type='many2one',
            relation='account.account',
            string='Cuenta contable',
            domain="[('type', '=', 'other')]",
            required=True),
        'anticipo_debit_account':fields.many2one('account.account', 'Cuenta anticipo al debe'),
        }
hr_employee_ec()