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
    'name': "Module Payment in Ecuador",
    'version': "1.0",
    'category': "Enterprise Specific Modules/Accounting",
    'author': "LeadSolutions Cia. Ltda.",
    'website' : 'http://www.leadsolutions.ec',
    "description": """
                   Payments Ecuador: Pagos por Transferencia, Cheque y Tarjetas de Credito de la Empresa
                   """,
    'depends': ['base','account','account_invoice_retention'],
    'init_xml': [],
    'data': [
                   "sequence/payments_sequence.xml",
                   "security/payments_groups.xml",
                   "views/cash_management.xml",
                   "views/payment_menu.xml",
                   "views/wizard_payment_statement.xml",
                   "views/wizard_payment_unreconcile.xml",
                   "views/wizard_payment_transfer_excel.xml",
                   "views/payment_view.xml",
                   "views/wizard_payment_report.xml",
                   "security/ir.model.access.csv",
                   "views/wizard_payment_regenerate_view.xml",
                   "views/wizard_payment_nomina_public.xml",
                   "views/account_bank_statement.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
