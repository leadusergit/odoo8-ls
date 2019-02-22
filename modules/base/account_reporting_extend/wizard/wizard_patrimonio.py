# -*- encoding: utf-8 -*-
###################################################
#
#    BUILDING CRM Module
#    Copyright (C) 2011-2011 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################

from openerp.osv import osv, fields
from xlrd import open_workbook

from xlwt.Style import easyxf
import openerp.modules
import cStringIO, base64
from xlutils.copy import copy
from xlwt import Formula

def get_style(bold=False, font_name='Calibri', height=12, font_color='black',
              rotation=0, align='center',
              border=False, color=None, format=None):
    str_style = 'font: bold %s, name %s, height %s, color %s;' % (bold, font_name, height * 20, font_color)
    str_style += 'alignment: rotation %s, horizontal %s, vertical center, wrap True;' % (rotation, align)
    str_style += border and 'border: left thin, right thin, top thin, bottom thin;' or ''
    str_style += color and 'pattern: pattern solid, fore_colour %s;' % color or ''
    return easyxf(str_style, num_format_str=format)

class report_patrimonio(osv.osv_memory):
    _name = "evolution.patrimony"
    
    
    
    
    def obtener_resultado_periodo(self, cr, uid, ids, periodo,context=None):
        
        context['fiscalyear'] = periodo.fiscalyear_id.id
        context['periods'] = [periodo.id]
        context['period'] = periodo.id  
        account_account_obj = self.pool.get('account.account')
        value = account_account_obj.get_profit_or_loss(cr, uid, context)
        
    
    
    
    def evolucion_patrimonio(self, cr, uid, ids, context=None):
        path_book = openerp.modules.get_module_resource('account_reporting_extend', 'data', 'Formato_Reporte.xls')
        format_book = open_workbook(path_book, formatting_info=True, on_demand=True)
        book = copy(format_book)
        sheet = book.get_sheet(0)
        
        lista_datos = self.browse(cr, uid, ids)[0]
        
        periodo_inicial = lista_datos.period_ini
        periodo_final = lista_datos.period_fin

        ctx_periodo_anterior = {'periods':[self.pool.get('account.period').before(cr, uid, periodo_inicial, 1)]}
        
#         print ' ctx_periodo_anterior ', ctx_periodo_anterior
        
        periodo_anterior = self.pool.get('account.period').browse(cr, uid, ctx_periodo_anterior['periods'])[0]
       
        fila = 4
        
        sheet.write(1, 3, 'Per: %s' % periodo_inicial.name, get_style(height=8))
        sheet.write(1, 4, 'al Per: %s' % periodo_final.name, get_style(height=8))
        
        cr.execute("select id, code,name, level \
        from account_account a \
        where a.code ilike %s \
        and level > %s", ('3.1.%', 2))
    
        account_ids = [x[0] for x in cr.fetchall()]
        
#         print ' account_ids ', account_ids
        
        accounts_period_anterior = self.pool.get('account.account').browse(cr, uid, account_ids, ctx_periodo_anterior)
        
        accounts_anterior = dict((aux.id, aux.balance) for aux in accounts_period_anterior)
        
        # sheet.write(3, 0, '01/01/%s' % year, get_style(height=8))
        sheet.write(3, 1, 'Saldo al %s' % periodo_anterior.date_stop, get_style(height=8))
        sheet.write(3, 2, accounts_anterior[1550], get_style(height=8, format="0.00"))
        sheet.write(3, 3, accounts_anterior[1551], get_style(height=8, format="0.00"))
        sheet.write(3, 4, accounts_anterior[1553], get_style(height=8, format="0.00"))
        sheet.write(3, 5, accounts_anterior[1731], get_style(height=8, format="0.00"))
        sheet.write(3, 6, Formula('D4+E4+F4'), get_style(height=8, format="0.00"))
        sheet.write(3, 7, accounts_anterior[1552], get_style(height=8, format="0.00"))
        sheet.write(3, 8, Formula('C4+G4+H4'), get_style(height=8, format="0.00")) 
        
        
        periods_id = self.pool.get('account.period').build_ctx_periods(cr, uid, periodo_inicial.id, periodo_final.id)
        
#         print ' periods_id ', periods_id
        longitud = len(periods_id)
        a = 1
        periods_txt = ''
        
#         print ' long periods_txt ', longitud 
        
        for period_id in periods_id:
            if a != longitud:
                periods_txt += str(period_id) + ','
            else:
                periods_txt += str(period_id)
            a = a + 1
        
#         print ' periods_txt ', periods_txt
        
        
#         print ' account_ids ', account_ids
        accounts_txt = ''
        longitud = len(account_ids)
        a = 1
        
#         print ' longitud accounts_txt ', longitud
            
        for account_id in account_ids:
            if a != longitud:
                accounts_txt += str(account_id) + ','
            else:
                accounts_txt += str(account_id)
            a = a + 1
        
#         print ' accounts_txt ', accounts_txt    
             
        fila = 4
        
        cr.execute("select aml.account_id as id,aml.date, aml.ref, aml.name, (aml.debit - aml.credit) as saldo from account_move_line aml where account_id in (" + accounts_txt + ") and period_id in (" + periods_txt + ")")
        
        # account_ids = [x[0] for x in cr.fetchall()]
        
        datos = cr.dictfetchall()
        
        for dato in datos:
            sheet.write(fila, 0, dato['date'], get_style(height=8))
            sheet.write(fila, 1, dato['ref'] or '' + ' ' + dato['name'], get_style(height=8))
            if dato.account_id.id == 1550:
                sheet.write(fila, 2, round(dato['saldo'], 2), get_style(height=8, format="0.00"))
            if dato.account_id.id == 1551:
                sheet.write(fila, 3, round(dato['saldo'], 2), get_style(height=8, format="0.00"))
            if dato.account_id.id == 1553:
                sheet.write(fila, 4, round(dato['saldo'], 2), get_style(height=8, format="0.00"))
            if dato.account_id.id == 1731:
                sheet.write(fila, 5, round(dato['saldo'], 2), get_style(height=8, format="0.00"))    
                
            sheet.write(fila, 6, Formula('D%s+E%s+F%s' % (fila + 1, fila + 1, fila + 1)), get_style(height=8, format="0.00"))
            if dato.account_id.id == 1552:
                sheet.write(fila, 7, round(dato['saldo'], 2), get_style(height=8, format="0.00"))
            sheet.write(fila, 8, Formula('C%s+G%s+H%s' % (fila + 1, fila + 1, fila + 1)), get_style(height=8, format="0.00"))
            fila += 1        
    
    
        sheet.write(fila, 1, 'TOTAL', get_style(height=8, bold=True, border=True))
        sheet.write(fila, 2, Formula('SUM(C4:C%s)' % (fila)), get_style(height=8, format="0.00", bold=True, border=True))
        sheet.write(fila, 3, Formula('SUM(D4:D%s)' % (fila)), get_style(height=8, format="0.00", bold=True, border=True))
        sheet.write(fila, 4, Formula('SUM(E4:E%s)' % (fila)), get_style(height=8, format="0.00", bold=True, border=True))
        sheet.write(fila, 5, Formula('SUM(F4:F%s)' % (fila)), get_style(height=8, format="0.00", bold=True, border=True))
        sheet.write(fila, 6, Formula('SUM(G4:G%s)' % (fila)), get_style(height=8, format="0.00", bold=True, border=True))
        sheet.write(fila, 7, Formula('SUM(H4:H%s)' % (fila)), get_style(height=8, format="0.00", bold=True, border=True))
        sheet.write(fila, 8, Formula('SUM(I4:I%s)' % (fila)), get_style(height=8, format="0.00", bold=True, border=True))
                
        sheet.col(2).width = 4000        
        sheet.col(3).width = 4000
        sheet.col(4).width = 4000
        sheet.col(5).width = 4000
        sheet.col(6).width = 4000
        sheet.col(7).width = 4000
        buf = cStringIO.StringIO()
        book.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'file': out, 'file_name': 'Evolución Patrimonio.xls'})
    
    _columns = {
        'file':fields.binary('Archivo'),
        'file_name':fields.char('Nombre del archivo', size=64),
        # 'year_id':fields.many2one('account.fiscalyear', 'Año Inicio'),
		# 'year_end':fields.many2one('account.fiscalyear', 'Año Final'),
        'period_ini':fields.many2one('account.period', 'Periodo Inicial'),
        'period_fin':fields.many2one('account.period', 'Periodo Final'),
    }

report_patrimonio()
