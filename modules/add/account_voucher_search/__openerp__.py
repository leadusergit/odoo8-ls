# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 LS
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name' : 'VoucherSearch',
    'version' : '0.1.0',
    'author' : 'LS',
    'category': 'Busqueda/Filtros',
    'complexity': 'normal',
    'website': 'http://www.leadsolutions.ec',
    'data': [
        'view/account_voucher_search_view.xml',],
    'depends' : [
        'base','account','account_voucher','account_invoice_retention'
    ],
    'js': [
    ],
    'qweb': [
    ],
    'css': [
    ],
    'installable': True,
    'auto_install': False,                
}
