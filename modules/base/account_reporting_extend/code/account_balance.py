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
import time
from openerp.osv import fields, osv
from lxml import etree

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime


class account_list_report_bs(osv.osv):
    _inherit = "account.report.bs"
    
    def load_account_list(self, cr, uid, ids, context):
        
        cr.execute('delete from account_report_rel where report_id=%s', (ids))
        
        cr.execute('delete from account_list_account where report_bs_id=%s', (ids))
        
        report_bs_data = self.browse(cr, uid, ids)[0]
        
        if report_bs_data.code == 'PYG':
            list_account = ['4', '5', '6']
        elif report_bs_data.code == 'BG':
            list_account = ['1', '2', '3']
            
        account_obj = self.pool.get('account.account')
        
        
        res = []

        account_obj.get_list_account_ordering(cr, uid, ids, report_bs_data.chart_account_id.id , 0, 0, res, context)
        account_ids = []
        otro_ids = []
        for account_list_res in res:
            if account_list_res['parent_id']:
                inicio = account_list_res['code'][0:1]
                if inicio in list_account:
                    ##print ' account_list_res ', account_list_res
                    account_ids.append(account_list_res['id'])
                    vals = {'account_id':account_list_res['id'],
                            'orden':account_list_res['sec'],
                        }
                    
                    otro_ids.append((0, 0, vals))
                    
                    
        vals = {'account_id':[(6, 0, account_ids)], 'detalle_ctas_ids':otro_ids}   
        self.write(cr, uid, ids, vals)
        return True
    
    _columns = {
        'detalle_ctas_ids':fields.one2many('account.list.account', 'report_bs_id', 'Detalle Cuentas',),
        'chart_account_id': fields.many2one('account.account', 'Plan contable', required=True, domain=[('parent_id','=',False)]),
        'company_id': fields.related('chart_account_id', 'company_id', string='Compañia', type='many2one', relation='res.company', store=True)
    }
    _defaults = {  
        'chart_account_id': lambda self, *a: self.pool.get('account.common.report')._get_account(*a)
    }
    
account_list_report_bs()


class account_list_account(osv.osv):
    _name = 'account.list.account'

    _columns = {
        'report_bs_id':fields.many2one('account.report.bs', 'Reporte Balance'),
        'account_id':fields.many2one('account.account', 'Cuenta Contable'),
        'orden':fields.integer('Orden')
              
    }

account_list_account()
