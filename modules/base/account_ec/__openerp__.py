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
    "name" : "Accounting and Financial Management Ecuador",
    "version" : "1.0",
    "author" : "Openconsulting Cia. Ltda.",
    "category": 'Generic Modules/Accounting',
    "description": """
                    Financial and accounting Ecuador
                   """,
    'website': 'http://www.openconsulting.com.ec/',
    'init_xml': [],
    "depends" : ['base_ec', 'account'],
    'data': [
        "account_ec_data.xml",
        "views/account_invoice_view.xml",
        'views/pay_invoice_btn.xml',
        "views/account_menuitem.xml",
#         "views/account_wizard.xml",
        "views/bank_statement.xml",
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
