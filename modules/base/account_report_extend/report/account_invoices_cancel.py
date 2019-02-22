# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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
##############################################################################

import xml
import copy
from operator import itemgetter
import time
import datetime
from openerp.report import report_sxw
import re

class account_invoices_cancel(report_sxw.rml_parse):
    _name = 'account.invoices.cancel'
    def __init__(self, cr, uid, name, context):
        
        self.subadd = 0.0
        self.subdiscount = 0.0
        self.subiva = 0.0
        self.subamount = 0.0
        
        self.tsuman = 0.0
        self.tdescuento = 0.0
        self.tiva = 0.0
        self.total = 0.0
        
        self.out_invoice = 0
        self.out_refund = 0
        self.invoice_cancel = 0
        self.refund_cancel = 0
        
        super(account_invoices_cancel, self).__init__(cr, uid, name, context)
        
        self.localcontext.update({
            'time': time,
            'separador':self.comma_me,
            'customers': self.customers,
            'invoices':self.get_invoices,
            'total':self.totales,
            'get_date':self.get_date,
            'subtotal':self.subtotal
        })
        self.context = context
    
    def get_date(self, form):
        res = ''
        filtro = form.get('filter', False)
        if filtro =='date':
            date_from = form.get('date_from', False)
            date_to = form.get('date_to', False)
            res = 'Desde: ' +str(date_from)+ ' Hasta: '+str(date_to)
        elif filtro =='period':
            period_id = form.get('period_id', False)
            obj_period = self.pool.get('account.period').browse(self.cr,self.uid, period_id)
            res= 'Mes de: '+str(obj_period.name)
        return res    
    
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
    
    def get_invoices(self,parameter,form):
        
        self.subadd = 0.0
        self.subdiscount = 0.0
        self.subiva = 0.0
        self.subamount = 0.0
        
        res = []
        filtro = form.get('filter', False)
        tipo = form.get('type_report', False)
        
        if filtro =='date':
            date_from = form.get('date_from', False)
            date_to = form.get('date_to', False)
            filter  = "AND ai.date_invoice BETWEEN '"+date_from+"' AND '"+date_to+ "' "
        elif filtro =='period':
            period_id = form.get('period_id', False)
            filter = "AND ai.period_id="+str(period_id)+" "
        
        sql = "SELECT ai.id,ai.date_invoice, ai.date_due,ai.type,ai.num_retention as factura,rp.name as partner,ai.amount_subtotal as suman, "\
              "ai.amount_discount as descuento, ai.t_iva as iva, ai.amount_pay as total, ai.state FROM account_invoice as ai "\
              "JOIN res_partner as rp ON (rp.id = ai.partner_id) "\
              "LEFT JOIN res_users as ru ON (ru.id = ai.saleer_id) "
                   
        case = 0
        order = 'ORDER BY date_invoice,factura'
        if tipo == 'customer':
            #print '1'
            if parameter:
                #print '2'
                where = "WHERE ai.partner_id = "+str(parameter)+" AND ai.type in ('out_invoice') AND ai.state in ('cancel') "
        elif tipo == 'seller':
            #print '4'
            if parameter:
                #print '5'
                where = "WHERE ai.saleer_id = "+str(parameter)+" AND ai.type in ('out_invoice') AND ai.state in ('cancel') "
            else:
                where = "WHERE ai.type in ('out_invoice') AND ai.state in (cancel') and ai.saleer_id is null "
        else:
            #print '6'
            where = "WHERE ai.type in ('out_invoice') AND ai.state in ('cancel') AND ai.id="+str(parameter)+" "
        
        
        sql = sql + where + filter + order
        ##print "##", sql
    
        self.cr.execute(sql)
        result = self.cr.dictfetchall()
        if result:
            out_refund = 0
            refund_cancel = 0
            out_invoice = 0
            invoice_cancel = 0
            for inv in result:
                tipo = ''
                estado = ''
                suman = round(inv['suman'],2)
                descuento = round(inv['descuento'],2)
                iva = round(inv['iva'],2)
                total = round(inv['total'],2)
                if inv['type']=='out_refund':
                    tipo = 'NC'
                    out_refund+=1
                    suman = -suman
                    descuento = -descuento
                    iva = -iva
                    total = -total
                    if inv['state']=='cancel':
                        refund_cancel+=1
                else:
                    tipo = 'FAC'
                    out_invoice +=1
                    if inv['state']=='cancel':
                        invoice_cancel+=1
                
                if inv['state']=='open':
                    estado = 'MY'
                elif inv['state']=='paid':
                    estado = 'MY'
                elif inv['state']=='cancel':
                    estado = 'AN'
                    suman = 0.0
                    descuento = 0.0
                    iva = 0.0
                    total = 0.0
                    
                val = {
                       'nro': inv['factura'],
                       'tipo': tipo,
                       'partner': inv['partner'][:48],
                       'emision': inv['date_invoice'],
                       'vencimiento' : inv['date_due'],
                       'suman': suman,
                       'descuento': descuento,
                       'iva': iva,
                       'total': total,
                       'estado' : estado,
                       
                       }
                res.append(val)
                self.subadd += suman
                self.subdiscount += descuento
                self.subiva += iva
                self.subamount += total
            
            self.tsuman += self.subadd
            self.tdescuento += self.subdiscount
            self.tiva += self.subiva
            self.total += self.subamount
                
            self.out_invoice += out_invoice
            self.out_refund += out_refund
            self.invoice_cancel += invoice_cancel
            self.refund_cancel += refund_cancel
        return res
         
    
    def customers(self, form):
        case = 0
        customer = form.get('partner_id', False)
        seller = form.get('seller_id', False)
        tipo = form.get('type_report', False)
        
        where = ''
        sql =''
        self.totalfactura = 0.0
        self.totalabono = 0.0
        self.totalretencion = 0.0
        self.totalsaldo = 0.0
        
        filtro = form.get('filter', False)
        if filtro =='date':
            date_from = form.get('date_from', False)
            date_to = form.get('date_to', False)
            filter  = "AND ai.date_invoice BETWEEN '"+date_from+"' AND '"+date_to + "' "
        elif filtro =='period':
            period_id = form.get('period_id', False)
            filter = "AND ai.period_id="+str(period_id)+" "
            
        where = "AND ai.type in ('out_invoice') AND ai.state in ('cancel') "
        case = 0
        if tipo=='customer':
            case = 1
            sql = "SELECT ai.partner_id as parameter, rp.name as customer, '1' as case FROM account_invoice as ai "\
                   "LEFT JOIN res_partner as rp ON (rp.id = ai.partner_id) "
            
            if customer:
                where = "WHERE ai.partner_id = "+str(customer) + where +filter
            else:
                where = "WHERE "+filter[4:] + where
            order = "GROUP by ai.partner_id, rp.name ORDER by rp.name"
        elif tipo =='seller':
            case = 2
            sql = "SELECT ai.saleer_id as parameter, ru.name as seller , '2' as case FROM account_invoice as ai "\
                  "LEFT JOIN res_users as ru ON (ru.id = ai.saleer_id) "
            
            if seller:
                where ="WHERE ai.saleer_id = "+str(seller)+ where +filter
            else:
               where = "WHERE "+filter[4:] + where
            order = "GROUP by ai.saleer_id,ru.name ORDER by ru.name" 
        else:#ambos
            case = 3
            sql = "SELECT ai.id as parameter, 'customer' as customer, 'seller' as seller, '3' as case FROM account_invoice as ai "
            where = "WHERE ai.type in ('out_invoice') AND ai.state in ('cancel') " + filter+" "
            order = "ORDER by ai.date_invoice,ai.factura "                  
        
        sql = sql + where + order
        ##print "customer ##", sql
    
        self.cr.execute(sql)
        result = self.cr.dictfetchall()
        ##print "result", result
        return result
    
    
    def subtotal(self):
        res =[self.subadd,
              self.subdiscount,
              self.subiva,
              self.subamount
              ]
        return res      
            
    def totales(self):
        res =[self.tsuman,
              self.tdescuento,
              self.tiva,
              self.total,
              self.out_invoice,
              self.out_refund,
              self.invoice_cancel,
              self.refund_cancel]
        return res
        
report_sxw.report_sxw('report.account_invoices_cancel',
                      'account.invoice',
                      'addons/account_report_extend/report/account_invoices_cancel.rml',
                      parser=account_invoices_cancel,
                      header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
