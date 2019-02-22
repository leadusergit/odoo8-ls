# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

import time, datetime, openerp.pooler, re, openerp.tools
#x = datetime.datetime.now()
from number_to_text import Numero_a_Texto

class generic_payment_cheque():
    debit = 0.00
    credit = 0.00

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
        new = re.sub("^(-?\d+)(\d{3})", "\g<1>.\g<2>", amount)
        if orig == new:
            return new
        else:
            return self.comma_me(new)

    def obt_texto(self,cantidad):
        cant=float(cantidad)
        res=''
        res=Numero_a_Texto(cant)
        tam=len(res)
        if tam<55:
            for i in range(((55-tam)/10)+1):
                #print i
                res+='  ********'
        #res+='\n ********** ********** ********* ********** ********** *********'
        return res
    
    def cambiar_estado(self,id_cheque,fecha):
        res=''
        obj_pc = self.pool.get('payment.cheque')
        pc_id = obj_pc.browse(self.cr, self.uid, id_cheque)
        if not pc_id.state=='cancel':
            obj_pc.write(self.cr,self.uid,id_cheque,{'state':'printed','payment_date':fecha})
        return res
    
    def _get_line_debit(self, lines):
        res = []
        for line in lines:
            if line.debit:
                res.append({'code':line.line_id.account_id.code,
                   'account':openerp.tools.ustr(line.line_id.account_id.name)[:30],
                   'proveedor':line.line_id.partner_id and openerp.tools.ustr(line.line_id.partner_id.name)[:30] or '',
                   'factura':line.line_id.inv_number and openerp.tools.ustr(line.line_id.inv_number)[14:] or '',
                   'debit':round(line.line_id.debit,2),
                   'credit':round(line.line_id.credit,2),
                })
                self.debit += line.line_id.debit
        return res
#         res = []
#         debito = 0.00
#         account_bank = self.pool.get('account.account').search(self.cr,self.uid, [('parent_id','=',1365)])
#         if lines:
#             for line in lines:
#                 if line.line_id.account_id.id not in account_bank:
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
#             if not res:#Caso de solo bancos
#                 for line in lines:
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
#                  
#         return res
    
    def _get_line_credit(self, lines):
        res = []
        for line in lines:
            if line.credit:
                res.append({'code':line.line_id.account_id.code,
                   'account':openerp.tools.ustr(line.line_id.account_id.name)[:30],
                   'proveedor':line.line_id.partner_id and openerp.tools.ustr(line.line_id.partner_id.name)[:30] or '',
                   'factura':line.line_id.inv_number and openerp.tools.ustr(line.line_id.inv_number)[14:] or '',
                   'debit':round(line.line_id.debit,2),
                   'credit':round(line.line_id.credit,2),
                })
                self.credit += line.line_id.credit
        return res
#         res = []
#         credito = 0.00
#         account_bank = self.pool.get('account.account').search(self.cr,self.uid, [('parent_id','=',1365)])
#         
#         if lines:
#             for line in lines:
#                 if line.line_id.account_id.id in account_bank: #Sumo solo bancos
#                     val1 = {'code':line.line_id.account_id.code,
#                          'account':tools.ustr(line.line_id.account_id.name)[:30],
#                          'proveedor':line.line_id.partner_id and tools.ustr(line.line_id.partner_id.name)[:30] or '',
#                          'factura':'',
#                          'debit':0.00,
#                          'credit':round(line.line_id.credit,2),
#                          }
#                     credito += line.line_id.credit or 0.00 - line.line_id.debit or 0.00
#                 else: # Si existe algu otro credito tambien le muestro al credito
#                     if line.line_id.credit:
#                         val = {'code':line.line_id.account_id.code,
#                                'account':tools.ustr(line.line_id.account_id.name)[:30],
#                                'proveedor':line.line_id.partner_id and tools.ustr(line.line_id.partner_id.name)[:30] or '',
#                                'factura':line.line_id.inv_number and tools.ustr(line.line_id.inv_number)[14:] or '',
#                                'debit': 0.00,
#                                'credit':round(line.line_id.credit,2),
#                                }
#                         res.append(val)
#                         self.credit += line.line_id.credit 
#                         
#         if credito: # Valores al credito resto los banco para saber los valores netos a pagar
#             if credito > 0:
#                 val1.update({'credit': abs(round(credito,2))})
#                 res.insert(0,val1)
#                 self.credit += credito
#         else: # 
#              for line in lines:
#                if line.line_id.credit:
#                     val1={'code':line.line_id.account_id.code,
#                          'account':tools.ustr(line.line_id.account_id.name)[:30],
#                          'proveedor':line.line_id.partner_id and tools.ustr(line.line_id.partner_id.name)[:30] or '',
#                          'factura':'',
#                          'debit':0.00,
#                          'credit':round(line.line_id.credit,2),
#                          }
#                     res.insert(0,val1)
#                     self.credit += line.line_id.credit
#         
#         return res
    
    def total (self):
        res = [self.debit, self.credit]
        return res
    
    def _user(self):
        user = pooler.get_pool(self.cr.dbname).get('res.users').browse(self.cr, self.uid, self.uid)
        return openerp.tools.ustr(user.name)
    
    def get_company(self):
        res = []
        user = pooler.get_pool(self.cr.dbname).get('res.users').browse(self.cr, self.uid, self.uid)
        nombre = ''
        direccion = ''
        ruc = ''
        nombre = user.company_id.partner_id.name
        direccion = user.company_id.partner_id.street +' Y ' + user.company_id.partner_id.street2
        ruc = user.company_id.partner_id.ident_num        
        res = [nombre,direccion ,ruc]
        return res
    
    def get_date_invoice(self, o):
        res = ''
        
        if o.date_invoice:
            date_p = o.date_invoice.strip()
            if date_p != 'False':
                date = time.strftime('%d de %B del %Y', time.strptime(date_p, '%Y-%m-%d'))
                if o.inv_type=='purchase_liq':
                    res = 'Fecha Liquidacion de Compra: '
                elif  o.inv_type=='invoice':
                    res = 'Fecha Factura: '
                elif  o.inv_type=='sales_note':
                    res = 'Fecha Nota de Venta: '
                elif  o.inv_type=='anticipo':
                    res = 'Fecha Anticipo: '
                elif  o.inv_type=='gas_no_dedu':
                    res = 'Fecha Gasto: '
                elif  o.inv_type=='doc_inst_est':
                    res = 'Fecha Documento Emit.: '
                res = res + date
                
        return res