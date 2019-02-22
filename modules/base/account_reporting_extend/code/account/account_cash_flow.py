# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenConsulting, 
#    Copyright (C) 2013-2013 OpenConsulting
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

from openerp.osv import osv, fields
from datetime import date
import time
import xlwt as pycel
import cStringIO
import base64
import datetime
import openerp.tools
import re
import openerp.addons
from xlrd import open_workbook
from xlwt import easyxf, Formula
from xlutils.copy import copy
from datetime import datetime


class account_cash_flow_elimination(osv.osv):
    _name = 'account.cash.flow.elimination'
    
    _columns = {
        'name':fields.char('Descripcion', size=32),
        'elimination_detail_ids':fields.one2many('account_cash_elimination_detail', 'cash_elimination_id', 'Detalle'),
    }
account_cash_flow_elimination()

class account_cash_elimination_detail(osv.osv):
    _name = 'account_cash_elimination_detail'
    
    _columns = {
        'name':fields.char('Descripcion', size=32),
        'account_period_base_id':fields.many2one('account.account', 'Cuenta Periodo Base'),
        'account_period_comparativo_id':fields.many2one('account.account', 'Cuenta Periodo Comparativo'),
        'account_debe_id':fields.many2one('account.account', 'Cuenta Debe (Resutados)'),
        'account_haber_id':fields.many2one('account.account', 'Cuenta Haber (General)'),
        'cash_elimination_id':fields.many2one('account.cash.flow.elimination', 'Eliminacion'),
    }

account_cash_elimination_detail()



def get_style(bold=False, font_name='Calibri', height=12, font_color='black',
              rotation=0, align='center',
              border=True, color=None, format=None):
    str_style = 'font: bold %s, name %s, height %s, color %s;' % (bold, font_name, height * 20, font_color)
    str_style += 'alignment: rotation %s, horizontal %s, vertical center, wrap True;' % (rotation, align)
    str_style += border and 'border: left thin, right thin, top thin, bottom thin;' or ''
    str_style += color and 'pattern: pattern solid, fore_colour %s;' % color or ''
    return easyxf(str_style, num_format_str=format)


class wizard_cash_flow(osv.osv_memory):
    _name = 'wizard.cash.flow'
    
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    def generar_flujo_efectivo(self, cr, uid, ids, context=None):
        
        path = addons.get_module_resource('account_reporting_extend', 'report', 'formato_flujo_efectivo.xls')
        format_book = open_workbook(path, formatting_info=True, on_demand=True)
        book = copy(format_book)
        sheet_general = book.get_sheet(0)
        sheet_resultado = book.get_sheet(1)
        sheet_flujo_caja = book.get_sheet(2)
        
        wizard = self.browse(cr, uid, ids)[0]
        
        account_account_obj = self.pool.get('account.account')
        account_cash_flow_obj = self.pool.get('account.cash.flow')
        
        context['fiscalyear'] = wizard.period_comparativo_id.fiscalyear_id.id
        context['periods'] = [wizard.period_comparativo_id]
        context['period'] = wizard.period_comparativo_id
        
        account_cash_flow_obj._get_periods(cr, uid, ids, context)
        
        data_accounts = account_account_obj.get_list_account_by_level(cr, uid, 3, 'BG', context)
        
        list_account = account_account_obj.get_accounts_add_value_profit_or_loss(cr, uid)
        
        value = account_account_obj.get_profit_or_loss(cr, uid, context)
        
        x = 1
        y = 8
        a = 0
        
        bold = True
        for data in data_accounts:
            
            if data.level == 3:
                bold = False
            
            if data.code[0:1] == '1':
                x = 1
            else:
                if a == 0:
                    x = 5
                    y = 8
                    a += 1
                else:
                    x = 5
                
            sheet_general.write(y, x, data.code, get_style(bold, 'Calibri', 8, border=False, align='left'))
            x += 1
            sheet_general.write(y, x, data.name, get_style(bold, 'Calibri', 8, border=False, align='left'))
            x += 1
            
            saldo = data.balance
            if data.id in list_account:
                saldo = saldo + value
            
            sheet_general.write(y, x, round(saldo, 2), get_style(bold, 'Calibri', 8, border=False))
            y += 1
            bold = True
            
        self._generate_balance_resultados(cr, uid, ids, sheet_resultado, context)
        
        self._generar_flujo_caja(cr, uid, ids, sheet_flujo_caja, wizard, context)    
        
        buf = cStringIO.StringIO()
        book.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        
        return self.write(cr, uid, ids, {'file': out, 'file_name': 'flujo_efectivo.xls', 'state':'done'})
    
    
    def _generate_balance_resultados(self, cr, uid, ids, hoja_excel, context):
        
        account_account_obj = self.pool.get('account.account')
        
        context['periods'] = [context['period'].id]
        
        data_accounts = account_account_obj.get_list_account_by_level(cr, uid, 4, 'PYG', context)
       
        y = 8
        bold = True
        utilidad_bruta = 0
        utilidad_neta = 0
        for data in data_accounts:   
            x = 1
            if data.level == 4:
                bold = False
            
            hoja_excel.write(y, x, data.code, get_style(bold, 'Calibri', 8, border=False, align='left'))
            x += 1
            hoja_excel.write(y, x, data.name, get_style(bold, 'Calibri', 8, border=False, align='left'))
            x += 1
            saldo = round(data.balance, 2)
            hoja_excel.write(y, x, saldo, get_style(bold, 'Calibri', 8, border=False))
            y += 1
            if data.code == '4.':
                utilidad_bruta = saldo
                utilidad_neta = saldo
            if data.code == '5.1.2.':
                utilidad_bruta -= saldo
            if data.code == '5.':
                utilidad_neta -= saldo     
            
            bold = True
            if data.code == '5.1.2.':
                bold = True
                x = 2
                hoja_excel.write(y, x, "UTILIDAD O PERDIDA BRUTA", get_style(bold, 'Calibri', 8, border=False, align='left'))
                x += 1
                hoja_excel.write(y, x, utilidad_bruta, get_style(bold, 'Calibri', 8, border=False, align='left')) 
                y += 1
        
        x = 2
        bold = True
        hoja_excel.write(y, x, "UTILIDAD O PERDIDA NETA", get_style(bold, 'Calibri', 8, border=False, align='left'))
        x += 1
        hoja_excel.write(y, x, utilidad_neta, get_style(bold, 'Calibri', 8, border=False))
    
    
    def _generar_flujo_caja(self, cr, uid, ids, hoja_excel, form, context):
        
        account_cash_flow_obj = self.pool.get('account.cash.flow')
        
        account_cash_flow_obj.set_sheet_excel(hoja_excel)
        
        account_cash_flow_obj.variaciones = {}
        
        ultimo = account_cash_flow_obj._get_account_balance(cr, uid, ids, form, context)
        
        account_cash_flow_obj._get_account_lost_gain(cr, uid, ids, ultimo, form, context)
        
        account_cash_flow_obj._show_flujo_efectivo(cr, uid, form, context)
    
    
    def view_init(self, cr, uid, fields, context):
        # print ' context view init ', context
        ids = context['active_id']
        account_detail_obj = self.pool.get('account.cash.flow.detail')
        detail_ids = account_detail_obj.search(cr, uid, [('state', '=', 'ACT')])
        context['default_details_ids'] = detail_ids
    
    
    _columns = {
        'period_comparativo_id':fields.many2one('account.period', 'Periodo Comparativo'),
        'period_base_id':fields.many2one('account.period', 'Periodo Base'),
        'eliminations_ids':fields.many2many('account.cash.flow.elimination', 'elimination_cash_flow_rel', 'cash_flow_id', 'elemination_id', 'Eliminaciones'),
        'details_ids':fields.many2many('account.cash.flow.detail', 'cash_flow_detail_rel', 'cash_flow_id', 'detail_id', 'Detalles'),
        'state':fields.selection([('init', 'init'), ('done', 'done')]),
        'file':fields.binary('Archivo generado', readonly=True),
        'file_name':fields.char('Nombre del archivo', size=512, readonly=True),
    }
      
    _defaults = {
        'state':'init',
    }

wizard_cash_flow()

class account_cash_flow(osv.osv):
    
    _name = 'account.cash.flow'
    
    _sheet_excel = None
    
    eliminacion_resultados = {}
    
    totales = {}
    
    variaciones = {}
    
    fuentes_usos = {}
    
    _periodo_base = {}
    
    agrupar_por = [('detail_operation', 'ActividadesOperacion'), ('detail_inversion', 'ActividadesInversion'), ('detail_finance', 'ActividadesFinanciamiento'), ('caja', 'Saldo Al Final Bancos')]
    
    
    def _show_flujo_efectivo(self, cr, uid, form, context):
        
        
        detail_obj = self.pool.get('account.cash.flow.detail')
        
        resultado = self._generate_flujo_efectivo(cr, uid, form, context)
        # print ' resultado ', resultado
        
        x = 15
        y = 8
        
        total_operaciones = 0.0
        for agrupa_por in self.agrupar_por:
            actividades = resultado.get(agrupa_por[0])
            if not actividades:
                continue
            valor_actividad = 0.0
            for actividad in actividades:
                # print ' actividad ', actividad
                for k, v in actividad.iteritems():
                   
                    if k == 'tot_ope':
                        continue
                    
                    detail_data = detail_obj.browse(cr, uid, k)
                    self._sheet_excel.write(y, x, detail_data.name , get_style(False, 'Calibri', 8, border=False, align='center'))
                    x += 1
                    if not actividad['tot_ope']:
                        self._sheet_excel.write(y, x, round(v, 2) , get_style(False, 'Calibri', 8, border=False, align='center'))
                        valor_actividad += round(v, 2)
                    else:
                        self._sheet_excel.write(y, x, total_operaciones , get_style(False, 'Calibri', 8, border=False, align='center'))
                        valor_actividad += total_operaciones
                        total_operaciones = 0.0
                    y += 1
                    x = 15
                    
                    
            if agrupa_por[0] != 'caja':
                self._sheet_excel.write(y, x, 'Efectivo neto proveniente de ' + agrupa_por[1] , get_style(True, 'Calibri', 9, border=False, align='center'))
            else:
                self._sheet_excel.write(y, x, agrupa_por[1] , get_style(True, 'Calibri', 9, border=False, align='center'))
            x += 1
            total_operaciones += valor_actividad
            self._sheet_excel.write(y, x, valor_actividad , get_style(True, 'Calibri', 9, border=False, align='center'))
            y += 2
            x = 15
            
                
    def _generate_flujo_efectivo(self, cr, uid, form, context):
        """
        Metodo que muestra los detalles del flujo de efectivo con sus respectivos valores
        """
        detail_obj = self.pool.get('account.cash.flow.detail')
        
        query = """select name,pertenece_a,id,totales_operaciones
        from account_cash_flow_detail
        where state = 'ACT'
        group by pertenece_a,name,id
        order by orden"""
        
        cr.execute(query)
        
        estado_flujo_efectivo = {}
        
        detalles = cr.dictfetchall()
        for detalle in detalles:
            pertenece_a = estado_flujo_efectivo.get(detalle['pertenece_a'])
            if pertenece_a == None:
                res = []
                res.append({'tot_ope':detalle['totales_operaciones'], detalle['id']:detail_obj.get_value(cr, uid, detalle['id'], self.fuentes_usos, self.totales, self._periodo_base)})
                estado_flujo_efectivo.update({detalle['pertenece_a']:res})
            else:
                pertenece_a.append({'tot_ope':detalle['totales_operaciones'], detalle['id']:detail_obj.get_value(cr, uid, detalle['id'], self.fuentes_usos, self.totales, self._periodo_base)})
                
        return estado_flujo_efectivo
    
    
    def set_sheet_excel(self, hoja):
        self._sheet_excel = hoja
        self.eliminacion_resultados = {}
        self.totales = {}
        self.variaciones = {}
        self.fuentes_usos = {}
        self._periodo_base = {}
        
        
    def _get_periods(self, cr, uid, ids, context):
        account_period_obj = self.pool.get('account.period')
        period_data = context.get('periods')
        period_to_id = period_data[0].id 
        
        # fecha_inicio_str = period_data[0].fiscalyear_id.name + '-' + '01' + '-' + '01' 
        # dt = time.strptime(fecha_inicio_str, '%Y-%m-%d')
        dt = period_data[0].fiscalyear_id.name + '-' + '01' + '-' + '01'
        period_from_id = account_period_obj.find(cr, uid, dt)
        period_ids = account_period_obj.build_ctx_periods(cr, uid, period_from_id[0], period_to_id)
        
        context['periods'] = period_ids 
        
    
    def _get_account_balance(self, cr, uid, ids, form, context):
        
        account_account_obj = self.pool.get('account.account')
        
        list_account = account_account_obj.get_accounts_add_value_profit_or_loss(cr, uid)
        
        # Obtener el valor de utilidad o perdida
        context['fiscalyear'] = form.period_comparativo_id.fiscalyear_id.id
        context['periods'] = [form.period_comparativo_id]
        self._get_periods(cr, uid, ids, context)
        
        value = account_account_obj.get_profit_or_loss(cr, uid, context)
        
        context_base = {}
        context_base['fiscalyear'] = form.period_base_id.fiscalyear_id.id
        context_base['periods'] = [form.period_base_id]
        self._get_periods(cr, uid, ids, context_base)
        
        value_base = account_account_obj.get_profit_or_loss(cr, uid, context_base)                    
        
        data_accounts = account_account_obj.get_list_account_by_level(cr, uid, 3, 'BG', context)
        
        self._sheet_excel.write(5, 4, form.period_comparativo_id.name, get_style(True, 'Calibri', 8, border=False, align='center'))
        self._sheet_excel.write(5, 7, form.period_base_id.name, get_style(True, 'Calibri', 8, border=False, align='center'))
        
        
        x = 0
        y = 6
        bold = True
        
        pasivo_patrimonio = 0.0
        pasivo_patrimonio_base = 0.0
        
        for data in data_accounts:
            
            if data.level == 3:
                bold = False
            
            self._sheet_excel.write(y, x, data.code, get_style(bold, 'Calibri', 8, border=False, align='left'))
            # sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)
            x += 1
            # print ' x ', x
            # print ' y ', y
            self._sheet_excel.write_merge(y, y, x, 3, data.name, get_style(bold, 'Calibri', 8, border=False, align='left'))
            
            x += 3
            saldo = round(data.balance, 2)
            value = round(value, 2)
            if data.id in list_account:
                saldo += value 
            self._sheet_excel.write(y, x, saldo, get_style(bold, 'Calibri', 8, border=False, align='right'))
            
            # Obtener informacion de la linea
            linea_info = self._get_line_data(cr, uid, ids, form, data, value_base, value, list_account)
            self.variaciones.update({linea_info.get_code_cuenta():linea_info.get_variacion()})
            self.fuentes_usos.update({linea_info.get_code_cuenta():linea_info.get_fuentes_uso()})
            
            saldo_periodo_comparativo = linea_info.get_saldo_periodo_comparativo()
            if saldo_periodo_comparativo == 0:
                saldo_periodo_comparativo = ''
            else:
                saldo_periodo_comparativo = round(saldo_periodo_comparativo, 2)
            
            eliminacion_db = linea_info.get_eliminacion_db()
            if eliminacion_db == 0:
                eliminacion_db = ''
            else:
                eliminacion_db = round(eliminacion_db, 2)
            
            eliminacion_cr = linea_info.get_eliminacion_cr()
            if eliminacion_cr == 0:
                eliminacion_cr = ''
            else:
                eliminacion_cr = round(eliminacion_cr, 2)
                                
            saldo_periodo_base = linea_info.get_saldo_periodo_base()
            if saldo_periodo_base == 0:
                saldo_periodo_base = ''
            else:
                saldo_periodo_base = round(saldo_periodo_base, 2)
            
            variacion = linea_info.get_variacion()
            if variacion == 0:
                variacion = ''
            else:
                variacion = round(variacion, 2)
            
            
            x += 1
            self._sheet_excel.write(y, x, eliminacion_db, get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, eliminacion_cr, get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, saldo_periodo_base, get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, variacion, get_style(bold, 'Calibri', 8, border=False, align='right'))
            
            x += 1
            self._sheet_excel.write(y, x, linea_info.get_cliente(), get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, linea_info.get_proveedor(), get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, linea_info.get_otros(), get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, linea_info.get_inversion(), get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, linea_info.get_financiamiento(), get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, linea_info.get_total(), get_style(bold, 'Calibri', 8, border=False, align='right'))
            
            x = 0
            y += 1
            
            
            # Comprobanción del periodo comparativo
            if data.code == '2':
                pasivo_patrimonio = saldo
            if data.code == '3':
                pasivo_patrimonio += saldo
            
            # Comprobanción del periodo base
            if linea_info.get_pasivo_mas_patrimonio_base():
                pasivo_patrimonio_base += linea_info.get_pasivo_mas_patrimonio_base()
                
            bold = True
                    
            
        x = 1
        y += 1
        bold = True
        self._sheet_excel.write_merge(y, y, x, 3, "TOTAL PASIVO + PATRIMONIO", get_style(bold, 'Calibri', 8, border=False, align='left'))
        x += 3
        self._sheet_excel.write(y, x, pasivo_patrimonio, get_style(bold, 'Calibri', 8, border=False, align='right'))
        
        x += 3
        self._sheet_excel.write(y, x, pasivo_patrimonio_base, get_style(bold, 'Calibri', 8, border=False, align='right'))
        
        return y
        
            
           
    def _get_account_lost_gain(self, cr, uid, ids, ultimo, form, context):
        
        account_account_obj = self.pool.get('account.account')
        
        # print ' context _get_account_lost_gain ', context
        
        context['periods'] = [context['period'].id]
        
        data_accounts = account_account_obj.get_list_account_by_level(cr, uid, 4, 'PYG', context)
        
        bold = True
        
        y = ultimo + 2
        x = 0
        # print ' y ', y
        utilidad_neta = 0
        
        for data in data_accounts:
            
            if data.level == 4:
                bold = False
            
            self._sheet_excel.write(y, x, data.code, get_style(bold, 'Calibri', 8, border=False, align='left'))
            # sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)
            x += 1
            # print ' y ', y
            # print ' x ', x
            self._sheet_excel.write_merge(y, y, x, 3, data.name, get_style(bold, 'Calibri', 8, border=False, align='left'))
            x += 3
            saldo = round(data.balance, 2)
            self._sheet_excel.write(y, x, saldo, get_style(bold, 'Calibri', 8, border=False, align='right'))
            
            # Obtener informacion de la linea
            linea_info = self._get_line_data(cr, uid, ids, form, data)
            
            if data.code in ('1.2.6.', '5.2.1.13.'):
                print ' linea_info.get_eliminacion_cr() ', linea_info.get_eliminacion_cr()
                print ' linea_info.get_eliminacion_db() ', linea_info.get_eliminacion_db()
            
            
            self.variaciones.update({linea_info.get_code_cuenta():linea_info.get_variacion()})
            self.fuentes_usos.update({linea_info.get_code_cuenta():linea_info.get_fuentes_uso()})
            
            eliminacion_db = linea_info.get_eliminacion_db()
            if eliminacion_db == 0:
                eliminacion_db = ''
            else:
                eliminacion_db = round(eliminacion_db, 2)
            
            eliminacion_cr = linea_info.get_eliminacion_cr()
            if eliminacion_cr == 0:
                eliminacion_cr = ''
            else:
                eliminacion_cr = round(eliminacion_cr, 2)
                                
            saldo_periodo_base = linea_info.get_saldo_periodo_base()
            if saldo_periodo_base == 0:
                saldo_periodo_base = ''
            else:
                saldo_periodo_base = round(saldo_periodo_base, 2)
            
            variacion = linea_info.get_variacion()
            if variacion == 0:
                variacion = ''
            else:
                variacion = round(variacion, 2)
            
            
            x += 1
            self._sheet_excel.write(y, x, eliminacion_db, get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, eliminacion_cr, get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, saldo_periodo_base, get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, variacion, get_style(bold, 'Calibri', 8, border=False, align='right'))
            
            x += 1
            self._sheet_excel.write(y, x, linea_info.get_cliente(), get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, linea_info.get_proveedor(), get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, linea_info.get_otros(), get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, linea_info.get_inversion(), get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, linea_info.get_financiamiento(), get_style(bold, 'Calibri', 8, border=False, align='right'))
            x += 1
            self._sheet_excel.write(y, x, linea_info.get_total(), get_style(bold, 'Calibri', 8, border=False, align='right'))
            
            x = 0
            y += 1
            
            if data.code == '4.':
                if saldo < 0:
                    utilidad_neta = (-1) * saldo
                else:
                    utilidad_neta = saldo
            if data.code == '5.':
                if saldo < 0:
                    utilidad_neta -= (-1) * saldo
                else:
                    utilidad_neta -= saldo
            
            bold = True
        
        x = 1
        y += 1
        bold = True    
        self._sheet_excel.write_merge(y, y, x, 3, "UTILIDAD NETA", get_style(bold, 'Calibri', 8, border=False, align='left'))
        x += 3
        self._sheet_excel.write(y, x, utilidad_neta, get_style(bold, 'Calibri', 8, border=False, align='right'))
        
        x += 5
        self._sheet_excel.write(y, x, self.totales.get('clie') or 0, get_style(bold, 'Calibri', 8, border=False, align='right'))
        x += 1
        self._sheet_excel.write(y, x, self.totales.get('prov') or 0, get_style(bold, 'Calibri', 8, border=False, align='right'))
        x += 1
        self._sheet_excel.write(y, x, self.totales.get('otro') or 0, get_style(bold, 'Calibri', 8, border=False, align='right'))
        x += 1
        self._sheet_excel.write(y, x, self.totales.get('inve') or 0, get_style(bold, 'Calibri', 8, border=False, align='right'))
        x += 1
        self._sheet_excel.write(y, x, self.totales.get('fina') or 0, get_style(bold, 'Calibri', 8, border=False, align='right'))
        
        
        
        return y
                
    
    
    def _get_line_data(self, cr, uid, ids, form, account_comprativo, value_base=0, value_comp=0, list_account=None):    
        """
        form: el formulario del wizard
        ultimo: ultimo fila que esta pintando
        data:Datos de la cuenta contable actual
        """
        eliminations_data = form.eliminations_ids
        code_cuenta_actual = account_comprativo.code
        
        
        val_eliminacion = 0.0
        """
        Representa la linea del excel
        """
        linea_cash_flow = account_cash_flow_view_object()
        
        linea_cash_flow.set_code_cuenta(account_comprativo.code)
        saldo_periodo_comp = account_comprativo.balance
        if list_account and account_comprativo.id in list_account:
            value_comp = round(value_comp, 2)
            saldo_periodo_comp += value_comp
        
        linea_cash_flow.set_saldo_periodo_comparativo(saldo_periodo_comp)
        
        """
        Obtener los datos de saldo de la cuenta del periodo base
        """
        account_account_obj = self.pool.get('account.account')
        # print ' form.period_base_id ', form.period_base_id
        # print ' form.period_base_id.fiscalyear_id.id ', form.period_base_id.fiscalyear_id.id
        
        account_base = None
        if list_account:
            context_base = {}
            context_base['fiscalyear'] = form.period_base_id.fiscalyear_id.id
            context_base['periods'] = [form.period_base_id]
            self._get_periods(cr, uid, ids, context_base)
                                
            cuenta_period_base_id = account_comprativo.id
            
            account_base = account_account_obj.browse(cr, uid, cuenta_period_base_id, context_base)
            
            saldo_periodo_base = round(account_base.balance, 2)
            
            self._periodo_base.update({account_comprativo.code:saldo_periodo_base})
            
        else:
            saldo_periodo_base = 0
        
        # Es balance general
        for elimination_data in eliminations_data:
            eli_details = elimination_data.elimination_detail_ids
            for eli_detail in eli_details:
                if eli_detail.account_debe_id and eli_detail.account_haber_id and (code_cuenta_actual == eli_detail.account_debe_id.code or code_cuenta_actual == eli_detail.account_haber_id.code):
                    if list_account:
                        val_eliminacion = account_comprativo.balance - saldo_periodo_base
                        if val_eliminacion != 0:
                            val_eliminacion = (-1) * val_eliminacion

                        if eli_detail.account_debe_id.code == code_cuenta_actual:
                            linea_cash_flow.set_eliminacion_db(val_eliminacion)
                            self.eliminacion_resultados.update({eli_detail.account_haber_id.code:val_eliminacion})
                        elif eli_detail.account_haber_id.code == code_cuenta_actual:
                            linea_cash_flow.set_eliminacion_cr(val_eliminacion)
                            self.eliminacion_resultados.update({eli_detail.account_debe_id.code:val_eliminacion})
                    else:
                        if eli_detail.account_debe_id.code == code_cuenta_actual:
                            val_eliminacion = self.eliminacion_resultados.get(code_cuenta_actual) or val_eliminacion 
                            linea_cash_flow.set_eliminacion_db(val_eliminacion)
                        elif eli_detail.account_haber_id.code == code_cuenta_actual:
                            val_eliminacion = self.eliminacion_resultados.get(code_cuenta_actual) or val_eliminacion
                            linea_cash_flow.set_eliminacion_cr(val_eliminacion)
                                
        value_base = round(value_base, 2)
        if list_account and cuenta_period_base_id in list_account:
            saldo_periodo_base += value_base
        
        
            
        linea_cash_flow.set_saldo_periodo_base(saldo_periodo_base)
        self._get_variaciones(cr, uid, ids, linea_cash_flow, account_comprativo)
        self._actividades_de_operacion(cr, uid, ids, linea_cash_flow, account_comprativo)
        
        if account_base and account_base.code == '2':
            linea_cash_flow.set_pasivo_mas_patrimonio_base(saldo_periodo_base)
        else:
            linea_cash_flow.set_pasivo_mas_patrimonio_base(0)
        if account_base and account_base.code == '3':
            linea_cash_flow.set_pasivo_mas_patrimonio_base(saldo_periodo_base)
        else:
            linea_cash_flow.set_pasivo_mas_patrimonio_base(0)
                    
        
        return linea_cash_flow
                    
    
    def _get_variaciones(self, cr, uid, ids, linea_cash_flow, account):
        # variacion = linea_cash_flow.get_saldo_periodo_base() + linea_cash_flow.get_eliminacion_db() - linea_cash_flow.get_eliminacion_cr() - linea_cash_flow.get_saldo_periodo_comparativo()
        
        print ' linea_cash_flow.get_saldo_periodo_comparativo() ', linea_cash_flow.get_saldo_periodo_comparativo()
        print ' linea_cash_flow.get_eliminacion_db() ', linea_cash_flow.get_eliminacion_db()
        print ' linea_cash_flow.get_eliminacion_cr() ', linea_cash_flow.get_eliminacion_cr()
        print ' linea_cash_flow.get_saldo_periodo_base() ', linea_cash_flow.get_saldo_periodo_base()
        print ' account.code ', account.code
        print ' account.name ', account.name
        
        variacion = linea_cash_flow.get_saldo_periodo_comparativo() + linea_cash_flow.get_eliminacion_db() - linea_cash_flow.get_eliminacion_cr() - linea_cash_flow.get_saldo_periodo_base()
        
        if account.code.startswith('4.'):
            if variacion < 0:
                    variacion = (-1) * variacion

        if account.code.startswith('5.'):
            if variacion > 0:
                variacion = (-1) * variacion
        
        linea_cash_flow.set_variacion(variacion)
        
    
    def _actividades_de_operacion(self, cr, uid, ids, linea_cash_flow, cuenta):
        
        val = 0.0
        total = 0.0
        
        if cuenta.clasificacion_flu_efe:
            # ('clie', 'Clientes'), ('prov', 'Proveedores'), ('otro', 'Otros'), ('inve', 'Inversion'), ('fina', 'Financiamiento')
            val = self._get_fuente_uso(cr, uid, ids, linea_cash_flow, cuenta)
            
            if cuenta.clasificacion_flu_efe == 'clie':
                linea_cash_flow.set_cliente(val)
            elif cuenta.clasificacion_flu_efe == 'prov':
                linea_cash_flow.set_proveedor(val)
            elif cuenta.clasificacion_flu_efe == 'otro':
                linea_cash_flow.set_otros(val)
            elif cuenta.clasificacion_flu_efe == 'inve':
                linea_cash_flow.set_inversion(val)
            elif cuenta.clasificacion_flu_efe == 'fina':
                linea_cash_flow.set_financiamiento(val)
            
            # val = linea_cash_flow.get_variacion()
            val += self.totales.get(cuenta.clasificacion_flu_efe) or 0.0
            self.totales.update({cuenta.clasificacion_flu_efe:val})
            
        if len(cuenta.code) >= 5:
            total = linea_cash_flow.get_cliente() + linea_cash_flow.get_proveedor() + linea_cash_flow.get_otros() + linea_cash_flow.get_inversion() + linea_cash_flow.get_financiamiento()
            total = linea_cash_flow.get_variacion() - total
            total = round(total, 2)
            linea_cash_flow.set_total(total)
        else:
            linea_cash_flow.set_total(total)
    
    def _get_fuente_uso(self, cr, uid, ids, linea_cash_flow, cuenta):
       
        variacion = linea_cash_flow.get_variacion()
           
        if cuenta.code.startswith('1.'):
            linea_cash_flow.set_fuentes_uso(variacion * (-1))
            return variacion * (-1)
        elif cuenta.code.startswith('2.') or cuenta.code.startswith('4.') or cuenta.code.startswith('5.'):
            linea_cash_flow.set_fuentes_uso(variacion)
            return variacion
        else:
            linea_cash_flow.set_fuentes_uso(variacion)
            return variacion
                
account_cash_flow() 



class account_cash_flow_view_object:
    'No es parte del framework OpenObjet sirva para representar una fila del excel del cash flow'
    __code_cuenta = ''
    __saldo_periodo_comparativo = 0.0
    __eliminacion_db = 0.0
    __eliminacion_cr = 0.0
    __saldo_periodo_base = 0.0
    __variacion = 0.0
    __fuentes_uso = 0.0
    __pasivo_mas_patrimonio = 0.0
    
    __cliente = 0.0
    __proveedor = 0.0
    __otros = 0.0
    __inversion = 0.0
    __financiamiento = 0.0
    __total = 0.0
    
    
    def get_fuentes_uso(self):
        return self.__fuentes_uso
    
    def set_fuentes_uso(self, fuentes_uso):
        self.__fuentes_uso = fuentes_uso
    
    def get_pasivo_mas_patrimonio_base(self):
        return self.__pasivo_mas_patrimonio
    
    def set_pasivo_mas_patrimonio_base(self, pasivo_patrimonio):
        self.__pasivo_mas_patrimonio = pasivo_patrimonio
    
    def get_cliente(self):
        return self.__cliente
    
    def set_cliente(self, cliente):
        self.__cliente = cliente
    
    def get_proveedor(self):
        return self.__proveedor
    
    def set_proveedor(self, proveedor):
        self.__proveedor = proveedor
    
    def get_otros(self):
        return self.__otros
    
    def set_otros(self, otros):
        self.__otros = otros
    
    def get_inversion(self):
        return self.__inversion
    
    def set_inversion(self, inversion):
        self.__inversion = inversion
    
    def get_financiamiento(self):
        return self.__financiamiento
    
    def set_financiamiento(self, financiamiento):
        self.__financiamiento = financiamiento
    
    def get_total(self):
        return self.__total
    
    def set_total(self, total):
        self.__total = total
    
    
    def get_code_cuenta(self):
        return self.__code_cuenta
    
    def set_code_cuenta(self, code_cuenta):
        self.__code_cuenta = code_cuenta
        
    
    def get_saldo_periodo_comparativo(self):
        return self.__saldo_periodo_comparativo
    
    def set_saldo_periodo_comparativo(self, saldo_periodo_comparativo):
        self.__saldo_periodo_comparativo = saldo_periodo_comparativo
    
    def get_eliminacion_db(self):
        return self.__eliminacion_db
    
    def set_eliminacion_db(self, eliminacion_db):
        self.__eliminacion_db = eliminacion_db    
    
    
    def get_eliminacion_cr(self):
        return self.__eliminacion_cr
    
    def set_eliminacion_cr(self, eliminacion_cr):
        self.__eliminacion_cr = eliminacion_cr
    
    def get_saldo_periodo_base(self):
        return self.__saldo_periodo_base
    
    def set_saldo_periodo_base(self, saldo_periodo_base):
        self.__saldo_periodo_base = saldo_periodo_base
    
    def get_variacion(self):
        return self.__variacion
    
    def set_variacion(self, variacion):
        self.__variacion = variacion
    
    
    
account_cash_flow_view_object()
   
    


