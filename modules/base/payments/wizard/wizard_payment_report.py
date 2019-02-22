# -*- coding: utf-8 -*-
###################################################
#
#    Payments Module
#    Copyright (C) 2012 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
#    $autor: Dairon Medina Caro <dairon.medina@gmail.com>
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
import time
from openerp.osv import osv, fields

class wizard_payment_report(osv.osv_memory):
    _name = 'wizard.payment.report'
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    def onchage_type(self, cr, uid, ids, type, context={}):
        res = {'value':{}}
        return res
    
    def _print_report_cheque(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {'type':'ir.actions.report.xml',
                  'report_name':'report_cheque',
                  'datas': data}
        return result
    
    def _print_report_transfer(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {'type':'ir.actions.report.xml',
                  'report_name':'report_transfer',
                  'datas': data}
        return result

    def act_report_cheque(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        return self._print_report_cheque(cr, uid, ids, data, context=context)
    
    def act_report_transfer(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        return self._print_report_transfer(cr, uid, ids, data, context=context)
    
    _columns = {
            'type':fields.selection([('bycheque','Por Cheque'),('bytransfer','Por Transferencia')], 'Tipo', required=True, help="Tipo de Pago"),
            'date_from':fields.date('Fecha Inicio', required=True),
            'date_to':fields.date('Fecha Fin', required=True),
            'state':fields.selection([('draft','Borrador'),('done','Realizado'),('all','Todo')
                                      ], 'Estado', required=True, help="Estado del Pago"),
    }
    _defaults = {
                 'type':lambda *a:'bycheque',
                 'date_from':lambda *a: time.strftime('%Y-01-01'),
                 'date_to':lambda *a: time.strftime('%Y-%m-%d'),
                 'state':lambda *a:'done',
    }      
    
wizard_payment_report()