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

__author__ = 'vllumiquinga@atikasoft.com.ec (Vinicio Ll.)'

import time
import datetime
from openerp.osv import osv
from openerp.osv import fields
from mx import DateTime
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime
from itertools import izip

class wizard_report_sale_product(osv.osv_memory):
    _name = "wizard.report.sale.product"
    _description = 'Reporte de Productos por Vendedor'
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        
        result = {'type':'ir.actions.report.xml',
                  'report_name': 'sale.product.saler',
                  'datas': data}
        return result
     
    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        return self._print_report(cr, uid, ids, data, context=context) 


    _columns = {
            'product_id':fields.many2one('product.product', 'Producto', required=False, domain=[('default_code', 'ilike', 'vs%')]),
            'date_start':fields.date('Fecha Desde'),
            'date_finish':fields.date('Fecha Hasta'),
            'user_id':fields.many2one('res.users', 'Vendedor', domain=[('groups_id','in',[21,20])] ,required=False),
        }                            
                                                                              
    _defaults = {
        'date_start': lambda * a: time.strftime('%Y-%m-01'),
        'date_finish': lambda * a: time.strftime('%Y-%m-%d'),
        'product_id':lambda * a: 0,
        'user_id':lambda * a: 0,
        }
        
wizard_report_sale_product()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
