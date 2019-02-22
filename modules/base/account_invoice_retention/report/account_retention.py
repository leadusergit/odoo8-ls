# -*- coding: utf-8 -*-
###################################################
#
#    Invoice Retention Module
#    Copyright (C) 2012 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
#    $autor: Dairon Medina Caro <dairon.medina@gmail.com>
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################
from __future__ import absolute_import
import time
from openerp.report import report_sxw
from datetime import datetime
from openerp.osv import osv, fields
from openerp import tools
import re

class account_retention(report_sxw.rml_parse):
    _name = 'report.account.retention'

    def _get_taxes(self, invoice_id):
        res = self.pool.get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=', invoice_id), ('tax_group','in',('ret_vat','ret_ir'))])
        
        if res !=[]:
            res1  = self.pool.get('account.invoice.tax').browse(self.cr, self.uid, res)
            codigo = int(res1[0].invoice_id)
            invoice  = self.pool.get('account.invoice').browse(self.cr, self.uid, codigo)
            base = invoice.baseretencion
            
            for aux in res1:
                if not aux.percent:
                    if aux.tax_group=='ret_vat':
                        self.pool.get('account.invoice.tax').write(self.cr, self.uid, aux.id, {"percent":round(abs(aux.amount)*100/base)})
                    else:
                        self.pool.get('account.invoice.tax').write(self.cr, self.uid, aux.id, {"percent":round(abs(aux.amount)*100/aux.base)})
        res = self.pool.get('account.invoice.tax').browse(self.cr, self.uid, res)
        return res or []

    def _get_tax_group(self,group):
        if group == 'ret_vat':
            return 'Imp. IVA'
        elif group == 'ret_ir':
            return 'Imp. Renta'
        else:
            return ''
    
    def _get_total(self, inv):
        return abs(inv.t_ret_iva + inv.t_ret_ir)

    def _user(self):
        user = self.pool.get('res.users').browse(self.cr, self.uid, self.uid)
        return user.name
    
    def direccion(self, obj):
        dir = ' '
        if obj:
            if obj.street:
                dir = tools.ustr(obj.street)
                if dir !=' ':
                    if obj.street2:
                        dir = dir + ' y ' + tools.ustr(obj.street2)
        return dir[:37]
    
    def _anio(self, invoice): 
        anio = ''
        if invoice.move_id:
            anio = invoice.move_id.period_id.name.split('/')[1]
        else:
            anio=''
        return anio
    
    def _cadena(self,cadena):
        return cadena.encode('"UTF-8"')[:54]
    
    def _get_type(self, nombre):
        
        if nombre == 'invoice':
            return 'FACTURA'
        elif nombre == 'purchase_liq':
            return 'LIQUIDACION'
        elif nombre == 'sales_note':
            return 'NOTA DE VENTA'
        elif nombre == 'anticipo':
            return 'ANTICIPO'
        elif nombre == 'gas_no_dedu':
            return 'GASTO NO DEDUCIBLE'
        elif nombre == 'doc_inst_est':
            return 'DOC. ESTADO'
        elif nombre == 'gasto_financiero': #####
            return 'GASTOS FINANCIEROS'
        else:
            return ''
            
    #Funcion que separa el punto en lugar de comas y pone a 2 decimales las cantidades
    def comma_me(self,amount):
        
        #print ' FORMATO a ret **** '
        if not amount:
            amount = 0.0
        if type(amount) is float:
            #print ' FORMATO b ret **** '
            amount = str('%.2f'%amount)
        else :
            #print ' FORMATO c ret **** '
            amount = str('%.2f'%amount)
        if (amount == '0'):
            return ' '
        orig = amount
        new = re.sub("^(-?\d+)(\d{3})", "\g<1>,\g<2>", amount)
        if orig == new:
            return new
        else:
            return self.comma_me(new)
    

    def quitar_punto(self, amount):
        #print ' quitar punto '
        amount_string=str(amount)
        #print amount_string
        num = re.sub(r'\D', "", amount_string)    
        #print "Amount : ", num
        return num
            

    
    def __init__(self, cr, uid, name, context):
        super(account_retention, self).__init__(cr, uid, name, context)
        self.localcontext.update({
                'time' : time,
                'get_taxes' : self._get_taxes,
                'get_total': self._get_total,
                'user': self._user,
                'direccion':self.direccion,
                'anio':self._anio,
                'DateTime': datetime,
                'cadena':self._cadena,
                'tipo':self._get_type,
                'tax_group':self._get_tax_group,
                'formato':self.comma_me,
                'quitar':self.quitar_punto,
                })
        self.context = context

report_sxw.report_sxw('report.account.retention', 
                      'account.invoice', 
                      'addons/account_invoice_retention/report/account_retention.rml', 
                      parser=account_retention, 
                      header=False)
