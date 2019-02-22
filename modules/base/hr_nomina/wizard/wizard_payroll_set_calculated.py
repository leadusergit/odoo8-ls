# -*- coding: utf-8 -*-
###################################################
#
#    HR Nomina
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
from openerp.osv import osv, fields

class wizard_payroll_set_calculated(osv.osv_memory):
    _name = 'wizard.payroll.set.calculated'
    _description = 'Cambiar a calculado roles de pagos'
    _columns = {
        'observation': fields.text('Roles con error', readonly=True),
        'state': fields.selection([('draft', 'Borrador'), ('res', 'Resultado')], required=True, readonly=True)
    }
    _defaults = {
        'state': lambda *a: 'draft'
    }
    
    def action_set_calculated(self, cr, uid, ids, context=None):
        payroll_obj, obs = self.pool.get('hr.payroll'), ''
        for payroll_id in context.get('active_ids', []):
            try:
                payroll_obj.from_validated_to(cr, uid, [payroll_id], context)
            except osv.except_osv, ex:
                payroll = payroll_obj.browse(cr, uid, payroll_id)
                obs += '%s: %s: %s\n'%(payroll.employee_id.name, ex[0], ex[1])
        self.write(cr, uid, ids, {'observation': obs, 'state': 'res'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Romper contabilidad de la nómina',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.payroll.set.calculated',
            'res_id': ids[0],
            'view_id': False,
            'views': False,
            'target': 'new',
        }
    
wizard_payroll_set_calculated()