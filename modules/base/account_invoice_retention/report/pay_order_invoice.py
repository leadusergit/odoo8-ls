
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

from openerp.report import report_sxw
import time
from datetime import datetime
from openerp import pooler
from openerp import tools
import re

def get_date(fecha):
    obj_fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
    return obj_fecha.strftime("%d-%m-%Y")
    
class pay_order_invoice(report_sxw.rml_parse):

 
    def _sum_total(self, inv, data):
        suma = 0.0
        if inv.move_id:
            for line in inv.move_id.line_id:
                suma += line.debit
        return suma
    
       
    def _get_lines(self, lines):
        res=[]
        if lines:
            for line in lines:
                if not(line.debit == 0 and line.credit == 0):
                    res.append(line)
            
            for i in range(len(res)-1):
                for j in range(i+1, len(res)):
                    if res[i].debit < res[j].debit:
                        aux=res[i]
                        res[i]=res[j]
                        res[j]=aux
        return res
    
    
    
    def quitar_punto(self, amount):
        amount_string=str(amount)
        num = re.sub(r'\D', "", amount_string)    
        return num
    
    def fundsname(self, account_id, analytic_id, preproject_id, invoice_id):
        line_model = self.pool.get('account.invoice.line')
        line_id = line_model.search(self.cr, self.uid, [('invoice_id', '=', invoice_id),
                                                        ('account_id', '=', account_id),
                                                        ('account_analytic_id', '=', analytic_id),
                                                        ('preproject_id', '=', preproject_id)], limit=1)
        name = ''
        if line_id:
            line_id = line_model.read(self.cr, self.uid, line_id[0], ['funds_certificate_id'])
            name = line_id['funds_certificate_id'][1]
        return name and name.split('-')[0] or ''
                    
    def __init__(self, cr, uid, name, context):
        super(pay_order_invoice, self).__init__(cr, uid, name, context)
        self.localcontext.update({
                'time': time,
                'date':get_date,                  
                'sum_credit': self._sum_total,
                'sum_debit': self._sum_total,
                'lines': self._get_lines,
                'quitar':self.quitar_punto,
                'fundsname': self.fundsname
                })
        self.context = context
        
report_sxw.report_sxw('report.pay.order.invoice', 'account.invoice', 'addons/account_invoice_retention/report/pay_order_invoice.rml', parser=pay_order_invoice,header=False)