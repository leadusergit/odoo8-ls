# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
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
    'name': "Reporting of Balancesheet for accounting",
    'version': '1.0',
    'depends': ['account'],
    'author': "Tiny",
    'category': 'Accounting & Finance',
    'description': """Financial and accounting reporting
    Balance Sheet Report""",
    # data files always loaded at installation
    'data': [
        'security/ir.model.access.csv',
        'account_view.xml',
        'account_report.xml',
        'account_data.xml',
        'wizard/account_reporting_balance_report_view.xml',
    ],
    # data files containing optionally loaded demonstration data
    'demo': [],
    'certificate': '0072305016797',
}