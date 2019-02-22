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
from mx import DateTime
from openerp.osv import osv, fields
from number_to_text import Numero_a_Texto
import re
from openerp import tools #Ayuda a mostrar datos con eñes y tíldes

class credit_note(report_sxw.rml_parse):
    _name = 'report.credit.note'
    _description = 'Nota de Credito de Cliente'
    
    def __init__(self, cr, uid, name, context):
        super(credit_note, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'telefono':self._fono,
            'fecha': self._fecha,
            'detalle':self._detalle,
            'customer':self._customer,
            'get_date':self.get_date,
            'get_text':self.get_text,
            'formato':self.comma_me,
            'autorizacion':self._get_autorization,
        })
    
    #Funcion que separa el punto en lugar de comas y pone a 2 decimales las cantidades
    def comma_me(self,amount):
        if not amount:
            amount = 0.0
        if type(amount) is float:
            amount = str('%.2f'%amount)
        else :
            amount = str(amount)
        if (amount == '0'):
             return ' '
        orig = amount
        new = re.sub("^(-?\d+)(\d{3})", "\g<1>,\g<2>", amount)
        if orig == new:
            return new
        else:
            return self.comma_me(new)
    
    def get_date(self, o):
        res = ''
        if o.date_invoice:
            res = time.strftime('%d de %B del %Y', time.strptime(o.date_invoice, '%Y-%m-%d'))
        else:
            res = time.strftime('%d de %B del %Y')
        return res
        
    def _fono(self, partner):
        if partner and partner.address:
            for address in partner.address:
                if address.type:
                    if address.type == 'invoice':
                        return address.phone[0:10]
                        break
        else:
            return
        
    def get_text(self, cantidad):
        cant = float(cantidad)
        res = Numero_a_Texto(cant)
        tam = len(res)
        return res
    
    def _fecha(self, o):
        res = ['','','']
        origen = o.origin
        if origen:
            factura = pooler.get_pool(self.cr.dbname).get('account.invoice').search(self.cr, self.uid, [('num_retention', '=', origen)])
            if factura :
                fecha = pooler.get_pool(self.cr.dbname).get('account.invoice').read(self.cr, self.uid, factura, ['date_invoice'])
                if fecha:
                    for date in fecha:
                        d = date['date_invoice']
                        d = str(d).split('-')
                        dia = d[2]
                        mes = d[1]
                        anio = d[0]
                        res = [dia, mes, anio]
                        return res
                        break
        else:
            return res
       
    def _detalle (self, line):
        res = []
        cantidad = 0
        cuenta = ''
        for l in line:
            cantidad += l.quantity
            cuenta = l.product_id.code
        res = [cantidad, cuenta]
        return res
    
    def _customer(self, invoice):
        res = ''
        if invoice:
            if invoice.partner_id:
                partner = invoice.partner_id.name 
                return tools.ustr(partner)[:40]
            else:
                res
                
    def _get_autorization(self, invoice):
        res = ''
        if invoice:
            if invoice.auth_ret_id:
                auto = invoice.auth_ret_id
                res = auto.serie_entidad + ' - ' + auto.serie_emision 
                return res
            else:
                res
    
            
report_sxw.report_sxw('report.credit.note',
                      'account.invoice',
                      'addons/account_invoice_retention/report/credit_note.rml',
                      parser=credit_note,
                      header=False)
   