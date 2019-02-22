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

import time
from openerp.osv import osv
from openerp.report import report_sxw

class voucher_ret_daily(report_sxw.rml_parse):

    def _get_lines(self, move):
        ##print 'entra a las lineas de move ', move
        res = self.pool['account.move.line'].search(self.cr, self.uid, [('move_id', '=', int(move))])
        ##print 'res', res
        res1 = self.pool['account.move.line'].browse(self.cr, self.uid, res)
        
        res2 = []
        for line in res1:
            if not(line.debit == 0 and line.credit == 0):
                res2.append(line)
        for i in range(len(res2) - 1):
            for j in range(i + 1, len(res2)):
                if res2[i].debit < res2[j].debit:
                    aux = res2[i]
                    res2[i] = res2[j]
                    res2[j] = aux
        return res2
        
    def _usuario_contabilizo(self, vou):

        perm =  self.pool['account.invoice.retention.voucher'].perm_read(self.cr, self.uid, [vou.id])
        if perm:
            return perm[0]['create_uid'][1]
        else:
            return 'No Disponible'
    
    def _detail (self, o):
        if o.number and o.numero:
            return 'R.RENTA#'+str(o.number)+'FACT#'+str(o.numero.lstrip('0'))
        else:
            return
        
    def __init__(self, cr, uid, name, context):
        super(voucher_ret_daily, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time' : time, 'get_lines':self._get_lines, 
                                  'usuario':self._usuario_contabilizo,
                                  'detalle':self._detail})
        self.context = context
      
    
            
     
report_sxw.report_sxw('report.account.invoice.retention.voucher', 
                      'account.invoice.retention.voucher', 
                      "addons/payments/report/voucher_ret_daily.rml", 
                      parser=voucher_ret_daily, header=False)
