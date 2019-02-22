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

{
    'name': "Reporting of Balancesheet for accounting",
    'version': '1.0',
    'depends': ['base', 'account_reporting', 'account_report', 'account_invoice_retention'],
    'author': "LeadSolutions Cia. Ltda.",
    'category': 'Accounting & Finance',
    'description': """Financial and accounting reporting
                      Balance Sheet Report""",
    # data files always loaded at installation
    'data': [
        'sequence/account_ats_sequence.xml',
        'account_reportfa_view.xml',
        'report_tax_view.xml',
        'views/report_wizard_menu.xml',
        'views/report_account_balance_results.xml',
        'views/report_statement_customer.xml',
        'views/report_statement_supplier.xml',
        'views/report_invoices_customer.xml', #Reporte de Facturas de Clientes
        'views/report_customer_portfolio.xml', #Analisis de Cartera
        'views/wizard_generate_xml_ats.xml',
        'views/wizard_report_account_ats.xml',
        'views/wizard_report_sale_product.xml',
        'views/wizard_report_tax.xml',
        'views/wizard_report_incomes.xml',
        'views/wizard_report_invoice_supplier.xml',
        'security/ir.model.access.csv',
        'views/wizard_sales_by_product_report.xml',
        'views/wizard_report_formulario101.xml',
        #'views/account_move_line.xml',
    ],
    # data files containing optionally loaded demonstration data
    'demo': [],
}