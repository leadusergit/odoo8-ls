# -*- encoding: utf-8 -*-
##############################################################################
#
#    Tax reporte
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
#creador  *Vll

from openerp.osv import fields, osv
import time
import xlwt as pycel
import cStringIO
import base64
import datetime
import openerp.tools
import re


class wizard_report_tax(osv.osv_memory):
    
    _name = "wizard.report.tax"
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    
    def generate_report(self, cr, uid, ids, context=None):
        
        
        #print ' ids ', ids
        
        
        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                        'align: vertical center, horizontal center;'
                                        )
        
        linea = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center;'
                                    'borders:bottom 1;')
        
        wb = pycel.Workbook(encoding='utf-8')
        ws = wb.add_sheet("Estado Cliente")
        ws.show_grid = False
        
        
        
        
        j = 5
        i = j + 1
        
        for active_id in context['active_ids']:

            obj_header = self.pool.get('account.tax.header').browse(cr, uid, active_id)
            for tax in obj_header.tax_ids:
                if i != 6:
                    j = i + 2
                    i = j + 1
                        
                ws.write(j, 1, tax.name, style_cabecera)
                ws.write(j, 2, 'FECHA', style_cabecera)
                ws.write(j, 3, 'DOCUMENTO', style_cabecera)
                ws.write(j, 4, 'NOMBRE', style_cabecera)
                ws.write(j, 5, 'RUC', style_cabecera)
                ws.write(j, 6, 'BASE IMPONIBLE', style_cabecera)
                ws.write(j, 7, 'VALOR', style_cabecera)
                
                for line in tax.lineas_ids:
                        
                    ws.write(i, 2, line.fecha, linea)
                    ws.write(i, 3, line.documento, linea)
                    ws.write(i, 4, line.nombre, linea)
                    ws.write(i, 5, line.ruc, linea)
                    ws.write(i, 6, line.b_imponible, linea)
                    ws.write(i, 7, line.valor, linea)
                    i+=1
                
                
        buf = cStringIO.StringIO()
        
        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'data':out, 'name':'reporte_impuestos.xls'})

    _columns = {
                
            'data': fields.binary(string='Archivo'),
            'name':fields.char('Nombre', size=60),
    }                          
                                                                            

wizard_report_tax()
