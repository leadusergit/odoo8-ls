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
    'name': "Report Balance Format Excel",
    'version': '1.0',
    'depends': ['account', 'account_invoice_retention', 'account_reporting'],
    'author': "OpenConsulting Cia. Ltda.",
    'website': 'http://www.openconsulting.com.ec',
    'category': 'Accounting & Finance',
    'description': """
      Reporte de Balances General y Perdidas y Ganacias en formato Excel
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/view_rel_det_cash_flow_acc.xml',
        'views/view_wizard_report_balance.xml',
        'views/view_wizard_report_balance_general.xml',
        'views/view_wizard_general_ledger_xsl.xml',
        'views/account_list_ordering_view.xml',
        'views/view_cash_flow_elimination.xml',
        'views/view_cash_flow_elimination.xml',
        'views/wizard/view_cash_flow.xml',
        'views/view_menu_item.xml',
        'views/wizard_patrimonio.xml',
        'views/view_account.xml',
    ],
}