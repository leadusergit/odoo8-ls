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

class report_transfer(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(report_transfer,self).__init__(cr, uid, name, context)
        self.localcontext.update({'time' : time,
                                  'get_lines':self._get_lines,
                                })
        self.context = context

    def _get_lines(self, form):
            #print '_get_lines_TRANSFER:',form
            date_from = form.get('date_from')
            date_to = form.get('date_to')
            lines = []
            where = ''
            sql='SELECT * FROM payment_transfer_payment '\
                            'WHERE generation_date BETWEEN \''+str(date_from)+'\' AND \''+str(date_to)+'\' '\
                            'AND type=\'transfer\''
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
                            if line.state=='valid' and line.note=='Transferencia' and line.has_transfer:
                                origen = ''
                                tipo = ''
                                cuenta = ''
                                origen = line.origin
                                if line.origin =='invoice':
                                    origen = 'Factura'
                                if line.payment_type=='CTA':
                                    tipo = 'Cuenta'
                                elif line.payment_type=='CHQINDV':
                                    tipo = 'Cheque'
                                elif line.payment_type=='EFE':
                                    tipo = 'Efectivo'
                                if line.acc_number:
                                    cuenta = line.acc_number 
                                             
                                val ={'invoice_num':line.invoice_num,
                                      'date_maturity':line.date_maturity,
                                      'name':line.name,
                                      'amount':line.amount_total,
                                      'payment_date':line.generation_date,
                                      'origen':origen,
                                      'tipo': tipo,
                                      'cuenta':cuenta,
                                      }
                                lines.append(val)
            return lines
        
   
     
report_sxw.report_sxw('report.report_transfer', 
                      'payment.transfer.payment',
                      "addons/payments/report/report_transfer.rml",
                      parser=report_transfer,header=False)
