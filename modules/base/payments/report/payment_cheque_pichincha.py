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
from openerp.report import report_sxw
from generic_payment_cheque import generic_payment_cheque

class payment_cheque_pichincha(generic_payment_cheque, report_sxw.rml_parse):
    _name = 'payment.cheque.pichincha'
    _description = 'Formato Banco de Pichincha'
    
    def __init__(self, cr, uid, name, context=None):
        super(payment_cheque_pichincha,self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time' : time,
                                  'obt_texto':self.obt_texto,
                                  'cambiar_estado':self.cambiar_estado,
                                  'debit':self._get_line_debit,
                                  'credit':self._get_line_credit,
                                  'total':self.total,
                                  'usuario':self._user,
                                  'get_company':self.get_company,
                                  'formato':self.comma_me,
                                  'get_date_invoice':self.get_date_invoice,
                                  })
        self.context = context
    
report_sxw.report_sxw('report.payment.cheque.pichincha', 
                      'payment.cheque',
                      "addons/payments/report/payment_cheque_pichincha.rml",
                      parser=payment_cheque_pichincha,header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: