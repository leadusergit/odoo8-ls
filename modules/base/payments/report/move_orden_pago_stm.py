# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 4R Soft (<http://4rsoft.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

#
# Please note that these reports are not multi-currency !!!
#

from openerp.osv import fields, osv
import openerp.tools
from openerp.report import report_sxw
import re
from datetime import datetime



def get_date(fecha):
    obj_fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
    return obj_fecha.strftime("%d-%m-%Y")


class move_orden_pago_stm(report_sxw.rml_parse):
    
    #Obtener el numero de orden de pago
    def _get_opago(self, lines):
        res = []
        if lines:
            for line in lines:
                #Obtengo el numero de referencia de la factura
                statement_id = line.statement_id
                #Obtengo el statement_id del extracto bancario
            if statement_id:
                                
                #Obtengo el move_id que se genera
                self.cr.execute("select distinct(move_id) from account_move_line where statement_id=%i order by move_id" % (statement_id,))
                datos2 = self.cr.fetchall()
                if datos2:
                    move_id = datos2[0][0]
                    #Obtengo el numero de comprobante de orden de pago del extracto
                    self.cr.execute("select no_comp from account_move where id=%i" % (move_id,))
                    datos3 = self.cr.fetchall()       
                    num_orden = datos3[0][0]    
                    if num_orden:
                        if num_orden != "0000000":
                            val = {'num_orden':num_orden,
                                  }
                        
                      
                            res.append(val)
                            self.orden = num_orden
                        else:
                            val = {'num_orden':"",
                                  }
                        
                      
                            res.append(val)
                            self.orden = num_orden
                                            
        return res
    
    def _get_line_debit(self, lines):
        res = []
        if lines:
            
            #Recorro las facturas importadas
            for line in lines:
                #Obtengo el numero de referencia de la factura
                statement_id = line.statement_id
                
                #Obtengo los movimientos contables de la factura
            if statement_id:
                self.cr.execute("select id from account_journal where code='RCCH'")
                journal = self.cr.fetchall() 
                if journal:
                    journal_id = journal[0][0] 
                self.cr.execute("select id from account_journal where code='DP'")
                journal2 = self.cr.fetchall() 
                if journal2:
#<<<<<<< TREE
#                    journal_id2=journal2[0][0]
                

#                query="(SELECT b.code,'resumido' as factura, b.name as nombre, sum(a.debit), sum(a.credit) FROM account_move_line a, account_account b where       a.account_id=b.id  and a.journal_id=%i and a.statement_id IS NULL and lower(b.name) not like 'proveedores%s' and a.ref in (select c.ref  from account_bank_statement_line c where c.statement_id = %i) and a.partner_id in (select c.partner_id from account_bank_statement_line c where c.statement_id = %i) group by factura,  b.name, b.code ) UNION ALL (SELECT b.code,a.ref as factura, b.name as nombre, a.debit, a.credit FROM account_move_line a, account_account b where a.account_id=b.id  and a.journal_id=%i and a.statement_id IS NULL and lower(b.name) like 'proveedores%s' and a.ref in (select c.ref  from account_bank_statement_line c where c.statement_id = %i ) and a.partner_id in (select c.partner_id  from account_bank_statement_line c where c.statement_id = %i)) UNION ALL (SELECT b.code,'general' as factura, b.name as nombre, sum(a.debit), sum(a.credit) FROM account_move_line a, account_account b,account_bank_statement_line z, account_bank_statement_line_move_rel c where a.account_id=b.id and a.move_id=c.statement_id and z.id=c.move_id and a.statement_id=z.statement_id and (a.ref=z.ref or a.ref is null or z.ref is null) and a.journal_id=%i and a.statement_id in (select c.statement_id from account_bank_statement_line c where c.statement_id = %i) and z.type='general' group by factura,  b.name, b.code) order by factura desc " % (journal_id,'%',statement_id,statement_id,journal_id,'%',statement_id,statement_id,journal_id2,statement_id,)

#                #print 'query', query

#                self.cr.execute(query)
#=======
                    journal_id2 = journal2[0][0]
                
                query = """(SELECT b.code,'resumido' as factura, b.name as nombre, sum(a.debit), sum(a.credit), a.funds_certificate_id, a.preproject_id, a.analytic_account_id
                FROM account_move_line a, account_account b
                where a.account_id=b.id --and a.journal_id=%i
                and a.statement_id IS NULL and lower(b.name) not like 'proveedores%s'
                and a.ref in (select c.ref from account_bank_statement_line c where c.statement_id = %i)
                and a.partner_id in (select c.partner_id from account_bank_statement_line c where c.statement_id = %i)
                group by factura,  b.name, b.code, a.funds_certificate_id, a.preproject_id, a.analytic_account_id)
                UNION ALL
                (SELECT b.code,a.ref as factura, b.name as nombre, a.debit, a.credit, a.funds_certificate_id, a.preproject_id, a.analytic_account_id
                FROM account_move_line a, account_account b where a.account_id=b.id
                --and a.journal_id=%i
                and a.statement_id IS NULL and lower(b.name) like 'proveedores%s'
                and a.ref in (select c.ref  from account_bank_statement_line c where c.statement_id = %i)
                and a.partner_id in (select c.partner_id from account_bank_statement_line c where c.statement_id = %i))
                UNION ALL
                (select b.code,'general' as factura, b.name as nombre, sum(a.debit), sum(a.credit), z.funds_certificate_id, z.preproject_id, z.analytic_account_id
                from account_bank_statement_line z, account_move_line a, account_account b
                where
                z.id = a.statement_line_id
                and a.account_id = b.id
                and a.journal_id = %i
                and z.statement_id = %i
                and z.type = 'general'
                group by factura,  b.name, b.code, z.funds_certificate_id, z.preproject_id, z.analytic_account_id)
                order by factura desc""" % (journal_id, '%', statement_id, statement_id, journal_id, '%', statement_id, statement_id, journal_id2, statement_id,)
                
                print query
                
                self.cr.execute(query)
                datos = self.cr.fetchall()
                ##print ' datos del debit ', datos
                
                i = 0
                for a in datos:
                    code = datos[i][0]
                    name = datos[i][2]
                    debit = datos[i][3]
                    credit = datos[i][4]
                    ref1 = datos[i][1]
                    funds_id = datos[i][5]
                    preproject_id = datos[i][6]
                    analytic_id = datos[i][7]
                    if debit:
                        val = {'code':code,
                               'account':tools.ustr(name)[:30],
                               'debit':round(debit, 2),
                               'credit':0.00,
                               'factura':ref1,
                               'funds_id': funds_id,
                               'preproject_id': preproject_id,
                               'analytic_id': analytic_id
                        }
                                                
                        res.append(val)
                        self.debit += debit
                    i += 1
        return res
        
        
    def _get_line_credit(self, lines):
        res = []
        if lines:
            
            #Recorro las facturas importadas
            for line in lines:
                #Obtengo el numero de referencia de la factura
                statement_id = line.statement_id
                #Obtengo los movimientos contables de la factura
                
            if statement_id:
                
                self.cr.execute("select id from account_journal where code='RCCH'")
                journal = self.cr.fetchall() 
                if journal:
                    journal_id = journal[0][0] 
                
                self.cr.execute("select id from account_journal where code='DP'")
                journal2 = self.cr.fetchall()
                if journal2:
                    journal_id2 = journal2[0][0]
                
                query = """(SELECT b.code,'resumido' as factura, b.name as nombre, sum(a.debit), sum(a.credit), a.funds_certificate_id, a.preproject_id, a.analytic_account_id
                                FROM account_move_line a, account_account b where a.account_id=b.id  --and a.journal_id=%i
                                and a.statement_id IS NULL and lower(b.name) not like 'proveedores%s'
                                and a.ref in (select c.ref  from account_bank_statement_line c where c.statement_id = %i)
                                and a.partner_id in (select c.partner_id from account_bank_statement_line c
                                where c.statement_id = %i) group by factura, b.name, b.code, a.funds_certificate_id, a.preproject_id, a.analytic_account_id)
                                UNION ALL
                                (SELECT b.code,a.ref as factura, b.name as nombre, a.debit, a.credit, a.funds_certificate_id, a.preproject_id, a.analytic_account_id
                                FROM account_move_line a, account_account b
                                where a.account_id=b.id  --and a.journal_id=%i
                                and a.statement_id IS NULL and lower(b.name) like 'proveedores%s'
                                and a.ref in (select c.ref  from account_bank_statement_line c where c.statement_id = %i)
                                and a.partner_id in (select c.partner_id  from account_bank_statement_line c where c.statement_id = %i))
                                UNION ALL
                                (select b.code,'general' as factura, b.name as nombre, sum(a.debit), sum(a.credit), z.funds_certificate_id, z.preproject_id, z.analytic_account_id
                                    from account_bank_statement_line z, account_move_line a, account_account b
                                    where
                                    z.id = a.statement_line_id
                                    and a.account_id = b.id
                                    and a.journal_id = %i
                                    and z.statement_id = %i
                                    and z.type = 'general'
                                    group by factura,  b.name, b.code, z.funds_certificate_id, z.preproject_id, z.analytic_account_id)
                                order by factura desc""" % (journal_id, '%', statement_id, statement_id, journal_id, '%', statement_id, statement_id, journal_id2, statement_id,) 
                print query
                self.cr.execute(query)
                
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
                datos = self.cr.fetchall()
                
                i = 0
                for a in datos:
                    code = datos[i][0]
                    name = datos[i][2]
                    debit = datos[i][3]
                    credit = datos[i][4]
                    ref1 = datos[i][1]
                    funds_id = datos[i][5]
                    preproject_id = datos[i][6]
                    analytic_id = datos[i][7]
                    if credit:
                        val = {'code':code,
                               'account':tools.ustr(name)[:30],
                               'debit':0.00,
                               'credit':round(credit, 2),
                               'factura':ref1,
                               'funds_id': funds_id,
                               'preproject_id': preproject_id,
                               'analytic_id': analytic_id
                        }
                                                
                        res.append(val)
                        self.credit += credit
                    i += 1
        
                                            
        return res
    #def total_credit (self, lines):
    #    total = 0
    #    if lines:
    #        for line in lines:
    #            if not(line.credit == 0):
#   #                 #print line.credit
    #                total += line.credit
        
    #    return total
    
    
    
    #def total_debit(self, lines):
    #    total = 0
    #    #print ' lines ####'
    #    if lines:
    #        for line in lines:
    #            #print ' line.debit ', line.debit
    #            if not(line.debit == 0):
    #                total += line.debit
    #    return total 
    
    def total (self):
        res = [self.debit, self.credit]
        return res
    
    def comma_me(self, amount):
        if not amount:
            amount = 0.0
        if type(amount) is float:
            amount = str('%.2f' % amount)
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
        
    def line_field(self, model, obj_id, *fields):
        if not obj_id:
            return ''
        line_model = self.pool.get(model)
        obj_id = line_model.browse(self.cr, self.uid, obj_id)
        value = obj_id
        for field in fields:
            if not eval('value.' + field):
                return ''
            value = eval('value.' + field)
        return value
    
    def __init__(self, cr, uid, name, context):
        super(move_orden_pago_stm, self).__init__(cr, uid, name, context)
        self.localcontext.update({'orden':self._get_opago,
                                  'debit':self._get_line_debit,
                                  'formato':self.comma_me,
                                  'credit':self._get_line_credit,
                                  'total':self.total,
                                  'date':get_date,
                                  'linefield': self.line_field,
                                  'fundsname': lambda name: name and name.split('-')[0] or ''
                                  })
        self.context = context
        self.orden = ""
        self.debit = 0 
        self.credit = 0
                
report_sxw.report_sxw('report.move.orden.pago.stm', 'account.bank.statement', "payments/report/move_orden_pago_stm.rml", parser=move_orden_pago_stm, header=False)

