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
{
    'name': "Account module for basic payroll in Ecuador",
    'version': '1.0',
    'depends': ["hr_nomina", "payments"],
    'author': "LeadSolutions Cia. Ltda.",
    'website': 'http://leadsolutions.ec',
    'category': 'Accounting & Finance',
    'description': """
Módulo contable para la nómina de Ecuador.
==========================================

Éste módulo extiende la funcionalidad del módulo de nómina ecuatoriano para la creación de asientos contables.

Provee las siguientes funcionalidades:
--------------------------------------
* Administración contable para los ingresos, egresos y provisiones.
* Crea el Diario de Nómina.
* Creación automática de asientos contables a partir de la nómina.
    """,
    'init_xml': ['data/nomina_account.xml'],
    'data': [
        "security/ir.model.access.csv",
        "views/hr_payroll_view.xml",
        "views/hr_employee_view.xml",
        "views/hr_wizards.xml",
        "views/hr_menu_items.xml",
    ],
}