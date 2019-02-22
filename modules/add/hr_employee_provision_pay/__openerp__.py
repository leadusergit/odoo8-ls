# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
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
{
    'name': "Pago Decimos",
    'version': '1.0',
    'depends': ['account_voucher','payments','hr_payroll','hr_nomina','hr_employee_plantillac'],
    'author': "LeadSolutions Cia. Ltda.",
    'category': 'Human Resources',
    'description': """    """,
    # data files always loaded at installation
    'data': ['views/hr_employee_provision_pay_view.xml',
             'views/hr_payslip_payments_decimos.xml',
             'wizard/wizard_provision_pay.xml',
             'wizard/wizard_generated_decimos.xml',
    ],
}