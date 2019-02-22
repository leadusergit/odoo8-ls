#!/usr/bin/python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Reporting
#    Copyright (C) 2010-2010 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
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
#Creado por *EG

import time
from openerp.report import report_sxw
from openerp.osv import osv, fields


class account_invoice_customer(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_invoice_customer, self).__init__(cr, uid, name, context=context)
        
        self.vamout_invoice = 0.00
        self.vamount_abono= 0.00
        self.vamount_retencion= 0.00
        self.vamount_residual= 0.00
        
        self.pvamout_invoice = 0.00
        self.pvamount_abono= 0.00
        self.pvamount_retencion= 0.00
        self.pvamount_residual= 0.00
        
        self.stinvoice = 0.00
        self.stabono = 0.00
        self.stretencion = 0.00
        self.stresidual = 0.00
        
        self.tinvoice = 0.00
        self.tabono = 0.00
        self.tretencion = 0.00
        self.tresidual = 0.00
        
        self.localcontext.update( {
            'time': time,
            'lineas_g': self.customer_invoices,
            'lineas_v':self.invoices_vencidas,
            'lineas_pv':self.invoices_por_vencer,
            'has_vencidas':self.vencidas,
            'has_por_vencer':self.por_vencer,
            'sbtvencidas':self.sbtvencidas,
            'sbtporvencer':self.sbtpvencer,
            'total':self.sbtotal,
            'gtotal':self.totales,
        })
        self.context = context
    
    def vencidas(self, customer, form):
        ##print "form", form
        date_start = form.get('date_start', False)
        date_to = form.get('date', False)
        date_now = time.strftime('%Y-%m-%d') #Buscar todas las facturas a la fecha del vendedor
        type = form.get('type', False)
        self.cr.execute("""
                     SELECT id AS id, factura AS nro, date_invoice AS emision, date_due AS vencimiento, amount_total AS total, (date_due-%s) as dias, '1' as case 
                     FROM account_invoice WHERE
                     partner_id =%s
                     AND type = 'out_invoice'
                     AND state in('open','paid')
                     AND date_invoice BETWEEN %s and %s
                     AND (date_due-%s) < 0 
                     ORDER BY dias, factura
                    """,(date_to, customer,date_start,date_to, date_to))
        #self.cr.execute(sql)
        res = self.cr.dictfetchall()
        return res
    
    def por_vencer(self, customer, form):
        ##print "form", form
        date_start = form.get('date_start', False)
        date_to = form.get('date', False)
        type = form.get('type', False)
        self.cr.execute("""
                     SELECT id AS id, factura AS nro, date_invoice AS emision, date_due AS vencimiento, amount_total AS total, (date_due-%s) as dias, '2' as case 
                     FROM account_invoice WHERE
                     partner_id =%s
                     AND type = 'out_invoice'
                     AND reconciled is not True
                     AND state = 'open'
                     AND date_invoice BETWEEN %s and %s
                     AND (date_due-%s) > 0 
                     ORDER BY dias, factura
                    """,(date_to, customer,date_start,date_to, date_to))
        #self.cr.execute(sql)
        res = self.cr.dictfetchall()
        return res

        
    def customer_invoices(self,form):
        #print "form", form
        type = form.get('type', False)
        date_start = form.get('date_start', False)
        date_to = form.get('date', False)
        seller = form.get('seller_id', False)
        customer = form.get('partner_id', False)
        grupo = form.get('group_id', False)
        where = "WHERE date_invoice BETWEEN '"+str(date_start)+"' and '"+str(date_to)+"' AND type = 'out_invoice' AND reconciled is not True AND state = 'open' "
        
        if type =='customer':
            sql = "SELECT ai.partner_id AS customer, rp.name as name, '2' as case "\
                   "FROM account_invoice AS ai "\
                   "JOIN res_partner AS rp ON (ai.partner_id = rp.id) "
            if customer:
                where = where + "AND ai.partner_id="+str(customer)+" "
            group = "GROUP BY ai.partner_id, rp.name ORDER BY rp.name"
        
        if type =='group':
            sql = "SELECT ai.partner_id AS customer, rp.name as name, '2' as case "\
                   "FROM account_invoice AS ai "\
                   "JOIN res_partner AS rp ON (ai.partner_id = rp.id) "
            if grupo:
                where = where + "AND ai.partner_id in (SELECT partner_id "\
                                                        "FROM res_partner_category_rel "\
                                                       "WHERE category_id ="+str(grupo)+") "
            group = "GROUP BY ai.partner_id, rp.name ORDER BY rp.name"
        sql = sql + where + group
        #print "sql\n", sql 
        self.cr.execute(sql)
        res = self.cr.dictfetchall()
        if res:
            for r in res:
                calle = ''
                nombre = ''
                if r['customer']:
                    partner = self.pool.get('res.partner').browse(self.cr, self.uid ,r['customer'])
                    ##print "partner", partner
                    r['code'] = partner.ref
                    ##print "name", partner.name.encode('"UTF-8"')
                    r['name'] = str(partner.name.encode('"UTF-8"'))
                    if partner.address:
                        for a in partner.address:
                            r['fono'] = a.phone
                            if a.street:
                                x = a.street
                                y = str(x.encode('"UTF-8"'))
                                calle = y
                            ##print "calle", calle 
                            r['direccion'] = calle
                            r['contacto'] = a.name
                            r['city'] = a.city
        return res
    
    
    
    def invoices_vencidas(self, customer, form):
        ##print "form", form
        date_start = form.get('date_start', False)
        date_to = form.get('date', False)
        
        self.vamout_invoice = 0.00
        self.vamount_abono= 0.00
        self.vamount_retencion= 0.00
        self.vamount_residual= 0.00
      
        if customer:
            self.cr.execute("""
                     SELECT id AS id, factura AS nro, date_invoice AS emision, date_due AS vencimiento, amount_total AS total, (date_due-%s) as dias, '1' as case 
                     FROM account_invoice WHERE
                     partner_id =%s
                     AND type = 'out_invoice'
                     AND reconciled is not True
                     AND state = 'open'
                     AND date_invoice BETWEEN %s and %s
                     AND (date_due-%s) < 0
                     ORDER BY dias, factura
                    """,(date_to, customer,date_start,date_to, date_to))

        
        res = self.cr.dictfetchall()

        vencidas = []
        if res:
            for r in res:
                ##print "r", r
                retencion = 0.00
                abono = 0.00
                saldo = 0.00
                debit = 0.00
                credit = 0.0
                opc = ''
               
                self.cr.execute("""SELECT order_id FROM sale_order_invoice_rel WHERE invoice_id = %s""",(r['id'],))
                
                order = self.cr.fetchone()
                if order != None:
                    sale_obj = self.pool.get('sale.order').browse(self.cr, self.uid, order[0])
                    for ol in sale_obj.order_line:
                        opc = ol.number_opc
                        break
                i = self.pool.get('account.invoice').browse(self.cr, self.uid ,r['id'])
                for lines in i.move_lines:
                    debit+=lines.debit
                    credit+=lines.credit
                 
                if i and i.residual:
                    saldo = i.residual
                      
                if i and i.ret_voucher_id:
                    ret = self.pool.get('account.invoice.retention.voucher').browse(self.cr, self.uid ,i.ret_voucher_id.id)
                    if ret.state=='valid':
                        retencion = ret.total or 0.0
                        
                abono = (round(credit,2) or 0.0)-(round(debit,2) or 0.0)
                
                if abono > 0:
                   abono = abono-retencion
                
                vencidas.append({'nro': r['nro'],
                                 'emision': r['emision'],
                                 'vencimiento' : r['vencimiento'],
                                 'dias': r['dias'] or 's/f',
                                 'factura': r['total'],
                                 'retencion':retencion,
                                 'abono':abono,
                                 'saldo': saldo,
                                 'opc':opc})
                self.vamout_invoice += r['total']
                self.vamount_abono += abono
                self.vamount_retencion += retencion
                self.vamount_residual += saldo
                    
            self.stinvoice += self.vamout_invoice
            self.stabono += self.vamount_abono
            self.stretencion += self.vamount_retencion
            self.stresidual += self.vamount_residual
                    
        
        return vencidas
    
    def invoices_por_vencer(self, customer, form):
        date_start = form.get('date_start', False)
        date_to = form.get('date', False)
        
        self.pvamout_invoice = 0.00
        self.pvamount_abono= 0.00
        self.pvamount_retencion= 0.00
        self.pvamount_residual= 0.00
      
        if customer:
            self.cr.execute("""
                     SELECT id AS id, factura AS nro, date_invoice AS emision, date_due AS vencimiento, amount_total AS total, (date_due-%s) as dias , '2' as case
                     FROM account_invoice 
                     WHERE 
                     partner_id =%s
                     AND type = 'out_invoice'
                     AND reconciled is not True
                     AND state = 'open'
                     AND date_invoice BETWEEN %s and %s
                     AND (date_due-%s) > 0
                     ORDER BY dias DESC, factura
                    """,(date_to, customer,date_start,date_to, date_to))
        res = self.cr.dictfetchall()
        
        pvencer = []
        
        if res:
            for r in res:
                retencion = 0.00
                abono = 0.00
                saldo = 0.00
                debit =0.00 
                credit = 0.0
                opc = ''
                self.cr.execute("""SELECT order_id FROM sale_order_invoice_rel WHERE invoice_id = %s""",(r['id'],))
                order = self.cr.fetchone()
                if order != None:
                    sale_obj = self.pool.get('sale.order').browse(self.cr, self.uid, order[0])
                    for ol in sale_obj.order_line:
                        opc = ol.number_opc
                        break
                i = self.pool.get('account.invoice').browse(self.cr, self.uid ,r['id'])
                for lines in i.move_lines:
                    debit+=lines.debit
                    credit+=lines.credit
                if i and i.residual:
                    saldo = i.residual
                    
                if i and i.ret_voucher_id:
                    ret = self.pool.get('account.invoice.retention.voucher').browse(self.cr, self.uid ,i.ret_voucher_id.id)
                    if ret.state=="valid":
                        retencion = ret.total or 0.0
                abono = (round(credit,2) or 0.0)-(round(debit,2) or 0.0)
                if abono > 0:
                   abono = abono-retencion
                pvencer.append({'nro': r['nro'],
                                 'emision': r['emision'],
                                 'vencimiento' : r['vencimiento'],
                                 'dias': r['dias'] or 's/f',
                                 'factura': r['total'],
                                 'retencion':retencion,
                                 'abono':abono,
                                 'saldo': saldo,
                                 'opc':opc,
                                 })
                self.pvamout_invoice += r['total']
                self.pvamount_abono += abono
                self.pvamount_retencion += retencion
                self.pvamount_residual += saldo
            
            self.stinvoice += self.pvamout_invoice
            self.stabono += self.pvamount_abono
            self.stretencion += self.pvamount_retencion
            self.stresidual += self.pvamount_residual
            
        return pvencer
    
    def sbtvencidas(self):
        res =[self.vamout_invoice, self.vamount_abono, self.vamount_retencion, self.vamount_residual]
        ##print "res vencidas", res
        return res
    
    def sbtpvencer(self):
        res =[self.pvamout_invoice, self.pvamount_abono, self.pvamount_retencion, self.pvamount_residual]
        ##print "res por vencer", res
        return res
    
    def sbtotal (self):
        res = [self.vamout_invoice+self.pvamout_invoice,
               self.vamount_abono+ self.pvamount_abono,
               self.vamount_retencion+self.pvamount_retencion,
               self.vamount_residual+self.pvamount_residual
               ]
        ##print "sbtotal", res
    
        return res
    
    def totales(self):
        res =[self.stinvoice, self.stabono, self.stretencion, self.stresidual]
        ##print "totales",res
        return res
    
    
        
report_sxw.report_sxw('report.customer_portfolio',
                      'account.invoice',
                      'addons/account_report_extend/report/account_invoice_portfolio_customer.rml',
                      parser=account_invoice_customer, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
    