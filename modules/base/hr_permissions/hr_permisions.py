# -*- coding: UTF-8 -*-
#################################################################################
#
#    HHRR Module
#    Copyright (C) 2011-2011 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
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
#################################################################################

from openerp.osv import osv
from openerp.osv import fields
from datetime import datetime
import time

class hr_permission_support(osv.osv):
    """Archivos que respaldan un permiso"""
    _name = 'hr.permission.support'
    _description = 'Respaldos de Permisos'
    _columns = {
            'name': fields.char('Tipo de Respaldo', size=100, help='Tipo de Respaldo del permiso(ej: Certificado Médico)'),
            'attachment' : fields.many2one('ir.attachment', 'Archivo Adjunto'),
            'description' : fields.text('Descripcion'),
            }

hr_permission_support()

class hr_permission(osv.osv):
    """"Clase para manejo de permisos de los empleados"""
    _name = 'hr.permission'
    _inherit = 'ir.needaction_mixin'
    _rec_name = 'employee_id'
    _description = 'Manejo de Permisos'

    def _not_negative(self, cr, uid, ids):
        """Validar que la solicitud tenga más de un día de duración"""
        solicitud = self.browse(cr, uid, ids)[0]
        if solicitud.number_of_days < 0:
            return False
        else:
            return True

    def onchange_employee_id(self, cr, uid, ids, employee_id):
        res = {}
        if employee_id:
            employee_data = self.pool.get('hr.employee').read(cr, uid, employee_id, ['department_id'])
            res['value'] = dict(departament_id=employee_data['department_id'] and employee_data['department_id'][0])
        return res

    def approve_permission(self, cr, uid, ids, context={}):
        """Aprobar Permisos solicitados"""
        self.write(cr, uid, ids, {'state': 'approved'})
        return True

    def deny_permission(self, cr, uid, ids, context={}):
        """Aprobar Permisos solicitados"""
        self.write(cr, uid, ids, {'state': 'deny'})
        return True
    def request_permission(self, cr, uid, ids, context={}):
        """Aprobar Permisos solicitados"""
        self.write(cr, uid, ids, {'state': 'requested'})
        return True
    
    def validate_permission(self, cr, uid, ids, context={}):
        """Validar permisos aprobados con las horas reales de permisos"""
        self.write(cr, uid, ids, {'state': 'validate'})
        return True    
    
    def no_validate_permission(self, cr, uid, ids, context={}):
        """El empleado no pudo Justificar sus permisos. Y el usuario no valido su permiso"""
        self.write(cr, uid, ids, {'state': 'no_validate'})
        return True    
    
    def _get_employee(self, cr, uid, context=None):
        user_name = self.pool.get('res.users').read(cr, uid, uid, ['name'])
        employee = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])
        if not employee:
            raise osv.except_osv("Error Configuracion", "El usuario " + user_name['name'] + " no tiene empleado asociado")
        return employee[0]
    
    def _get_department(self, cr, uid, context=None):
        department_id = False
        employee_ob = self.pool.get('hr.employee')
        user_name = self.pool.get('res.users').read(cr, uid, uid, ['name'])
        employee_ids = employee_ob.search(cr, uid, [('user_id', '=', uid)])
        if employee_ids:
            employee_info = employee_ob.browse(cr, uid, employee_ids[0])
            department_id =  employee_info.department_id and employee_info.department_id.id or False 
        
        return department_id
    
    def check_coach(self, cr, uid, ids):
        for obj in self.browse(cr, uid, ids):
            if not obj.jefe_uid:
                raise osv.except_osv('Error', u'Error: Ud. no puede realizar esta acción.')
            if obj.jefe_uid.id != uid:
                raise osv.except_osv('Error', u'Error: Ud. no puede realizar esta acción, solamente %s lo puede hacer.' % obj.jefe_uid.name)
        return True
    
    def onchange_fecha_permiso(self, cr, uid, ids, permission_date):
        res = {}
        if permission_date:
            period_data = self.pool.get('hr.contract.period').search(cr, uid, [('date_start', '<=', permission_date), ('date_stop', '>=', permission_date)])
            res['value'] = dict(period_id=period_data[0])
        return res    
    
    def _validar_horas_segun_tipo(self, cr, uid, ids):
        """Validar que la solicitud de permiso de tipo MATERNIDAD no pida horas de permiso"""
        solicitud = self.browse(cr, uid, ids)[0]
        if solicitud.permission_type != 'maternidad' and solicitud.number_of_days == 0:
            return False
        else:
            return True
        
    _columns = {
    		'employee_id' : fields.many2one('hr.employee', 'Nombre del Solicitante', select=True, required=True, readonly=True, states={'draft': [('readonly', False)]}),
            'departament_id' : fields.many2one('hr.department', 'Departamento', select=True, readonly=True, states={'draft': [('readonly', False)]}),
            'requested_date' : fields.date('Fecha de Solicitud', readonly=True, select=True),
            'permission_date' : fields.datetime('Fecha desde Permiso', required=True, readonly=True, states={'draft': [('readonly', False)]}),
            'permission_date_to' : fields.datetime('Fecha hasta Permiso', readonly=True, required=True, states={'draft': [('readonly', False)]}),
            'number_of_days' : fields.float('Duración ( Horas )', required=True, digits=(16, 4), help="Cantidad de horas del Permiso", readonly=True, states={'draft': [('readonly', False)]}),
            'permission_type' : fields.selection([('private', 'Permisos (Personal)'), 
                                                  ('laboral', 'Ausencias Temporales (Laboral)'), 
                                                  ('maternidad', 'Maternidad'),
                                                  ('paternidad', 'Paternidad'),
                                                  ('disease', 'Enfermedad')], 'Tipo de Permiso', select=True, required=True, readonly=True, states={'draft': [('readonly', False)]}),
            'other_permission' : fields.char('Otros', size=100, readonly=True, states={'draft': [('readonly', False)]}),
            'reason' : fields.text('Motivo', readonly=True, states={'draft': [('readonly', False)]}),
            'support_attachment' : fields.many2one('hr.permission.support', 'Respaldo que Adjunta', readonly=True, states={'draft': [('readonly', False)]}),
            'period_id' : fields.many2one('hr.contract.period', 'Periodo', required=True, select=True, readonly=True, states={'draft': [('readonly', False)]}),
            'state' : fields.selection([('draft', 'Borrador'), ('requested', 'Esperando Aprobacion'), ('approved', 'Aprobado'), ('deny', 'Denegado'), ('validate', 'Validado'), ('no_validate', 'No Validado')], 'Estado', select=True, readonly=True),
            'observacion':fields.text('Observaciones', readonly=True, states={'requested': [('readonly', False)]}),
            'procesado':fields.boolean('Procesado', required=False, readonly=True),
            'jefe_uid':fields.related('employee_id', 'coach_id', 'user_id', string='JefeUID', type='many2one', relation='res.users'),
            'no_descontar':fields.boolean('No descontar', readonly=True, states={'approved': [('readonly', False)]}),
            'descontar':fields.boolean('Descontar', readonly=True, states={'approved': [('readonly', False)]}),
            'payroll_id':fields.many2one('hr.payroll', 'Rol de Pagos'),
            'user_id':fields.integer('UserID'),
    		}
    
    _defaults = {
    	'requested_date': lambda * a: time.strftime('%Y-%m-%d'),
        'state': lambda * a: 'draft',
        'employee_id':_get_employee,
        #'departament_id': lambda self, cr, uid, *a: self.pool.get('hr.employee').read(cr, 1, self._get_employee(cr, uid), ['department_id'])['department_id'],
        'departament_id': _get_department,
        'user_id':lambda self, cr, uid, *a: uid,
    	}

    _constraints = [
        (_not_negative, "La cantidad de horas de permiso no pueden ser negativas.", ['number_of_days']),
        (_validar_horas_segun_tipo, "La cantidad de horas de permiso no pueden ser cero.", ['number_of_days'])
        ]
hr_permission()
