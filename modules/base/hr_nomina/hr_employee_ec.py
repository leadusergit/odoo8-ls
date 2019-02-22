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
import time, openerp.modules as addons
from openerp.osv import osv, fields
from payroll_tools import *

class hr_notification_mail_settings(osv.osv):
    _name = 'hr.notification.mail.settings'
    _description = 'Cliente SMTP que usa y los empleados a notificar'
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.has_key('default') and vals['default']:
            notifications_ids = self.search(cr, uid, [])
            map(lambda x: notifications_ids.remove(x), ids)
            self.write(cr, uid, notifications_ids, {'default': False})
        res = super(hr_notification_mail_settings, self).write(cr, uid, ids, vals, context)
        return res
    
    _columns = {
        'employees_ids': fields.many2many('hr.employee', 'notification_employee_rel', 'notification_id', 'employee_id',
                                          'Empleados a notificar', domain=[('work_email', '!=', False)]),
        'subject': fields.char('Asunto', size=500),
        'default': fields.boolean('Activo')
    }
hr_notification_mail_settings()

class hr_employee_ec(osv.osv):
    _inherit = "hr.employee"
    
    def _get_latest_contract(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        obj_contract = self.pool.get('hr.contract')
        for emp in self.browse(cr, uid, ids, context=context):
            contract_ids = obj_contract.search(cr, uid, [('employee_id', '=', emp.id),
                                                         ('state', 'in', ['vigente','por_caducar'])], order='date_start', context=context)
            res[emp.id] = contract_ids and contract_ids[-1] or False
        return res
    
    def _compute_14(self, cr, uid, ids, field_name, arg, context):
        sql = "SELECT sueldo_basico FROM hr_contract WHERE employee_id = %s" % ids[0]
        cr.execute(sql)
        res = cr.fetchall()
        val = 0.0
        if res:
            val = res[0][0]
        return {ids[0] : val}
    
    def _metodo_ingreso(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for employee_id in ids:
            dias_vacacion = 0            
            contrato = self.pool.get('hr.contract')
            contract_ids_val = contrato.search(cr, uid, [('employee_id', '=', employee_id)])
            contracts_val = contrato.read(cr, uid, contract_ids_val)
            for contract_val in contracts_val:
                if contract_val['state'] in ('vigente', 'por_caducar'):
                    res[employee_id] = contract_val['date_start']
                    break
        return res
    
    def _metodo_salida(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for employee_id in ids:
            dias_vacacion = 0            
            contrato = self.pool.get('hr.contract')
            contract_ids_val = contrato.search(cr, uid, [('employee_id', '=', employee_id)])
            contracts_val = contrato.read(cr, uid, contract_ids_val)                
            for contract_val in contracts_val:
                if contract_val['state'] in ('vigente', 'por_caducar'):
                    res[employee_id] = contract_val['date_end']
                    break
        return res
    
    def _metodo_tipo_contr(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for employee_id in ids:
            contrato = self.pool.get('hr.contract')
            contract_ids_val = contrato.search(cr, uid, [('employee_id', '=', employee_id)])
            contracts_val = contrato.read(cr, uid, contract_ids_val)
            for contract_val in contracts_val:
                #if contract_val['state'] in ('vigente', 'por_caducar'):
                    res[employee_id] = contract_val['name']
                    break
        return res

    def _metodo_num_cuenta(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for id in self.browse(cr, uid, ids):
            if id.bank_account_id:
               res[id.id] = id.bank_account_id.acc_number
            else:
               res[id.id] = '' 
        return res
    
    def _metodo_tip_cuenta(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for id in self.browse(cr, uid, ids):
            if id.bank_account_id:
               res[id.id] = id.bank_account_id.acc_type
            else:
               res[id.id] = '' 
        return res
    
    def _metodo_nom_banco(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for id in self.browse(cr, uid, ids):
            if id.bank_account_id:
               res[id.id] = id.bank_account_id.bank_name
            else:
               res[id.id] = '' 
        return res
    
    def change_contract(self, cr, uid, contract_ids, context):
        employee = {}
        for contract in self.browse(cr, uid, contract_ids):
            employee[contract.employee_id.id] = False
        return employee.keys()
    
    _columns = {
        'contract_id':fields.function(_get_latest_contract, method=True, string='Contrato', type='many2one', relation="hr.contract", help='Latest valid contract of the employee'),
#         'bank_account_id' : fields.many2one('hr.employee.bank', 'Cta Bancaria'),
        'dias_tomados' : fields.integer('Dias Tomados', readonly=True),
        'cargas_ids' : fields.one2many("hr.family.item", 'employee_id', "Familia"),
        'tipo' : fields.selection((('admin', 'Jefatura'), ('oper', 'Otros')), "Tipo Empleado"),
        'check_25' : fields.boolean('Administrativo 25%', help="Activar este campo cuando sea un caso especial de Administrativos con 25%"),
        #: Tomado de http://es.wikipedia.org/wiki/Grupo_sangu%C3%ADneo
        'tiposangre' : fields.selection([('ap', 'A+'), ('an', 'A-'), ('bp', 'B+'), ('bn', 'B-'), ('abp', 'AB+'), ('abn', 'AB-'), ('op', 'O+'), ('on', 'O-')], 'Tipo de Sangre'),
        'address' : fields.char('Calle1', size=150),
        'tipoid' : fields.selection((('c', 'Cedula'), ('p', 'Pasaporte')), "Tipo ID"),
        'total_13' : fields.float("Total Decimo 3", digits=(8, 2)),
        'total_14' : fields.function(_compute_14, method=True, string="Total Decimo 4", store=True, type="float"),
        'maintain_reserve_funds' : fields.boolean('Ahorra Fondos de Reserva(IESS)', help="Marque este campo cuando el empleado desee ahorrar el valor de Fondo de Reserva"),
        'departments_ids': fields.one2many('hr.history.department', 'employee_id', 'Departamentos', readonly=True),
        # LO NUEVO
        'jefe_compras_id': fields.many2one('hr.employee', 'Aprobacion Compras'),
        'subalteros_compras_ids': fields.one2many('hr.employee', 'jefe_compras_id', 'Subalternos Compras'),
        'discapacidad': fields.boolean('Discapacidad', help='Seleccionar si el empleado posee algun tipo de Discapacidad'),
        'modo_pago': fields.selection([('transferencia', 'Transferencia'), ('cheque', 'Cheque')], 'Modo de Pago'),
        'pago_provisiones': fields.boolean('Cobra Provisiones', help="Seleccionar si el empleado cobra las provisiones (no acumula)"),
        'state_emp':fields.selection([('active', 'Activo'), ('inactive', 'Inactivo')], 'Estado', required=True),
        'address_numero':fields.char('Número', size=10),
        'addres_calle2':fields.char('Calle2', size=150),
        'state_id': fields.many2one("res.country.state", 'Provincia', domain="[('country_id','=',nationality_id)]"),
        'nationality_id': fields.many2one('res.country', 'Country'),
        'parroquia':fields.char('Parroquia', size=100),
        'canton':fields.char('Canton', size=100),
        'barrio':fields.char('Barrio', size=100),
        'telefono1':fields.char('Teléfono1', size=100),
        'telefono2':fields.char('Teléfono2', size=100),
        'celular':fields.char('Celular', size=100),
        'nivel':fields.integer('Nivel'),
        'incomes_ids' : fields.many2many('hr.adm.incomes', 'employess_to_income_adm', 'employees_id', 'incomes_id', 'Ingresos',
                                         domain=[('type', '=', 'static_value')]),
        'photo': fields.binary('Photo'),
        'fecha_inic':fields.function(_metodo_ingreso, method=True, string='Fecha Inicio', type='date',
                                     store={'hr.employee': (lambda self, cr, uid, ids, ctx: ids, [], 10),
                                            'hr.contract': (change_contract, ['employee_id', 'date_start'], 10)}),
        'fecha_sali':fields.function(_metodo_salida, method=True, string='Fecha Salida', type='date',
                                     store={'hr.employee': (lambda self, cr, uid, ids, ctx: ids, [], 10),
                                            'hr.contract': (change_contract, ['employee_id', 'date_start'], 10)}),
        'fnt_tipo_contrato':fields.function(_metodo_tipo_contr, method=True, string='Tipo Contrato', store=True, type='char' , size=50),
        'fnt_num_cuenta':fields.function(_metodo_num_cuenta, method=True, string='Numero de Cuenta', store=True, type='char', size=30),
        'fnt_tipo_cuenta':fields.function(_metodo_tip_cuenta, method=True, string='Tipo de Cuenta', store=True, type='char', size=30),
        'fnt_nombre_banco':fields.function(_metodo_nom_banco, method=True, string='Banco', store=True, type='char', size=30),
        
        'caso_emergencia': fields.char('Familiar Caso Emergencia', size=150),
        'parentes_emergencia': fields.char('Parentesco', size=150),
    }
    
    def _get_photo(self, cr, uid, context=None):
        path = addons.get_module_resource('hr_nomina', 'image', 'photo.png')
        return open(path, 'rb').read().encode('base64')
    
    _defaults = {
        'children' : lambda * a: 0,
        'company_id' : lambda self, cr, uid, context: self.pool.get('res.company')._company_default_get(cr, uid, 'hr.employee', context=context),
        'state_emp':lambda * a : 'active',
        'photo': _get_photo,
        'tipoid': lambda * a : 'c',
    }
    
#     def init(self, cr):
#         cr.execute("ALTER TABLE hr_employee DROP CONSTRAINT hr_employee_bank_account_id_fkey")
#         cr.execute("ALTER TABLE hr_employee ADD CONSTRAINT hr_employee_bank_account_id_fkey FOREIGN KEY (bank_account_id)"
#                    "    REFERENCES hr_employee_bank (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE SET NULL")
    
    def _check_department_id(self, cr, uid, ids, context=None):
        return True
   
    def _check_cedula(self, cr, uid, ids, context=None):
        this_record = self.browse(cr, uid, ids)
        if this_record[0].identification_id and this_record[0].tipoid == 'c':
            cedula = this_record[0].identification_id
            if len(cedula) == 10 and cedula.isdigit():
                string = ""
                resultado = 0
                for i in range (0, 10):
                    string += cedula[i] + " "
                lista = string.split()
                coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
                for j in range(0, len(coeficientes)):
                    valor = int(lista[j]) * coeficientes[j]
                    if valor >= 10:
                        str1 = str(valor)
                        suma = int(str1[0]) + int(str1[1])
                        resultado += suma
                    else:
                        resultado += int(lista[j]) * coeficientes[j]
                residuo = resultado % 10
                if residuo == 0:
                    verificador = 0
                else:
                    verificador = 10 - residuo
                if verificador == int(lista[9]):
                    return True
                else:
                    return False              
            else:
                return False
        return True
            
    _constraints = [
        (_check_cedula, 'La Cédula Introducida es Incorrecta', ['identification_id']),
        (_check_department_id, 'Error ! You cannot select a department for which the employee is the manager.', ['department_id']),
    ]

    _sql_constraints = [
        ('identification_id_uniq', 'unique(identification_id,passport_id)', 'Un Empleado esta ya registrado con esa cedula.'),
    ]
    
    def write(self, cr, user, ids, vals, context=None):
        sueldo = 0
        val_quincena_actual = 0
        historial = self.pool.get('hr.history.department')
        contract_obj = self.pool.get('hr.contract')
        tipo_contrato = '' 
        #Valores nuevos
        nombre_contrato = 'No Registrado'
        #Valores anteriores
        data = self.read(cr, user, ids, ['contract_ids', 'category_id', 'quincena', 'porcentaje_quincena', 'quincena_numero'])
        if not data:
            return 
        
        dic = data[0]
        if dic.has_key('contract_ids'):
            id_contract = dic['contract_ids']
            contracts_data = contract_obj.browse(cr, user, id_contract)
            for contract_data in contracts_data:
                if contract_data.state in ('vigente', 'por_caducar'):
                    tipo_contrato = contract_data.type_id.id
                    nombre_contrato = contract_data.type_id.name
                    sueldo = contract_data.wage
                    cargo = contract_data.job_id.id
                    nombre_cargo = contract_data.job_id.name

        if dic.has_key('category_id'):
            if dic['category_id']:
                category_id = dic['category_id'][0]
                categoria_nombre = dic['category_id'][1]
            else:
                categoria_nombre = ''
                category_id = 0
            
        if vals.has_key('category_id'):
            category_id_nuevo = vals['category_id']   
            if category_id_nuevo != category_id:
                category_obj = self.pool.get('hr.employee.category')
                category_nombre_nuevo = category_obj.read(cr, user, category_id_nuevo)
                vals_history = {'employee_id': ids[0], 'date': time.strftime('%Y-%m-%d'),
                                'tipo_novedad':'Cambio de Departamento', 'valor_nuevo':category_nombre_nuevo['name'],
                                'valor_anterior':categoria_nombre, 'sueldo':sueldo, 'tipo_contrato':nombre_contrato} 
                historial.create(cr, user, vals_history)
        super(hr_employee_ec, self).write(cr, user, ids, vals, context)
        return ids
    
    def onchange_parent(self, cr, uid, ids, parent_id, context=None):
        res = {}
        user_id = self.pool.get('hr.employee').read(cr, uid, parent_id, ['user_id'])['user_id']
        if not user_id:
            res['value'] = {'parent_id':""}
            res['warning'] = {'title': 'Error', 'message': 'El Empleado indicado no posee un usuario OpenERP'}
        return res

    def get_wage(self, cr, uid, payroll_id):
        '''METODO PARA EL INGRESO DE SUELDOS Y SALARIOS'''
        dias = DIAS_LABORADOS((payroll_id.contract_id.date_start, payroll_id.contract_id.date_end),
                              (payroll_id.period_id.date_start, payroll_id.period_id.date_stop), DIAS_PERIODO=None)
        return payroll_id.contract_id.wage * payroll_id.num_dias / dias['dias_periodo']
    
hr_employee_ec()

class hr_level(osv.osv):
    _name = 'hr.level'
    _description = 'Niveles de empleados'
    
    _columns = {
        'name':fields.char('Level', size=100),
        'description': fields.text('Description'),
        'categories_ids': fields.one2many('hr.employee.category', 'level_id', 'Categorias')
    }
hr_level()

class hr_employee_category(osv.osv):
    _inherit = "hr.employee.category"

    _columns = {
        'code' : fields.char('Cod. Centro de Utilidad', size=30, required=True),
        'level_id': fields.many2one('hr.level', "Nivel"),
    }
hr_employee_category()

class hr_history_department(osv.osv):
    _name = "hr.history.department"
    _description = "Historial de los departamentos por los que pasa un empleado"
    
    _columns = {'employee_id': fields.many2one('hr.employee', 'Empleado'),
                'date': fields.date('Fecha'),
                'tipo_novedad':fields.char('Novedad', size=64, required=False),
                'valor_anterior':fields.char('Valor Anterior', size=128, required=False),
                'valor_nuevo':fields.char('Valor Nuevo', size=128, required=True),
                'sueldo':fields.float('Valor Sueldo', required=True),
                'tipo_contrato':fields.char('Contrato', size=64, required=True),
                }
hr_history_department()