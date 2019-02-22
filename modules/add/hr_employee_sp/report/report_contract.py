#-*- coding:utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
from openerp.report import report_sxw
from openerp import api, models


class contract_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(contract_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'run_sql':self._run_sql
        })
      
    def _run_sql(self, qry,date_from,date_to):
        self.cr.execute(qry,(date_from,date_to))
        res = self.cr.dictfetchall()
        print"res=%s"%res
        return res


class wrapped_report_employee_sp(osv.AbstractModel):
    _name = 'report.hr_employee_sp.report_contract'
    _inherit = 'report.abstract_report'
    _template = 'hr_employee_sp.report_contract'
    _wrapped_report_class = contract_report

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: