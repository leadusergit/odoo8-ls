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
    'name': "Datos contables para Ecuador",
    'description': """
        Carga de datos contables para Ecuador:
            - Código de impuestos
            - Impuestos
            - Tipos de Contribuyentes
    """,
    'author': "OpenConsulting Cia. Ltda.",
    'website': "http://www.openconsulting.com.ec",
    'category': 'Extra Tools',
    'version': '0.1',
    'depends': ['account_invoice_retention'],
    'data': [
        'data/account.tax.code.csv',
        'data/account.tax.csv',
	'data/account.fiscal.position.csv',
    ],
}
