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
from openerp import pooler
from openerp.report import report_sxw
from number_to_text import Numero_a_Texto
from openerp import tools #Ayuda a mostrar datos con eñes y tíldes
import re    #Muestra los valores de numeros separados por coma
from datetime import datetime

def get_date(fecha):
    obj_fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
    #print obj_fecha
    return obj_fecha.strftime("%d-%m-%Y")

class purchase_liq_report(report_sxw.rml_parse):
    
    def get_dir(self, objeto):
        #print '**************//////////entro get datos',objeto
        res=''
        if objeto.street:
            res+=tools.ustr(objeto.street)
        #print 'res ',res
        if objeto.street2:
            res+=' y ' +tools.ustr(objeto.street2)
        return res
    
    def get_text(self, cantidad):
        cant = float(cantidad)
        res = Numero_a_Texto(cant)
        tam = len(res)
        return res
    
    #Funcion que separa el punto en lugar de comas y pone a 2 decimales las cantidades
    def comma_me(self,amount):
        
        #print ' FORMATO a **** '
        
        if not amount:
            amount = 0.0
        if type(amount) is float:
            #print ' FORMATO b **** '
            amount = str('%.2f'%amount)
        else :
            #print ' FORMATO c **** '
            amount = str('%.2f'%amount)
        if (amount == '0'):
             return ' '
        orig = amount
        new = re.sub("^(-?\d+)(\d{3})", "\g<1>,\g<2>", amount)
        if orig == new:
            return new
        else:
            return self.comma_me(new)

   
    def __init__(self, cr, uid, name, context):
        super(purchase_liq_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,'get_dir':self.get_dir,
            'get_text':self.get_text,
            'date':get_date, 
            'formato':self.comma_me
        })
    
report_sxw.report_sxw('report.purchase.liq.report',
                      'account.invoice',
                      'addons/account_invoice_retention/report/purchase_liq_report.rml',
                      parser=purchase_liq_report)
    
    
   