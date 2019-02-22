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
from openerp.osv import osv, fields
from cStringIO import StringIO
from base64 import encodestring
from xlwt import Workbook, Formula
from datetime import datetime
from openerp.addons.base_ec.tools.xls_tools import *
import time

TYPES_INVOICE = [('out_invoice,out_refund', 'Ventas'), ('in_invoice,in_refund', 'Compras')]

TYPES_INV = [
    ('out_invoice','FACTURA CLIENTES'),
    ('in_invoice','FACTURAS PROVEEDORES'),
    ('out_refund','NOTAS DE CRÉDITO'),
    ('in_refund','NOTAS DE DÉBITO'),
]

def style(bold=False, font_name='Calibri', height=11, font_color='black',
          rotation=0, align='left', vertical='center', wrap=True,
          border=False, color=None, format=None):
    return get_style(bold, font_name, height, font_color, rotation, align, vertical, wrap, border, color, format)

styles = {
    'header': style(True, align='center', border=True),
    'type': style(True, wrap=False, color='ice_blue'),
    'body': style(),
    'number': style(format='0.00', align='right'),
    'total': style(True, format='0.00', color='periwinkle', align='right'),
    'total2': style(True, height=13, format='0.00', color='lime', border=True, align='right') 
}

class wizard_reporte_tributario(osv.osv_memory):
    _name = 'wizard.reporte.tributario'
    #_inherit = 'ir.wizard.screen'
    _description = 'Reporte tributario de compras o ventas'
    _columns = {
        'type': fields.selection(TYPES_INVOICE, 'Tipo', required=True),
        'date_from': fields.date('Fecha desde'),
        'date_to': fields.date('Fecha hasta'),
        'file': fields.binary('Archivo', readonly=True),
        'filename': fields.char('Archivo', size=512, readonly=True),
        'state': fields.selection([('draft', 'draft'), ('done', 'done')], readonly=True, required=True)
    }
    _defaults = {
        'state': lambda *a: 'draft'
    }
    
    def __get_data(self, cr, uid, ids, type_name, invoice_ids, sheet, row=7):
        sheet.write_merge(row, row, 0, 3, type_name, styles['type'])
        sheet.write(row, 4, Formula('SUBTOTAL(9, E{0}:E{1})'.format(row+2, row+1+len(invoice_ids))), styles['total'])
        sheet.write(row, 5, Formula('SUBTOTAL(9, F{0}:F{1})'.format(row+2, row+1+len(invoice_ids))), styles['total'])
        sheet.write(row, 6, Formula('SUBTOTAL(9, G{0}:G{1})'.format(row+2, row+1+len(invoice_ids))), styles['total'])
        sheet.write(row, 7, Formula('SUBTOTAL(9, H{0}:H{1})'.format(row+2, row+1+len(invoice_ids))), styles['total'])
        sheet.write(row, 9, Formula('SUBTOTAL(9, J{0}:J{1})'.format(row+2, row+1+len(invoice_ids))), styles['total'])
        sheet.write(row, 10,Formula('SUBTOTAL(9, K{0}:K{1})'.format(row+2, row+1+len(invoice_ids))), styles['total'])
        sheet.write(row, 11,Formula('SUBTOTAL(9, L{0}:L{1})'.format(row+2, row+1+len(invoice_ids))), styles['total'])

        row += 1
        for invoice in invoice_ids:
            print"/*/*invoice/*/*=%s"%invoice
            sheet.write(row, 0, invoice.date_invoice, styles['body'])
            sheet.write(row, 1, invoice.factura or '', styles['body'])
            sheet.write(row, 2, invoice.partner_id.name, styles['body'])
            sheet.write(row, 3, invoice.fiscal_position.name or '', styles['body'])
            sheet.write(row, 4, invoice.t_b_excenta_iva, styles['number'])
            sheet.write(row, 5, invoice.t_bi_iva, styles['number'])
            sheet.write(row, 6, invoice.t_iva, styles['number'])
            sheet.write(row, 7, Formula('SUM(E{0}:G{0})'.format(row+1)), styles['number'])
            sheet.write(row, 8, invoice.ret_id.name or invoice.ret_voucher_id.number, styles['body'])
            sheet.write(row, 9, invoice.t_ret_iva or invoice.ret_voucher_id.ret_vat or 0.00, styles['number'])
            sheet.write(row, 10, invoice.amount_ret_ir or invoice.ret_voucher_id.ret_ir or 0.00, styles['number'])
            sheet.write(row, 11, Formula('SUM(J{0}:K{0})'.format(row+1)), styles['number'])
            row += 1
            
                
        return sheet, row
    
    def generate(self, cr, uid, ids, context=None):
        obj = self.read(cr, uid, ids[0], ['date_from', 'date_to', 'type'])
        book = Workbook('utf-8')
        sheet = book.add_sheet('Hoja1')
        name = 'REPORTE TRIBUTARIO DE ' + dict(TYPES_INVOICE)[obj['type']].upper()
        row = 7
        sheet.write_merge(row-3, row-3, 0, 7, name, style(True, align='center', height=14))
        totas_rows = []
        for col, field in enumerate(['Fecha', 'No. Factura', 'Cliente', 'Contribuyente', 'Sub 0%', 'Sub 12%', 'IVA', 'TOTAL','Nº Retención','RIVA','RIR','TotalRetención']):
            sheet.write(row-1, col, field, styles['header'])
        for type in obj['type'].split(','):
            args = [('state', 'in', ['open', 'paid']), ('type', '=', type)]
            if obj['date_from']: args.append(('date_invoice', '>=', obj['date_from']))
            if obj['date_to']: args.append(('date_invoice', '<=', obj['date_to']))
            invoice_ids = self.pool.get('account.invoice').search(cr, uid, args)
            if not invoice_ids:
                continue
            invoice_ids = self.pool.get('account.invoice').browse(cr, uid, invoice_ids)
            totas_rows.append(row+1)
            sheet, row = self.__get_data(cr, uid, ids, dict(TYPES_INV)[type], invoice_ids, sheet, row)
        sheet.write(row, 3, 'TOTAL GENERAL', style(True, height=13, color='lime', border=True))
        sheet.write(row, 4, Formula('+'.join(['E{0}'.format(aux) for aux in totas_rows])), styles['total2'])
        sheet.write(row, 5, Formula('+'.join(['F{0}'.format(aux) for aux in totas_rows])), styles['total2'])
        sheet.write(row, 6, Formula('+'.join(['G{0}'.format(aux) for aux in totas_rows])), styles['total2'])
        sheet.write(row, 7, Formula('+'.join(['H{0}'.format(aux) for aux in totas_rows])), styles['total2'])
        sheet.write(row, 9, Formula('+'.join(['J{0}'.format(aux) for aux in totas_rows])), styles['total2'])
        sheet.write(row, 10, Formula('+'.join(['K{0}'.format(aux) for aux in totas_rows])), styles['total2'])
        sheet.write(row, 11, Formula('+'.join(['L{0}'.format(aux) for aux in totas_rows])), styles['total2'])



        
        buf = StringIO()
        book.save(buf)
        out = encodestring(buf.getvalue())
        buf.close()
        return self.pool['base.file.report'].show(cr, uid, out, name + '.xls')
#         return self.write(cr, uid, ids, {'file': out, 'filename': name + '.xls','state': 'done'})
    
wizard_reporte_tributario()