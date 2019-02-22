# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
import time
from openerp.osv import fields, osv
from openerp.tools.misc import currency

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

class res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {
        'num_establecimiento': fields.char('No. Establecimiento', size=8, help='Número del establecimiento el cual se está administrando por éste sistema registrado en el S.R.I.'),
        'num_sucursal': fields.char('No. Sucursal', size=8, help='Número de la sucursal o punto de emisión el cual se está administrando por éste sistema registrado en el S.R.I.'),
    }
    _defaults = {  
        'num_establecimiento': lambda *a: '001',
        'num_sucursal': lambda *a: '001',
    }
res_company()

class account_report_bs_fa(osv.osv):
    '''
    Open ERP Model
    '''
    _name='account.report.bs'
    _inherit='account.report.bs'
    _description = 'Open ERP Model'
    
    _columns = {
        'nivel': fields.integer('Niveles', required=True),     
        'account_report_ids':fields.many2many('account.report.report', 'accountreport_rel','bs_id', 'report_id', 'Indicadores'),
    }

account_report_bs_fa()

class account_account_rfa(osv.osv):
    '''
    Open ERP Model
    '''
    _name = 'account.account'
    _inherit='account.account'
    _description = 'Open ERP Model'

    def _get_level(self, cr, uid, ids, nivel=0,inicial=0):
        inicial+=1
        result = []
        if inicial < nivel:
            ids2 = self.search(cr, uid, [('parent_id', 'in', ids)])
            result = ids2
            ids3 = []
            for rec in self.browse(cr, uid, ids2):
                ids3 = self._get_cuentas_hijas(cr, uid, ids2,nivel,inicial)
                if ids3:
                    result = ids2 + ids3    
            return result


    def _get_cuentas_hijas(self, cr, uid, ids, nivel=0,inicial=0):
        inicial+=1
        result = []
        if inicial < nivel:
            ids2 = self.search(cr, uid, [('parent_id', 'in', ids)])
            result = ids2
            ids3 = []
#            for rec in self.browse(cr, uid, ids2):
            ids3 = self._get_cuentas_hijas(cr, uid, ids2,nivel,inicial)
            if ids3:
                result = ids2 + ids3    
            return result
        
        _columns = {
        
            }
account_account_rfa()

class account_report_history_dummy(osv.osv):

    def _calc_value_period(self, cr, uid, ids, name, args, context):
        acc_report_id=self.read(cr,uid,ids,['tmp','period_id'])
        tmp_ids={}
        for a in acc_report_id:
            tmp_ids[a['id']] = self.pool.get('account.report.report').read(cr,uid,[a['tmp']],context={'periods':a['period_id']})[0]['amount']
        return tmp_ids

    _name = "account.report.history"
    _inherit = "account.report.history"

    _columns = {
        'valor': fields.function(_calc_value_period, method=True, string='Valor', readonly=True),
    }

account_report_history_dummy()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

