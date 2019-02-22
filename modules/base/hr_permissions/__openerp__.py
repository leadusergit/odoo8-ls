# -*- coding: utf-8 -*-
###################################################
#
#    HR Nomina
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
    "name" : "Permission of employees",
    "version" : "1.0",
    "depends" : ["hr_nomina"],
    'author': 'OpenConsulting Cia. Ltda.',
    "category": "Human Resources",
    'website': 'http://www.openconsulting.com.ec',
    'description': """
Permisos de los trabajadores
============================
Permissions module that covers:
-------------------------------
* In this module your employees will can register their permissions, after their boss will validate this permissions.
    """,
    'init_xml': ['data/hr_permissions.xml'],
    'update_xml': [
               "security/security.xml",
               "security/ir.model.access.csv",
               "views/hr_permissions_view.xml",
               "views/hr_menu_items.xml",               
               "workflows/hr_ec_workflow.xml",
               "sequence/sequence_permission.xml"
    ],
    'installable': True,
    'active': False,
}