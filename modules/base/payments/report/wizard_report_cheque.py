# -*- encoding: utf-8 -*-
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import xml
import copy
from operator import itemgetter
import time
import datetime
from openerp.report import report_sxw
import openerp.pooler

class report_cheque(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(report_cheque,self).__init__(cr, uid, name, context)
        
        self.localcontext.update({'time' : time,
                                  'get_lines':self._get_lines,})

    def _get_lines(self, form):
            #print '_get_lines_cheque:',form
            date_from = form.get('date_from')
            date_to = form.get('date_to')
            lines = []
            where = ''
            sql='SELECT * FROM payment_transfer_payment '\
                            'WHERE generation_date BETWEEN \''+str(date_from)+'\' AND \''+str(date_to)+'\' '\
                            'AND type=\'check\''
            #print "sql", sql
            if form.get('date_to')=='draft':
                where = ' AND state=\'draft\''
            elif form.get('date_to')=='done':
                where = ' AND state=\'done\''
            elif form.get('date_to')=='all':
                where = ''
                
            #print "consulta", sql+where+' ORDER BY generation_date DESC'
            self.cr.execute(sql+where+' ORDER BY generation_date DESC')
            res = self.cr.dictfetchall()
#            #print "res", res
            if res:
                for pay in res:
                    for item in self.pool.get('payment.transfer.payment').browse(self.cr, self.uid, [pay['id']]):
                        for line in item.invoce_line_ids:
                            if line.state=='valid' and line.note=='Cheque' and line.cheque:
                                cheque = ''
                                origen = ''
                                if line.account_mov_id:
                                    self.cr.execute('Select * FROM payment_cheque_detail where line_id=%s and state=%s',(line.account_mov_id.id, 'done'))
                                    res1 = res = self.cr.dictfetchall()
                                    #print "res1", res1 
                                    if res1:
                                        for lc in res1:
                                            chd = self.pool.get('payment.cheque.detail').browse(self.cr, self.uid, int(lc['id']))
                                            if chd.cheque_id:
                                                cheque = chd.cheque_id.num_cheque
                                                if chd.cheque_id.inv_type == 'invoice':
                                                     origen = 'Factura'
                                                elif chd.cheque_id.inv_type == 'purchase_liq':
                                                     origen = 'Liquidacion de Compra'
                                                elif chd.cheque_id.inv_type == 'anticipo':
                                                     origen = 'Anticipo'
                                                elif chd.cheque_id.inv_type == 'apunte':
                                                     origen = 'Apunte'
                                if not origen:
                                    origen = line.origin
                                    if line.origin =='invoice':
                                        origen = 'Factura'
                                             
                                val ={'invoice_num':line.invoice_num,
                                      'date_maturity':line.date_maturity,
                                      'name':line.name,
                                      'amount':line.amount_total,
                                      'payment_date':line.generation_date,
                                      'origen':origen,
                                      'cheque': cheque,
                                      }
                                lines.append(val)
            return lines
    
      
report_sxw.report_sxw('report.report_cheque',
                      'payment.cheque',
                      "addons/payments/report/report_cheque.rml",
                      parser=report_cheque,header=False)
