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


class account_invoice_resume(report_sxw.rml_parse):
    _name = 'account.invoice.resume'
    _description = 'Factura Cliente Resumen'
    
    def __init__(self, cr, uid, name, context):
        super(account_invoice_resume, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_text':self.get_text,
            'get_dir':self.get_dir,
            'get_tax':self.get_tax,
            'get_contact_invoice':self.get_contact_invoice,
            'cantidad':self.get_cantidad,
            'sitios':self.get_sitios,
            'formato':self.comma_me,
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
        
    def get_contact_invoice(self, partner):
        name = ''
        if partner.address:
            for address in partner.address:
                if address.type:
                    if address.type == 'invoice':
                        if address.name:
                            name = tools.ustr(address.name).upper()
                        break
        return name
        
    def get_dir(self, objeto):
        res = ''
        if objeto:
            res += tools.ustr(objeto.street).upper()
            if objeto.street2:
                res += ' y ' + tools.ustr(objeto.street2).upper()
        return res
    
    def get_text(self, cantidad):
        cant = float(cantidad)
        res = Numero_a_Texto(cant)
        tam = len(res)
        return res
    
    def get_tax(self, id_fac):
        tax_obj = pooler.get_pool(self.cr.dbname).get('account.invoice.tax')
        res = 0
        id_imp = tax_obj.search(self.cr, self.uid, [('invoice_id', '=', int(id_fac))])
        if id_imp:
            obj_imp = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').browse(self.cr, self.uid, id_imp)
            code_tax = int(obj_imp[0].tax_code_id.id)

            id_tax = pooler.get_pool(self.cr.dbname).get('account.tax').search(self.cr, self.uid, [('ref_tax_code_id', '=', code_tax)])

            if id_tax != []:
                obj_tax = pooler.get_pool(self.cr.dbname).get('account.tax').browse(self.cr, self.uid, id_tax)
                res = int(abs((obj_tax[0].amount) * 100))
                ##print 'res_entro ', res
        return res
    
    def get_cantidad(self, invoice):
        res = {}
        cantidad = 0
        if invoice.invoice_line:
            for line in invoice.invoice_line:
                if line.price_unit != 0:
                    cantidad += line.quantity
        return cantidad
        
    def get_sitios(self, invoice):
        sitios = 'Sitios: '
        if invoice.origin:
            order = pooler.get_pool(self.cr.dbname).get('sale.order').search(self.cr,self.uid, [('name','=',invoice.origin)])
            if order != []:
                obj_order = pooler.get_pool(self.cr.dbname).get('sale.order').browse(self.cr, self.uid, order[0])
                if obj_order.order_line:
                    for line in obj_order.order_line:
                        if line.code_site and line.price_unit != 0:
                            sitios += line.code_site +' \\ '
        return sitios[:-2]
    
report_sxw.report_sxw('report.account.invoice.resume',
                      'account.invoice',
                      'addons/account_invoice_retention/report/invoice_resume.rml',
                      parser=account_invoice_resume,
                      header=False)
    
    
   
