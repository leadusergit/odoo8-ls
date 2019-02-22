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
import base64
import StringIO
import csv
from time import strftime
from openerp.osv import osv,fields


class wizard_account_report_novedades(osv.osv_memory):
    """
    Reporte de Novedades
    """
    _name = 'wizard.account.report.novedades'
    _description = __doc__

    def generate_file(self, cr, uid, data, context):
        ##print"data:",data
        buf = StringIO.StringIO()
        writer = csv.writer(buf, delimiter=',')
        period_id = data['form']['period_id']
        #print "period_id:",period_id
        emp_id = data['form']['employee_id']
        #print "emp_id:",emp_id
        depa_id = data['form']['level_id']
        #print "depa_id:",depa_id
       
        consulta = []
        if period_id:
            criterio = ('period_id','=',period_id)
            #print"criterio_periodo:",criterio
            criterio = ('tipo','=','payrol')
            #print"criterio_tipo:",criterio
            consulta.append(criterio)
        if emp_id:
            criterio = ('employee_id','=',emp_id)
            #print"criterio_empleado:",criterio
            #criterio = ('tipo','=','payrol')
            ##print"criterio_tipo:",criterio
            consulta.append(criterio)
            
#        if emp_id:
#            criterio = ('tipo','=','payrol')
#            #print"criterio_tipo:",criterio
#            consulta.append(criterio)
        payrolls_ids = self.pool.get('hr.payroll').search(cr, uid,consulta )
        #print "payrolls_ids_consul:",payrolls_ids    
        payrolls = self.pool.get('hr.payroll').browse(cr, uid, payrolls_ids)
        ##print"payrolls:",payrolls
        # CAABECERA NOVEDADES
        cabecera = []
        cabeceraini = []
        cabeceraini = ['EMPLEADO', 'CEDULA', '# H-LABORADAS','ATRASOS', 'F. INJUST', 'PER-MED', 'CAL-DOM','PERMISOS','VACACIONES']
        writer.writerow(cabeceraini) 
        
        # DETALLES EMPLEADOS NOVEDADES        
        for payroll in payrolls:
            #print"payroll:",payroll.id
            filaemp = []
            if depa_id:
                emp_id = depa_id
                if payroll.employee_id.category_id.id != depa_id :
                   continue
            filaemp.append(payroll.employee_id.name.encode('UTF-8'))
            filaemp.append(payroll.employee_id.cedula)
            filaemp.append(payroll.horas_trabajadas or '0.0')
            
            for line in payroll.horas_resumen:
                #print"linefalta:",line.falta_inj
                filaemp.append(line.perm_particular or '0.0')
                filaemp.append(line.falta_inj or '0.0')
                filaemp.append(line.perm_medico or '0.0')
                filaemp.append(line.cal_dom or '0.0')
                
                for permisos in payroll.permission_ids:
                    #print"permisos:",permisos.number_of_days
                    if permisos.state == 'validate':
                        #print"paso_permisos"

                        filaemp.append(permisos.number_of_days or '0.0')
                    
                    for hollidays in payroll.holidays_request_ids:
                        #print"vacaciones:",hollidays.number_of_days
                        if hollidays.state == 'validate':
                            filaemp.append(hollidays.number_of_days or '0.0')
            writer.writerow(filaemp)   
               
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return {'data' : out, 'name' : 'novedades_empleados.csv', 'state': 'done'}

    _columns = {
        'period_id': fields.many2one('hr.contract.period', 'Periodo', required=True),
        'employee_id': fields.many2one('hr.employee', 'Empleado'),
        'level_id': fields.many2one('hr.employee.category', 'Departamento'),
        'data': fields.binary('Archivo Banco', readonly=True),
        'name': fields.char('Nombre', size=255, readonly=True),
        'state': fields.selection([('init', 'init'), ('done', 'done')]),
    }

    _defaults = {
        'state': lambda * a: 'init',
    }
wizard_account_report_novedades()