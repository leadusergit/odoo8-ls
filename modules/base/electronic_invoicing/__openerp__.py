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
    'name': "Electronic invoicing in Ecuador",
    'version': '1.0',
    'depends': ['base', 'account_invoice_retention'],
    'author': "OpenConsulting Cia. Ltda.",
    'category': 'Accounting & Finance',
    'description': """
=====================================
Facturación electrónica para Ecuador
=====================================
Este módulo se conecta al servicio de OpenConsulting para la generación de documentos electrónicos.
    """,
    'data': [
        'account.xml',
        'account_invoice.xml',
        'electronic_invoicing.xml',
        'data.xml'
    ],
    'demo': [
    ],
}