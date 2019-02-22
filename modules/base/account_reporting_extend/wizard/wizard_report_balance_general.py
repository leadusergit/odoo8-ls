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


from openerp.osv import fields, osv
import time
import xlwt as pycel
import cStringIO
import base64
import datetime
import openerp.tools
import re


class wizard_report_balance_general(osv.osv_memory):
    
    _name = "wizard.report.balance.general" 
    
    def onchange_fiscalyear_id(self, cr, uid, ids, fiscalyear_id):
        res = {'value': {}}
        if fiscalyear_id:
            period_pool = self.pool.get('account.period')
            res['value']['periods'] = period_pool.search(cr, uid, [('fiscalyear_id', '=', fiscalyear_id),
                                                                   ('special', '=', False),
                                                                   ('date_stop', '<=', time.strftime('%Y-%m-%d'))])
        return res
#     _resultados = {}
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    def generate_report(self, cr, uid, ids, context=None):
        resultados = {}
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
        ws = wb.add_sheet("BALANCE")
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u"" 
        # Version 5
        # compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        
        # Version 6
        company_id = self.pool.get('res.users').read(cr, uid, uid, ['company_id'])['company_id'][0]
#         compania_ids = self.pool.get('res.company').search(cr, uid, [('name', 'ilike', 'EMPRESA%')])
        compania = self.pool.get('res.company').browse(cr, uid, company_id)
        
        

        x0 = 3
#        sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)        
        ws.write_merge(1, 1, 1, x0, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, x0, compania.rml_header1, style_cabecera)
        ws.write_merge(3, 3, 1, x0, compania.rml_footer, style_cabecera)
        ws.write_merge(5, 5, 1, x0, 'BALANCE GENERAL', style_cabecera)
        
        ws.fit_num_pages = 1
        ws.fit_height_to_pages = 0
        ws.fit_width_to_pages = 1
        
        
        ws.write(7, 1, time.strftime('%d de %B del %Y').upper(), style_cabecera)
        
        
        form = self.browse(cr, uid, ids)[0]
        
        periodos = form.periods
        anio_fiscal = form.fiscalyear_id
        options = form.options
        
        ctx = context
        anio_fiscal_id = anio_fiscal.id
        ctx['fiscalyear'] = anio_fiscal_id
        ctx['balance'] = True
#        
        ws.write(9, 1, "CUENTA", style_header)
        ws.write(9, 2, "NOMBRE DE LA CUENTA", style_header)
       
        xp = 3
        per_id = []
        delta_per = 4
        if len(periodos) > 1:
            for periodo in periodos:
                per_id.append(periodo.id)
                ws.write_merge(9, 9, xp, xp + delta_per, "PER: " + periodo.name, style_header)
                xp += 1
                xp += delta_per 
                
            ctx['periods'] = [per_id[0]]
        elif len(periodos) == 1:
            todos_periodos = anio_fiscal.period_ids
            for un_period in todos_periodos:
                if un_period.id <= periodos[0].id:
                    per_id.append(un_period.id)
            for periodo in periodos:
                # sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)
                ws.write_merge(9, 9, xp, xp + delta_per, "PER: " + periodo.name, style_header)
                xp += 1
                xp += delta_per
            ctx['periods'] = [periodos[0].id]
            
        # sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)
        ws.write_merge(9, 9, xp, xp + delta_per, "TOTAL", style_header)
        report_bs_id = self.pool['account.report.bs'].search(cr, uid, [('code', '=', 'BG')], limit=1)
        if not report_bs_id:
            raise osv.except_osv('MissingError', u'No se ha encontrado un reporte de código "BG" para el balance general.')
        account_account_obj = self.pool.get('account.account')
        cr.execute('select aa.id \
        from account_list_account ala, account_account aa \
        where ala.account_id = aa.id \
        and report_bs_id = %s \
        and aa.level=ANY(%s) \
        order by orden', (report_bs_id[0], [(aux + 1) for aux in range(int(form.code or 100))]))
        
        account_ids = [x[0] for x in cr.fetchall()]
        account_objs = account_account_obj.browse(cr, uid, account_ids, ctx)
        x = 4
        y = 10
        fila_totales = []
        intervalo = 5
        
        list_account = account_account_obj.get_accounts_add_value_profit_or_loss(cr, uid)
        
        
        # value = account_account_obj.get_profit_or_loss(cr, uid, ctx)
        
        for account in account_objs:
                
            fila = []
            total_fila = 0.0
            puntero_periodo = 0
            
            name = ''
            name = account.name
            name = name.encode('UTF-8')
            
            y += 1
            x = 1
            
            x_prima = 7
            
            if account.type == 'view':
                ctx['periods'] = [per_id[0]]   
                ws.write(y, x, account.code, style_cuarto_nivel)
                x += 1
                ws.write(y, x, name, style_cuarto_nivel)
                x += 1
                saldo = account.balance
                saldo += self.get_add_value(cr, uid, list_account, account.id, resultados, ctx)
                saldo = round(saldo, 2)
                
                if len(account.code.replace('0', '')) in (2, 3):
                    ws.write(y, x_prima, saldo, style2)
                    x_prima += intervalo
                elif len(account.code.replace('0', '')) in (4, 5):
                    x_prima = 6
                    ws.write(y, x_prima, saldo, style2)
                    x_prima += intervalo
                elif len(account.code.replace('0', '')) in (6, 7):    
                    x_prima = 5
                    ws.write(y, x_prima, saldo, style2)
                    x_prima += intervalo
                elif len(account.code.replace('0', '')) in (8, 9):
                    x_prima = 4
                    ws.write(y, x_prima, saldo, style2)
                    x_prima += intervalo
                elif len(account.code.replace('0', '')) in (10, 11):
                    x_prima = 3
                    ws.write(y, x_prima, saldo, style2)
                    x_prima += intervalo    
                                        
                
                i = 1
                for ap in periodos[1:]:
                    # #print ' periodo ', ap                   
                    ctx['periods'] = [ap.id]
                    cuenta = account_account_obj.browse(cr, uid, account.id, ctx)
                    # value = account_account_obj.get_profit_or_loss(cr, uid, ctx)
                    x += 1
                    saldo = cuenta.balance 
                    saldo += self.get_add_value(cr, uid, list_account, cuenta.id, resultados, ctx)
                    saldo = round(saldo, 2)
                    
                    if len(cuenta.code) == 2:
                        ws.write(y, x_prima, saldo, style2)
                        x_prima += intervalo
                    elif len(cuenta.code) == 4:
                        ws.write(y, x_prima, saldo, style2)
                        x_prima += intervalo
                    elif len(cuenta.code) == 6 or len(cuenta.code) == 7 or len(cuenta.code) == 9:
                        ws.write(y, x_prima, saldo, style2)
                        x_prima += intervalo
                    elif len(cuenta.code) == 8:
                        ws.write(y, x_prima, saldo, style2)
                        x_prima += intervalo                    
                    
                    
                ctx['periods'] = per_id
                cuenta = account_account_obj.browse(cr, uid, account.id, ctx)
                # value = account_account_obj.get_profit_or_loss(cr, uid, ctx)
                x += 1
                saldo = cuenta.balance
                saldo += self.get_add_value(cr, uid, list_account, cuenta.id, resultados, ctx)
                saldo = round(saldo, 2)
                
                if len(cuenta.code) == 2:
                    ws.write(y, x_prima, saldo, style2)
                    x_prima += intervalo
                elif len(cuenta.code) == 4:
                    ws.write(y, x_prima, saldo, style2)
                    x_prima += intervalo
                elif len(cuenta.code) == 6 or len(cuenta.code) == 7 or len(cuenta.code) == 9:
                    ws.write(y, x_prima, saldo, style2)
                    x_prima += intervalo
                elif len(cuenta.code) == 8:
                    ws.write(y, x_prima, saldo, style2)
                    x_prima += intervalo                    

            else:
                ctx['periods'] = [per_id[0]]
                ws.write(y, x, account.code, style_cuenta)
                x += 1
                ws.write(y, x, name.title(), style_cuenta)
                if len(account.code) > 9:
                    x += 1
                    saldo = account.balance
                    saldo += self.get_add_value(cr, uid, list_account, account.id, resultados, ctx)
                    saldo = round(saldo, 2)
                    
                    ws.write(y, x, saldo, style3)
                elif len(account.code) == 9:
                    x += 2
                    saldo = account.balance 
                    saldo += self.get_add_value(cr, uid, list_account, account.id, resultados, ctx)
                    saldo = round(saldo, 2) 
                    ws.write(y, x, saldo, style3)
                elif len(account.code) < 9:
                    x += 3
                    saldo = account.balance 
                    saldo += self.get_add_value(cr, uid, list_account, account.id, resultados, ctx)
                    saldo = round(saldo, 2) 
                    ws.write(y, x, saldo, style3)
                    
                
                delta = 5 
                for ap in periodos[1:]:
                    ctx['periods'] = [ap.id]
                    cuenta = account_account_obj.browse(cr, uid, account.id, ctx)
                    x += delta
                    saldo = cuenta.balance
                    saldo += self.get_add_value(cr, uid, list_account, cuenta.id, resultados, ctx)
                    saldo = round(saldo, 2) 
                    ws.write(y, x, saldo, style3)
                    
                ctx['periods'] = per_id
                cuenta = account_account_obj.browse(cr, uid, account.id, ctx)
                x += delta
                saldo = cuenta.balance
                saldo += self.get_add_value(cr, uid, list_account, cuenta.id, resultados, ctx)
                saldo = round(saldo, 2) 
                ws.write(y, x, saldo, style3)    
            
        y += 4
        
        # ws.write(y, 2, 'GERENTE GENERAL', style_firma)
        ws.write_merge(y, y, 4, 5, 'CONTADOR GENERAL', style_firma)
        ws.col(2).width = 7500
        ws.col(2).width = 10500
        buf = cStringIO.StringIO()
        
        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return self.pool.get('base.file.report').show(cr, uid, out, 'Balance General.xls')
#         return self.write(cr, uid, ids, {'data':out, 'name':'report_advance.xls', 'state':'res'})

    
    def get_add_value(self, cr, uid, list_account, account_id, resultados, ctx=None):
         
        account_account_obj = self.pool.get('account.account')
        
        key = str(ctx['fiscalyear'])
        periodos = ctx['periods']
        
        for period in periodos:
            key += '_' + str(period)
    
        if account_id in list_account:
            value = resultados.get(key)
            if not value:
                #print ' resssss **** AAAA ', ctx
                #print ' resssss **** BBBB ', key
                value = account_account_obj.get_profit_or_loss(cr, uid, ctx)
                resultados.update({key:value})
                #print ' resssss **** CCCC ', self._resultados
                    
            return round(value, 2)
        else:
            return 0
    
    
    def __max_level(self, cr):
        cr.execute('select max(level) from account_account')
        return cr.fetchone()[0]
    
    _columns = {
        
        'fiscalyear_id':fields.many2one('account.fiscalyear', 'Anio Fiscal'),
        'periods':fields.many2many('account.period',
                                 'account_period_report_general_rel',
                                 'acp_id',
                                 'wrep_id', 'Periodos:'),
        'data': fields.binary(string='Archivo'),
        'name':fields.char('Nombre', size=60),
        'state':fields.selection([('ini', 'Inicial'),
                                   ('res', 'Resultado'),
                                  ], 'Estado'),
        'options':fields.selection([('todasCuentas', 'Todas'),
                                   ('ctasConMovimientos', 'Cuentas Con Movimientos'),
                                  ], 'Opciones'),
        'code':fields.selection(lambda self, cr, uid, context: [(aux, aux) for aux in [aux + 1 for aux in range(self.__max_level(cr))]],
                                'Nivel', required=True),
    }
    
    _defaults = {
        'state':lambda * a:'ini',
        'code': lambda self, cr, *a: self.__max_level(cr),
        'options':lambda * a:'todasCuentas',
    } 
    
wizard_report_balance_general()
