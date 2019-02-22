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


class laundry_order(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(laundry_order, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_laundry_lines': self.get_laundry_lines,
        })

    def get_laundry_lines(self, obj):
        laundry_line = self.pool.get('laundry.management.line')
        res = []
        ids = []
        for id in range(len(obj)):
            #if obj[id].appears_on_laundry is True:
            ids.append(obj[id].id)
        if ids:
            res = laundry_line.browse(self.cr, self.uid, ids)
        return res


class wrapped_report_laundry_order(osv.AbstractModel):
    _name = 'report.laundry_management.report_laundry_order'
    _inherit = 'report.abstract_report'
    _template = 'laundry_management.report_laundry_order'
    _wrapped_report_class = laundry_order

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: