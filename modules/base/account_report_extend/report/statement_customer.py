#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import openerp.tools
import re



class statement_customer(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(statement_customer, self).__init__(cr, uid, name, context=context)
        
        self.debito = 0
        self.credito = 0
        self.sbtsaldo = 0
        
        self.sumdebito = 0
        self.sumcredito = 0
        self.sumsaldo = 0
        
        self.localcontext.update( {
            'time': time,
            'customer':self.customer,
            'move_line': self.moves_customer,
            'saldo':self.saldo,
            'subtotales': self.subtotales,
            'totales': self.totales,
        })
        
    def saldo (self, customer, form ):
        res = {}
        date_from = form.get('date_from', False)
        date_start = form.get('date_start', False)
        saldo = 0.0
        if customer:
            if date_from==date_start:
                return saldo
            else:
                self.cr.execute("""
                --Facturas Cliente
                SELECT sum (am.debit) as debit ,sum(am.credit) as credit , sum (am.debit - am.credit) as diferencia
                       FROM account_move_line AS am
                       JOIN account_invoice AS ai
                       ON (am.move_id = ai.move_id)
                       WHERE am.partner_id = %s
                       AND ai.date_invoice >= %s
                       AND ai.date_invoice < %s
                       AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226) 
                       AND ai.state in ('open', 'paid')
                       AND ai.type in ('out_invoice', 'out_refund')
                   UNION 
                --Retenciones
                SELECT sum (am.debit) as debit ,sum(am.credit) as credit , sum (am.debit - am.credit) as diferencia
                       FROM account_move_line am
                       JOIN account_invoice_retention_voucher as ar
                       ON (am.move_id = ar.move_id)
                       WHERE am.partner_id = %s
                       AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                       AND ar.broadcast_date >= %s
                       AND ar.broadcast_date < %s
                    UNION
                --Pagos TOTALES
                SELECT sum (am.debit) as debit ,sum(am.credit) as credit , sum (am.debit - am.credit) as diferencia
                       FROM account_move_line am
                       WHERE am.partner_id = %s
                       AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                       AND am.reconcile_id > 1
                       AND am.statement_id > 1
                       AND am.date >= %s
                       AND am.date < %s
                --Pagos PARCIALES
                UNION
                SELECT sum (am.debit) as debit ,sum(am.credit) as credit , sum (am.debit - am.credit) as diferencia
                       FROM account_move_line am
                       WHERE am.partner_id = %s
                       AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                       AND am.reconcile_partial_id > 1
                       AND am.credit > 0
                       AND am.date >= %s
                       AND am.date < %s
                --SALDO INICIAL CON PAGOS TOTALES
                UNION
                SELECT sum (am.debit) as debit ,sum(am.credit) as credit , sum (am.debit - am.credit) as diferencia
                       FROM account_move_line am
                       WHERE am.partner_id = %s
                       AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                       AND am.journal_id =19
                       AND am.date >= %s
                       AND am.date < %s
                       AND am.reconcile_id >1
                --SALDO INICIAL CON PAGOS PARCIALES
                UNION
                SELECT sum (am.debit) as debit ,sum(am.credit) as credit , sum (am.debit - am.credit) as diferencia
                       FROM account_move_line am
                       WHERE am.partner_id = %s
                       AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                       AND am.journal_id =19
                       AND am.date >= %s
                       AND am.date < %s
                       AND am.reconcile_partial_id >1
                --Anticipos Clientes estan en la parte de Extractos Bancarios
                UNION
                SELECT sum (am.debit) as debit ,sum(am.credit) as credit , sum (am.debit - am.credit) as diferencia
                       FROM account_move_line am, account_bank_statement abs
                       WHERE am.partner_id = %s
                       AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                       AND am.statement_id = abs.id
                       AND abs.is_advance is True
                       AND am.date >= %s
                       AND am.date < %s
                """,(customer, date_start, date_from,#Facturas
                     customer, date_start, date_from,#Retenciones
                     customer, date_start, date_from,#Pagos Totales
                     customer, date_start, date_from,#Pagos Parciales
                     customer, date_start, date_from,#Saldo Inicial Total
                     customer, date_start, date_from,#Saldo Inicial Partial Pagado
                     customer, date_start, date_from,#Anticipos de Clientes
                     )
                )
                res = self.cr.dictfetchall()
        if res:
            saldo = 0.0
            for r in res:
                saldo += (r['debit'] or 0.0) - (r['credit'] or 0.0)
        return saldo
    
    def customer(self, form):
        ##print "form Customer", form
        customer = form.get('partner_id', False)
        if customer:
            sql ="SELECT id, name as customer FROM res_partner WHERE customer is True AND id ="+str(customer) +" AND active is True"
        else:
            sql = "SELECT id, name as customer from res_partner  WHERE customer is True AND active is True ORDER BY name"
        self.cr.execute(sql)
        res = self.cr.dictfetchall()    
        if res:
            for r in res:
                city = ''
                street = ''
                phone = ''
                representante = ''
                zona = ''
                p = self.pool.get('res.partner').browse(self.cr, self.uid, r['id'])
                if p:
                    r['codcontable']= p.property_account_receivable.code
                    r['note']= p.comment
                    r['ruc'] = p.ident_num
                    r['cod'] = p.ref
                    if p.address:
                        for a in p.address:
                            if a.function and a.function.code=='REF':
                                representante = a.name and a.name.encode('"UTF-8"')
                            if a.state_id:
                                zona = a.state_id.name
                            city = a.city or ''
                            street = a.street or ''
                            phone = a.phone or ''
                            break
                    r['zona'] = zona
                    r['representate']= representante
                    r['city'] = city
                    r['street'] = street
                    r['phone']= phone
        return res
        
    def moves_customer(self, customer, form):
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        date_start = form.get('date_start', False)
        if customer:
            sql="""
              --FACTURAS
               SELECT am.id as id, am.partner_id as p, ai.date_invoice as emision, 'FAC' AS cod, ai.factura as nro, ai.date_due as vence, 'FAC.CLIENTE'AS det, am.debit as debit , am.credit as credit
                     FROM account_move_line AS am
                   JOIN account_invoice AS ai
                     ON (am.move_id = ai.move_id)
                   WHERE am.partner_id = %s
                     AND ai.date_invoice BETWEEN '%s'AND '%s'
                     AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                     AND ai.state in ('open', 'paid')
                     AND ai.type in ('out_invoice')
              --NOTAS DE CREDITO
              UNION
               SELECT am.id as id, am.partner_id as p, ai.date_invoice as emision, 'NC' AS cod, ai.factura as nro, ai.date_due as vence, 'FAC.CLIENTE'AS det, am.debit as debit , am.credit as credit
                     FROM account_move_line AS am
                   JOIN account_invoice AS ai
                     ON (am.move_id = ai.move_id)
                   WHERE am.partner_id = %s
                     AND ai.date_invoice BETWEEN '%s' AND '%s'
                     AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                     AND ai.state in ('open', 'paid')
                     AND ai.type in ('out_refund')
              --RETENCION
               UNION 
                   SELECT am.id as id, am.partner_id as p, ar.broadcast_date as emision, 'RET' AS cod, ar.numero as nro, am.date_created as vence, am.name as det, am.debit as debit, am.credit as credit
                     FROM account_move_line am
                   JOIN account_invoice_retention_voucher as ar
                     ON (am.move_id = ar.move_id)
                   WHERE am.partner_id = %s
                     AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                     AND ar.broadcast_date BETWEEN '%s' AND '%s'
                     AND ar.state='valid'
              --PAGO COMPLETOS
               UNION
                   SELECT am.id as id, am.partner_id as p, am.date as emision, 'CAN' AS cod, am.ref AS nro, am.date_maturity as vence, ru.name ||' CAN FACURAS'as det, am.debit as debit, am.credit as credit
                     FROM account_move_line am
                   LEFT JOIN res_users as ru
                     ON(am.create_uid = ru.id)
                   WHERE am.partner_id = %s
                     AND am.date BETWEEN '%s' AND '%s'
                     AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                     AND am.reconcile_id >1
                     AND am.statement_id >1
                     AND am.credit > 0
             -- PAGOS PARCIALES
               UNION
                SELECT am.id as id, am.partner_id as p, am.date as emision, 'CAN' AS cod, am.ref AS nro, am.date_maturity as vence, ru.name ||' CAN FACURAS'as det, am.debit as debit, am.credit as credit
                     FROM account_move_line am
                   LEFT JOIN res_users as ru
                     ON(am.create_uid = ru.id)
                   WHERE am.partner_id = %s
                     AND am.date BETWEEN '%s' AND '%s'
                     AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                     AND am.reconcile_partial_id >1
                     AND am.credit > 0
             
               --ANULADAS
               UNION 
                   SELECT ai.id as id, ai.partner_id as p, ai.date_invoice as emision, 'ANU' AS cod, ai.factura as nro, ai.date_due as vence, 'FAC.CLIENTE'AS det, 0.0 as debit, 0.0 as credit
                     FROM account_invoice as ai
                   WHERE ai.partner_id = %s
                     AND ai.date_invoice BETWEEN '%s' AND '%s'
                     AND ai.state = 'cancel'
                     AND ai.type in ('out_invoice', 'out_refund')
              --ANTICIPOS
               UNION 
                   SELECT am.id as id, am.partner_id as p, am.date as emision, 'ANT' AS cod, am.ref AS nro, am.date_maturity as vence, ru.name ||' '|| abs.name as det, am.debit as debit, am.credit as credit
                        FROM account_move_line am, account_bank_statement abs, res_users ru
                       WHERE am.partner_id = %s
                       AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                       AND am.statement_id = abs.id
                       AND abs.is_advance is True
                       AND am.credit > 0
                       AND am.date BETWEEN '%s' AND '%s'
                       AND am.create_uid = ru.id
                     
               """%(customer, date_from,date_to,#FAC
                    customer, date_from,date_to,#NC
                    customer, date_from,date_to,#RET
                    customer, date_from,date_to,#Pago Completos
                    customer, date_from,date_to,#Pago parciales
                    customer, date_from,date_to,#Anuladas)
                    customer, date_from,date_to)#Anticipos de Clientes
            if date_start == date_from:
                sql = sql +"""--SALDO INICIAL 
                             UNION
                             SELECT am.id as id, am.partner_id as p, cast(am.name as date) as emision, 'INI' AS cod, am.ref AS nro, am.date_maturity as vence, ru.name ||' FAC.SI'as det, am.debit as debit, am.credit as credit
                               FROM account_move_line am
                             LEFT JOIN res_users as ru
                              ON(am.create_uid = ru.id)
                             WHERE am.partner_id = %s
                              AND am.date BETWEEN '%s' AND '%s'
                              AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                              AND am.journal_id = 19
                              """%(customer, date_start,date_to)
            else:
                sql = sql +"""--SALDO INICIAL
                         UNION 
                         SELECT am.id as id, am.partner_id as p, cast(am.name as date) as emision, 'INI' AS cod, am.ref AS nro, am.date_maturity as vence, ru.name ||' FAC.SI'as det, am.debit as debit, am.credit as credit
                               FROM account_move_line am
                            LEFT JOIN res_users as ru
                             ON(am.create_uid = ru.id)
                            WHERE am.partner_id = %s
                              AND am.date BETWEEN '%s' AND '%s'
                              AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                              AND am.journal_id = 19
                              AND am.reconcile_id is null
                              AND am.reconcile_partial_id is null"""%(customer, date_start,date_to)
            order = " ORDER BY nro"
            sql = sql + order
            ##print "sql\n", sql
            self.cr.execute(sql)
            res = self.cr.dictfetchall()
            saldo = 0
            self.debito = 0
            self.credito = 0
            self.sbtsaldo = 0
            if res:
                saldo = self.saldo(customer,form)
                for r in res:
                    saldo += r['debit'] - r['credit'] 
                    r['saldo'] =  saldo
                    self.debito += r['debit'] 
                    self.credito += r['credit']
                    self.sbtsaldo = saldo
            self.sumdebito += self.debito
            self.sumcredito += self.credito
            self.sumsaldo += self.sbtsaldo
        return res
    
    def subtotales (self):
        res = [self.debito, self.credito, self.sbtsaldo]
        return res
    
    def totales (self):
        res = [self.sumdebito, self.sumcredito, self.sumsaldo]
        return res

report_sxw.report_sxw('report.estado_cuenta',
                      'account.move.line',
                      'addons/account_report_extend/report/statement_customer.rml',
                      parser=statement_customer, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

        