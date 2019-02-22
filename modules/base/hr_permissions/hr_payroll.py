# -*- encoding: utf-8 -*-
##############################################################################
#
#    HHRR Module
#    Copyright (C) 2009 GnuThink Software  All Rights Reserved
#    Fixed all funtionality Atikasoft Cia Ltda
#    info@atikasoft.com.ec
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

from openerp.osv import fields, osv
from openerp.addons.hr_nomina import payroll_tools
from datetime import datetime

class hr_payroll(osv.osv):
    _inherit = 'hr.payroll'
    _columns = {
          'permission_ids':fields.one2many('hr.permission', 'payroll_id', 'Permisos'),
    }
hr_payroll()

class hr_expense(osv.osv):
    _inherit = "hr.expense"

    meses = [('enero', 'Enero'), ('febrero', 'Febrero'), ('marzo', 'Marzo'), ('abril', 'Abril'),
           ('mayo', 'Mayo'), ('junio', 'Junio'), ('julio', 'Julio'), ('agosto', 'Agosto'),
           ('septiembre', 'Septiembre'), ('octubre', 'Octubre'), ('noviembre', 'Noviembre'), ('diciembre', 'Diciembre')]
    
    def calcular_subsidio_iess(self, cr, uid, payroll_id):
        permissions_ids = self.pool.get('hr.permission').search(cr, uid, [('employee_id', '=', payroll_id.employee_id.id), ('permission_type', '=', 'disease'), ('state', '=', 'validate')])
        value = 0.0
        if permissions_ids:
            permissions = self.pool.get('hr.permission').read(cr, uid, permissions_ids)
            
            for permission in permissions:
                
                fecha_inicio_permiso = permission['permission_date']
                fecha_fin_permiso = permission['permission_date']
                fecha_inicio_periodo = payroll_id.period_id.date_start
                fecha_fin_periodo = payroll_id.period_id.date_stop
                    
                periodo_contenido = (fecha_inicio_periodo, fecha_fin_periodo)
                periodo_contenedor = (fecha_inicio_permiso, fecha_fin_permiso)
                    
                dias_intersecados = payroll_tools.OBTIENE_DIAS_PERMISO_ENFERMEDAD(periodo_contenido, periodo_contenedor, permission['number_of_days'])
                #print 'subsidio enfermedad ', dias_intersecados
                if dias_intersecados > 0:
                    contract = self.pool.get('hr.contract').read(cr, uid, payroll_id.contract_id.id)
                    horas_iess = contract['working_hours_per_day'] * dias_intersecados
                    #print 'horas iess ', horas_iess
                    #print 'costo hora ', contract['costo_hora'] 
                    value = horas_iess * contract['costo_hora'] * 0.75
                    self.pool.get('hr.permission').write(cr, uid, permissions_ids, {'payroll_id': payroll_id.id})
            
        return round(value, 2)
    
        
    def calcular_subsidio_iess_maternidad(self, cr, uid, payroll_id):
        value = 0
        permissions_ids = self.pool.get('hr.permission').search(cr, uid,
                                                                [('employee_id', '=', payroll_id.employee_id.id), 
                                                                 ('permission_type', '=', 'maternidad'), 
                                                                 ('state', '=', 'approved')])
        if permissions_ids:
            permissions = self.pool.get('hr.permission').read(cr, uid, permissions_ids)
            for permission in permissions:
                
                fecha_inicio_permiso = permission['permission_date']
                fecha_fin_permiso = permission['permission_date_to']
                fecha_inicio_periodo = payroll_id.period_id.date_start
                fecha_fin_periodo = payroll_id.period_id.date_stop
                
                periodo_contenido = (fecha_inicio_periodo, fecha_fin_periodo)
                periodo_contenedor = (fecha_inicio_permiso, fecha_fin_permiso)                
                
                dias_intersecados = payroll_tools.DIAS_PERIODOS_INTERSECAN(periodo_contenido, periodo_contenedor)
                                
                if dias_intersecados > 0:
                    contract = self.pool.get('hr.contract').read(cr, uid, payroll_id.contract_id.id)
                    horas_iess = contract['working_hours_per_day'] * dias_intersecados
                    
                    diff = payroll_tools.PERIODOS(contract['date_start'], payroll_id.period_id.date_start)
                    # a partir de 12 meses de aportaciones al iess se calcula con el 75%
                    if len(diff) > 12:
                        value = horas_iess * contract['costo_hora'] * 0.75
                    else:
                        value = 0 #sueldo total
            
        return round(value,2)
    
    
    def calcular_subsidio_licencia_sin_sueldo(self, cr, uid, payroll_id):
        value = 0
        permissions_ids = self.pool.get('hr.permission').search(cr, uid,
                                                                [('employee_id', '=', payroll_id.employee_id.id), 
                                                                 ('permission_type', '=', 'licencia_sin_sueldo'), 
                                                                 ('state', '=', 'approved')])
        
        if permissions_ids:
            permissions = self.pool.get('hr.permission').read(cr, uid, permissions_ids)
            for permission in permissions:
                
                fecha_inicio_permiso = permission['permission_date']
                fecha_fin_permiso = permission['permission_date_to']
                fecha_inicio_periodo = payroll_id.period_id.date_start
                fecha_fin_periodo = payroll_id.period_id.date_stop
                
                periodo_contenido = (fecha_inicio_periodo, fecha_fin_periodo)
                periodo_contenedor = (fecha_inicio_permiso, fecha_fin_permiso)                               
                
                dias_intersecados = payroll_tools.DIAS_PERIODOS_INTERSECAN(periodo_contenido, periodo_contenedor)           
                           
                if dias_intersecados > 0:
                    contract = self.pool.get('hr.contract').read(cr, uid, payroll_id.contract_id.id)
                    horas_iess = contract['working_hours_per_day'] * dias_intersecados
                    value = horas_iess * contract['costo_hora']  #sueldo total
            
        return round(value)
        
    
    def calcular_subsidio_enfermedad(self, cr, uid, payroll_id):
        value = 0
        permissions_ids = self.pool.get('hr.permission').search(cr, uid,
                                                                [('employee_id', '=', payroll_id.employee_id.id), 
                                                                 ('permission_type', '=', 'enfermedad'), 
                                                                 ('state', '=', 'approved')])
        if permissions_ids:
            permissions = self.pool.get('hr.permission').read(cr, uid, permissions_ids)
            for permission in permissions:
                fecha_inicio_permiso = permission['permission_date']
                fecha_fin_permiso = permission['permission_date_to']
                fecha_inicio_periodo = payroll_id.period_id.date_start
                fecha_fin_periodo = payroll_id.period_id.date_stop
                
                periodo_contenido = (fecha_inicio_periodo, fecha_fin_periodo)
                periodo_contenedor = (fecha_inicio_permiso, fecha_fin_permiso)
                
                dias_intersecados = payroll_tools.DIAS_PERIODOS_INTERSECAN(periodo_contenido, periodo_contenedor)

                if dias_intersecados > 0:
                    contract = self.pool.get('hr.contract').read(cr, uid, payroll_id.contract_id.id)
                    
                    meses_trabajo = payroll_tools.PERIODOS(contract['date_start'], payroll_id.period_id.date_start)
                    # a partir de 6 meses de aportaciones al iess se calcula con el 75%
                    #se le paga a partir del 4 dia el 75%
                    value = 0
                    if dias_intersecados > 3 and len(meses_trabajo) > 6:
                        value = (contract['working_hours_per_day'] * (dias_intersecados-3) * 0.75 * contract['costo_hora'])
                    else:
                        value = 0

        return round(value,2)
        
    def calcular_subsidio_iess_asumido(self, cr, uid, payroll_id, **args):
        value = total = 0.0
        if not args.has_key('base_iess'):
            return self.calcular_subsidio_iess_asumido
        
        #calculo de ingreso por licencia sin sueldo
        value = self.calcular_subsidio_licencia_sin_sueldo(cr, uid, payroll_id)
        if value:
            total += value * 0.0945
        #------------------------------------ #calculo de ingreso por enfermedad
        #-------- value = self.calcular_subsidio_enfermedad(cr, uid, payroll_id)
        #------------------------------------------------------------- if value:
            #------------------------------------------- total += value * 0.0945
        #------------------------------------ #calculo de ingreso por maternidad
        #--- value = self.calcular_subsidio_iess_maternidad(cr, uid, payroll_id)
        #------------------------------------------------------------- if value:
            #------------------------------------------- total += value * 0.0945
            
        return total
    
    def calcular_permisos_particulares(self, cr, uid, res, **args):
        
        """Obtiene el valor de permisos particulares desde las solicitudes de permisos aprobadas"""
        
        valor_hora = res.contract_id.costo_hora
        valor_hora_ind = valor_hora * 0.1
        period_id = res.period_id.id
        employee_id = res.employee_id.id
        horas_trabajadas = res.num_dias * res.contract_id.working_hours_per_day
        value = 0
        numero_horas = 0
        
        permission_obj = self.pool.get('hr.permission')
        
        permission_ids = permission_obj.search(cr, uid, [('employee_id', '=', employee_id), ('period_id', '=', period_id), ('state', '=', 'validate'), ('permission_type', '=', 'private'), ('descontar', '=', True)])
        if permission_ids:
            permission_data = permission_obj.read(cr, uid, permission_ids, ['number_of_days'])
            for permission_data_line in permission_data:
                numero_horas += permission_data_line['number_of_days']
            # value = numero_horas * valor_hora
            args['horas_trabajadas'] = horas_trabajadas - numero_horas
            value = numero_horas * valor_hora_ind
            # Actualizar los permission_id con el rol_id
            permission_obj.write(cr, uid, permission_ids, {'payroll_id':res['id']})
        return round(value, 2)

hr_expense()
