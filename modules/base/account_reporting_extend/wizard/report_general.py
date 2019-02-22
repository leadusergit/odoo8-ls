# -*- encoding: utf-8 -*-
##############################################################################
#
#    Balance General
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

import xlwt as pycel
import time



class report_general():
    
    
    style_cabecera = None
    
    style_cuenta = None
    
    style_cuarto_nivel = None
    
    style_header = None
    
    style_firma = None
   
    align = None
    
    font2 = None
    
    style2 = None

    font3 = None
    
    style3 = None
    
    wb = None
    
    pool = None
   
    
    def __init__(self):
        
        self.style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                    'align: vertical center, horizontal center;'
                                    )
    
        self.style_cuenta = pycel.easyxf('font: colour black;'
                                   'align: vertical center, horizontal left;'
                                   )
        
        self.style_cuarto_nivel = pycel.easyxf('font: colour black, bold True;'
                                   'align: vertical center, horizontal left;'
                                   )
        
        self.style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')
        
        self.style_firma = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 0, right 0, top 1, bottom 0;')
             
        self.align = pycel.Alignment()
        self.align.horz = pycel.Alignment.HORZ_RIGHT  
        self.align.vert = pycel.Alignment.VERT_CENTER
        
        self.font2 = pycel.Font()
        self.font2.bold = True
        self.font2.colour_index = 0x0
        
        self.style2 = pycel.XFStyle()
        self.style2.num_format_str = '#,##0.00'
        self.style2.alignment = self.align
        self.style2.font = self.font2
        
        self.font3 = pycel.Font()
        self.font3.bold = False
        self.font3.colour_index = 0x0
        
        self.style3 = pycel.XFStyle()
        self.style3.num_format_str = '#,##0.00'
        self.style3.alignment = self.align
        self.style3.font = self.font3
        
    

    def get_cabecera_libro_mayor(self, cr, uid, wb, form, ws, write_fields=True):
        
        #ws = wb.add_sheet("LIBRO MAYOR")
        #ws.show_grid = False
        #ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        #ws.footer_str = u""
        
        #Version 6
        company_id = self.pool.get('res.users').read(cr, uid, uid, ['company_id'])['company_id'][0]
#         compania_ids = self.pool.get('res.company').search(cr, uid, [('name', 'ilike', 'EMPRESA PROVINCIAL DE VIVIENDA%')])
        #print ' compania_ids ', compania_ids
        compania = self.pool.get('res.company').browse(cr, uid, company_id)
        
        x0 = 3
#        sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)        
        ws.write_merge(1, 1, 1, x0, compania.name, self.style_cabecera)
        ws.write_merge(2, 2, 1, x0, 'Direccion: ' + compania.rml_header1, self.style_cabecera)
        ws.write_merge(3, 3, 1, x0, 'Ruc: ' + compania.rml_footer1, self.style_cabecera)
        ws.write_merge(5, 5, 1, x0, 'LIBRO MAYOR', self.style_cabecera)
        
        ws.fit_num_pages = 1
        ws.fit_height_to_pages = 0
        ws.fit_width_to_pages = 1
        
        ws.write(7, 1, time.strftime('%d de %B del %Y').upper(), self.style_cabecera)
        
        
        if form['filter'] == 'filter_date':
            ws.write(8, 1, "FECHA INICIO", self.style_cuarto_nivel)
            ws.write(8, 2, form['date_start'], self.style_cuenta)
            ws.write(8, 3, "FECHA DESDE", self.style_cuarto_nivel)
            ws.write(8, 4, form['date_from'], self.style_cuenta)
            ws.write(8, 5, "FECHA HASTA", self.style_cuarto_nivel)
            ws.write(8, 6, form['date_to'], self.style_cuenta)
            
        
        ws.write(9, 1, "FECHA", self.style_header)
        ws.write(9, 2, "DIARIO", self.style_header)
        if write_fields:
            ws.write(9, 3, "NO. COMPO", self.style_header)
            ws.write(9, 4, "TIPO COMP.", self.style_header)
            ws.write(9, 5, "REFERENCIA", self.style_header)
            ws.write(9, 6, "NO CHEQUE", self.style_header)
            ws.write(9, 7, "CÉDULA", self.style_header)
            ws.write(9, 8, "COMPANIA", self.style_header)
            ws.write(9, 9, "EMPLEADO", self.style_header)
            ws.write(9, 10, "PROYECTO", self.style_header)
            ws.write(9, 11, "COD. IMPUESTO", self.style_header)
            ws.write(9, 12, "DETALLE", self.style_header)
            ws.write(9, 13, "DEBITO", self.style_header)
            ws.write(9, 14, "CREDITO", self.style_header)
            ws.write(9, 15, "SALDO FINAL", self.style_header)
        
        #return ws
    
