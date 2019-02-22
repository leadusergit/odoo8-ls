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
    'name' : 'Ecuador - General Data',
    'version' : '1.1',
    'author' : 'Leadsolutions Cia. Ltda.',
    'category' : 'Accounting & Finance',
    'description' : """
Datos básicos para el Ecuador.
====================================
Éste módulo aumenta datos básicos para el manejo de empresas en Ecuador, además crea datos básicos como provincias entre otras.
""",
    'website': 'http://leadsolutions.com.ec',
    'images' : [],#'images/accounts.jpeg','images/bank_statement.jpeg','images/cash_register.jpeg','images/chart_of_accounts.jpeg','images/customer_invoice.jpeg','images/journal_entries.jpeg'],
    'depends' : ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/ec_data.xml',
        'data/res_partner_titles.xml',
        'data/res_bank.xml',
        'views/base_ec.xml',
        'views/states_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}