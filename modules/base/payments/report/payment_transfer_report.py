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
import openerp.tools

class payment_transfer_report(report_sxw.rml_parse):
    
    _name='payment.transfer.report'
    _description = 'Transferencia Bancaria'
    
    def __init__(self, cr, uid, name, context):
        super(payment_transfer_report,self).__init__(cr, uid, name, context)
        self.localcontext.update({
                                  'time' : time,
                                  'get_datos':self.get_datos,
                                  'texto':self._texto,
                                  'debit':self._get_line_debit,
                                  'credit':self._get_line_credit,
                                  'total':self.total,
                                  'usuario':self._user,
                                  'estado':self._printed,
                                  'company':self.get_company()
                                  })
        self.context = context
        self.debit = 0.00
        self.credit = 0.00
        

    def get_datos(self, partner_id,num):
        obj_emp = self.pool.get('res.partner').read(self.cr,self.uid,[str(partner_id)],['ident_num','bank_ids'])
        #print 'obj_emp ',obj_emp
        res=''
        if num==1:
            res=str(obj_emp['ident_num'])
        elif num==2:
            res=str(obj_emp['bank_ids'][0])
        elif num==3:
            res= str(obj_emp.bank_ids[0].acc_num)
        return res

    def _printed(self,id_transferencia,fecha):
        obj_transfer = self.pool.get('payment.transfer')
        id_transfer = obj_transfer.browse(self.cr, self.uid,id_transferencia)
        if not id_transfer.state=='cancel':
            self.pool.get('payment.transfer').write(self.cr,self.uid,id_transferencia,{'state':'printed','payment_date':fecha})
        return True
    
    def _get_line_debit(self, lines):
        res = []
        for line in lines:
            if line.debit:
                res.append({'code':line.line_id.account_id.code,
                   'account':tools.ustr(line.line_id.account_id.name)[:30],
                   'proveedor':line.line_id.partner_id and tools.ustr(line.line_id.partner_id.name)[:30] or '',
                   'factura':line.line_id.inv_number and tools.ustr(line.line_id.inv_number)[14:] or '',
                   'debit':round(line.line_id.debit,2),
                   'credit':round(line.line_id.credit,2),
                })
                self.debit += line.line_id.debit
        return res
    
#===============================================================================
#     def _get_line_debit(self, lines):
#         res = []
#         debito = 0.00
#         account_bank = self.pool.get('account.account').search(self.cr,self.uid, [('parent_id','=',12)])
#         if lines:
#             for line in lines:
#                 
#                 proveedor = line.line_id.partner_id and tools.ustr(line.line_id.partner_id.name)[:30] or ''
#                 
# #                 if line.line_id.employee_id:
# #                     proveedor = line.line_id.employee_id.name
#                 
#                 if not line.line_id:
#                     continue
#                 if line.line_id.account_id.id not in account_bank:#Todos los cuentas que no sean bancos
#                     if line.line_id.debit:
#                         val = {'code':line.line_id.account_id.code,
#                                'account':tools.ustr(line.line_id.account_id.name)[:30],
#                                'proveedor':proveedor,
#                                'factura':line.line_id.inv_number and tools.ustr(line.line_id.inv_number)[14:] or '',
#                                'debit':round(line.line_id.debit,2),
#                                'credit':0.00,
#                                }
#                         res.append(val)
#                         self.debit += line.line_id.debit
#                         
#             if not res:#Caso de solo bancos
#                 for line in lines:
#                     if not line.line_id:
#                         continue
#                     if line.line_id.debit:
#                         val = {'code':line.line_id.account_id.code,
#                                'account':tools.ustr(line.line_id.account_id.name)[:30],
#                                'proveedor':line.line_id.partner_id and tools.ustr(line.line_id.partner_id.name)[:30] or '',
#                                'factura':line.line_id.inv_number and tools.ustr(line.line_id.inv_number)[14:] or '',
#                                'debit':round(line.line_id.debit,2),
#                                'credit':0.00,
#                                }
#                         res.append(val)
#                         self.debit += line.line_id.debit
#             if not res:
#                 for item in lines:
#                     if item.debit > 0:
#                         v = {
#                                'code':item.name,
#                                'account':item.account,
#                                'proveedor':item.partner,
#                                'factura':len(item.invoice_num) > 14 and str(item.invoice_num)[14:] or item.invoice_num or '',
#                                'debit':item.debit,
#                                'credit':0.00,
#                                }
#                         res.append(v)
#                         self.debit += line.debit
#                  
#         return res
#===============================================================================
    
    def _get_line_credit(self, lines):
        res = []
        for line in lines:
            if line.credit:
                res.append({'code':line.line_id.account_id.code,
                   'account':tools.ustr(line.line_id.account_id.name)[:30],
                   'proveedor':line.line_id.partner_id and tools.ustr(line.line_id.partner_id.name)[:30] or '',
                   'factura':line.line_id.inv_number and tools.ustr(line.line_id.inv_number)[14:] or '',
                   'debit':round(line.line_id.debit,2),
                   'credit':round(line.line_id.credit,2),
                })
                self.credit += line.line_id.credit
        return res
    
    #===========================================================================
    # def _get_line_credit(self, lines):
    #     res = []
    #     credito = 0.00
    #     account_bank = self.pool.get('account.account').search(self.cr,self.uid, [('parent_id','=',12)])
    #     
    #     if lines:
    #         for line in lines:
    #             if not line.line_id:
    #                 continue
    #             if line.line_id.account_id.id in account_bank: 
    #                 #Sumo solo bancos
    #                 val1 = {'code':line.line_id.account_id.code,
    #                      'account':tools.ustr(line.line_id.account_id.name)[:30],
    #                      'proveedor':line.line_id.partner_id and tools.ustr(line.line_id.partner_id.name)[:30] or '',
    #                      'factura':'',
    #                      'debit':0.00,
    #                      'credit':round(line.line_id.credit,2),
    #                      }
    #                 credito += line.line_id.credit or 0.00 - line.line_id.debit or 0.00
    #             else: 
    #                 #Si existe algu otro credito tambien le muestro al credito
    #                 if line.line_id.credit:
    #                     val = {'code':line.line_id.account_id.code,
    #                            'account':tools.ustr(line.line_id.account_id.name)[:30],
    #                            'proveedor':line.line_id.partner_id and tools.ustr(line.line_id.partner_id.name)[:30] or '',
    #                            'factura':line.line_id.inv_number and tools.ustr(line.line_id.inv_number)[14:] or '',
    #                            'debit': 0.00,
    #                            'credit':round(line.line_id.credit,2),
    #                            }
    #                     res.append(val)
    #                     self.credit += line.line_id.credit 
    #     #print credito
    #     if credito: # Valores al credito resto los banco para saber los valores netos a pagar
    #         if credito > 0:
    #             val1.update({'credit': abs(round(credito,2))})
    #             res.insert(0,val1)
    #             self.credit += credito
    #     else: # 
    #          for line in lines:
    #              if not line.line_id:
    #                 continue
    #              if line.line_id.credit:
    #                 val1={'code':line.line_id.account_id.code,
    #                      'account':tools.ustr(line.line_id.account_id.name)[:30],
    #                      'proveedor':line.line_id.partner_id and tools.ustr(line.line_id.partner_id.name)[:30] or '',
    #                      'factura':'',
    #                      'debit':0.00,
    #                      'credit':round(line.line_id.credit,2),
    #                      }
    #                 res.insert(0,val1)
    #                 self.credit += line.line_id.credit
    #     if not res:
    #         for item in lines:
    #             if item.credit > 0:
    #                 v = {
    #                        'code':item.name,
    #                        'account':item.account,
    #                        'proveedor':item.partner,
    #                        'factura':'',
    #                        'debit':0.00,
    #                        'credit':item.credit,
    #                    }
    #                 res.append(v)
    #     return res
    #===========================================================================
    
    def total (self):
        res = [self.debit, self.credit]
        return res
    
    def _texto (self, account, partner, invoice_num):
        if account:
            return account[:30]
        if partner:
            return partner.name[:30]
        if invoice_num:
            return invoice_num[14:]
    
    def _user(self):
        user = pooler.get_pool(self.cr.dbname).get('res.users').browse(self.cr, self.uid, self.uid)
        return user.name
    
    def get_company(self):
        res = []
        user = pooler.get_pool(self.cr.dbname).get('res.users').browse(self.cr, self.uid, self.uid)
        nombre = ''
        direccion = ''
        ruc = ''
        nombre = user.company_id.partner_id.name
        if user.company_id.partner_id and user.company_id.partner_id.address:
            if user.company_id.partner_id.street:
                direccion = user.company_id.partner_id.street
                if user.company_id.partner_id.street2:
                    direccion += ' Y '
                    direccion += user.company_id.partner_id.street2
            else:
                direccion = ''
         
        ruc = user.company_id.partner_id.ident_num or ''        
        res = [nombre,direccion ,ruc]
        return res

report_sxw.report_sxw('report.payment.transfer',
                      'payment.transfer',
                      "addons/payments/report/payment_transfer_report.rml", 
                      parser=payment_transfer_report,
                      header=False)

