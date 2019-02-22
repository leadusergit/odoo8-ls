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
from xlrd import open_workbook
from xlwt.Style import easyxf
from xlutils.copy import copy
import cStringIO
import base64
from openerp.modules import get_module_resource

def get_style(bold=False, font_name='Calibri', height=12, font_color='black',
              rotation=0, align='center',
              border=False, color=None, format=None):
    str_style = 'font: bold %s, name %s, height %s, color %s;' % (bold, font_name, height * 20, font_color)
    str_style += 'alignment: rotation %s, horizontal %s, vertical center, wrap True;' % (rotation, align)
    if border:
        if type(border) == str:
            str_style += 'border: %s thin;' % border
        else:
            str_style += 'border: left thin, right thin, top thin, bottom thin;'
    str_style += color and 'pattern: pattern solid, fore_colour %s;' % color or ''
    return easyxf(str_style, num_format_str=format)

class pay_order(osv.osv_memory):
    _name = 'pay.order'
    
    def generate_report(self, cr, uid, id_move, context):
        id_move = context.get('active_id', None)
        if not id_move:
            raise osv.except_osv('Error', 'Registro no encontrado')
#        vals = self.generate_report(cr, uid, id_move, context)
#        self.write(cr, uid, ids, vals)
        
        path_book = get_module_resource('account_invoice_retention', 'data', 'ordenpago.xls')
        format_book = open_workbook(path_book, formatting_info=True, on_demand=True)
        book = copy(format_book)
        path_image = get_module_resource('account_invoice_retention', 'data', 'coviprov_logo.bmp')
        sheet = book.get_sheet(0)
        sheet_res = book.get_sheet(1)
        sheet.insert_bitmap(path_image, 1, 2, scale_x=0.7 , scale_y=0.7)
        
        fila = 7        
        dato = self.pool.get('account.move').browse(cr, uid, id_move)
        #print  "Dato", dato
        sheet.write(2, 7, dato.no_comp, get_style(height=8, border=True))
        sheet.write(3, 7, dato.date, get_style(height=8, border=True))
        sheet.write(2, 10, dato.name, get_style(height=8, border=True))
        sheet.write(3, 10, dato.journal_id.name, get_style(height=8, border=True))
        sheet.write(4, 10, dato.tipo_comprobante, get_style(height=8, border=True))
        sheet.write(2, 13, dato.ref, get_style(height=8, border=True))
        sheet.write(3, 13, dato.period_id.name, get_style(height=8, border=True))
        total_sin_impuesto = 0.0
        total_impuesto = 0.0
        
        for line in dato.line_id:
            sheet.write(fila, 0, line.ref or '', get_style(height=8))
            sheet.write(fila, 1, '', get_style(height=8))
            sheet.write(fila, 2, line.name or '', get_style(height=8))
            sheet.write(fila, 3, line.partner_id.name or '', get_style(height=8))
            sheet.write(fila, 4, line.account_id.code + line.account_id.name, get_style(height=8))
            sheet.write(fila, 5, line.date_maturity or '', get_style(height=8))
            total_sin_impuesto += line.debit
            sheet.write(fila, 6, line.debit , get_style(height=8, align='left'))
            total_impuesto += line.credit
            sheet.write(fila, 7, line.credit, get_style(height=8, align='left'))
#             sheet.write(fila, 8, line.preproject_id.name or '' , get_style(height=8))
            sheet.write(fila, 9, line.analytic_account_id.name or '' , get_style(height=8))
            sheet.write(fila, 10, line.journal_id.name or '' , get_style(height=8))
#             sheet.write(fila, 11, line.employee_id.name or '' , get_style(height=8))
#             sheet.write(fila, 12, line.type_hr or '', get_style(height=8))
            sheet.write(fila, 13, line.period_id.name or '', get_style(height=8))
#             sheet.write(fila, 14, line.funds_certificate_id.name or '', get_style(height=8))
            sheet.write(fila, 15, line.tax_code_id.name or '' , get_style(height=8))
            sheet.write(fila, 16, line.tax_amount or '', get_style(height=8))
            sheet.write(fila, 17, line.state, get_style(height=8))
            sheet.write(fila, 18, line.reconcile_id.name or '', get_style(height=8))
            sheet.write(fila, 19, line.reconcile_partial_id.name or '', get_style(height=8))
                     
            fila += 1
       
        sheet.write(fila, 6, total_sin_impuesto, get_style(height=8, bold=True,))
        sheet.write(fila, 7, total_impuesto, get_style(height=8, bold=True,))     
        self.generate_report2(cr, uid, dato, sheet_res, context)    
            
            # Save the workbook
        buf = cStringIO.StringIO()
        book.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return {'file': out, 'file_name': 'detalle_asiento.xls'}
    
    
    def generate_report2(self, cr, uid, dato, hoja2, context):
        
        # query = """select sum(aml.debit) as debit, sum(aml.credit) as credit, aa.name as cuenta,aa.code, 
        # d.name as dep
        # from account_move_line aml, account_account aa, hr_employee e, hr_department d
        # where aml.move_id = %s
        # and aml.account_id = aa.id
        # and aml.employee_id = e.id
        # and e.department_id = d.id
        # group by d.name, aa.name, aa.code
        # order by d.name, debit desc""" % (dato.id)
        

        query = """select aaa.name as dep, sum(aml.debit) as debit, sum(aml.credit) as credit, aa1.name as cuenta, aa1.code as code 
        from account_move_line aml, account_account aa1, account_analytic_account aaa
        where
        aml.analytic_account_id = aaa.id 
        and aml.account_id = aa1.id
        and aml.move_id = %s
        group by aaa.id,aaa.name,aa1.name, aa1.code
        union all
        (select 'no tiene' as dep,sum(aml.debit) as debit, sum(aml.credit) as credit, aa.name as cuenta, aa.code as code
        from account_move_line aml, account_account aa
        where aml.account_id = aa.id
        and aml.move_id = %s 
        and aml.analytic_account_id is null
        group by aa.name, aa.code
        )
        order by dep,code""" % (dato.id, dato.id)
        
        

        cr.execute(query)
        
        res_agrupados_dep = cr.dictfetchall()
        
        fila = 7
        debit = 0.0
        credit = 0.0
        
        hoja2.write(2, 3, dato.no_comp, get_style(height=8, border=True))
        hoja2.write(3, 3, dato.date, get_style(height=8, border=True))
        hoja2.write(2, 6, dato.name, get_style(height=8, border=True))
        hoja2.write(3, 6, dato.journal_id.name, get_style(height=8, border=True))
        hoja2.write(4, 6, dato.tipo_comprobante, get_style(height=8, border=True))
        hoja2.write(2, 9, dato.ref, get_style(height=8, border=True))
        hoja2.write(3, 9, dato.period_id.name, get_style(height=8, border=True))
        
        for res_agrupado in res_agrupados_dep:
            
            
            debit += res_agrupado['debit']
            credit += res_agrupado['credit']
                         
            hoja2.write(fila, 1, res_agrupado['code'] or '', get_style(height=8))
            hoja2.write(fila, 2, res_agrupado['cuenta'] or '', get_style(height=8))
            hoja2.write(fila, 3, res_agrupado['debit'] or '', get_style(height=8))
            hoja2.write(fila, 4, res_agrupado['credit'] or '', get_style(height=8))
            hoja2.write(fila, 5, res_agrupado['dep'] or '', get_style(height=8))
                     
            fila += 1
        
        
        hoja2.write(fila, 3, debit, get_style(height=8, border=True))
        hoja2.write(fila, 4, credit, get_style(height=8, border=True))
    
    
    
    def view_init(self, cr, uid, fields, context):
        id_move = context.get('active_id', None)
        if not id_move:
            raise osv.except_osv('Error', 'Registro no encontrado')
        vals = self.generate_report(cr, uid, id_move, context)
        vals2 = {}
        for key, value in vals.iteritems():
            vals2['default_' + key] = value
        context.update(vals2)
        
    _columns = {
                'file': fields.binary(string='Archivo Excel', help='Nombre del fichero de reporte a generar'),
                'file_name': fields.char('Nombre', size=60),
                }
    
pay_order()
