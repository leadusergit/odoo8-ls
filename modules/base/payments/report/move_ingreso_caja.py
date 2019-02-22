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
import openerp.pooler
from openerp.report import report_sxw
from number_to_text import Numero_a_Texto
import re
import openerp.tools #Ayuda a mostrar datos con eñes y tíldes


class move_ingreso_caja(report_sxw.rml_parse):
    _name = 'move.ingreso.caja'
    _description = 'Formato para el ingreso de caja'
    
    def __init__(self, cr, uid, name, context):
        super(move_ingreso_caja, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time' : time,
                                  'obt_texto':self.obt_texto,
                                  'texto':self.texto,
                                  'debit':self._get_line_debit,
                                  'credit':self._get_line_credit,
                                  'total':self.total,
                                  'usuario':self._user,
                                  'get_company':self.get_company,
                                  'formato':self.comma_me,
                                  'total_debit':self.total_debit,
                                  'ref_empresa':self.ref_empresa,
                                  'data_deposit':self._data_deposit,
                                  'get_ruc':self._get_ruc,
                                  'get_cheque':self._get_cheque,
                                  'get_name_extra':self._get_name_extra,
                                  'get_secuencial':self._get_secuencial,
                                  })
        self.context = context
        self.debit = 0 
        self.credit = 0
    
    
    
    def ref_empresa(self, lines):
        
        res = ''
        i = 0
        for line in lines:
            if i == 0:
                nombre = line.partner_id.name
                res = nombre
            else:
                nombre_actual = line.partner_id.name
                if nombre != nombre_actual:
                    res = ', ' + nombre_actual
                        
        return res      
                 
    def _get_ruc(self, det):
        res = ''
        i = 0
        for line in det:
            if i == 0:
                nombre = line.partner_id.name
                res = line.partner_id.ident_num
            else:
                nombre_actual = line.partner_id.name
                ruc = line.partner_id.ident_num
                if nombre != nombre_actual:
                    res = ', ' + ruc      
        return res
                 
             
    
    def total (self):
        res = [self.debit, self.credit]
        return res
    
    
        #Funcion que separa el punto en lugar de comas y pone a 2 decimales las cantidades
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

    def obt_texto(self, cantidad):
#        #print 'cantidad',cantidad
        cant = float(cantidad)
        res = ''
        res = Numero_a_Texto(cant)
#        #print 'res',res
        tam = len(res)
        if tam < 55:
            for i in range(((55 - tam) / 10) + 1):
                #print i
                res += '*********** '
        res += '\n ********** ********** ********* ********** ********** *********'
        return res
    
    
    def _get_line_debit(self, lines):
        res = []
        
        #for line in lines:
        #    #print ' line ', line
        #    #print '  line ', line.debit
        #    #print '  line ', line.credit
        #    #print '  line ', line.account_id
            
        i = 0      
        ##print '  val ##### 1'
        debito = 0.00
        ##print '  val ##### 2'
        account_bank = self.pool.get('account.account').search(self.cr, self.uid, [('parent_id', '=', 7)])
        ##print '  val ##### 3'
        if lines:
            ##print '  val ##### 4'
            for line in lines:
                ##print '  val ##### 5'
                if line.account_id.id not in account_bank: 
                    if line.debit:
                        val = {'code':line.account_id.code,
                               'account':tools.ustr(line.account_id.name)[:30],
                               'proveedor':tools.ustr(line.partner_id.name)[:30],
                               'factura':'',
                               'debit':round(line.debit, 2),
                               'credit':0.00,
                               }
                        
                        
                        res.append(val)
                        self.debit += line.debit
                else:
                    
                    if line.debit:
                        ##print '  val ##### 10', line.ref
                        self.debit += line.debit
                        i += 1
                        val = {'code':line.account_id.code,
                               'account':tools.ustr(line.account_id.name)[:30],
                               'proveedor':tools.ustr(line.partner_id.name)[:30],
                               'factura':'',
                               'debit':round(self.debit, 2),
                               'credit':0.00,
                        }
            if i != 0:            
                res.append(val)
#         for resu in res:
            #print ' resu ', resu
                               
        return res
    
    def _get_line_credit(self, lines):
        res = []
        credito = 0.00
        account_bank = self.pool.get('account.account').search(self.cr, self.uid, [('parent_id', '=', 7)])
        if lines:
            for line in lines:
                #print ' lines #### ', line.ref
                if line.account_id.id in account_bank and line.credit:
                    val1 = {'code':line.account_id.code,
                         'account':tools.ustr(line.account_id.name)[:30],
                         'proveedor':tools.ustr(line.partner_id.name)[:30],
                         'factura':line.ref and tools.ustr(line.ref)[:14] or '',
                         'debit':0.00,
                         'credit':round(line.credit, 2),
                         }
                    credito += line.credit or 0.00 - line.debit or 0.00
                    self.credit += credito
                    res.append(val1)
                else:
                    if line.credit:
                        self.credit += line.credit
                        #print ' line.credit ', line.ref
                        #print ' line.ref ', line.ref
                        val1 = {'code':line.account_id.code,
                               'account':tools.ustr(line.account_id.name)[:30],
                               'proveedor':tools.ustr(line.partner_id.name)[:30],
                               'factura':line.ref and tools.ustr(line.ref)[:14] or '',
                               'debit': 0.00,
                               'credit':round(line.credit, 2),
                               }
                        res.append(val1)
                     
        #self.credit += credito
        #res.insert(0,val1)
        
#         for resu in res:
            #print ' resu ', resu
            
        return res
    
    def total_credit (self, lines):
        total = 0
        if lines:
            for line in lines:
                if not(line.credit == 0):
#                    #print line.credit
                    total += line.credit
        
        return total
    
    def total_debit(self, lines):
        total = 0
        #print ' lines ####'
        if lines:
            for line in lines:
                #print ' line.debit ', line.debit
                if not(line.debit == 0):
                    total += line.debit
        return total            
    
    def texto (self, account, partner, invoice_num):
        if account:
            return account[:30]
        if partner:
            return tools.ustr(partner.name)[:30]
        if invoice_num:
            return invoice_num[14:]
    
    def _user(self):
        user = pooler.get_pool(self.cr.dbname).get('res.users').browse(self.cr, self.uid, self.uid)
        return tools.ustr(user.name)
    
    def get_company(self):
        res = []
        user = pooler.get_pool(self.cr.dbname).get('res.users').browse(self.cr, self.uid, self.uid)
        nombre = ''
        direccion = ''
        ruc = ''
        nombre = user.company_id.partner_id.name
        direccion = user.company_id.partner_id.street + ' Y ' + user.company_id.partner_id.street2
        ruc = user.company_id.partner_id.ident_num        
        res = [nombre, direccion , ruc]
        return res
    
    def _get_secuencial(self, o):
        
        account_bank_statement = self.pool.get('account.bank.statement')
        if o.no_comp_rel:
            return o.no_comp_rel
        else:
            seq = self.pool.get('ir.sequence').get(self.cr, self.uid, 'ingreso_caja_seq')
            account_bank_statement.write(self.cr, self.uid, o.id, {'sequence':seq})
            return seq
    
    
    
    def _data_deposit(self, stm, column):
        
        res = ''
        abs = pooler.get_pool(self.cr.dbname).get('account.bank.statement')
        rpb = pooler.get_pool(self.cr.dbname).get('res.partner.bank') 
       
        if stm.has_deposit:
           
            statemen_infos = abs.read(self.cr, self.uid, stm.id, ['has_deposit', 'num_deposit', 'date_deposit', 'amount_deposit', 'acc_deposit_id', 'payments'])
           
            if column == 'deposit':
                payments = statemen_infos['payments'] or ''
                if payments == 'depo':
                    res = 'Forma de Pago:' + 'Depósito'
                else:
                    res = 'Forma de Pago:' + 'Transfere'                    
                return res
                
            if column == 'num_deposit':
                res = '  NUM COMPROBANTE: ' + str(statemen_infos['num_deposit'])
                return res
            
            if column == 'date_deposit':    
                res = ' FECHA: ' + str(statemen_infos['date_deposit'])
                return res
            
            if column == 'amount_deposit':    
                res = ' VALOR: ' + str(statemen_infos['amount_deposit'])
                return res
            
            acc_deposit_id = statemen_infos['acc_deposit_id'][0]
            bank_ids = rpb.search(self.cr, self.uid, [('id', '=', acc_deposit_id)])
            partner_bank_info = rpb.read(self.cr, self.uid, bank_ids, ['acc_number', 'bank'])
            ##print ' partner_bank_info ', partner_bank_info
            
            if column == 'acc_number':
                res = ' CUENTA ' + str(partner_bank_info[0]['acc_number'])
                return res
                
            if column == 'bank':
                res = ' BANCO: ' + str(partner_bank_info[0]['bank'][1])
                return res                
                
        else:
           return res            
        return res
    
    def _get_cheque(self, cheque_details):
        res = ''
        for cheque in  cheque_details:
            res += cheque.number + " ,"   
        return res
    
    def _get_name_extra(self, extracto):
        return extracto.name[:30]
    
report_sxw.report_sxw('report.move.ingreso.caja',
                      'account.bank.statement',
                      "addons/payments/report/move_ingreso_caja.rml",
                      parser=move_ingreso_caja, header=False)

