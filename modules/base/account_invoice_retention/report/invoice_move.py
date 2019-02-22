# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author :  Cristian Salamea cristian.salamea@gnuthink.com
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

from openerp.report import report_sxw
import time
from openerp import pooler
from openerp import tools

TYPO_FACTURA = dict([
    ('invoice', 'Factura'),
    ('purchase_liq', 'Liquidación de Compra'),
    ('sales_note', 'Nota de Venta'),
    ('anticipo', 'Anticipo'),
    ('gas_no_dedu', 'Gastos No Deduci'),
    ('doc_inst_est', 'Doc Emitido Estado'),
    ('gasto_financiero', 'Gastos Financieros')
])

class invoice_move(report_sxw.rml_parse):

    def _sum_total(self, inv, data):
        suma = 0.0
        if inv.move_id:
            for line in inv.move_id.line_id:
                suma += line.debit
        return suma
    
    def usuario(self, inv):
        res = ''
        if inv.move_id:
            perm = pooler.get_pool(self.cr.dbname).get('account.move').perm_read(self.cr, self.uid, [inv.move_id.id], self.context)
            if perm:
                return perm[0]['create_uid'][1]
        return res
    
    def _get_lines(self, lines):
        res=[]
        if lines:
            for line in lines:
                if not(line.debit == 0 and line.credit == 0):
                    res.append(line)
            
            for i in range(len(res)-1):
                for j in range(i+1, len(res)):
                    if res[i].debit < res[j].debit:
                        aux=res[i]
                        res[i]=res[j]
                        res[j]=aux
        return res
    
    def _detalle(self, inv, move):
        res = ''
        if inv.state in ('open','paid'):
            if move.product_id:
                res = move.product_id and move.product_id.product_tmpl_id and move.product_id.product_tmpl_id.name or ''
                return tools.ustr(res)[:40]
            else:
                if inv.ret_id:
                    res = 'R.RENTA # '+ inv.ret_id.name + ' '
                elif inv.ret_voucher_id and inv.ret_voucher_id.state=='valid':
                    res = 'R.RENTA #' + str(inv.ret_voucher_id.nro_retencion).zfill(9) + ' '
                if inv.type in ('in_invoice'):
                    if inv.tipo_factura in ('invoice','purchase_liq','sales_note'):
                        if inv.tipo_factura in ('invoice'):
                            res += 'FACT/ '
                        elif inv.tipo_factura in ('purchase_liq'):
                            res += 'LIQ/ '
                        elif inv.tipo_factura in ('sales_note'):
                            res += 'NotaVta/ '    
                        res += str(inv.auth_inv_id.serie_entidad) 
                        res += '-' + str(inv.auth_inv_id.serie_emision)
                        res += '-' + str(inv.number_inv_supplier).zfill(9)
                    elif inv.tipo_factura in ('anticipo'):
                        res += 'ANT/ ' + inv.code_advance_liq
                    elif inv.tipo_factura in ('gas_no_dedu','doc_inst_est','gasto_financiero'):
                        if inv.tipo_factura in ('gas_no_dedu'):
                            res += 'Gasto/ ' + inv.number
                        elif inv.tipo_factura in ('gas_no_dedu'):
                            res += 'Doc.Int/ ' + inv.number
                        elif inv.tipo_factura in ('gasto_financiero'):
                            res += 'Gasto.Fin/ ' + inv.number
                elif inv.type in ('in_refund'):
                    res += 'NC/ '
                    res += str(inv.auth_inv_id.serie_entidad) 
                    res += '-' + str(inv.auth_inv_id.serie_emision)
                    res += '-' + str(inv.number_inv_supplier).zfill(9)
                    
                elif inv.type in ('out_invoice','out_refund'):
                    if inv.type in ('out_invoice'):
                        res += 'FACT/ ' + str(inv.num_retention).zfill(9)
                    else:
                        res += 'NC/ ' + str(inv.num_retention).zfill(9)
                ##print 'imprime',res
                return res
        else:
            return res

    def invoice(self,invoice, documento):
        result = ''
        if documento == 'invoice' and invoice.state in ('open','paid'):
            if invoice.type == 'in_invoice':
                if invoice.tipo_factura in ('invoice','purchase_liq','sales_note'):
                    res = invoice.auth_inv_id.serie_entidad 
                    res += '-' + invoice.auth_inv_id.serie_emision
                    res += '-' + str(invoice.number_inv_supplier).zfill(9)
                    if invoice.tipo_factura in ('invoice'):
                        result = 'Factura: ' + res
                    elif invoice.tipo_factura in ('purchase_liq'):
                        result = 'Liquidacion de Compra: ' + res
                    elif invoice.tipo_factura in ('sales_note'):
                        result = 'Nota de Venta: ' + res
                elif invoice.tipo_factura in ('anticipo'):
                    res = invoice.code_advance_liq
                    result = 'Anticipo: '+ res
                elif invoice.tipo_factura in ('gas_no_dedu','doc_inst_est','gasto_financiero'):
                    res = invoice.number
                    if invoice.tipo_factura in ('gas_no_dedu'):
                        result = 'Gasto no deducible: '+ res
                    elif invoice.tipo_factura in ('doc_inst_est'):
                        result = 'Doc Emitido Estado: '+ res
                    elif invoice.tipo_factura in ('gasto_financiero'):
                        result = 'Gastos Financieros: '+ res
                        
            elif invoice.type == 'in_refund':
                res = invoice.auth_inv_id.serie_entidad 
                res += '-' + invoice.auth_inv_id.serie_emision
                res += '-' + str(invoice.number_inv_supplier).zfill(9)
                result = 'Nota de Credito: '+ res
                
            elif invoice.type == 'out_invoice':
                result = 'Factura: '+ str(invoice.num_retention).zfill(9)
            elif invoice.type == 'out_refund':
                result = 'Nota de Credito: '+ str(invoice.num_retention).zfill(9)
            
        if documento == 'retention' and invoice.state in ('open','paid'):
            if invoice.type in ('in_invoice','in_refund'):
                if invoice.ret_id:
                    res = str(invoice.ret_id.name)
                    result = 'Retencion: '+ res
            elif invoice.type in ('out_invoice','out_refund'):
                if invoice.ret_voucher_id and invoice.ret_voucher_id.state=='valid':
                    res = str(invoice.ret_voucher_id.nro_retencion).zfill(9)
                    result = 'Retencion: '+ res
        return result
                    
    
    def get_date(self, o):
        res = ''
        if o.date_invoice:
            res = 'Fecha: ' + time.strftime('Quito, %d de %B del %Y', time.strptime(o.date_invoice, '%Y-%m-%d'))
        else:
            res = 'Fecha: ' + time.strftime('Quito, %d de %B del %Y')
        return res
    
    def get_tipo(self, tipo_factura):
        return TYPO_FACTURA[tipo_factura]
    
    def __init__(self, cr, uid, name, context):
        super(invoice_move, self).__init__(cr, uid, name, context)
        self.localcontext.update({
                'time': time,
                'sum_credit': self._sum_total,
                'sum_debit': self._sum_total,
                'detalle': self._detalle,
                'lines': self._get_lines,
                'usuario':self.usuario,
                'get_date':self.get_date,
                'invoice':self.invoice,
                'sum':sum,
                'tipo_com': self.get_tipo
                })
        self.context = context

report_sxw.report_sxw('report.invoice.move',
                      'account.invoice',
                      'addons/account_invoice_retention/report/invoice_move.rml',
                      parser=invoice_move,
                      header=False)

