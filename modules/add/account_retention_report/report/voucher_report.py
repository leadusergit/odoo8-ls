# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today OpenERP SA (<http://www.openerp.com>).
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

from openerp.osv import osv
from openerp.tools.translate import _


class AcoountVoucherReport(osv.AbstractModel):
    _name = 'report.account_retention_report.vouchertc_reporte'

    def render_html(self, cr, uid, ids, data=None, context=None):
        
        report_obj = self.pool['report']
        ret_obj = self.pool['account.voucher']
        report = report_obj._get_report_from_name(cr, uid, 'account_retention_report.vouchertc_reporte')
        selected_voucher = ret_obj.browse(cr, uid, ids, context=context)

        ids_to_print = []
        invoiced_ids = []

        for order in selected_voucher:
            if order.id:
                ids_to_print.append(order.id)
                invoiced_ids.append(order.id)      


        docargs = {
            'doc_ids': ids_to_print,
            'doc_model': report.model,
            'docs': selected_fact,
        }
        print"docargs=%s"%docargs 

        docargs = {
            'doc_ids': ids_to_print,
            'doc_model': report.model,
            'docs': selected_fact,

        }
        print"docargs=%s"%docargs 
        
        return report_obj.render(cr, uid, ids, 'account_retention_report.vouchertc_reporte', docargs, context=context)



