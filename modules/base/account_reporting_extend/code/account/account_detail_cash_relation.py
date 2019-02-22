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
import parser
import traceback




class account_cash_flow_relation(osv.osv):
    _name = 'account.cash.flow.relation'
    _columns = {
        'name':fields.char('Descripcion', size=32),
        'account_id':fields.many2one('account.account', 'Cuenta Periodo Base', domain=[('level', '=', 3)]),
        'letra':fields.char('Letra', size=4),
        'operator':fields.selection([('+', 'Suma'), ('-', 'Resta'), ('/', 'Division'), ('*', 'Multiplicacion')], 'Operador', help='Operador para la formula'),
    }
    
    
    def _generate_formula(self, indice_linea):
        formula = ""
        
        if not indice_linea.operator:
            formula += "+"
        else:
            formula += indice_linea.operator
        
        if indice_linea.letra:
            formula += indice_linea.letra
        
        return formula
    
    
    
account_cash_flow_relation()


class account_cash_flow_detail(osv.osv):
    _name = 'account.cash.flow.detail'
    
    _columns = {
        'name':fields.char('Descripcion', size=32),
        'accounts_rel_ids':fields.many2many('account.cash.flow.relation', 'account_detail_cash_rel', 'cash_flow_detail_id', 'cash_flow_rel_id', 'RelacionVariaciones'),
        'totales':fields.boolean('Totales Variaciones', help="Si marca esta casilla, el sistema obtiene los valores de los totales de las variaciones"),
        'actividades_operacion':fields.selection([('clie', 'Clientes'), ('prov', 'Proveedores'), ('otro', 'Otros'), ('inve', 'Inversion'), ('fina', 'Financiamiento')], 'Grupo', help=''),
        'state':fields.selection([('ACT', 'Activo'), ('DES', 'DesActivo')], 'Estado', help='Estado del Detalle del F.E. Si es activo Aparece en el flujo de efectivo caso contrario no aparece', required="True"),
        'pertenece_a':fields.selection([('detail_operation', 'ActividadesOperacion'), ('detail_inversion', 'ActividadesInversion'), ('detail_finance', 'ActividadesFinanciamiento'), ('caja', 'CajaEquivalentesCaja')], 'Agrupado Por', help='Agrupa los detalles del estado del flujo de efectivo', required="True"),
        'orden':fields.integer('Orden Presentacion'),
        'totales_operaciones':fields.boolean('Totales Operaciones', help="Si marca esta casilla. El sistema obtiene el valor de los totales de las actividades del estado flujo de efectivo"),
        'valores_periodo_base':fields.boolean('Obtener Valores Periodo Base', help="Si marca esta casilla, el sistema obtiene los valores y hace el cálculo de la formula generada con los saldos de las cuentas contables del periodo base"),
    }
    
    
    def _get_value_total(self, detail_data, totales):
        if totales:
            return totales.get(detail_data.actividades_operacion)
        else:
            return 0.0
        
    
    def _get_value_period_base(self, detail_data, period_base):
        if period_base:
            return period_base.get(detail_data.actividades_operacion)
        else:
            return 0.0
        
    
    
    def get_value(self, cr, uid, ids, variaciones, totales, periodo_base):
        
        # try:
        
        
        #print ' ids ', ids
            
        relation_obj = self.pool.get('account.cash.flow.relation')
        
        detail_data = self.browse(cr, uid, ids)
        
        if detail_data.totales:
            return self._get_value_period_base(detail_data, totales)
        
        if detail_data.totales_operaciones:
            return 0.0
        
        
        relations_data = detail_data.accounts_rel_ids
        account_ids = {}
        formula = ''
        res = 0
        for relation_data in relations_data:
            formula += relation_obj._generate_formula(relation_data)
            if relation_data.letra and relation_data.account_id.code:
                balance = 0.0
                if not detail_data.valores_periodo_base:
                    # print ' relation_data.account_id.code ', relation_data.account_id.code
                    # print ' variaciones ', variaciones              
                    balance = variaciones.get(relation_data.account_id.code)
                    # print ' balance ', balance
                else:
                    balance = periodo_base.get(relation_data.account_id.code)
                    
                account_ids.update({relation_data.letra:float(balance)})
        
        # print ' account_ids ', account_ids
        if len(formula) > 0:
            # print ' formula ', formula    
            code = parser.expr(formula).compile()
            # print ' code ', code
            for kk, vv in account_ids.iteritems():
                # print ' k, v' , k, v
                # print '  tipo k ', type(k)
                # print '  tipo v ', type(v)
                exec("%s=%s" % (kk, vv))
            res = eval(code)
            # print ' detail_data.name ', detail_data.name
        return res
    
        # except SyntaxError:
        #    raise osv.except_osv(('Error Sintactico'), ("La expresion no esta correcta " + formula + ' del indice ' + detail_data.name))
        # except TypeError:
        #    raise osv.except_osv(('Error de Tipo'), ("No se admiten NULLs en la expresion" + formula + " valores: " + str(account_ids) + ' indice: ' + detail_data.name))
        # except ZeroDivisionError:
        #    raise osv.except_osv(('Error Datos'), ("El valor que divide es cero formula: " + formula + ' valores: ' + str(account_ids) + ' del indice ' + detail_data.name))
        # except Exception as error:
        #    traceback.print_exc()
        #    raise osv.except_osv(('Error General'), ("No se pudo procesar la formula"))
            
    

    _defaults = {
        'state':lambda * a: 'ACT',
    }
account_cash_flow_detail()









