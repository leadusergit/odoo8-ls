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

from datetime import datetime, date
from openerp.osv import osv, fields
from payroll_tools import EDAD_ANIO

class hr_family_item(osv.osv):
    _name = "hr.family.item"
    _description = "Items employee family"
    
    def _get_age(self, cr, uid, ids, field_name, args, context):
        return dict((obj.id, EDAD_ANIO(obj.birth)) for obj in self.browse(cr, uid, ids))
    
    _columns = {
          'name' : fields.char('Nombre Completo', size=50),
          'age_util' : fields.integer("Edad para Utilidades"),
          'age': fields.function(_get_age, method=True, string="Edad", type="integer"),
          'birth' : fields.date('Fecha de Nacimiento', required=True),
          'parentezco' : fields.selection((('padre', 'Padres'), ('hermano', 'Hermanos'), ('hb_wife', 'Conyugue'), ('son', 'Hijo(a)'), ('otro', 'Otro')), 'Parentesco'),
          'asegurado' : fields.boolean('Asegurado'),
          'employee_id' : fields.many2one('hr.employee', 'Empleado', required=True),
          'discapacidad' : fields.boolean('Discapacidad'),
          'fnt_nombre_empleado': fields.related('employee_id', 'name', string='Empleado', store=True, type='char', size=60, readonly=True),
          'fnt_direccion_empleado' : fields.related('employee_id', 'address', string='Direccion Empl.', store=True, type='char', size=60, readonly=True),
          'fnt_cedula_empleado' : fields.related('employee_id', 'identification_id', string='Cedula Empl.', store=True, type='char', size=12, readonly=True),
          'phone': fields.char('Teléfono', size=32, readonly=False),
          'address': fields.char('Dirección', size=255, readonly=False),
          'state':fields.char('Estado', size=12),
          'otro':fields.char('Otro Parentesco', size=32),
          }
    
    _defaults = {
           'age' : lambda * a: 0,
           'state':lambda * a: 'active',
           }
    
    def onchange_birth(self, cr, uid, ids, birth):
        v = {}
        result = {}
        if birth:
            fecha_n = datetime.strptime(birth, "%Y-%m-%d")
            if fecha_n <= datetime.today():
                today = date.today().strftime("%Y-%m-%d")
                now = today.split('-')
                birth = birth.split('-')
                datenow = date(int(now[0]), int(now[1]), int(now[2]))
                datebirth = date(int(birth[0]), int(birth[1]), int(birth[2]))
                delta = datenow - datebirth
                age = delta.days / 365
            else:
                result['value'] = {'birth':""}
                result['warning'] = {'title' : 'Error', 'message':'La fecha de nacimiento no puede ser mayor a la actual'}
                return result
    
hr_family_item()