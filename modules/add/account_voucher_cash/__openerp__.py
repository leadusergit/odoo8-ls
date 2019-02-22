# -*- coding: utf-8 -*-
###################################################
#
#    Payments Module
#    Copyright (C) 2012 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
#    $autor: Dairon Medina Caro <dairon.medina@gmail.com>
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
###################################################
{
    'name': "Account Voucher Cash Management",
    'version': "1.0",
    'category': "Enterprise Specific Modules/Accounting",
    'author': "LeadSolutions Cia. Ltda.",
    'website' : 'http://www.leadsolutions.ec',
    "description": """
                   Genera Cash Management de vouchers seleccionados
                   """,
    'depends': ['base','account_voucher'],
    'init_xml': [],
    'data': ["views/voucher_cash_management.xml",],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
