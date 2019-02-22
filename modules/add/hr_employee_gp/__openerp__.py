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
    'name': "Gastos Personales Empleados EC",
    'version': '1.0',
    'depends': ['hr_payroll','hr_nomina'],
    'author': "LeadSolutions Cia. Ltda.",
    'category': 'Human Resources',
    'description': """
Impuesto sobre la renta de los empleados en Ecuador
===================================================
Permite registrar los datos necesarios para causar el impuesto a la renta de los empleados.
Según la normativa vigente, el empleado deberá presentar el formulario 107 y actuar como agente de retención del impuesto

Éste modulo permite:
--------------------
    * Registrar la tabla anual para el cálculo del impuesto a la renta.
    * Registrar las bases para las deducciones.
    * Cada empleado podrá realizar su deducción de gastos personales.
    * Automáticamente mostrará el total de ingresos estimados.
    """,
    # data files always loaded at installation
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'hr_employee_gp_data.xml',
        'models/hr_employee_gp.xml',
        #'wizards/create_collection_plan.xml'
    ],
}