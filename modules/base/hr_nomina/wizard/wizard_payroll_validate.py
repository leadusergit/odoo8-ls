# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Asset work
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
#creador  *EG

import time
import datetime
from openerp.osv import osv
from openerp.osv import fields
from mx import DateTime
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime
import openerp.tools
from openerp.tools.translate import _
from openerp.tools import config
import calendar

class wizard_payroll_validate(osv.osv_memory):
    _name = 'wizard.payroll.validate'
    _description = 'Validar varios roles de pagos'
    _columns = {
        'ref': fields.char('Referencia'),
        'period_id': fields.many2one('hr.contract.period', 'Periodo'),
        'date': fields.date('Fecha de asiento'),
        'observation': fields.text('Roles no validados', readonly=True),
        'state': fields.selection([('draft','Borrador'),('res','Resultado')], 'Estado', required=True, readonly=True)
    }
    _defaults = {
        'state': lambda *a: 'draft'
    }
    
    def onchange_date(self, cr, uid, ids, date):
        res = {'value': {'period_id': False}}
        if date:
            period_id = self.pool.get('hr.contract.period').search(cr, uid, [('date_start', '<=', date), ('date_stop', '>=', date)])
            res['value']['period_id'] = bool(period_id) and period_id[0]
        return res
    
    def payroll_check(self, cr, uid, ids, context=None):
        obs = ''
        context = context or {}
        context.update({'analytic_distribution': True, 'only_check': True})
        for payroll_id in context.get('active_ids'):
            try:
                self.pool.get('hr.payroll')._validate_payrolls(cr, uid, [payroll_id], context=context)
            except osv.except_osv, ex:
                obs += '%s(%s): %s\n'%(ex[0], payroll_id, ex[1])
        self.write(cr, uid, ids[0], {'observation': obs, 'state': 'res'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Validar roles',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.payroll.validate',
            'res_id': ids[0],
            'view_id': False,
            'views': False,
            'context': context,
            'target': 'new',
        }
    
    def payroll_validate(self, cr, uid, ids, context=None):
        context = context or {}
        wiz = self.browse(cr, uid, ids[0], context=context)
        context.update({'ref': wiz.ref, 'date': wiz.date, 'period_id': wiz.period_id.id})
        context.update({'analytic_distribution': True, 'only_check': False})
        vals = self.pool.get('hr.payroll')._validate_payrolls(cr, uid, context.get('active_ids'), context=context)
        move_id = self.pool['account.move'].create(cr, uid, vals, context=context)
        self.pool.get('hr.payroll').write(cr, uid, context.get('active_ids'), {'account_move_id': move_id, 'account_move_provisions_id': move_id})
        #=======================================================================
        # for payroll_id in context.get('active_ids'):
        #     try:
        #         self.pool.get('hr.payroll').validar_registro(cr, uid, [payroll_id], context=context)
        #     except osv.except_osv, ex:
        #         payroll = self.pool['hr.payroll'].browse(cr, uid, payroll_id, context=context)
        #         obs += '%s: %s: %s\n'%(payroll.employee_id.name, ex[0], ex[1])
        #=======================================================================
        return True
    
wizard_payroll_validate()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
