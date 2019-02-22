# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
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
from psycopg2 import IntegrityError
import time

class wizard_generate_calculated_payroll(osv.osv_memory):
    _name = 'wizard.generate.calculated.payroll'
    _columns = {
        'period_id': fields.many2one('hr.contract.period', 'Periodo', required=True),
        'employee_ids': fields.many2many('hr.employee', 'employee_wizard_rel', 'wiz_id', 'employee_id', 'Empleados',
                                         domain=[('state_emp', '=', 'active')], default=lambda self: self._get_defaults('employee_ids')),
        'notes': fields.text('Novedades', readonly=True),
        'state': fields.selection([('draft', 'Borrador'), ('done', 'Generado')], readonly=True)
    }
    
    def _get_defaults(self, cr, uid, field, context=None):
        context, res = context or {}, {}
        if context.get('active_model') == 'hr.employee':
            employee_ids = self.pool.get('hr.employee').search(cr, uid, [('id', 'in', context['active_ids']),
                                                                         ('state_emp', '=', 'active')])
            res['employee_ids'] = employee_ids
        return res.get(field)
    
    def generate(self, cr, uid, ids, context):
        payroll_model = self.pool.get('hr.payroll')
        obs = u''
        for obj in self.read(cr, uid, ids, ['period_id', 'employee_ids']):
            names = dict(self.pool.get('hr.employee').name_get(cr, uid, obj['employee_ids']))
            for employee_id in obj['employee_ids']:
                contract_id = payroll_model.onchange_contract(cr, uid, [], None, employee_id)['value']
                if not contract_id.get('contract_id'):
                    obs += '%s, no posee un contrato en el periodo.'%names[employee_id]
                    continue
                contract_id = contract_id['contract_id']
                vals = {'employee_id': employee_id, 'contract_id': contract_id, 'period_id': obj['period_id'][0]}
                if not payroll_model.search(cr, uid, [(key, '=', val) for key, val in vals.iteritems()]):
                    try:
                        vals.update(payroll_model.onchange_period(cr, uid, [], obj['period_id'][0], employee_id, contract_id)['value'])
                        payroll_id = payroll_model.create(cr, uid, vals)
                        payroll_model.load_info(cr, uid, [payroll_id], context)
                    except IntegrityError as exc:
                        obs += u'%s:  %s.\n'%(names[employee_id], exc.pgerror)
                    except osv.except_osv as exc:
                        obs += u'%s:  %s.\n'%(names[employee_id], exc.value)
                else:
                    obs += u'%s:  Ya tiene generado un rol de pagos.\n'%names[employee_id]
        self.write(cr, uid, ids, {'state': 'done', 'notes': obs})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Roles de pago generados',
            'res_model': self._name,
            'res_id': ids[0],
            'view_mode': 'form',
            'target': 'new'
        }
    
    _defaults = {
        'state': lambda *a: 'draft'
    }

wizard_generate_calculated_payroll()