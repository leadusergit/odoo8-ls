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
{
    'name': "Exportar Resumen Impuestos Ventas",
    'version': '1.0',
    "depends" : ["account","account_invoice_retention","account_report_extend"],
    'author': "LeadSolutions Cia. Ltda",
    'website': 'http://leadsolutions.ec',
    'category': 'Accounting',
    'description': u"""Exportar XML""",
    'init_xml': [],
    'data': [
        "views/export_saletax.xml",
    ],
}