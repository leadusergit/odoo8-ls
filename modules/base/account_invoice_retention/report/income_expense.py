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

import time
from openerp.report import report_sxw
from number_to_text import Numero_a_Texto

class income_expense(report_sxw.rml_parse):
    _name = 'income.expense'
    _description = 'Ingresos o Egresos'
    
    def __init__(self, cr, uid, name, context):
        super(income_expense, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'amount2text': Numero_a_Texto,
            'sum': sum,
            'get_partner': self.get_partner
        })
        self.context = context
    
    def get_partner(self, lines):
        lines_ids = [line.id for line in lines]
        self.cr.execute('SELECT partner_id, count(1) FROM account_move_line WHERE id=ANY(%s) '
                        'GROUP BY partner_id ORDER BY 2 DESC', (lines_ids,))
        partner_id = self.cr.fetchone()
        return self.pool.get('res.partner').browse(self.cr, self.uid, partner_id and partner_id[0] or False)
        
report_sxw.report_sxw('report.account.move.inex', 'account.move', 'addons/account_invoice_retention/report/income_expense.rml',
                      parser=income_expense, header=False)