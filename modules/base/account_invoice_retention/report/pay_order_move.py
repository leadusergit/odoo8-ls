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

class pay_order_move(report_sxw.rml_parse):
    _provisiones_por_varios = 1721

    def _sum_total(self, move, data):
        suma = 0.0
        for line in move.line_id:
            suma += line.debit
        return suma
    
    def _valor_orden_pago(self, move):
        suma = 0.0
        for line in move.line_id:
            if line.account_id.id == self._provisiones_por_varios:
                suma += line.credit
        if suma == 0.0:
            suma = self._sum_total(move,None)
        return suma
        
    def usuario(self, mov):
        perm = pooler.get_pool(self.cr.dbname).get('account.move').perm_read(self.cr, self.uid, [mov.id])
        if perm:
            return perm[0]['create_uid'][1]
        else:
            return ''
    
    def _detalle(self, move, info):
        band = False
        res = ''
        result = ''
        invoice_obj = pooler.get_pool(self.cr.dbname).get('account.invoice')
        if info == 'linea':
            if move.product_id:
                band = True
                res = move.product_id and move.product_id.product_tmpl_id and move.product_id.product_tmpl_id.name or ''
                return tools.ustr(res)[:40]
            else:
                return self.get_detalle(move, info)
        else:
            return self.get_detalle(move, info)
        
                
    def get_detalle (self, var, info):
        res = ''
        invoice_obj = pooler.get_pool(self.cr.dbname).get('account.invoice')
        if info == 'linea':
            invoice_id = invoice_obj.search(self.cr, self.uid, [('move_id', '=', var.move_id.id)])
        else:
            invoice_id = invoice_obj.search(self.cr, self.uid, [('move_id', '=', var.id)])
    
        if invoice_id:
            inv = invoice_obj.browse(self.cr, self.uid, invoice_id[0])            
            if inv.state in ('open', 'paid'):
                if inv.ret_id:
                    res = 'R.RENTA # ' + inv.ret_id.name + ' '
                elif inv.ret_voucher_id:
                    res = 'R.RENTA #' + str(inv.ret_voucher_id.nro_retencion) + ' '
                if inv.type in ('in_invoice'):
                    if inv.tipo_factura in ('invoice', 'purchase_liq', 'sales_note'):
                        if inv.tipo_factura in ('invoice'):
                            res += 'FACT / '
                        elif inv.tipo_factura in ('purchase_liq'):
                            res += 'LIQ / '
                        elif inv.tipo_factura in ('sales_note'):
                            res += 'NotaVta / '    
                        res += str(inv.auth_inv_id.serie_entidad) 
                        res += '-' + str(inv.auth_inv_id.serie_emision)
                        res += '-' + str(inv.number_inv_supplier).zfill(9)
                    elif inv.tipo_factura in ('anticipo'):
                        res += 'ANT / ' + inv.code_advance_liq
                    elif inv.tipo_factura in ('gas_no_dedu', 'doc_inst_est','gasto_financiero'):
                        if inv.tipo_factura in ('gas_no_dedu'):
                            res += 'Gasto / ' + inv.number
                        elif inv.tipo_factura in ('gas_no_dedu'):
                            res += 'Doc.Int / ' + inv.number
                        elif inv.tipo_factura in ('gasto_financiero'):
                            res += 'Gasto.Fin / ' + inv.number
                elif inv.type in ('in_refund'):
                    res += 'NC / '
                    res += str(inv.auth_inv_id.serie_entidad) 
                    res += '-' + str(inv.auth_inv_id.serie_emision)
                    res += '-' + str(inv.number_inv_supplier).zfill(9)
                    
                elif inv.type in ('out_invoice', 'out_refund'):
                    if inv.type in ('out_invoice'):
                        res += 'FACT / ' + str(inv.num_retention).zfill(9)
                    else:
                        res += 'NC / ' + str(inv.num_retention).zfill(9)
        return res

    
    def _info_invoice(self, mov, info):
        result = ''
        invoice_obj = pooler.get_pool(self.cr.dbname).get('account.invoice')
        invoice_id = invoice_obj.search(self.cr, self.uid, [('move_id', '=', mov.id)])
        if invoice_id:
            invoices = invoice_obj.browse(self.cr, self.uid, invoice_id)
            for inv in invoices:
                if info == 'invoice':
                    if inv.type in ('in_invoice', 'in_refund'):
                        if inv.tipo_factura in ('invoice', 'purchase_liq', 'sales_note'):
                            res = str(inv.number_inv_supplier).zfill(9)
                            if inv.tipo_factura == 'invoice':
                                result = 'Factura: ' + res
                            elif inv.tipo_factura == 'purchase_liq':
                                result = 'Liquidación de Compra: ' + res
                            elif inv.tipo_factura == 'sales_note':
                                result = 'Nota de Venta: ' + res
                            
                        elif inv.tipo_factura in ('anticipo'):
                            result = 'Anticipo: ' + inv.code_advance_liq
                        elif inv.tipo_factura in ('doc_inst_est', 'gas_no_dedu','gasto_financiero'):
                            res = inv.number
                            if inv.tipo_factura == 'doc_inst_est':
                                result = 'Documento de Institucion: ' + res
                            elif inv.tipo_factura == 'gas_no_dedu':
                                result = 'Gasto No Deducible: ' + res
                            elif inv.tipo_factura == 'gasto_financiero':
                                result = 'Gastos Financieros: ' + res
                                
                    elif inv.type in ('out_invoice', 'out_refund'):
                        res = str(inv.num_retention).zfill(9)
                        if inv.type == 'out_invoice':
                            result = 'Factura: ' + res
                        elif inv.type == 'out_refund':
                            result = 'Nota de Credito: ' + res
                        
                if info == 'retention':
                    if inv.type in ('in_invoice'):
                        res = inv.ret_id and inv.ret_id.name or ''
                        if res:
                            result = 'Retencion: ' + res
                    elif inv.type in ('out_invoice'):
                        res = inv.ret_voucher_id and inv.ret_voucher_id.nro_retencion or ''
                        if res:
                            result = 'Retencion:' + res.zfill(9)      
        return result
    
    
    def _get_lines(self, lines):
        res = []
        for line in lines:
            if not(line.debit == 0 and line.credit == 0):
                res.append(line)
        for i in range(len(res) - 1):
            for j in range(i + 1, len(res)):
                if res[i].debit < res[j].debit:
                    aux = res[i]
                    res[i] = res[j]
                    res[j] = aux
        return res
    
    def get_date(self, mov):
        invoice_obj = pooler.get_pool(self.cr.dbname).get('account.move')
        res = ''
        invoices = invoice_obj.search(self.cr, self.uid, [('move_id', '=', mov.id)])
        if invoices:
            invoice = invoice_obj.browse(self.cr, self.uid, invoices[0])
            res = str(time.strftime('QUITO, %d de %B del %Y', time.strptime(invoice.date_invoice, '%Y-%m-%d'))).upper()
        else:
            res = str(time.strftime('QUITO, %d de %B del %Y', time.strptime(mov.date, '%Y-%m-%d'))).upper()
        return res
    

    def __init__(self, cr, uid, name, context):
        super(pay_order_move, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
                'time': time,
                'sum_credit': self._sum_total,
                'sum_debit': self._sum_total,
                'user_create':self.usuario,
                'detalle':self._detalle,
                'lines': self._get_lines,
                'get_date':self.get_date,
                'get_detalle':self.get_detalle,
                'val_op':self._valor_orden_pago,
                'fundsname': lambda name: name and name.split('-')[0] or ''
                })

report_sxw.report_sxw('report.pay.order.move', 'account.move', 'addons/account_invoice_retention/report/pay_order_move.rml', parser=pay_order_move)
        
