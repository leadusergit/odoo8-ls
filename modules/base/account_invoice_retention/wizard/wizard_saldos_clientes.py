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

def style(bold=False, font_name='Calibri', height=11, font_color='black',
          rotation=0, align='left', vertical='center', wrap=True,
          border=False, color=None, format=None):
    return get_style(bold, font_name, height, font_color, rotation, align, vertical, wrap, border, color, format)

styles = {
    'title': style(True, align='center', height=14),
    'header': style(True, align='center', border=True),
    'partner': style(True, wrap=False, color='ice_blue'),
    'body': style(),
    'number': style(format='0.00', align='right'),
    'total': style(True, format='0.00', color='periwinkle', align='right'),
    'total2': style(True, height=13, format='0.00', color='lime', border=True, align='right') 
}

class wizard_saldos_clientes(osv.osv_memory):
    _name = 'wizard.saldos.clientes'
    #_inherit = 'ir.wizard.screen'
    _description = u'Reporte de antigüedad de saldos de clientes'
    _columns = {
        'type': fields.selection([('out_invoice', 'Por cobrar'), ('in_invoice', 'Por pagar')], 'Tipo', required=True),
        'period': fields.integer('Periodicidad', required=True),
        'days': fields.integer('Días de cada periodo', required=True),
        'date': fields.date('Fecha', required=True),
        'partner_id': fields.many2one('res.partner', 'Empresa'),
        'date_from': fields.date('Fecha desde'),
        'date_to': fields.date('Fecha hasta'),
        'file': fields.binary('Archivo', readonly=True),
        'filename': fields.char('Archivo', size=512, readonly=True),
        'state': fields.selection([('draft', 'draft'), ('done', 'done')], readonly=True)
    }
    _defaults = {
        'period': lambda *a : 5,
        'days': lambda *a : 30,
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft'
    }
    
    def __group(self, invoice_ids, field='partner_id'):
        res = {}
        for invoice in invoice_ids:
            aux = eval('invoice.' + field)
            value = res.get(aux, [])
            res[aux] = value + [invoice]
        return res
    
    def __evaluator(self, days, part=30, period=5):
        aux = int(days) / int(part)
        aux -= 0 if (int(days)%int(part)) else 1
        return aux if aux < period else period - 1
    
    def generate(self, cr, uid, ids, context=None):
        obj = self.read(cr, uid, ids[0], context=context)
        #print"obj::::",obj
        args = [('type', '=', obj['type']), ('state', '=', 'open'), ('date_invoice', '<=', obj['date'])]
        if obj['partner_id']: args.append(('partner_id', '=', obj['partner_id']))
        if obj['date_from']: args.append(('date_invoice', '>=', obj['date_from']))
        if obj['date_to']: args.append(('date_invoice', '<=', obj['date_to']))
        invoice_ids = self.pool.get('account.invoice').search(cr, uid, args, context=context)
        #print"invoice_ids:::::",invoice_ids
        if not invoice_ids:
            raise osv.except_osv('Mensaje', 'No existen registros coicidentes')
        wb = Workbook('utf-8')
        sheet = wb.add_sheet('Hoja1')
        sheet.col(0).width = 1307
        invoice_ids = self.pool.get('account.invoice').browse(cr, uid, invoice_ids, context=context)
        #print"hdsjhjdinvoice_ids:::",invoice_ids
        row = 7
        title = 'REPORTE DE ANTIGUEDAD DE SALDOS ' + (obj['type']=='out_invoice' and 'CLIENTES' or 'PROVEEDORES')
        sheet.write_merge(row-3, row-3, 0, 10, title, styles['title'])
        total_rows = []
        for col, field in enumerate(['No. Doc.', 'Fecha', 'Importe', 'Pagado', 'Por pagar'], 1):
            sheet.write(row-1, col, field, styles['header'])
        for col, period in enumerate(range(obj['period'])):
            name = '{0}{1}{2} Días'.format(col*obj['days']+1, ' - ', (col+1)*obj['days'])
            if period == obj['period'] - 1:
                name = '+{0} Días'.format(col*obj['days'])
            sheet.write(row-1, 6+col, name, styles['header'])
        for partner, invoice_ids in self.__group(invoice_ids, 'partner_id.name').iteritems():
            sheet.write_merge(row, row, 0, 5, partner, styles['partner'])
            for col in range(obj['period']):
                sheet.write(row, 6+col, Formula('SUBTOTAL(9,{0}{1}:{0}{2})'.format(GET_LETTER(6+col), row+2, row+1+len(invoice_ids))), styles['total'])
            row += 1
            total_rows.append(row)
            for invoice in invoice_ids:
                sheet.write(row, 1, invoice.num_retention or '', styles['body'])
                sheet.write(row, 2, invoice.date_invoice, styles['body'])
                sheet.write(row, 3, invoice.amount_total, styles['number'])
                sheet.write(row, 4, invoice.amount_total - invoice.residual, styles['number'])
                sheet.write(row, 5, invoice.residual, styles['number'])
                days = (datetime.strptime(obj['date'], '%Y-%m-%d').date() - datetime.strptime(invoice.date_invoice, '%Y-%m-%d').date()).days
                col = self.__evaluator(days, obj['days'], obj['period'])
                sheet.write(row, 7+col, invoice.residual, styles['number'])
                row += 1
                
        sheet.write(row, 4, 'TOTAL', style(True, height=13, format='0.00', color='lime', border=True))
        sheet.write(row, 5, Formula('SUBTOTAL(9, G{0}:{1}{0})'.format(row+1, GET_LETTER(5+obj['period']))), styles['total2'])
        for col in range(obj['period']):
            sheet.write(row, 6+col, Formula('+'.join(['{0}{1}'.format(GET_LETTER(6+col), aux) for aux in total_rows])), styles['total2'])
        
        buf = StringIO()
        wb.save(buf)
        out = encodestring(buf.getvalue())
        buf.close()
        return self.pool.get('base.file.report').show(cr, uid, out, title + '.xls')
        return self.write(cr, uid, ids, {'state': 'done', 'file': out, 'filename': title + '.xls'})

wizard_saldos_clientes()