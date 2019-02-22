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
from openerp.addons.hr_nomina.payroll_tools import *
from openerp import api
import unicodedata

def elimina_tildes(s):
   return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

     
class res_company(osv.osv):
    
    _inherit = 'res.company'
    
    _columns = {                
        'pagos_base_30_dias':fields.boolean('Calculo Nomina(30 dias)',default= True,help="Si la empresa ejecuta el calculo de la nomina con base en 30 dias"),
        
    }
    
class hr_employee_ec(osv.osv):
    _inherit = "hr.employee"
    
    def _get_latest_contract(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        context = context or {}
        date = context.get('date') or time.strftime('%Y-%m-%d')
        period = self.pool.get('hr.contract.period').find(cr, uid, date, context, True)
        period = period[0] if period else False
        obj_contract = self.pool.get('hr.contract')
        for emp in self.browse(cr, uid, ids, context=context):

            cr.execute('select id from '
                       '(SELECT id, date_start FROM hr_contract where employee_id=%i and date_end is null '
                       'UNION SELECT id, date_start FROM hr_contract WHERE employee_id=%i and date_end is not null AND '
                       "(date_start, date_end) OVERLAPS ('%s' :: date, '%s' :: date)) as aux "
            'ORDER BY date_start desc'%(emp.id, emp.id, period.date_start, period.date_stop))

            aux = cr.fetchone()
            contract_id = aux[0] if aux else False
            res[emp.id] = contract_id

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
        'telefonos_emergencia': fields.char('Teléfonos en caso de emergencia'),
        'biometric_code': fields.char('Código de reloj biométrico'),
        'discapacidad_s': fields.selection([('own', u'Propia'), ('surrogate', u'Sustituto')], 'Discapacidad', help='Seleccionar si el empleado posee algun tipo de Discapacidad'),
        'porciento_discapacidad': fields.float('Porcentaje de discapacidad'),
        'carnet_conadis': fields.char('Carnet Conadis'),
        'tipo_discapacidad': fields.char('Tipo Discapacidad'),
        'tipo_sustituto':fields.selection([('c', u'cedula'), ('p', u'pasaporte'),('e', u'Ident¡ficacion Exterior')], 'Tipo Identificacion'),
        'indent_sustituto':fields.char('Nº CI'),
    }
    
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
    
    """def write(self, cr, user, ids, vals, context=None):
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
                    tipo_contrato = contract_data.sudo().type_id.id
                    nombre_contrato = contract_data.sudo().type_id.name
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
        return ids"""
    
    def onchange_parent(self, cr, uid, ids, parent_id, context=None):
        res = {}
        user_id = self.pool.get('hr.employee').read(cr, uid, parent_id, ['user_id'])['user_id']
        if not user_id:
            res['value'] = {'parent_id':""}
            res['warning'] = {'title': 'Error', 'message': 'El Empleado indicado no posee un usuario OpenERP'}
        return res

    def get_wage(self, cr, uid, payslip_id):
        '''METODO PARA EL INGRESO DE SUELDOS Y SALARIOS'''
        dias_periodo = 30 if payslip_id.employee_id.company_id.pagos_base_30_dias else None
        dias = DIAS_LABORADOS((payslip_id.contract_id.date_start, payslip_id.contract_id.date_end),
                              (payslip_id.period_id.date_start, payslip_id.period_id.date_stop), DIAS_PERIODO=dias_periodo)
        return payslip_id.contract_id.wage * payslip_id.num_dias / dias['dias_periodo']

    #Funcion para calcular ingresos por sueldo anuales
    @api.multi
    def get_salarios_anuales(self, fiscalyear_id):
        self = self.sudo()
        period_ids = self.env['account.period'].sudo().search([('fiscalyear_id', '=', fiscalyear_id.id)]).ids       
        print"period_ids sa=%s"%period_ids
        #obtenemos los ingresos
        """self.env.cr.execute('select sum(psi.amount)'
                               'from hr_payslip ps ,hr_payslip_input psi where ps.id= psi.payslip_id ' 
                               'and psi.expense_type_id is null '
                               'and psi.employee_id =%s '
                               'and ps.company_id=%s '
                               'and psi.period_id = ANY(%s)',(self.id,self.company_id.id,period_ids))"""
        
        self.env.cr.execute('select sum(psl.amount)'
                            'from hr_payslip ps,hr_payslip_line psl where ps.id= psl.slip_id ' 
                            'and psl.employee_id =%s '
                            'and psl.salary_rule_id in (27,42) '
                            'and psl.company_id=%s '
                            'and ps.period_id = ANY(%s)',(self.id,self.company_id.id,period_ids))
        value = self.env.cr.fetchone()
        print"value sa=%s"%value
        return value[0] if value and value[0] else 0.0

    #Funcion para calcular ingresos anuales sin el sueldo
    @api.multi
    def get_ingresos_anuales(self, fiscalyear_id):
        self = self.sudo()
        period_ids = self.env['account.period'].sudo().search([('fiscalyear_id', '=', fiscalyear_id.id)]).ids       
        print"period_ids ia=%s"%period_ids

        #obtenemos los ingresos
        self.env.cr.execute('select sum(psl.amount) '
                            'from hr_payslip ps,hr_payslip_line psl '
                            'where ps.id= psl.slip_id '
                            'and psl.code in (select code from hr_adm_incomes where impuesto_renta=True) '
                            'and psl.employee_id =%s ' 
                            'and ps.company_id=%s '
                            'and ps.period_id = ANY(%s)',(self.id,self.company_id.id,period_ids))

        value = self.env.cr.fetchone()
        print"value ia=%s"%value
        return value[0] if value and value[0] else 0.0

    #Funcion para calcular decimo tercer sueldo anual
    @api.multi
    def get_decimo_tercero_anual(self, fiscalyear_id):
        self = self.sudo()
        #obtenemos los ingresos
        decimo3 = 0.0
        payslip_line_ids = self.env['hr.payslip.line'].sudo().search([('employee_id', '=', self.id),('code', '=', 'PROV DTERCERO')]).ids
        print"payslip_line_ids=%s"%payslip_line_ids
        period_ids = self.env['account.period'].sudo().search([('fiscalyear_id', '=', fiscalyear_id.id)]).ids       
        print"period_ids dta=%s"%period_ids
        # value = sum([dt.amount for dt in payslip_line_ids if dt.slip_id.period_id.id in period_ids])
        
        #codido ='PROV DTERCERO'        
        self.env.cr.execute('select sum(psl.amount)'
                            'from hr_payslip ps,hr_payslip_line psl '
                            'where ps.id= psl.slip_id '
                            'and psl.employee_id=%s '
                            'and psl.id= ANY (%s) and ps.period_id = ANY (%s)',(self.id,payslip_line_ids,period_ids))

        value = self.env.cr.fetchone()
        decimo3 = value[0] if value and value[0] else 0.0
        print"decimo3=%s"%decimo3
        """self.env.cr.execute('SELECT sum(hp.decimo3ro) FROM hr_provision hp '
                       ' JOIN hr_payroll rol ON rol.id = hp.payroll_id '
                       ' WHERE rol.company_id=%s AND rol.period_id = ANY (%s) '
                       ' AND rol.state = ANY (%s) AND hp.employee_id = %s ', (self.env.user.company_id.id, fiscalyear_id.period_ids.ids, ['paid', 'validate'], self.id))

        value = self.env.cr.fetchone()
        decimo3 += value[0] if value and value[0] else 0.0"""
        return decimo3

    #Funcion para calcular decimo cuarto sueldo anual
    @api.multi
    def get_decimo_cuarto_anual(self, fiscalyear_id):
        self = self.sudo()
        #obtenemos los ingresos
        decimo4to = 0.0
        payslip_line_ids = self.env['hr.payslip.line'].sudo().search([('employee_id', '=', self.id),('code', '=', 'PROV DCUARTO')]).ids
        print"payslip_line_ids dca=%s"%payslip_line_ids
        period_ids = self.env['account.period'].sudo().search([('fiscalyear_id', '=', fiscalyear_id.id)]).ids       
        print"period_ids dca=%s"%period_ids
        
        #value = sum([dt.amount for dc in payslip_line_ids if dc.slip_id.period_id.id in period_ids])

        #codido='PROV DCUARTO' 
        self.env.cr.execute('select sum(psl.amount)'
                            'from hr_payslip ps,hr_payslip_line psl '
                            'where ps.id= psl.slip_id '
                            'and psl.employee_id=%s '
                            'and psl.id= ANY (%s) and ps.period_id = ANY (%s)',(self.id,payslip_line_ids,period_ids))

        value = self.env.cr.fetchone()
        decimo4to = value[0] if value and value[0] else 0.0
        print"decimo4to=%s"%decimo4to
        """self.env.cr.execute('SELECT sum(hp.decimo4to) FROM hr_provision hp '
                       ' JOIN hr_payroll rol ON rol.id = hp.payroll_id '
                       ' WHERE rol.company_id=%s AND rol.period_id = ANY (%s) '
                       ' AND rol.state = ANY (%s) AND hp.employee_id = %s ', (self.env.user.company_id.id, fiscalyear_id.period_ids.ids, ['paid', 'validate'], self.id))

        value = self.env.cr.fetchone()
        
        decimo4to += value[0] if value and value[0] else 0.0"""
        return decimo4to

    #funcion para calcular el ultimo valor de utilidad que recibio
    """@api.multi
    def get_ultima_utilidad(self, fiscalyear_id):
        self = self.sudo()
        res = 0.0
        data = self.env['hr.employee.utility'].search(
            [
                ('utility_payment_id.company_id', '=', self.env.user.company_id.id),
                ('employee_id', '=', self.id),
                ('utility_payment_id.fiscalyear_id', '=', fiscalyear_id.id),
                ('state', '=', 'paid')
            ],
            order='create_date desc', limit=1
        )
        return data.total_a_recibir if data else 0.0"""

    #Funcion para calcular ingresos por sueldo anuales
    @api.multi
    def get_fondos_reserva_anuales(self, fiscalyear_id):
        self = self.sudo()
        
        payslip_line_ids = self.env['hr.payslip.line'].sudo().search([('employee_id', '=', self.id),('code', '=', 'PROV FOND RESERV')]).ids
        print"payslip_line_ids fra=%s"%payslip_line_ids
        period_ids = self.env['account.period'].sudo().search([('fiscalyear_id', '=', fiscalyear_id.id)]).ids       
        print"period_ids fra=%s"%period_ids
        
        #value = sum([dt.amount for fr in payslip_line_ids if fr.slip_id.period_id.id in period_ids])
        #codido='PROV FOND RESERV' 
        #obtenemos los ingresos
        self.env.cr.execute('select sum(psl.amount)'
                            'from hr_payslip ps,hr_payslip_line psl '
                            'where ps.id= psl.slip_id '
                            'and psl.employee_id=%s '
                            'and psl.id= ANY (%s) and ps.period_id = ANY (%s)',(self.id,payslip_line_ids,period_ids))

                            
        value = self.env.cr.fetchone()
        print"value-FR=%s"%value
        res = value[0] if value and value[0] else 0.0
        
        
        """self.env.cr.execute('SELECT sum(hp.fondo_reserva) FROM hr_provision hp '
                       ' JOIN hr_payroll rol ON rol.id = hp.payroll_id '
                       ' WHERE rol.company_id=%s AND rol.period_id = ANY (%s) '
                       ' AND rol.state = ANY (%s) AND hp.employee_id = %s ', (self.env.user.company_id.id, fiscalyear_id.period_ids.ids, ['paid', 'validate'], self.id))

        value = self.env.cr.fetchone()
        res += value[0] if value and value[0] else 0.0"""
        return res


    #aporte personal anual
    def apoPerIess(self, fiscalyear_id):
        self = self.sudo()
         
        payslip_line_ids = self.env['hr.payslip.line'].sudo().search([('employee_id', '=', self.id),('salary_rule_id', '=', 26)]).ids       
        print"payslip_line_ids api=%s"%payslip_line_ids
        if not payslip_line_ids:
           payslip_line_ids = self.env['hr.payslip.line'].sudo().search([('employee_id', '=', self.id),('salary_rule_id', '=', 63)]).ids       

        
        period_ids = self.env['account.period'].sudo().search([('fiscalyear_id', '=', fiscalyear_id.id)]).ids       
        print"period_ids apia=%s"%period_ids
        
        #value = sum([dt.amount for apersonal in payslip_line_ids if apersonal.slip_id.period_id.id in period_ids])
        #codido='IESSPERSONAL 11.45' 
        
        #obtenemos los APIES
        self.env.cr.execute('select sum(psl.amount)'
                            'from hr_payslip ps,hr_payslip_line psl '
                            'where ps.id= psl.slip_id '
                            'and psl.employee_id=%s '
                            'and psl.id= ANY (%s) and ps.period_id = ANY (%s)',(self.id,payslip_line_ids,period_ids))

        value = self.env.cr.fetchone()
        print"value API=%s"%value
        return value[0] if value and value[0] else 0.0

    #gastos personales
    @api.multi
    def get_gastos_personales(self, fiscalyear_id):
        self = self.sudo()
        self.env.cr.execute('SELECT housing, education, food, clothing, health ,arte FROM hr_employee_personal_expenses e '
                            'WHERE e.fiscalyear_id = %s AND e.employee_id = %s AND e.state = %s limit 1 ', (fiscalyear_id.id, self.id, 'validated'))

        value = self.env.cr.fetchone()
        return {
            'housing': value[0] if value and value[0] else 0.0,
            'education': value[1] if value and value[1] else 0.0,
            'food': value[2] if value and value[2] else 0.0,
            'clothing': value[3] if value and value[3] else 0.0,
            'health': value[4] if value and value[4] else 0.0,
            'arte': value[4] if value and value[4] else 0.0,
            #'disability': value[5] if value and value[5] else 0.0
        }

    def get_tax_amount(self, fiscalyear_id):
        pe_env = self.env['hr.employee.personal.expenses']
        tax = pe_env.get_tax_id(fiscalyear_id, self.baseImponible(fiscalyear_id))
        values = pe_env.get_table_amounts(tax, self.baseImponible(fiscalyear_id), fiscalyear_id)
        return values['tax_amount']

    def getTotalIngresos(self, fiscalyear_id, fiscalyear_before):
        self = self.sudo()
        return self.get_salarios_anuales(fiscalyear_id) + self.get_ingresos_anuales(fiscalyear_id) #+ self.get_ultima_utilidad(fiscalyear_before)

    def baseImponible(self, fiscalyear_id):
        self = self.sudo()
        fiscalyear = self.env['hr.fiscalyear'].search([('date_start', '<', fiscalyear_id.date_start)],
                                                      order='date_start desc', limit=1)
        expense = self.env['hr.employee.personal.expenses'].search([('employee_id', '=', self.id), ('fiscalyear_id', '=', fiscalyear_id.id)], limit=1)
        base = self.getTotalIngresos(fiscalyear_id, fiscalyear) + self.getIngresosOtroEmpleador(fiscalyear_id) - (self.aporPerIessConOtrosEmpls(fiscalyear_id) + self.apoPerIess(fiscalyear_id)) - (expense.expenses_amount if expense else 0)
        print"base imponible=%s"%base 
        return base if base > 0 else 0

    def getEmployeeNombre(self):
        self = self.sudo()
        res = {'lastname': '', 'fisrtname': ''}
        if self.name:
            nombresUnicode = elimina_tildes(self.name)
            nombres = nombresUnicode.split(' ')
            if len(nombres) <= 2:
                res['lastname'] = nombres[0]
                res['firstname'] = nombres[1] if len(nombres) > 1 else nombres[0]
            else:
                res['lastname'] = nombres[0]+' '+nombres[1] if len(nombres)>1 else nombres[0]
                res['firstname'] = nombres[2]+' '+nombres[3] if len(nombres) > 3 else (nombres[2] if len(nombres) > 2 else '')
        return res

    def getIngresosOtroEmpleador(self, fiscalyear_id):
        self = self.sudo()
        self.env.cr.execute('SELECT ingresos as income FROM hr_employee_expenses_adjustments '
                            'WHERE employee_id = %s AND company_id != %s '
                            'AND fiscalyear_id = %s limit 1 ', (self.id, self.company_id.id, fiscalyear_id.id))
        value = self.env.cr.fetchone()
        res = value[0] if value and value[0] else 0.0

        """self.env.cr.execute('SELECT sum(hi.value) FROM hr_income hi '
                            'JOIN hr_adm_incomes hai ON hai.id = hi.adm_id '
                            'WHERE hi.company_id != %s AND hi.period_id = ANY (%s)'
                            'AND hi.employee_id = %s ', (self.env.user.company_id.id, fiscalyear_id.period_ids.ids,self.id))
        value = self.env.cr.fetchone()
        res += value[0] if value and value[0] else 0.0"""
        return res

    def valorRetenidoOtroEmpleador(self, fiscalyear_id):
        ir_cobrado = 0.0
        self = self.sudo()
        #obtenemos los ingresos
        """self.env.cr.execute('SELECT sum(e.value) FROM hr_expense e '
                       ' JOIN hr_expense_type t ON t.id = e.expense_type_id '
                       ' JOIN hr_payroll p ON p.id = e.payroll_id '
                       ' WHERE e.company_id!=%s AND e.period_id = ANY (%s) AND t.code = %s '
                       ' AND p.state = ANY (%s) AND e.employee_id = %s ', (self.env.user.company_id.id, fiscalyear_id.period_ids.ids, 'IMREN', ['paid', 'validate'], self.id))

        value = self.env.cr.fetchone()
        ir_cobrado = value[0] if value and value[0] else 0.0"""
        #sumo los ajustes de los gastos personales
        self.env.cr.execute('SELECT gasto_recaudado FROM hr_employee_expenses_adjustments '
                            'WHERE employee_id = %s AND company_id != %s '
                            'AND fiscalyear_id = %s limit 1 ', (self.id, self.company_id.id, fiscalyear_id.id))
        value = self.env.cr.fetchone()
        ir_cobrado += value[0] if value and value[0] else 0.0
        return ir_cobrado

    def aporPerIessConOtrosEmpls(self, fiscalyear_id):
        self = self.sudo()
        #obtenemos los APIES
        """self.env.cr.execute('SELECT sum(e.value) FROM hr_expense e '
                       ' JOIN hr_expense_type t ON t.id = e.expense_type_id '
                       ' JOIN hr_payroll p ON p.id = e.payroll_id '
                       ' WHERE e.company_id!=%s AND e.period_id = ANY (%s) AND t.code = %s '
                       ' AND p.state = ANY (%s) AND e.employee_id = %s ', (self.env.user.company_id.id, fiscalyear_id.period_ids.ids, 'APIES', ['paid', 'validate'], self.id))

        value = self.env.cr.fetchone()
        res = value[0] if value and value[0] else 0.0"""

        self.env.cr.execute('SELECT aporte_iess_otro_empleador as apo_iess FROM hr_employee_expenses_adjustments '
                            ' WHERE employee_id = %s AND company_id != %s '
                            ' AND fiscalyear_id = %s limit 1 ', (self.id, self.company_id.id, fiscalyear_id.id))
        value = self.env.cr.fetchone()
        res = value[0] if value and value[0] else 0.0
        return res

    #impuesto a la renta retenido
    def valorRetenido(self, fiscalyear_id=None,  fecha_inicio=None, fecha_fin=None):
        if not fiscalyear_id:
            periods = self.env['hr.contract.period'].search([('date_start', '>=', fecha_inicio), ('date_stop', '<=', fecha_fin)])
        else:
            periods = fiscalyear_id.period_ids

        ir_cobrado = 0.0
        self = self.sudo()
        
        payslip_line_ids = self.env['hr.payslip.line'].sudo().search([('employee_id', '=', self.id),('code', '=', 'IMPRENTA')]).ids
        print"payslip_line_ids IMPR=%s"%payslip_line_ids
        period_ids = self.env['account.period'].sudo().search([('fiscalyear_id', '=', fiscalyear_id.id)]).ids
        print"period_ids vr=%s"%period_ids              
       # value = sum([dt.amount for ir in payslip_line_ids if ir.slip_id.period_id.id in period_ids])
        #codido='IMPRENTA'        
        self.env.cr.execute('select sum(psl.amount)'
                            'from hr_payslip ps,hr_payslip_line psl '
                            'where ps.id= psl.slip_id '
                            'and psl.employee_id=%s '
                            'and psl.id= ANY (%s) and ps.period_id = ANY (%s)',(self.id,payslip_line_ids,period_ids))
        
        value = self.env.cr.fetchone()
        ir_cobrado = value[0] if value and value[0] else 0.0
        #sumo los ajustes de los gastos personales
        self.env.cr.execute('SELECT gasto_recaudado FROM hr_employee_expenses_adjustments '
                            'WHERE employee_id = %s AND company_id = %s '
                            'AND fiscalyear_id = %s limit 1 ', (self.id, self.company_id.id, periods[0].fiscalyear_id.id))
        value = self.env.cr.fetchone()
        ir_cobrado += value[0] if value and value[0] else 0.0
        print"ir_cobrado rdep=%s"%ir_cobrado
        return ir_cobrado

hr_employee_ec()


class hr_employee_disability(osv.osv):
    _name = "hr.employee.disability"
    _description = "Tabla de rango de valores segun el porcentaje de discapacidad"

    _columns = {
        'min_value': fields.float('Mínimo', required=True),
        'max_value': fields.float('Maximo', required=True),
        'benefit': fields.float('Porcentaje del beneficio', required=True)
    }
