# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
import time
import xlwt as pycel
import cStringIO
import base64
import datetime
# import netsvc
from openerp import tools
import re

class wizard_report_concilation(osv.osv_memory):
    _name = "wizard.report.concilation"
    _description = "Conciliation Reporte"
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def unchecked(self, cr, uid, periodo, journal):
        res = []
        concilacion = self.pool.get('account.conciliation')
        concilacion_line = self.pool.get('account.conciliation.line')
        
        ids = concilacion.search(cr, uid, [('journal_id','=',journal),
                                           ('period_id','=',periodo),
                                           ('state','=','confirm')])
        if ids:
            no_conciliados = concilacion_line.search(cr,uid,[('conciliation_id','in',[ids[0]]),
                                                             ('conciliado','=',False)], order='date')
            if no_conciliados:
                for item in concilacion_line.browse(cr, uid, no_conciliados):
                    res.append(item.id)
        return res
    
    def checked(self, cr, uid, periodo, journal):
        res = []
        concilacion = self.pool.get('account.conciliation')
        concilacion_line = self.pool.get('account.conciliation.line')
        
        ids = concilacion.search(cr, uid, [('journal_id','=',journal),
                                           ('period_id','=',periodo),
                                           ('state','=','confirm')])
        if ids:
            no_conciliados = concilacion_line.search(cr,uid,[('conciliation_id','in',[ids[0]]),
                                                             ('conciliado','=',True)], order='date')
            if no_conciliados:
                for item in concilacion_line.browse(cr, uid, no_conciliados):
                    res.append(item.id)
        return res
    
    def _bank_conciliation(self, cr, uid, form):
        res = []
        periodo = form.get('period_id', False)
        journal = form.get('journal_id', False)
        sql = "select id from account_conciliation where state='confirm' "
        if periodo and journal:
             where = " and period_id="+str(periodo)+" and journal_id="+str(journal)
        elif periodo and not journal:
            where = " and period_id="+str(periodo)
        elif journal and not periodo:
            where = " and journal_id="+str(periodo)
        else:
            where = ""
        order = ' order by journal_id'
        cr.execute(sql+where + order)
        
        res = [aux[0] for aux in cr.fetchall()]
        
        return res
    
    def action_excel(self, cr, uid, ids, context=None):
        wb = pycel.Workbook(encoding='utf-8')
        if context is None:
            context = {}
        data = {}
        data['form'] = self.read(cr, uid, ids)[0]
        form = data['form']
        
        periodo = form.get('period_id')
        journal = form.get('journal_id')
        
        type = form.get('type')
        
        #Formato de la Hoja de Excel
        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                        'align: vertical center, horizontal center;'
                                        )
            
        style_cabecerader = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal right;'
                                    )
        
        style_cabeceraizq = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal left;'
                                    )
        
        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center;'
                                    'borders: left 1, right 1, top 1, bottom 1;')
        
        linea = pycel.easyxf('borders:bottom 1;')
        
        linea_center = pycel.easyxf('font: colour black;'
                                   'align: vertical center, horizontal center;'
                                   )
        
        linea_izq = pycel.easyxf('font: colour black;'
                                   'align: vertical center, horizontal left;'
                                   )
        linea_der = pycel.easyxf('font: colour black;'
                                 'align: vertical center, horizontal right;'
                                  )
        
        ws = wb.add_sheet("Concilacion Bancaria")
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u"" 
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        ##print 'compania', compania
        x0=25
        #sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)
        ws.write_merge(1,1,1,x0,compania.name, style_cabecera)
        ws.write_merge(2,2,1,x0,'Direccion: '+compania.partner_id.street, style_cabecera)
        ws.write_merge(3,3,1,x0,'Ruc: '+compania.partner_id.ident_num, style_cabecera)
        if form.get('type',False)=='uncheck':
            ws.write_merge(4,4,1,x0,'COMPROBANTES NO CONCILIADOS', style_cabecera)
        elif form.get('type',False)=='check':
            ws.write_merge(4,4,1,x0,'COMPROBANTES CONCILIADOS', style_cabecera)
        
        
        x1=6 #Fechas
        
        ws.write_merge(x1,x1,1,4, 'Hora:', style_cabecerader)
        ws.write_merge(x1,x1,5,10, time.strftime('%H:%M:%S'), style_cabeceraizq)

        ws.fit_num_pages = 1
        ws.fit_height_to_pages = 0
        ws.fit_width_to_pages = 1
        #ws.paper_size_code = 1
        ws.portrait = 1
        
        align = pycel.Alignment()
        align.horz = pycel.Alignment.HORZ_RIGHT  
        align.vert = pycel.Alignment.VERT_CENTER
        
        font1 = pycel.Font()
        font1.colour_index = 0x0
        
        #Formato de Numero
        style = pycel.XFStyle()
        style.num_format_str = '#,##0.00'
        style.alignment = align
        style.font = font1
        
        #Formato de Numero Saldo
        font = pycel.Font()
        font.bold = True
        font.colour_index = 0x27
        
        style1 = pycel.XFStyle()
        style1.num_format_str = '#,##0.00'
        style1.alignment = align
        style1.font = font
        
        
        font2 = pycel.Font()
        font2.bold = True
        font2.colour_index = 0x0
        
        style2 = pycel.XFStyle()
        style2.num_format_str = '#,##0.00'
        style2.alignment = align
        style2.font = font2
        
        style3 = pycel.XFStyle()
        style3.num_format_str = '0'
        style3.alignment = align
        style3.font = font1
        
        
        xi = 8 # 
        x = 12 # 
        xm = 8 #Movimientos
        tipo_move = ''
        cabecera = self._bank_conciliation(cr, uid, form)
        for cab in self.pool.get('account.conciliation').browse(cr,uid, cabecera):
            lines_ids = []
            if type == 'cheked':
                lines_ids = self.checked(cr, uid, cab.period_id.id, cab.journal_id.id)
                if not lines_ids:
                    continue
            
            else:
                lines_ids = self.unchecked(cr, uid, cab.period_id.id, cab.journal_id.id)
                if not lines_ids:
                    continue
            if lines_ids:
                ws.write_merge(xm,xm,1,5,'Concilacion Bancaria:', linea_der)
                ws.write_merge(xm,xm,6,15,cab.journal_id.default_credit_account_id.code,linea_izq )
                ws.write_merge(xm,xm,16,20,cab.journal_id.default_credit_account_id.name, linea_izq)
                xm+=1
                ws.write_merge(xm,xm,1,5,'DEL MES:', linea_der)
                ws.write_merge(xm,xm,6,15,str(time.strftime('%B del %Y', time.strptime(cab.period_id.date_start, '%Y-%m-%d'))).upper(), linea_izq)
                xm+=1
                ws.write_merge(xm,xm,1,3,'Fecha', style_header)
                ws.write_merge(xm,xm,4,5,'DOCUM', style_header)
                ws.write_merge(xm,xm,6,8,'T Mov', style_header)
                ws.write_merge(xm,xm,9,11,'No Cheque', style_header)
                ws.write_merge(xm,xm,12,20,'Beneficiario', style_header)
                ws.write_merge(xm,xm,21,25,'Detalle', style_header)
                ws.write_merge(xm,xm,26,27,'Valor', style_header)
                xm+=1
                ws.write_merge(xm,xm,20,25,'Saldo Segun Libros', style_cabecerader)
                ws.write_merge(xm,xm,26,27, round(cab.balance_journal,2), style_cabecerader)

            
            xm += 1
            for item in self.pool.get('account.conciliation.line').browse(cr, uid, lines_ids):
                
                if item.aml_id:
                    ws.write_merge(xm,xm,1,3,item.aml_id.date, linea_center)
                    ws.write_merge(xm,xm,4,5,item.aml_id.move_id.no_comp, linea_center)
                    if item.aml_id.credit:
                        tipo_move = 'EG'
                        monto = -item.aml_id.credit
                    if item.aml_id.debit:
                        tipo_move = 'IN'
                        monto = item.aml_id.debit
                    ws.write_merge(xm,xm,6,8,tipo_move, linea_center)
                    ws.write_merge(xm,xm,9,11,item.aml_id.type_move or '', linea_center)
                    ws.write_merge(xm,xm,12,20,item.aml_id.partner_id and item.aml_id.partner_id.name or '', linea_izq)
                    ws.write_merge(xm,xm,21, 25,item.aml_id.ref or item.aml_id.name, linea_izq)
                    ws.write_merge(xm,xm,26, 27,monto, style)
                    xm += 1
                elif item.moves:
                    for x in item.moves:
                        ws.write_merge(xm,xm,1,3,x.date, linea_center)
                        ws.write_merge(xm,xm,4,5,x.move_id.no_comp, linea_center)
                        if x.credit:
                            tipo_move = 'EG'
                            monto = -x.credit
                        if x.debit:
                            tipo_move = 'IN'
                            monto = x.debit
                        ws.write_merge(xm,xm,6,8,tipo_move, linea_center)
                        ws.write_merge(xm,xm,9,11,x.type_move or '', linea_center)
                        ws.write_merge(xm,xm,12,20,x.partner_id and x.partner_id.name or '', linea_izq)
                        ws.write_merge(xm,xm,21, 25,x.ref or x.name, linea_izq)
                        ws.write_merge(xm,xm,26, 27,monto, style)
                        xm += 1
                        
            ws.write_merge(xm,xm,20,25,'SALDO SEGUN BANCOS:', style_cabecerader)
            ws.write_merge(xm,xm,26,27, round(cab.balance_end_real,2), style_cabecerader)
                
            xm += 2
                
        w = 500
        y = 1000
        w0 = 2000
        w1 = 3000
        w2 = 1500
        
        ws.col(0).width = w #A
        #Fecha
        ws.col(1).width = w0 #B
        ws.col(2).width = w0 #C
        ws.col(3).width = y #D
        #Documento
        ws.col(4).width = w0 #E
        ws.col(5).width = y #F
        
        #Tipo
        ws.col(6).width = w #G
        ws.col(7).width = 1000 #H
        ws.col(8).width = 1000 #I
        
        #Cheque
        ws.col(9).width = w0 #J
        ws.col(10).width = y #K
        ws.col(11).width = w #L
        
        #Partner
        ws.col(12).width = w1 #M
        ws.col(13).width = w1 #N
        ws.col(14).width = w #O 
        ws.col(15).width = w #P
        ws.col(16).width = w #Q
        ws.col(17).width = w #R
        ws.col(18).width = w #S
        ws.col(19).width = w1 #T
        ws.col(20).width = w1 #U
        
        #Ref
        ws.col(21).width = 1000 #V
        ws.col(22).width = 1000 #W
        ws.col(23).width = 1000 #X
        ws.col(24).width = 1000 #Y
        ws.col(25).width = 1000 #Z
        
        #Valor
        ws.col(26).width = w0
        ws.col(27).width = w0
        
        
        ws.col(28).width = 1000
        ws.col(29).width = 1000
        ws.col(30).width = 1000
        ws.col(31).width = 1000
        ws.col(32).width = 1000
        ws.col(33).width = 1000
        ws.col(34).width = 1000
        ws.col(35).width = 1000
        ws.col(36).width = 1000
        ws.col(37).width = w
        ws.col(38).width = w
        ws.col(39).width = w
        ws.col(40).width = w                
        buf= cStringIO.StringIO()
        
        wb.save(buf)
        out=base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'data':out, 'name':'concilacion.xls'})
    
    def _get_period(self, cr, uid,context):
        period_ids= self.pool.get('account.period').search(cr,uid,[('date_start','<=', time.strftime('%Y-%m-%d')),
                                                                   ('date_stop','>=',time.strftime('%Y-%m-%d'))])
        if period_ids:
            return period_ids[0]

        
    _columns={
              'type':fields.selection([('check','Conciliados'),
                                       ('uncheck','No Conciliados'),
                                       ], 'Tipo'),
              'period_id':fields.many2one('account.period', 'Periodo', domain=[('state','=','draft')]),
              'journal_id':fields.many2one('account.journal', 'Banco', domain=[('type','=','cash')]),
              
              'data': fields.binary(string='Archivo'),
              'name':fields.char('Nombre', size=60),
    }
    _defaults = {
        'type': lambda *a: 'check',
        'period_id':_get_period
    }

wizard_report_concilation()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: