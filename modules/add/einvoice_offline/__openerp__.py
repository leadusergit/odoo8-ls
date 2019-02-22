# -*- coding: utf-8 -*-
##############################################################################
#
#    E-Invoice Module - Ecuador
#    Copyright (C) 2014 VIRTUALSAMI CIA. LTDA. All Rights Reserved
#    alcides@virtualsami.com.ec
#    $Id$
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
##############################################################################

{
    'name' : 'Electronic Documents for Ecuador Offline',
    'version': '0.1.0',
    'author': 'LS.',
    "category" : "Localization",
    'complexity' : 'normal',
    'website': 'http://www.leadsolutions.ec',
    'data': [
             'einvoice_offline_view.xml',
             'eretention_offline_view.xml',
             'company_view.xml',
             'einvoice_offline_report.xml',
             'wizard/lote_send_mail_view.xml',
             'edi/retention_data.xml'
           ],
     'depends': [
        'account','account_invoice_retention','authorisation_ec','l10n_ec_einvoice'
    ],
    'update_xml': [
    ],
    'js': [
    ],
    'qweb': [
    ],
    'css': [
    ],
    'description': '''
    This module allows make Electronic Documents IVA 12%/14% mode offline
    ''',
    'installable': True,
    'auto_install': False,
}
