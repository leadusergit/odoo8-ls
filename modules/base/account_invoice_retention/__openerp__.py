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
    'name': 'Retention Document for Taxing in Ecuador',
    'version': '1.0',
    'author': 'Openconsulting Cia. Ltda.',
    'website' : 'http://www.openconsulting.com.ec',
    'category' : 'Generic Modules/Accounting',
    'description': """Module for manage Retention document for Ecuador""",
    'depends': ['account_ec', 'account_voucher', 'sale', 'purchase'],
    'data': ['security/invoice_report_groups.xml',
                   'views/account_move.xml',
                   'invoice_view.xml',
                   'account_report.xml',
                   'sequence/retention_sequence.xml',
                   'sequence/account_invoice_retention_sequence.xml',
                   'views/account_codes_view.xml',
                   'views/account_conciliacion.xml',
                   'views/account_view_ind.xml',
                   'views/account_wizard.xml',
                   'views/anticipo_view.xml',
                   'views/wizard_account_retention.xml',
                   'views/wizard_account_deferred.xml',
                   'views/wizard_account_ats.xml',
                   'views/wizard_report_conciliation.xml',
                   'partner_view.xml',
                   'retention_view.xml',
                   'account_view.xml',
                   'tax_view.xml',
                   'security/ir.model.access.csv',
                   'views/reporte.xml',
                   
                   ],
    'installable': True,
    'active': False,
}
