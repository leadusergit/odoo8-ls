# -*- encoding: utf-8 -*-
##############################################################################
#
#    Formulario Ciento Uno
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


"""
Muestra el wizard del año y el periodo para generar este reporte
"""

class wizard_report_ciento_uno(osv.osv_memory):
    
    _name = "wizard.report.ciento.uno"
    
    def onchange_fiscalyear_id(self, cr, uid, ids, fiscalyear_id):
        res = {'value': {}}
        if fiscalyear_id:
            period_pool = self.pool.get('account.period')
            res['value']['periods'] = period_pool.search(cr, uid, [('fiscalyear_id', '=', fiscalyear_id),
                                                                   ('special', '=', False),
                                                                   ('date_stop', '<=', time.strftime('%Y-%m-%d'))])
        return res
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    def fill_data(self, cr, uid, ids, context=None):

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                        'align: vertical center, horizontal center;'
                                     )
        
        style_cuenta = pycel.easyxf('font: colour black;'
                                   'align: vertical center, horizontal left;'
                                   )
        
        style_cuarto_nivel = pycel.easyxf('font: colour black, bold True;'
                                   'align: vertical center, horizontal left;'
                                   )
        
        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')
        
        style_firma = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 0, right 0, top 1, bottom 0;')
        
        
        align = pycel.Alignment()
        align.horz = pycel.Alignment.HORZ_RIGHT  
        align.vert = pycel.Alignment.VERT_CENTER
        
        font2 = pycel.Font()
        font2.bold = True
        font2.colour_index = 0x0
        
        style2 = pycel.XFStyle()
        style2.num_format_str = '#,##0.00'
        style2.alignment = align
        style2.font = font2
        
    
        font3 = pycel.Font()
        font3.bold = False
        font3.colour_index = 0x0
        
        style3 = pycel.XFStyle()
        style3.num_format_str = '#,##0.00'
        style3.alignment = align
        style3.font = font3
        
        wb = pycel.Workbook(encoding='utf-8')
        ws = wb.add_sheet("FORMULARIO 101")
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u"" 
        #Version 5
        #compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        
        #Version 6
        form = self.browse(cr, uid, ids)[0]
        compania = form.company_id
        
        x0 = 3
#        sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)        
        ws.write_merge(1, 1, 1, x0, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, x0, compania.rml_header1, style_cabecera)
        ws.write_merge(3, 3, 1, x0, u'Dirección: ' + compania.street, style_cabecera)
        ws.write_merge(5, 5, 1, x0, 'BALANCE GENERAL', style_cabecera)
        ws.fit_num_pages = 1
        ws.fit_height_to_pages = 0
        ws.fit_width_to_pages = 1
        ws.write(7, 1, time.strftime('%d de %B del %Y').upper(), style_cabecera)
        
        periodos = form.periods
        anio_fiscal = form.fiscalyear_id

        ctx = context
        anio_fiscal_id = anio_fiscal.id
        ctx['fiscalyear'] = anio_fiscal_id
        ctx['balance'] = True
        
        ws.write(9,0,"CASILLERO",style_header)
        ws.write(9, 1, "CUENTA",style_header)
        ws.write(9, 2, "NOMBRE DE LA CUENTA",style_header)
        ws.write_merge(9, 9,3,4, "TOTAL",style_header)
        ws.write_merge(9,9,5,6, "TOTAL CASILLERO",style_header)
        
        account_account_obj = self.pool.get('account.account')
        
        #Balance General        
        query = "select casillero, id \
        from account_account \
        where casillero is not null \
        group by casillero, id \
        order by casillero"
        
        cr.execute(query)
        account_ids = [x[1] for x in cr.fetchall()]
        account_objs = account_account_obj.browse(cr, uid, account_ids, ctx)
        y = 10
        
        res = dict((aux.casillero, round(sum([o.balance for o in account_objs if o.casillero==aux.casillero]), 2)) for aux in account_objs)
        for account in account_objs:
            name = ''
            name = account.name
            name = name.encode('UTF-8')
            
            y += 1
            
            if len(account.code) <= 8:
                
                ws.write(y, 0, account.casillero, style_cuenta)
                ws.write(y, 1, account.code, style_cuenta)
                ws.write(y, 2, name, style_cuenta)
                if len(account.code) == 7:
                    ws.write_merge(y,y, 3,4, round(account.balance, 2), style3)
                    ws.write(y,5,res.get(account.casillero) and res.pop(account.casillero) or '')
                                              
            else:
                ws.write(y, 0, account.casillero, style_cuenta)
                ws.write(y, 1, account.code, style_cuenta)
                ws.write(y, 2, name.title(), style_cuenta)
        	ws.write_merge(y,y, 3,4, round(account.balance, 2), style3)
        	ws.write(y,5,res.get(account.casillero) and res.pop(account.casillero) or '')
        
        y += 4
        ws.write(y, 2, 'GERENTE GENERAL', style_firma)
        ws.write_merge(y, y, 4, 5, 'CONTADOR GENERAL', style_firma)
                  
        ws.col(2).width = 7500
        ws.col(2).width = 10500
        buf = cStringIO.StringIO()
        
        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        self.write(cr, uid, ids, {'data':out, 'name':'ciento_uno.xls', 'state':'res'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Archivo generado',
            'res_model': 'wizard.report.ciento.uno',
            'res_id': ids[0],
            'view_mode': 'form',
            'target': 'new'
        }
        

    _columns = {
        'company_id': fields.many2one('res.company', 'Compañia', required=True),
        'fiscalyear_id':fields.many2one('account.fiscalyear', 'Anio Fiscal'),
        'periods':fields.many2many('account.period',
                                 'account_period_report_rel',
                                 'acp_id',
                                 'wrep_id', 'Periodos:'),
        'data': fields.binary(string='Archivo', readonly=True),
        'name':fields.char('Nombre', size=60, readonly=True),
        'state':fields.selection([('ini', 'Inicial'),
                                   ('res', 'Resultado'),
                                  ], 'Estado'),
    }
    
    def default_company(self, cr, uid, context=None):
        print context
        res = self.pool.get('res.company').search(cr, uid, [])
        return bool(res) and res[0]
        
    _defaults = {
       'state': lambda * a: 'ini',
       'company_id': default_company
    }
        
wizard_report_ciento_uno()   
