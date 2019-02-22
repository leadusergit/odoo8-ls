# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution.
#    Module for basic payroll in Ecuador.
#    Copyright (C) 2010-2013 Israel Paredes Reyes. All Rights Reserved.
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
from openerp.osv import osv, fields

class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    _columns = {
        'company_id': fields.related('employee_id', 'company_id', type='many2one', relation='res.company',
                                     string='Compañia', store=True, readonly=True)
    }
hr_contract()

class hr_contract_period(osv.osv):
    _name = "hr.contract.period"
    _description = "Periodo de Contrato"
    _order = "date_start"
    _columns = {
        'name': fields.char('Nombre del Periodo', size=64, required=True, select=True),
        'code': fields.char('Code', size=12),
        'special': fields.boolean('Opening/Closing Period', size=12),
        'date_start': fields.date('Inicio de Periodo', required=True, states={'done':[('readonly', True)]}),
        'date_stop': fields.date('Fin de Periodo', required=True, states={'done':[('readonly', True)]}),
        'state': fields.selection([('draft', 'Borrador'), ('done', 'Terminado')], 'Estado', readonly=True),
        'fiscalyear_id': fields.many2one('hr.fiscalyear', 'Año Fiscal', required=True, states={'done':[('readonly', True)]}, select=True),
#         'payroll_ids': fields.one2many('hr.payroll', 'period_id', 'Rol de pagos'),
    }
    _defaults = {
        'state': lambda * a: 'draft',
    }

    def _check_duration(self, cr, uid, ids, context={}):
        obj_period = self.browse(cr, uid, ids[0])
        if obj_period.date_stop < obj_period.date_start:
            return False
        return True

    def _check_year_limit(self, cr, uid, ids, context={}):
        for obj_period in self.browse(cr, uid, ids):
            if obj_period.special:
                continue

            if obj_period.fiscalyear_id.date_stop < obj_period.date_stop or \
               obj_period.fiscalyear_id.date_stop < obj_period.date_start or \
               obj_period.fiscalyear_id.date_start > obj_period.date_start or \
               obj_period.fiscalyear_id.date_start > obj_period.date_stop:
                return False

            pids = self.search(cr, uid, [('date_stop', '>=', obj_period.date_start), ('date_start', '<=', obj_period.date_stop), ('special', '=', False), ('id', '<>', obj_period.id)])
            for period in self.browse(cr, uid, pids):
                if period.fiscalyear_id.company_id.id == obj_period.fiscalyear_id.company_id.id:
                    return False
        return True

    _constraints = [
        (_check_duration, 'Error ! La duración del periodo es invalida. ', ['date_stop']),
        (_check_year_limit, 'Periodo invalido ! Some periods overlap or the date period is not in the scope of the fiscal year. ', ['date_stop'])
    ]

    def next(self, cr, uid, period, step, context={}):
        ids = self.search(cr, uid, [('date_start', '>', period.date_start)])
        if len(ids) >= step:
            return ids[step - 1]
        return False

    def find(self, cr, uid, dt=None, context={}):
        if not dt:
            dt = time.strftime('%Y-%m-%d')
#CHECKME: shouldn't we check the state of the period?
        ids = self.search(cr, uid, [('date_start', '<=', dt), ('date_stop', '>=', dt)])
        if not ids:
            raise osv.except_osv('Error !', 'No period defined for this date !\nPlease create a fiscal year.')
        return ids

    def action_draft(self, cr, uid, ids, *args):
        users_roles = self.pool.get('res.users').browse(cr, uid, uid).roles_id
        for role in users_roles:
            if role.name == 'Period':
                mode = 'draft'
                for id in ids:
                    cr.execute('update hr_contract_period set state=%s where id=%s', (mode, id))
        return True

hr_contract_period()