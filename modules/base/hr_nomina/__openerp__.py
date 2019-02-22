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
    'name': "Basic payroll in Ecuador",
    'version': '1.0',
    "depends" : ["hr_ec", "hr_contract"],
    'author': "LeadSolutions Cia. Ltda",
    'website': 'http://leadsolutions.ec',
    'category': 'Human Resources',
    'description': u"""
=======================================
Módulo básico para la nómina de Ecuador
=======================================

Con él usted podrá administrar y crear el rol de pagos de los empleados de su empresa en régimen Ecuatoriano.

Éste modulo permite realizar las siguientes funcionalidades:
* Contratos secuenciales (prueba, definido, indefinido).
* Notifica que contratos están a punto de caducar.
* Administración de ingreso, egresos y provisiones.
* Ficha del empleado con registro de datos relevantes.
* Generación en masa de los roles de pago de empleados.
* Envia los roles de pagos a los correos de los empleados.
* Reporte de la Nómina.
    """,
    'init_xml': ['data/stored_procedures.xml', 'data/configurations.xml'],
    'data': [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/hr_import_csv.xml",
        "views/hr_contract_view.xml",
        "views/hr_payroll_view.xml",
        "views/hr_employee_view.xml",
        "views/hr_family_item_view.xml",
        "views/hr_report.xml",
        "views/wizard_payroll_validate.xml",
        "views/wizard_payroll_set_calculated.xml",
        "views/hr_wizard.xml",
        "views/hr_employee_family_view.xml",
        "views/hr_menu_items.xml",
    ],
}