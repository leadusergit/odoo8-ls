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
from reportlab.pdfgen import canvas


class statement_supplier(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(statement_supplier, self).__init__(cr, uid, name, context=context)
        
        self.debito = 0.0
        self.credito = 0.0
        self.sbtsaldo = 0.0
        
        self.sumdebito = 0.0
        self.sumcredito = 0.0
        self.sumsaldo = 0.0
        
        self.localcontext.update( {
            'time': time,
            'supplier':self.supplier,
            'move_line': self.move_supplier,
            'saldo':self.saldo,
            'subtotales': self.subtotales,
            'totales': self.totales,
            'detalle':self.detalle,
        })
        
    def detalle(self, detalle):
        if detalle:
            return detalle[:100]
        else:
            return
        
    def saldo (self, supplier, form):
        date_start = form.get('date_start', False)
        date_from = form.get('date_from', False)
        saldo = 0.0
        if supplier:
            if date_start==date_from:
                return saldo
            else:
                sql ="""--PAGOS FACTURAS
                     SELECT sum (am.debit) as debit ,sum(am.credit) as credit , 'pago factura' as type
                           FROM account_move_line am
                        WHERE am.partner_id = %s
                          AND am.date >= '%s'
                          AND am.date < '%s'
                          AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332)
                          AND am.reconcile_id >1
                          AND am.statement_id >1
                          AND am.debit > 0
                     UNION
                   --PAGO DE ANTICIPOS
                   SELECT sum (am.debit) as debit ,sum(am.credit) as credit , 'pago anticipo' as type
                         FROM account_move_line am
                       WHERE am.partner_id = %s
                         AND am.date >= '%s'
                         AND am.date < '%s'
                         AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332) 
                         AND am.statement_id > 1
                         AND am.reconcile_id > 1
                         AND am.credit > 0
                    UNION
                    --ABONOS FACTURAS
                    SELECT sum (am.debit) as debit ,sum(am.credit) as credit , 'ABONO' as type
                           FROM account_move_line am
                        WHERE am.partner_id = %s
                          AND am.date >= '%s'
                          AND am.date < '%s'
                          AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332)
                          AND am.reconcile_partial_id >1
                    --FACTURAS
                    UNION
                    SELECT 0.0 as debit, sum (ai.amount_pay) as credit, 'fac' as type
                           FROM account_invoice AS ai
                           WHERE ai.partner_id = %s
                           AND ai.date_invoice >= '%s'
                           AND ai.date_invoice < '%s'
                           AND ai.state in ('open', 'paid')
                           AND ai.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332)
                           AND type in ('in_invoice')
                     --RETENCIONES  
                    UNION
                     SELECT abs(sum (ai.amount_tax_retention)) as debit, 0.0 as credit, 'ret' as type
                           FROM account_invoice AS ai
                           WHERE ai.partner_id = %s
                           AND ai.date_invoice >= '%s'
                           AND ai.date_invoice < '%s'
                           AND ai.state in ('open', 'paid')
                           AND ai.type in ('in_invoice')
                           AND ai.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332)
                           AND abs(ai.amount_tax_retention) > 0
                    --NOTAS DE CREDITO
                    UNION
                     SELECT sum (ai.amount_total) as debit ,0.0 as credit, 'nc' as type
                           FROM account_invoice AS ai
                           WHERE ai.partner_id = %s
                           AND ai.date_invoice >= '%s'
                           AND ai.date_invoice < '%s'
                           AND ai.state in ('open','paid')
                           AND type in ('in_refund')
                     UNION
                    --SALDO INICIAL CON PAGOS TOTALES
                    SELECT sum (am.debit) as debit ,sum(am.credit) as credit , 'inicial total' as type
                           FROM account_move_line am
                           WHERE am.partner_id = %s
                           AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332)
                           AND am.journal_id =19
                           AND am.date >= '%s'
                           AND am.date < '%s'
                           AND am.reconcile_id >1
                     UNION
                    --SALDO INICIAL CON PAGOS PARCIALES
                    SELECT sum (am.debit) as debit ,sum(am.credit) as credit , 'inicial parcial' as type
                           FROM account_move_line am
                           WHERE am.partner_id = %s
                           AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332)
                           AND am.journal_id =19
                           AND am.date >= '%s'
                           AND am.date < '%s'
                           AND am.reconcile_partial_id >1
                    """%(supplier, date_start,date_from,#Pagos Facturas
                         supplier, date_start,date_from,#Pagos Anticipos
                         supplier, date_start,date_from,#abonos
                         supplier, date_start,date_from,#Facturas
                         supplier, date_start,date_from,#Retenciones
                         supplier, date_start,date_from,#Notas de credito
                         supplier, date_start,date_from,#Saldo inicial total
                         supplier, date_start,date_from#Saldo inicial parcial
                         )
        ##print "SALDO sql\n", sql
        self.cr.execute(sql)
        res = self.cr.dictfetchall()
        ##print "res", res
        if res:
            saldo = 0.0
            for r in res:
                saldo += (r['debit'] or 0.0) - (r['credit'] or 0.0)
            
        return saldo
    
    def supplier(self, form):
        supplier = form.get('partner_id', False)
        date_start = form.get('date_start', False)
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        
        if supplier:
            sql="SELECT id, name as supplier FROM res_partner WHERE supplier is True AND id ="+str(supplier)+ "AND active is True"
            self.cr.execute(sql)
            res = self.cr.dictfetchall()
        else:
            sql="""SELECT id, name as supplier FROM res_partner WHERE supplier is True AND active is True 
                   AND id in (SELECT partner_id FROM account_move_line WHERE date  BETWEEN '%s' AND '%s'AND statement_id > 1
                              AND reconcile_id > 1 AND account_id in (SELECT id FROM account_account WHERE parent_id = 1332))"""%(date_from,date_to)
            self.cr.execute(sql)
            pagos = [aux[0] for aux in self.cr.fetchall()]
            sql="""SELECT id, name as supplier FROM res_partner WHERE supplier is True AND active is True
                    AND id in (SELECT partner_id FROM account_invoice WHERE date_invoice BETWEEN '%s' AND '%s' AND state in ('open', 'paid')
                    AND type in ('in_invoice', 'in_refund'))
                    """%(date_from,date_to)
            self.cr.execute(sql)
            facturas = [aux[0] for aux in self.cr.fetchall()]
            sql="""SELECT id, name as supplier FROM res_partner WHERE supplier is True AND active is True 
                   AND id in (SELECT partner_id FROM account_move_line WHERE date  BETWEEN '%s' AND '%s'AND reconcile_partial_id > 1 
                   AND account_id in (SELECT id FROM account_account WHERE parent_id = 1332))"""%(date_from,date_to)
            self.cr.execute(sql)
            abonos = [aux[0] for aux in self.cr.fetchall()]
            sql="""SELECT id, name as supplier FROM res_partner WHERE supplier is True AND active is True 
                   AND id in (SELECT partner_id FROM account_move_line WHERE date  BETWEEN '%s' AND '%s' AND journal_id =19 
                              AND account_id in (SELECT id FROM account_account WHERE parent_id = 1332))"""%(date_start,date_to)
            self.cr.execute(sql)
            iniciales = [aux[0] for aux in self.cr.fetchall()]
            partners = pagos + facturas + abonos + iniciales
            ##print "1", partners
            partner = list(set(partners))
            ##print "2", partner
            if partner:
                sql = "select id, name as supplier from res_partner where id in ("+','.join([str(x) for x in partner])+") order by name"
                self.cr.execute(sql)
                res = self.cr.dictfetchall()
            else:
                res =[]
        if res:
            for r in res:
                city = ''
                street = ''
                phone = ''
                representante = ''
                zona = ''
                p = self.pool.get('res.partner').browse(self.cr, self.uid, r['id'])
                if p:
                    r['codcontable']= p.property_account_payable.code
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
        
    def move_supplier(self, supplier, form):
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        date_start = form.get('date_start', False)

        if supplier:
            sql ="""--PAGOS DE FACTURAS
                  SELECT am.id as id, am.partner_id as p, am.date as emision,
                     'CAN' AS cod, am.ref AS nro, am.date_maturity AS vence,
                     CASE 
                       WHEN Length(am.inv_number)>0 THEN 'REG. CAN. FAC '||am.ref
                       WHEN am.inv_number is null THEN am.ref
                     ELSE am.name
                    END AS det, am.debit AS debit, am.credit AS credit, '1' as orden
                         FROM account_move_line am
                       WHERE am.partner_id = %s
                         AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332) 
                         AND am.statement_id > 1
                         AND am.reconcile_id > 1
                         AND am.debit > 0
                         AND am.date BETWEEN '%s' AND '%s'
                  UNION
                  --PAGO DE ANTICIPOS
                  SELECT am.id as id, am.partner_id as p, am.date as emision,
                     'CA' AS cod, am.ref AS nro, am.date_maturity AS vence,
                     CASE 
                       WHEN Length(am.inv_number)>0 THEN 'REG. CAN. ANT. '||am.ref
                       WHEN am.inv_number is null THEN am.ref
                     ELSE am.name
                    END AS det, am.debit AS debit, am.credit AS credit, '2' as orden
                         FROM account_move_line am
                       WHERE am.partner_id = %s
                         AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332) 
                         AND am.statement_id > 1
                         AND am.reconcile_id > 1
                         AND am.credit > 0
                         AND am.date BETWEEN '%s' AND '%s'
                  UNION
                  --ABONOS DE FACTURAS
                  SELECT am.id as id, am.partner_id as p, am.date as emision,
                     'ABO' AS cod, am.ref AS nro, am.date_maturity AS vence,
                     CASE 
                       WHEN Length(am.inv_number)>0 THEN 'REG. ABONO. FAC '||am.ref
                       WHEN am.inv_number is null THEN am.ref
                     ELSE am.name
                    END AS det, am.debit AS debit, am.credit AS credit, '3' as orden
                      FROM account_move_line AS am
                       WHERE am.partner_id = %s
                         AND am.date BETWEEN '%s' AND '%s'
                         AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332) 
                         AND am.reconcile_partial_id > 1
                   UNION
                   --FACTURAS
                   SELECT am.id as id, am.partner_id AS p, ai.date_invoice AS emision, 
                   'FAC' AS cod, cast(ai.number_inv_supplier as char(10)) AS nro, 
                    ai.date_due AS vence, 'REG. FAC. ' || cast(ai.number_inv_supplier as char(10)) AS det,  0.0 AS debit, ai.amount_pay AS credit,'4' as orden
                         FROM account_invoice AS ai
                       JOIN account_move_line AS am
                         ON (ai.move_id = am.move_id)
                       WHERE am.partner_id = %s
                         AND ai.date_invoice BETWEEN '%s' AND '%s'
                         AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332) 
                         AND ai.state in ('open', 'paid')
                         AND ai.type in ('in_invoice')
                   --RETENCIONES
                   UNION
                       SELECT ai.id as id, ai.partner_id as p, ai.date_invoice AS emision, 'RET' AS cod, cast(ai.number_inv_supplier as char(10)) AS nro,
                       ai.date_due as vence,
                       CASE 
                         WHEN ai.origin is null
                          THEN 'Retencion-Factura:' || cast(ai.number_inv_supplier as char(10))
                         ELSE 'Retencion Factura: ' || cast(ai.number_inv_supplier as char(10)) ||' /'||ai.origin
                           END AS det, 
                        abs(ai.amount_tax_retention) as debit, 0.0 as credit, '5' as orden
                         FROM account_invoice ai
                       WHERE ai.partner_id = %s
                         AND ai.date_invoice BETWEEN '%s' AND '%s'
                         AND abs(ai.amount_tax_retention) > 0
                         AND ai.state in ('open', 'paid')
                         AND ai.type in ('in_invoice')
                   --NOTAS DE CREDITO
                   UNION 
                     SELECT am.id as id, am.partner_id as p, ai.date_invoice AS emision, 'NC' AS cod, cast(ai.number_inv_supplier as char(10)) as nro,
                            ai.date_due as vence, 'Doc. Origen: '||ai.origin AS det, ai.amount_total as debit , 0.0 as credit, '6' as orden
                         FROM account_move_line AS am
                       JOIN account_invoice AS ai
                         ON (am.move_id = ai.move_id)
                       WHERE am.partner_id = %s
                         AND ai.date_invoice BETWEEN '%s' AND '%s'
                         AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332) 
                         AND ai.state in ('open', 'paid')
                         AND ai.type in ('in_refund')
                         
                   --FACTURAS ANULADAS
                   UNION 
                       SELECT ai.id as id, ai.partner_id as p, ai.date_invoice as emision, 'ANU' AS cod, ai.factura as nro, ai.date_due as vence,
                        ai.comment AS det, 0.0 as debit, 0.0 as credit, '7' as orden
                         FROM account_invoice as ai
                       WHERE ai.partner_id = %s
                         AND ai.date_invoice BETWEEN '%s' AND '%s'
                         AND ai.state = 'cancel'
                         AND ai.type in ('in_invoice', 'in_refund')
                         
                   """%(supplier, date_from,date_to,#PAGOS
                        supplier, date_from,date_to,#ANTICIPOS
                        supplier, date_from,date_to,#PAGO PARCIAL
                        supplier, date_from,date_to,#FACT
                        supplier, date_from,date_to,#RET
                        supplier, date_from,date_to,#NC
                        supplier, date_from,date_to)#ANU
            if date_start == date_from:
                sql = sql +"""--SALDO inicio periodo 
                             UNION
                             SELECT am.id as id, am.partner_id AS p, cast(am.name as date) as emision, 'SA' AS cod, am.ref AS nro, 
                               am.date_maturity AS vence, 'Saldo Inicial '|| 'Fact.'|| am.ref AS det,  am.debit AS debit, am.credit AS credit,'8' as orden
                               FROM account_move_line am
                             WHERE am.partner_id = %s
                              AND am.date BETWEEN '%s' AND '%s'
                              AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332) 
                              AND am.journal_id = 19
                              """%(supplier, date_start,date_to)
            else:
                sql = sql +"""--SALDO fuera del inicio
                         UNION 
                          SELECT am.id as id, am.partner_id AS p, cast(am.name as date) as emision, 'SA' AS cod, am.ref AS nro, 
                               am.date_maturity AS vence, 'Saldo Inicial '|| 'Fact.'|| am.ref AS det,  am.debit AS debit, am.credit AS credit,'9' as orden
                               FROM account_move_line am
                            WHERE am.partner_id = %s
                              AND am.date BETWEEN '%s' AND '%s'
                              AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332) 
                              AND am.journal_id = 19
                              AND am.reconcile_id is null
                              AND am.reconcile_partial_id is null"""%(supplier, date_start,date_to)
            order = " ORDER BY emision, nro "
            
            ##print "lineas sql\n", sql
            self.cr.execute(sql + order)
            res = self.cr.dictfetchall()
            
            saldo = 0.0
            self.debito = 0.0
            self.credito = 0.0
            self.sbtsaldo = 0.0
            if res:
                saldo = self.saldo(supplier, form)
                #print 'saldo', saldo
                #saldo = 0.0
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

report_sxw.report_sxw('report.supplier_estado_cuenta',
                      'account.move.line',
                      'addons/account_report_extend/report/statement_supplier.rml',
                      parser=statement_supplier, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

        