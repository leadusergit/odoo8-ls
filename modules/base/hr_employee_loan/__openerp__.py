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
    "name": "Employee's Laon",
    "version": "1.0",
    "depends": ["hr_nomina"],
    "author": "OpenConsulting Cia. Ltda.",
    "category": "Human Resources",
    "description": """
==========================
Préstamos a colaboradores
==========================
Éste módulo permite registrar los préstamos que se hacen a los colaboradores. 
    """,
    'data': ['ir.model.access.csv', 'hr_employee_loan.xml'],
    'installable': True,
    'active': False,
}