# -*- coding: utf-8 -*-
##############################################################################
#
#    Atikasoft Cia. Ltda
#    Copyright (C) 2004-2009 
#    $Id$
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

__author__ = 'edison.guachamin@atikasoft.com.ec (Edison G.)'

import cStringIO
import base64
import StringIO
import csv
import time
from openerp.osv import fields, osv
import mx.DateTime
from mx.DateTime import RelativeDateTime
import openerp.tools
import datetime
import xlwt as pycel #Libreria que Exporta a Excel
from openerp.tools import config
bancos = []

class wizard_report_incomes(osv.osv_memory):
    _name = "wizard.report.incomes"
    _description = 'Reporte de Ingresos de Clientes'
    
    def _get_name(self, cr, uid, diario):
        account_journal_obj = self.pool.get('account.journal')
        name = ''
        cuenta = ''
        if diario == 'Diario B.Guayaquil':
            name = 'Banco Guayaquil'
            cuenta = '5805929'
        elif diario == "Diario B.Guayaquil 28976186":
            name = 'Banco Guayaquil'
            cuenta = '28976186'
            
        elif diario == "Diario B.Internacional":
            name = 'Banco Internacional'
            cuenta = '0700075355'
        
        elif diario == "Diario B.Pacifico":
            name = 'Banco Pacifico'
            cuenta = '5163331'
        
        elif diario == "Diario B.Pichincha":
            name = 'Banco Pichincha'
            cuenta = '3016897104'
            
        elif diario == "Diario B.Produbanco":
            name = 'Banco Produbanco'
            cuenta = '02005016130'
        return name +' / '+  cuenta + ' '
            
    
    def _get_period(self, cr, uid, ids, context=None):
        return self.pool.get('account.period').find(cr, uid)[0]
    
    def _get_journals(self, cr, uid, ids, context=None):
        sql = 'select id from account_account where parent_id=1219'
        cr.execute(sql)
        account_ids = [aux[0] for aux in cr.fetchall()]
        if account_ids:
            sql = "select id from account_journal where default_credit_account_id in ("+','.join([str(x) for x in account_ids])+")"
            cr.execute(sql)
            journal_ids = [aux[0] for aux in cr.fetchall()]
            if journal_ids:
                bancos=journal_ids
                return journal_ids
        
    def _format_date(self, date):
        if date:
            campos = date.split('-')
            date = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date
    
    def _order_moves(self, cr, uid, dict_move):
        ##print '_order_moves', dict_move
        res = []
        moves = [x['id'] for x in dict_move]
        sql = "select id from account_move_line where id in("+','.join([str(i) for i in moves])+") order by date"
        cr.execute(sql)
        res = [y[0] for y in cr.fetchall()]
        #print 'movimientos', res
        return res
    
    def _get_detalle(self, cr, uid, move_pay_info):
        account_bank_statement_obj = self.pool.get('account.bank.statement')
        detalle = ''
        statement = move_pay_info['statement_id']
        'Banco: Bolivariano GR: Corporacion Mucho Mejor Ecuador Cta: 4005014033 No CH: 2365'
        if statement:
            statment_info = account_bank_statement_obj.browse(cr, uid, statement[0])
            if len(statment_info.bank_deposits) == 1:
                banco, grupo, cuenta, cheque, monto, detalle = '','','','','',''
                for li in statment_info.bank_deposits:#Cheques
                    if li.partner_id.id == move_pay_info['partner_id'][0]:
                        if li.bank:
                            banco = 'Banco:' + tools.ustr(li.bank)
                        if li.partner_id:
                            grupo = ' GR:' + tools.ustr(li.partner_id.name)
                        if li.account:
                            cuenta = ' Cta:' + tools.ustr(li.account)
                        if li.number:
                            cheque = ' No CH:' + tools.ustr(li.number)
                        if li.amount:
                            monto = ' Monto:' +str(li.amount)
                detalle = banco + grupo + cuenta + cheque + monto
            elif len(statment_info.bank_deposits) > 1:
                banco, grupo, cuenta, cheque, monto, detalle = '','','','',''
                for li in statment_info.bank_deposits:
                    if li.partner_id.id == move_pay_info['partner_id'][0]:
                        #and self._format_date(li.date_income)>= self._format_date(date_from) and \
                        #self._format_date(move_pay_info['date']) <= self._format_date(date_to):
                        if li.bank:
                            banco = 'Banco:' + tools.ustr(li.bank)
                        if li.partner_id:
                            grupo = ' GR:' + tools.ustr(li.partner_id.name)
                        if li.account:
                            cuenta = ' Cta:' + tools.ustr(li.account)
                        if li.number and statment_info.payments =='depo':
                            cheque = ' No CH:' + tools.ustr(li.number)
                        elif li.number and statment_info.payments =='trans':
                            cheque = ' No Transferencia:' + tools.ustr(li.number)
                        if li.amount:
                            monto = ' Monto:' +str(li.amount)
                detalle = banco + grupo + cuenta + cheque + monto
                            
            elif len(statment_info.bank_deposits) == 0 and statment_info.has_deposit:
                #if self._format_date(statment_info.date_deposit)>= self._format_date(date_from) and \
                    #self._format_date(statment_info.date_deposit) <= self._format_date(date_to):
                banco, grupo, tipo, cheque, monto, date, detalle = '','','','','','',''
                
                banco = self._get_name(cr, uid, move_pay_info['journal_id'][1])
                grupo = ' GR:' + tools.ustr(move_pay_info['partner_id'][1])
                tipo = statment_info.payments == 'trans' and 'Transferencia' or \
                       statment_info.payments == 'depo' and 'Deposito'
                cheque = ' No Comprobante:' + str(statment_info.num_deposit)
                if statment_info.amount_deposit:
                    monto = ' Monto:' + str(statment_info.amount_deposit)
                date = ' Fecha:' +str (statment_info.date_deposit)
                
                detalle = banco + grupo + cheque + monto + date    
        
        return detalle
    
    
    def _get_lines(self, cr, uid, form):
        result = []
        account_invoice_obj = self.pool.get('account.invoice')
        account_move_line_obj = self.pool.get('account.move.line')
        account_period_obj = self.pool.get('account.period')
        
        
        date_now = time.strftime('%Y-%m-%d')
        
        sql = "select * from account_invoice where state in ('open','paid') and type='out_invoice'"
        where = (" and date_invoice between '%s' and '%s' ") % (form.get('date_start'), date_now)
        ##print 'whgere', where
        cr.execute(sql + where)
        invoices = [x[0] for x in cr.fetchall()]
        ##print 'invoices', invoices
        if invoices:
            for item in invoices:
                ##print 'entra', item
                invoice_info = account_invoice_obj.read(cr, uid, item, ['payment_ids'])
                if form.get('filter')=='by_date':
                    date_from  = form.get('date_from')
                    date_to = form.get('date_to')
                else:
                    period_info = account_period_obj.read(cr, uid, form.get('period_id'), ['date_start', 'date_stop']) 
                    date_from  = period_info.get('date_start')
                    date_to = period_info.get('date_stop')
                    
                if invoice_info['payment_ids']:
                    for pay in invoice_info['payment_ids']:
                        
                        move_pay_info = account_move_line_obj.read(cr, uid, pay,['date','id','type_move','journal_id'])
                        
                        if move_pay_info['type_move'] == 'ANU':
                            continue
                        
                        if self._format_date(move_pay_info['date']) >= self._format_date(date_from) \
                            and self._format_date(move_pay_info['date']) <= self._format_date(date_to):
                            val = {}
                            
                            if move_pay_info['journal_id'][1] == 'Diario de Retenciones':
                                continue
                            if move_pay_info['journal_id'][0] in form.get('journal_ids'):
                                val['id'] = move_pay_info['id']
                                result.append(val)
                                        
        return result 
    
    def action_excel(self, cr, uid, ids, context=None):
        
        account_move_line_obj = self.pool.get('account.move.line')
        
        wb = pycel.Workbook(encoding='utf-8')
        if context is None:
            context = {}
        data = {}
        data['form'] = self.read(cr, uid, ids)[0]
        form = data['form']
        date_from = form.get('date_from')
        date_to = form.get('date_to')
        
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
        
        linea_center = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal center;'
                                   )
        
        linea_izq = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical top, horizontal left, wrap True;'
                                   )
        linea_der = pycel.easyxf('font: colour black, height 140;'
                                 'align: vertical center, horizontal right;'
                                  )
        
        ws = wb.add_sheet("Detalle de Ingresos")
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u"" 
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        ##print 'compania', compania
        x0=22
        #sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)
        ws.write_merge(1,1,1,x0,compania.name, style_cabecera)
        ws.write_merge(2,2,1,x0,'Direccion: '+compania.partner_id.street, style_cabecera)
        ws.write_merge(3,3,1,x0,'Ruc: '+compania.partner_id.ident_num, style_cabecera)
        ws.write_merge(4,4,1,x0,'REPORTE DETALLES DE INGRESOS', style_cabecera)
        
        
        x1=6 #Fechas
        ws.write_merge(x1,x1,1,3, 'Fecha Desde: '+date_to, style_cabeceraizq)
        ws.write_merge(x1,x1,4,8, 'Fecha Hasta: '+date_from, style_cabeceraizq)
        
        ws.write_merge(x1,x1,10,12, 'Hora:', style_cabecerader)
        ws.write_merge(x1,x1, 13,16, time.strftime('%H:%M:%S'), style_cabeceraizq)

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
        font1.height = 140
        
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
        
        x = 7
        ws.write(x,1,'Fecha', style_header)
        ws.write(x,2,'Tmov', style_header)
        ws.write(x,3,'Factura', style_header)
        ws.write_merge(x,x,4,8,'Cliente', style_header)
        ws.write(x,9,'F.Vence', style_header)
        ws.write_merge(x,x,10,15,'Detalle', style_header)
        ws.write_merge(x,x,16,18,'Debito', style_header)
        ws.write_merge(x,x,19,21,'Credito', style_header)
        
        xm = 8#Movimientos
            
        'Busco los Pagos'
        get_lines = self._get_lines(cr, uid, form)
        amount = 0.00
        if get_lines:
            'ORDENO LOS PAGOS'
            move_lines = self._order_moves(cr, uid, get_lines)
            
            for mov in move_lines:
                ##print 'mov', mov 
                moves = account_move_line_obj.read(cr, uid, mov, ['id', 'date','type_move','ref','partner_id',
                                                                  'statement_id','debit', 'credit','date_maturity', 'journal_id'])
                detalle = self._get_detalle(cr, uid, moves)
                ws.write(xm,1,moves['date'], linea_center)
                ws.write(xm,2,moves['type_move'] or 'IN', linea_center)
                ws.write(xm,3,moves['ref'], linea_center)
                ws.write_merge(xm,xm,4,8,tools.ustr(moves['partner_id'][1]), linea_izq)
                ws.write(xm,9,moves['date_maturity'] or '', linea_center)
                ws.write_merge(xm,xm,10,15,tools.ustr(detalle) or '', linea_izq)
                ws.write_merge(xm,xm,16,18,moves['debit'], style)
                ws.write_merge(xm,xm,19,21,moves['credit'], style)
                amount += moves['credit']
                xm += 1
        
        ws.write_merge(xm,xm,16,18,'TOTAL', style)
        ws.write_merge(xm,xm,19,21,amount, style)           
        
        w = 1300
        y = 1300
        y0 = 1500
        
        ws.col(0).width = y
        
        ws.col(1).width = 3000
        ws.col(2).width = 1500
        ws.col(3).width = 2000
        
        ws.col(4).width = y
        ws.col(5).width = y
        ws.col(6).width = y
        ws.col(7).width = y
        ws.col(8).width = y
        
        ws.col(9).width = 3000
        
        ws.col(10).width = 9000
        ws.col(11).width = y0
        ws.col(12).width = y0
        ws.col(13).width = y0
        ws.col(14).width = y0
        ws.col(15).width = y0
        
        ws.col(16).width = 500
        ws.col(17).width = 1000
        ws.col(18).width = 500
        
        ws.col(19).width = w
        ws.col(20).width = w
        ws.col(21).width = 100
        
        buf= cStringIO.StringIO()
        
        wb.save(buf)
        out=base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'data':out, 'name':'Ingresos.xls'})
     

    _columns = {
            'journal_ids':fields.many2many('account.journal','journal_line_rel', 'wizard_id', 'journal_id','Banco', domain=[('id','in',bancos)]),
            'date_start':fields.date('Fecha Inicio'),
            
            'date_from':fields.date('Fecha Desde'),
            
            'date_to':fields.date('Fecha Hasta'),
            'period_id':fields.many2one('account.period', 'Periodo'),
            'filter':fields.selection([('by_date','Fecha'),
                                       ('by_period','Periodo'),
                                      ], 'Filtrar por', required=True),
            'data': fields.binary(string='Archivo'),
            'name':fields.char('Nombre', size=60),
        }                            
                                                                              
    _defaults = {
        'date_from': lambda * a: time.strftime('%Y-%m-01'),
        'date_to': lambda * a: time.strftime('%Y-%m-%d'),
        'date_start': lambda * a: time.strftime('2011-07-01'),
        'period_id':_get_period,
        'journal_ids':_get_journals,
        'filter':lambda * a: 'by_date',
        }
        
wizard_report_incomes()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
