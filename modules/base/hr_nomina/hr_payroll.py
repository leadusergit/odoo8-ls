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
import time, logging, openerp.modules as addons
from openerp.osv import fields, osv
from openerp.tools import config, email_send
from mako.template import Template
from payroll_tools import *
from openerp.tools.safe_eval import safe_eval as eval
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class hr_payroll(osv.osv):
    _name = 'hr.payroll'
    _description = "Payroll Info"
    _order = 'id Desc'
    
    def dummy(self, cr, uid, ids, context=None):
        return True
    
    def compute_amounts(self, cr, uid, ids, fields_names, args, context):
        res = dict((id, {}) for id in ids)
        for obj in self.browse(cr, uid, ids):
            res[obj.id]['total_ingresos'] = round(sum(aux.value for aux in obj.incomes_ids), 2)
            res[obj.id]['total_egresos'] = round(sum(aux.value for aux in obj.expenses_ids), 2)
            res[obj.id]['total'] = round(res[obj.id]['total_ingresos'] - res[obj.id]['total_egresos'], 2)
        return res
    
    def _update_payroll(self, cr, uid, ids, context):
        cr.execute('SELECT DISTINCT(payroll_id) FROM ' + self._table + ' WHERE id=ANY(%s)', (ids,))
        return [aux[0] for aux in cr.fetchall()]

    _columns = {
          'num_dias' : fields.integer('Dias. Trabaj.', readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'name' : fields.char('Descripcion', size=50, readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'employee_id' : fields.many2one('hr.employee', 'Empleado', required=True, readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'contract_id' : fields.many2one('hr.contract', 'Contrato', required=True, readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'period_id' : fields.many2one('hr.contract.period', 'Periodo de Trabajo', required=True, readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'month' : fields.char('Mes', size=30, readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'create_uid' : fields.many2one('res.users', 'Creado por', readonly=True),
          'create_date' : fields.date('Fecha de Creacion', readonly=True),
          'provisiones_id' : fields.one2many('hr.provision', 'payroll_id', 'Provisiones', readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'expenses_ids' : fields.one2many('hr.expense', 'payroll_id', 'Rubros Egresos', readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'incomes_ids' : fields.one2many('hr.income', 'payroll_id', 'Rubros Ingresos', readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'total_ingresos' : fields.function(compute_amounts, method=True, string='Total Ingresos', type='float', digits=(16, 2), multi='amounts'),
          'total_egresos' : fields.function(compute_amounts, method=True, string='Total Egresos', type='float', digits=(16, 2), multi='amounts'),
          'total' : fields.function(compute_amounts, method=True, string='Total a Recibir', type='float', digits=(16, 2), multi='amounts',
                                    store={'hr.income': (_update_payroll, ['payroll_id', 'value'], 10),
                                           'hr.expense': (_update_payroll, ['payroll_id', 'value'], 10),
                                           _name: (lambda self, cr, uid, ids, ctx: ids, ['incomes_ids', 'expenses_ids'], 10)}),
          'state' : fields.selection([('draft', 'Borrador'), ('calculated', 'Calculado'), ('validate', 'Validado'), ], 'Estado', readonly=True),
          #LO NUEVO
          'previous_total': fields.float('Total Para el Fondo de Reserva', digits=(12, 2), readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'total_fondo': fields.float('Total Fondos de Reserva', digits=(16, 2), readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'forma_pago': fields.char('Forma Pago', size=32, select=1, readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'valor_sueldo':fields.float('Valor Sueldo', readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'total_ingresos_sin_fi':fields.float('TotalIngresosSinFI', digits=(16, 2), readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'dias_periodo':fields.integer('Dias Mes', readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'horas_trabajadas':fields.float('Horas Trabajadas', digits=(16, 2), help='Es el campo num_dia en horas', readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}),
          'employee': fields.related('employee_id', 'name', string="Empleado", store=True, type='char', size=250),
          'is_validated':fields.boolean('Es validado'),
          'company_id': fields.related('employee_id', 'company_id', type='many2one', relation='res.company',
                                       string='Compañia', store=True, readonly=True)
    }

    def _convertir_mes(self, cr, uid, context={}):
        """ Change id for mounth """
        mes = int(time.strftime('%m'))
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return meses[int(mes) - 1]
    
    _defaults = {
        'state' : lambda * a: 'draft',
        'month' : _convertir_mes,
        'is_validated': lambda * a:False,
    }
    _sql_constraints = [
        ('unique_con_per', 'unique(contract_id,period_id)', 'Solo Puede realizar un Pago por mes a cada empleado')
    ]
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['id', 'month', 'period_id'], context)
        res = []
        for record in reads:
            id = record['id']
            month = record['month']
            period = record['period_id'][1]
            name = month + ' - ' + period 
            res.append((record['id'], name))
        return res
        
    def create(self, cr, uid, vals, context=None):
        employee = self.pool.get('hr.employee').browse(cr, uid, vals['employee_id'])
        period = self.pool.get('hr.contract.period').browse(cr, uid, vals['period_id'])
        contract = self.pool.get('hr.contract').browse(cr, uid, vals['contract_id'])
    #-------------------Validación de la vigencia del contrato-------------------
        dias_trabajados = DIAS_LABORADOS((contract.date_start, contract.date_end), (period.date_start, period.date_stop), DIAS_PERIODO=None)['dias_laborados']
        if dias_trabajados <= 0 and not contract.type_id.parcial:
            raise osv.except_osv("Error", 'El contrato no posee vigencia en este periodo, por favor verificar las fechas de inicio y fin del contrato')
    #--------------------------------------------------------------------
        return super(hr_payroll, self).create(cr, uid, vals, context=context)
    
    def unlink(self, cr, uid, ids, context):
        roles = self.read(cr, uid, ids)
        if [aux for aux in roles if aux['state'] == 'validate']:
            raise osv.except_osv('Error de Uso!', 'No puede borrar roles Validados')        
        self.clear_info(cr, [aux['id'] for aux in roles])
        return super(hr_payroll, self).unlink(cr, uid, ids, context)

    def _get_incomes_ids(self, cr, uid, id):
        """Método para obtener los ingresos de acuerdo a otros módulos"""
        return self.pool.get('hr.adm.incomes').search(cr, uid, [], order='orden')
    
    def _get_expense_ids(self, cr, uid, id):
        """Método para obtener los egresos de acuerdo a otros módulos"""
        return self.pool.get('hr.expense.type').search(cr, uid, [], order='code')
    
    def _get_provision_ids(self, cr, uid, id):
        """Método para obtener las provisiones de acuerdo a otros módulos"""
        return self.pool.get('hr.provision.type').search(cr, uid, [])
    
    def clear_info(self, cr, ids):
        cr.execute('DELETE FROM hr_income WHERE payroll_id=ANY(%s) AND auto=True', (ids,))
        cr.execute('DELETE FROM hr_expense WHERE payroll_id=ANY(%s) AND auto=True', (ids,))
        cr.execute('DELETE FROM hr_provision WHERE payroll_id=ANY(%s)', (ids,))
    
    def load_info(self, cr, uid, ids, context={}):
        self.clear_info(cr, ids)
        class Expense(object):
            def __init__(self, model, ref, excluir):
                self.model = model
                self.ref = ref
                self.excluir = excluir
                
        for obj in self.browse(cr, uid, ids):
            base_iess = base_renta = base_fondos = excl_iess = excl_irenta = 0.0
            vals = {'contract_id': obj.contract_id.id,
                    'employee_id': obj.employee_id.id,
                    'payroll_id': obj.id,
                    'period_id': obj.period_id.id,
                    'auto': True}
            #===================================================================
            # INGRESOS
            incomes_model = self.pool.get('hr.income')
            ext_functions = {}
            for adm_id in self.pool.get('hr.adm.incomes').browse(cr, uid, self._get_incomes_ids(cr, uid, obj.id)):
                if adm_id.type == 'static_value':
                    income_ids = incomes_model.search(cr, uid, [('adm_id', '=', adm_id.id),
                                                                ('employee_id', '=', obj.employee_id.id),
                                                                ('contract_id', '=', obj.contract_id.id),
                                                                ('period_id', '=', obj.period_id.id),
                                                                ('payroll_id', '=', None),
                                                                ('auto', '=', False)])
                    if income_ids:
                        incomes_ids = incomes_model.read(cr, uid, income_ids, ['value'])
                        value = sum([aux['value'] for aux in incomes_ids])
                        incomes_model.write(cr, uid, income_ids, {'payroll_id': obj.id})
                    elif adm_id in obj.employee_id.incomes_ids:
                        value = adm_id.default_value
                        if value:
                            incomes_model.create(cr, uid, dict({'adm_id': adm_id.id,
                                                                'name': adm_id.payroll_label,
                                                                'value': round(max(value, 0.0), 2)}, **vals))
                    else:
                        continue
                elif adm_id.type == 'obtained_value':
                    model = self.pool.get(adm_id.method_id.object_id.model)
                    aux1 = adm_id.method_id.reference.find('(')
                    args = eval('dict(%s)' % adm_id.method_id.reference[aux1 + 1:-1], locals_dict=locals())
                    if hasattr(model, adm_id.method_id.reference[:aux1]):
                        value = getattr(model, adm_id.method_id.reference[:aux1])(cr, uid, obj, **args)
                        if callable(value):
                            ext_functions[adm_id] = (value, args)
                            continue
                        if value:
                            incomes_model.create(cr, uid, dict({'adm_id': adm_id.id,
                                                                'name': adm_id.payroll_label,
                                                                'value': round(max(value, 0.0), 2)}, **vals))
                base_iess += adm_id.aporte_iess and value or 0.0
                base_renta += adm_id.impuesto_renta and value or 0.0
                base_fondos += adm_id.fondo_reserva and value or 0.0
            for adm_id, function in ext_functions.iteritems():
                args = dict(base_fondos=base_fondos, base_renta=base_renta, base_iess=base_iess, **function[1])
                value = function[0](cr, uid, obj, **args)
                if value:
                    incomes_model.create(cr, uid, dict({'adm_id': adm_id.id,
                                                        'name': adm_id.payroll_label,
                                                        'value': round(max(value, 0.0), 2)}, **vals))
            #===================================================================
            # EGRESOS
            expense_model = self.pool.get('hr.expense')
            expense_model.write(cr, uid, expense_model.search(cr, uid, [('employee_id', '=', obj.employee_id.id),
                                                                        ('contract_id', '=', obj.contract_id.id),
                                                                        ('period_id', '=', obj.period_id.id),
                                                                        ('payroll_id', '=', None),
                                                                        ('auto', '=', False)]),
                                {'payroll_id': obj.id})
            ext_functions = {}
            ADM_EGRESOS = {
                   'FAINJ': Expense('hr.expense', 'calcular_faltas_injustificadas(value_hour_ind=0.25)', True),
                   'APIES': Expense('hr.expense', 'calcular_aporte_personal(base_iess=base_iess)', False),
                   'IMREN': Expense('hr.expense', 'calcular_impuesto_renta(base_renta=base_renta)', False),
                   'PEPAR': Expense('hr.expense', 'calcular_permisos_particulares()', False),
                   'ATR': Expense('hr.expense', 'calcular_atrasos(iess_ingresos=base_iess)', False),
                   'PVAC': Expense('hr.expense', 'calcular_permiso_vacaciones()', False),
                   'AQUI': Expense('hr.expense', 'calcular_anticipo_quincena()', False),
                   'LOAN': Expense('hr.expense', 'obtener_valor_prestamos()', False),
                   'LOEM': Expense('hr.expense', 'obtener_valor_prestamos()', False),
                   'ANSUE': Expense('hr.expense', 'obtener_valor_anticipo_sueldo()', False),
                   'SUBMA': Expense('hr.expense', 'calcular_subsidio_iess_maternidad()', False),
                   'SUBIE': Expense('hr.expense', 'calcular_subsidio_iess()', False),
                   'SUBLS': Expense('hr.expense', 'calcular_subsidio_licencia_sin_sueldo()', False),
                   'ENFER': Expense('hr.expense', 'calcular_subsidio_enfermedad()', False),
            }
            expense_ids = self._get_expense_ids(cr, uid, obj.id)
            for expense_id in self.pool.get('hr.expense.type').browse(cr, uid, expense_ids):
                if ADM_EGRESOS.has_key(expense_id.code):
                    model = self.pool.get(ADM_EGRESOS[expense_id.code].model)
                    aux1 = ADM_EGRESOS[expense_id.code].ref.find('(')
                    args = eval('dict(%s)' % ADM_EGRESOS[expense_id.code].ref[aux1 + 1:-1], locals_dict=locals())
                    if hasattr(model, ADM_EGRESOS[expense_id.code].ref[:aux1]):
                        value = getattr(model, ADM_EGRESOS[expense_id.code].ref[:aux1])(cr, uid, obj, **args)
                        if callable(value):
                            ext_functions[expense_id] = (value, args)
                            continue
                        if value:
                            expense_model.create(cr, uid, dict({'expense_type_id': expense_id.id,
                                                                'name': expense_id.name,
                                                                'value': round(max(value, 0.0), 2)}, **vals))
                        excl_iess += ADM_EGRESOS[expense_id.code].excluir and value or 0.0
                        excl_irenta += expense_id.impuesto_renta and value or 0.0
            for expense_id, function in ext_functions.iteritems():
                args = dict(excl_iess=excl_iess, excl_irenta=excl_irenta, **function[1])
                value = function[0](cr, uid, obj, **args)
                excl_irenta += expense_id.impuesto_renta and value or 0.0
                if value:
                    expense_model.create(cr, uid, dict({'expense_type_id': expense_id.id,
                                                        'name': expense_id.name,
                                                        'value': round(max(value, 0.0), 2)}, **vals))
            #===================================================================
            # PROVISIONES
            provision_ids = self._get_provision_ids(cr, uid, obj.id)
            values = self.pool.get('hr.provision').compute(obj, base_iess, base_fondos, base_renta)
            
            for provision in self.pool.get('hr.provision.type').browse(cr, uid, provision_ids):
                if ((not obj.employee_id.pago_provisiones and provision.field_name.name != 'fondo_reserva')
                    or (obj.employee_id.maintain_reserve_funds and provision.field_name.name == 'fondo_reserva')
                    or (provision.field_name.name not in ['decimo3ro', 'decimo4to', 'fondo_reserva'])):
                    vals[provision.field_name.name] = round(max(values[provision.field_name.name], 0.0), 2)
            self.pool.get('hr.provision').create(cr, uid, vals)
            #===================================================================
        return self.write(cr, uid, ids, {'state': 'calculated'})

    def send_email(self, cr, uid, ids, context):
        if not config.get('smtp_server'):
            _logger.warning('"smtp_server" needs to be set to send mails to users')
            return False
        if not config.get('email_from'):
            _logger.warning('"email_from" needs to be set to send welcome mails to users')
            return False
        template = addons.get_module_resource('hr_nomina', 'report', 'payroll.mako')
        template = Template(filename=template)
        for payroll in self.browse(cr, uid, ids):
            email = payroll.employee_id.work_email or (payroll.employee_id.user_id and payroll.employee_id.user_id.user_email)
            if not email:
                _logger.warning(u'%s no tiene configurado ningún email' % payroll.employee_id.name)
                continue
            names = dict(self.name_get(cr, uid, ids, context))
            if not email_send(email_from=config['email_from'], email_to=[email],
                              subject="Rol de pagos",
                              body=template.render(o=payroll, name=names[payroll.id].upper()),
                              subtype='html'):
                _logger.error(u'El mensaje para %s no ha sido enviado.' % payroll.employee_id.name)
                continue
            _logger.info(u'El mensaje para %s ha sido enviado con éxito.' % payroll.employee_id.name)
        return True
    
    def validar_registro(self, cr, uid, ids, context=None):
        context = context or {}
        for this in self.browse(cr, uid, ids):
            if this.total < 0:
                raise osv.except_osv("Error de Uso", "No se pueden validar Roles con valores negativos a pagar.")
            self.pool.get('hr.expense').write(cr, uid, [aux.id for aux in this.expenses_ids], {'state': 'procesado'})
            self.pool.get('hr.income').write(cr, uid, [aux.id for aux in this.incomes_ids], {'state': 'procesado'})
            write_vals = context.get('write_vals', {}).get(this.id, {})
            self.write(cr, uid, [this.id], dict({'state' : 'validate', 'is_validated':True}, **write_vals))
                    
        return True
    
    def onchange_contract(self, cr, uid, ids, period_id, employee_id):
        res = {'value':{}}
        if not employee_id:
            return res
        info_employee = self.pool.get('hr.employee').read(cr, uid, employee_id, ['state_emp'])
        contrac_ids = self.pool.get('hr.contract').search(cr, uid, [('employee_id', '=', employee_id), ('state', 'in', ('vigente', 'por_caducar'))])
        if contrac_ids:
            if len(contrac_ids) > 1:
                raise osv.except_osv("Datos", "El empleado tiene mas de un contrato en estado vigente. No se puede continuar con la generación'")
            res['value']['contract_id'] = contrac_ids[0]
        return res
    
    def onchange_period(self, cr, uid, ids, period_id, employee_id, contract_id):
        res = {'value': {'previous_total': 0.0, 'num_dias': 0}}
        if period_id and employee_id and contract_id:
            contract_id = self.pool.get('hr.contract').read(cr, uid, contract_id, ['date_start', 'date_end'])
            period_id = self.pool.get('hr.contract.period').read(cr, uid, period_id, ['date_start', 'date_stop'])
            res['value']['num_dias'] = DIAS_LABORADOS((contract_id['date_start'], contract_id['date_end']),
                                                      (period_id['date_start'], period_id['date_stop']), DIAS_PERIODO=None)['dias_laborados']
            previous_payroll = self.search(cr, uid, [('employee_id', '=', employee_id), ('contract_id', '=', contract_id['id']), ('period_id', '=', period_id['id'])])
            if previous_payroll:
                fondo_reserva = self.browse(cr, uid, previous_payroll[0]).total_fondo
                res['value']['previous_total'] = fondo_reserva
        return res
    
    def from_validated_to(self, cr, uid, ids, context=None):
        context = context or {}
        for item in self.browse(cr, uid, ids):
            if not item.state == 'validate':
                continue
            write_vals = context.get('write_vals', {}).get(item.id, {})
            if not write_vals.get('state'): write_vals['state'] = 'calculated'
            self.write(cr, uid, item.id , dict(**write_vals))
        return True
    
hr_payroll()

class hr_expense_type(osv.osv):
    _name = 'hr.expense.type'

    _columns = {
            'name': fields.char('Nombre', size=40),
            'description': fields.char('Descripcion', size=200),
            'code':fields.char('Codigo', size=5),
            'company_id': fields.many2one('res.company', 'Compañia', required=True),
            'impuesto_renta': fields.boolean('Deducción de impuesto a la renta', help='Marque si hay resta a la base imponible del impuesto a la renta'),
                    }
    _defaults = {  
        'company_id': lambda self, cr, uid, ctx: self.pool['res.users'].browse(cr, uid, uid).company_id.id  
    }
    _sql_constraints = [
            ('name_uniq', 'unique (name, company_id)', 'No puede haber dos tipos de egresos con el mismo nombre !'),
        ]
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update(dict.fromkeys(['debit_account', 'credit_account'], False))
        expense = self.read(cr, uid, id, ['name'])
        default['name'] = expense['name'] + ' (COPY)' 
        return super(hr_expense_type, self).copy(cr, uid, id, default, context)
    
hr_expense_type()

class hr_expense(osv.osv):
    _name = "hr.expense"
    _description = "Expenses for Employee"
    _columns = {
        'payroll_id' : fields.many2one('hr.payroll', 'Rol de Pagos', ondelete='set null'),
        'contract_id': fields.many2one('hr.contract', 'Contrato', required=True),
        'name' : fields.char('Descripcion', size=128),
        'expense_type_id' : fields.many2one('hr.expense.type', 'Tipo de Egreso', required=True),
        'value' : fields.float('Valor', digits=(16, 2), required=True),
        'employee_id' : fields.many2one('hr.employee', "Empleado", ondelete='cascade', required=True),
        'period_id' : fields.many2one('hr.contract.period', 'Periodo', help="Mes al que pertenece el Egreso", ondelete='restrict', required=True),
        'date' : fields.datetime('Fecha de Registro'),
        'res_partner':fields.many2one('res.partner', 'Proveedor', domain=[('active', '=', True), ('supplier', '=', True)]),
        'comment':fields.text('Comentario'),
        'auto': fields.boolean('Automático', help='Este campo estará marcado si el egreso es generado automaticamente por el sistema'),
        'company_id': fields.related('employee_id', 'company_id', type='many2one', relation='res.company',
                                     string='Compañia', store=True, readonly=True)
    }
    _sql_constraints = [
        ('tipo_periodo', 'unique(employee_id,expense_type_id,period_id)', u'El cobro por período es único.'),
    ]
    _defaults = {
        'date' : lambda * a: time.strftime('%Y-%m-%d'),
        'auto': False
    }

    meses = [('enero', 'Enero'), ('febrero', 'Febrero'), ('marzo', 'Marzo'), ('abril', 'Abril'),
           ('mayo', 'Mayo'), ('junio', 'Junio'), ('julio', 'Julio'), ('agosto', 'Agosto'),
           ('septiembre', 'Septiembre'), ('octubre', 'Octubre'), ('noviembre', 'Noviembre'), ('diciembre', 'Diciembre')]
    
    def create(self, cr, uid, vals, context=None):
        if vals.has_key('res_partner'):
            if vals['res_partner']:
                partner_name = self.pool.get('res.partner').read(cr, uid, vals['res_partner'], ['name'])
                if vals.has_key('name'):
                    current_name = vals['name']
                else:
                    current_name = self.pool.get('hr.expense.type').read(cr, uid, vals['expense_type_id'], ['name'])
                vals['name'] = current_name['name'] + ' - ' + partner_name['name']
            else:
                current_name = self.pool.get('hr.expense.type').read(cr, uid, vals['expense_type_id'], ['name'])
                vals['name'] = current_name['name']
                  
        return super(hr_expense, self).create(cr, uid, vals, context=context)
        
    def write(self, cr, uid, ids, vals, context=None):
        if vals.has_key('res_partner') and vals['res_partner']:
            partner_name = self.pool.get('res.partner').read(cr, uid, vals['res_partner'], ['name'])
            current_name = self.read(cr, uid, ids, ['expense_type_id'])
            vals['name'] = current_name[0]['expense_type_id'][1] + ' - ' + partner_name['name'] 
        return super(hr_expense, self).write(cr, uid, ids, vals, context)
    
    def calcular_aporte_personal(self, cr, uid, payroll_id, **args):
        if not args.has_key('excl_iess'):
            return self.calcular_aporte_personal
        if args.has_key('base_iess'):
            return round((args['base_iess'] - args['excl_iess']) * 0.0945, 2)
        return 0.0
    
    def onchange_expense_type(self, cr, uid, ids, expense_type_id):
        res = {'value': {'name': ''}}
        if expense_type_id:
            expense_type = self.pool.get('hr.expense.type').read(cr, uid, expense_type_id, ['name'])
            res['value']['name'] = expense_type['name']
        return res
    
    def onchange_employee_id(self, cr, uid, ids, employee_id):
        return self.pool.get('hr.payroll').onchange_contract(cr, uid, ids, None, employee_id)
    
hr_expense()

class hr_method(osv.osv):
    _name = "hr.method"
    _description = "Administracion de Metodos"
    _columns = {
        'name': fields.char('Nombre', 128),
        'code': fields.char('Código', 50),
        'object_id': fields.many2one('ir.model', 'Objeto', help="Objeto en cual disparar el metodo", domain="[('model','like', 'hr')]"),
        'reference': fields.char('Referencia', size=256, help='Referencia al nombre del Metodo en el Objeto seleccionado. ej: get_wage'),
    }
    _sql_constraints = [('unique_code', 'unique(code)', 'El codigo debe ser unico')]

hr_method()

class hr_provision_type(osv.osv):
    _name = 'hr.provision.type'
    _columns = {
        'name': fields.char('Nombre', size=50),
        'description': fields.text('Descripción'),
        'field_name': fields.many2one('ir.model.fields', 'Campo', help="Nombre del campo en el objeto hr.provision al que hace referencia"),
        'company_id': fields.many2one('res.company', 'Compañia', required=True)
    }
    _defaults = {  
        'company_id': lambda self, cr, uid, ctx: self.pool['res.users'].browse(cr, uid, uid).company_id.id  
    }
    _sql_constraints = [
        ('name_field_uniq', 'unique(name, field_name, company_id)', 'Registro Duplicado !')
    ]
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update(dict.fromkeys(['debit_account_id', 'credit_account_id'], False))
        income = self.read(cr, uid, id, ['name'])
        default['name'] = income['name'] + (' (COPY)')
        return super(hr_provision_type, self).copy(cr, uid, id, default, context)
    
hr_provision_type()

class hr_formula(osv.osv):
    _name = "hr.formula"
    _description = "Administracion de Formulas"

    _columns = {
        'name' : fields.char('Nombre', size=128, required=True),
        'code' : fields.char('Codigo', size=128, required=True),
        'resume' : fields.char('Resumen', size=256, required=True),
        'resume' : fields.char('Resumen', size=256, required=True, help='La fórmula se contruye de los Metodos e Ingresos agregados y usando cualquiera de los operadores (+, -, *, /).'),
        'method_ids' : fields.many2many('hr.method', 'formula_method_rel', 'formula_id', 'method_id', 'Metodos'),
    }
hr_formula()

class hr_adm_incomes(osv.osv):
    _name = "hr.adm.incomes"
    _description = "Administracion de Ingresos al Rol de Pagos"
    _columns = {
        'name' : fields.char('Descripcion', size=128, required=True),
        'code' : fields.char('Codigo', size=128, required=True),
        'payroll_label': fields.char('Etiqueta en el Rol de Pagos', size=128, required=True),
        'aporte_iess': fields.boolean('Aportes Iess'),
        'impuesto_renta': fields.boolean('Impuesto Renta'),
        'fondo_reserva': fields.boolean('Fondo de Reserva', help="Seleccione si es su valor se toma en cuenta para el fondo de reserva"),
        'date_proportional': fields.boolean('Proporcional segun Fecha Ingreso o Salida'),
        'type' : fields.selection([
                ('proportional', 'Proporcional'),
                ('static_value', 'Valor Fijo'),
                ('obtained_value', 'Valor Obtenido'),
                ('variable_bonus', 'Bonificacion Variable'),
        ], 'Tipo', required=True, size=128, help="Tipo de valor."),
        'default_value': fields.float('Valor Por Defecto', digits=(8, 2)),
        'done_percent': fields.float('Porcentaje de Cumplimiento', digits=(8, 2)),
        'obtain_method' : fields.selection([
                ('none', '-'),
                ('method_func', 'Metodo'),
                ('func_formula', 'Funcion'),
        ], 'Forma de obtener', size=32, help="Forma de obtener el valor del Ingreso."),
        'method_id': fields.many2one('hr.method', 'Nombre del Metodo'),
        'formula_id': fields.many2one('hr.formula', 'Formula'),
        'formula': fields.text('Formula'),
        'value': fields.float('Valor', digits=(8, 2)),
        'orden':fields.integer('Orden'),
        'provision':fields.boolean('Provision'),
        'provision_id':fields.many2one('hr.provision.type', 'Provision Relacionada'),
        'company_id': fields.many2one('res.company', string='Compañia', required=True)
    }
    _defaults = {
        'type' : lambda * a: 'static_value',
        'default_value' : lambda * a : 0.0,
        'done_percent' : lambda * a : 0.0,
        'obtain_method' : lambda * a : 'none',
        'value' : lambda * a : 0.0,
        'company_id': lambda self, cr, uid, ctx: self.pool['res.users'].browse(cr, uid, uid).company_id.id
    }
    _sql_constraints = [
        ('unique_code', 'unique(code,company_id)', 'El codigo debe ser unico')
    ]
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update(dict.fromkeys(['debit_account', 'credit_account'], False))
        income = self.read(cr, uid, id, ['code'])
        default['code'] = income['code'] + (' (COPY)')
        return super(hr_adm_incomes, self).copy(cr, uid, id, default, context)

    def get_formula_resume(self, cr, uid, ids, formula_id):
        if not formula_id:
            return {'value': {'formula':False}}
        obj = self.pool.get('hr.formula').browse(cr, uid, formula_id)
        v_formula = obj.resume
        return {'value': {'formula': v_formula}}

    def _run_method(self, cr, uid, model, func, args):
        '''
        Ejecutar un metodo dados el modelo, metodo y argumentos
        '''
        args = (args or []) and eval('args')
        m = self.pool.get(model)
        if m and hasattr(m, func):
            fn = getattr(m, func)
            val = fn(cr, uid, args)
            return val
        else:
            raise osv.except_osv("Error", 'El metodo que desea ejecutar no existe en este objeto')

    def _run_formula(self, cr, uid, fx, values):
        '''
        Parsear y retornar el valor de evaluar una formula
        :param fx: Formula a calcular.
        :param values: Diccionario de valores a parsear en la formula.
        '''
        import formulas
        self.fn = formulas.formula_parser()
        for key, variable in values.items():
            self.fn.variables[key] = variable;
        self.fn.formula = fx
        val = self.fn.evaluate()
        return val

    def get_value(self, cr, uid, id, args):
        '''
        Devuelve el valor del Ingreso por el método configurado
        :param employee_id: ID del Empleado.
        '''
        calc_val = 0.0
        income = self.browse(cr, uid, id)
        percentage = income.done_percent
        modelo = income.method_id.object_id.model
        metodo = income.method_id.reference
        # Retornar default_value si el valor es fijo
        if income.type == 'static_value':
            calc_val = income.default_value
        # rutina por si el valor es proporcional
        elif income.type == 'proportional':
            # Si la forma de obtener es por metodo
            if income.obtain_method == 'method_func':
                # print "Datos del metodo: modelo: {0}, metodo: {1}, argumentos: {2}.".format(modelo, metodo, employee_id)
                method_val = self._run_method(cr, uid, modelo, metodo, args)
                calc_val = eval('method_val*percentage/100')
             # en caso de ser por formula
            else:
                # rutinas para la formula
                calc_val = 0.0
        # si es valor obtenido
        elif income.type == 'obtained_value':
            # si es metodo
            if income.obtain_method == 'method_func':
                # correr en metodo con id del empleado como argumento
                # print "Datos del metodo: modelo: {0}, metodo: {1}, argumentos: {2}.".format(modelo, metodo, employee_id)
                calc_val = self._run_method(cr, uid, modelo, metodo, args)
            else:
                # si es por formula
                calc_val = 0.0
        # Si es bonificacon variable
        else:
            calc_val = 0.0
        # print "El valor obtenido  es:", calc_val
        return calc_val

hr_adm_incomes()

class hr_formula_inherit(osv.osv):
    _inherit = "hr.formula"

    _columns = {
        'adm_incomes_ids' : fields.many2many('hr.adm.incomes', 'formula_income_rel', 'formula_id', 'income_id', 'Ingresos'),
    }
hr_formula_inherit()

class hr_income(osv.osv):
    _name = "hr.income"
    _description = "Incomes for Employee"
    _columns = {
        'payroll_id' : fields.many2one('hr.payroll', 'Rol de Pagos'),
        'contract_id': fields.many2one('hr.contract', 'Contrato', required=True),
        'name' : fields.char('Description', size=50),
        'adm_id' : fields.many2one('hr.adm.incomes', 'Tipo de Ingreso', required=True),
        'value' : fields.float('Valor', digits=(12, 2), required=True),
        'employee_id' : fields.many2one('hr.employee', 'Empleado', required=True),
        'state' : fields.selection([('draft', 'No Procesado'), ('procesado', 'Procesado'), ('no_usado', 'No Usado')], 'Status', readonly=True),
        'period_id' : fields.many2one('hr.contract.period', 'Periodo', required=True, help="Mes al que pertenece el Ingreso"),
        'date' : fields.datetime('Fecha de Registro'),
        'auto': fields.boolean('Automático', help='Este campo estará marcado si el egreso es generado automaticamente por el sistema'),
        'company_id': fields.related('employee_id', 'company_id', type='many2one', relation='res.company',
                                     string='Compañia', store=True, readonly=True)
    }
    _defaults = {
        'state' : lambda * a: 'draft',
        'auto': False
    }
    _sql_constraints = [
        ('name', 'unique(name, payroll_id)', 'Ya se ha cargado la informacion de este rol !.'),
    ]

    def onchange_adm_id(self, cr, uid, ids, adm_id):
        res = dict(value={'value': False, 'name': False})
        if adm_id:
            adm_id = self.pool.get('hr.adm.incomes').read(cr, uid, adm_id, ['payroll_label', 'default_value'])
            res['value']['value'] = adm_id['default_value']
            res['value']['name'] = adm_id['payroll_label']
        return res
    
    def onchange_employee_id(self, cr, uid, ids, employee_id):
        return self.pool.get('hr.payroll').onchange_contract(cr, uid, ids, None, employee_id)

    def recalcular_valor_sueldo(self, cr, uid, res, payroll, value_fa_in):
        incomes_ids = self.search(cr, uid, [('payroll_id', '=', res['id']), ('name', 'ilike', 'Suel%')])
        income_data = self.read(cr, uid, incomes_ids, ['value'])
        new_value = income_data[0]['value'] - value_fa_in
        self.write(cr, uid, incomes_ids, {'value':new_value})
        res['total_ingresos'] = res['total_ingresos'] - value_fa_in  
        
hr_income()

class hr_provision(osv.osv):
    _name = 'hr.provision'
    _description = "Provisiones por Ley"
    _columns = {
        'payroll_id' : fields.many2one('hr.payroll', 'Rol de Pagos', ondelete='cascade'),
        'contrato_id' : fields.many2one('hr.contract', 'Contrato'),
        'employee_id' : fields.many2one('hr.employee', 'Empleado'),
        'decimo3ro' : fields.float('Decimo Tercero', digits=(16, 2)),
        'decimo4to' : fields.float('Decimo Cuarto', digits=(16, 2)),
        'vacaciones' : fields.float('Vacaciones', digits=(16, 2)),
        'fondo_reserva' : fields.float('Fondo de Reserva', digits=(16, 2)),
        'aporte_patronal' : fields.float('Aporte Patronal', digits=(16, 2)),
        'secap' : fields.float('Secap', digits=(16, 2)),
        'iece' : fields.float('IECE', digits=(16, 2)),
        'total': fields.function(lambda self, cr, uid, ids, *a: dict((o.id, sum([o.decimo3ro, o.decimo4to, o.vacaciones,
                                                                                 o.fondo_reserva, o.aporte_patronal,
                                                                                 o.secap, o.iece])) for o in self.browse(cr, uid, ids)),
                                 method=True, string='Total', type='float', digits=(16, 2),
                                 store={_name: (lambda self, cr, uid, ids, *ctx: ids, ['decimo3ro', 'decimo4to', 'vacaciones',
                                                                                       'fondo_reserva', 'aporte_patronal',
                                                                                       'secap', 'iece'], 10)}),
        'dias_vacaciones':fields.float('Dias Vacaciones', digits=(16, 2)),
    }
    _defaults = {
        'decimo3ro' : lambda * a : 0.0,
        'decimo4to' : lambda * a: 0.0,
        'vacaciones' : lambda * a: 0.0,
        'fondo_reserva' : lambda * a: 0.0,
        'secap' : lambda * a : 0.0,
        'iece' : lambda * a: 0.0,
        'total' : lambda * a : 0.0,
        'dias_vacaciones' : lambda * a : 0.0,
    }
    
    def _get_fondos_reserva(self, cr, uid, payroll_id, **args):
        if not payroll_id.employee_id.maintain_reserve_funds:
            if args.has_key('base_fondos'):
                return self.compute(payroll_id, base_fondos=args['base_fondos'])['fondo_reserva']
            return self._get_fondos_reserva
        return 0.0
    
    def _get_iece(self, cr, uid, payroll_id, **args):
        if payroll_id.employee_id.pago_provisiones:
            if args.has_key('base_iess'):
                return self.compute(payroll_id, base_iess=args['base_iess'])['iece']
            return self._get_decimo_tercero
        return 0.0
    
    def _get_secap(self, cr, uid, payroll_id, **args):
        if payroll_id.employee_id.pago_provisiones:
            if args.has_key('base_iess'):
                return self.compute(payroll_id, base_iess=args['base_iess'])['secap']
            return self._get_decimo_tercero
        return 0.0
    
    def _get_vacaciones(self, cr, uid, payroll_id, **args):
        if payroll_id.employee_id.pago_provisiones:
            return self.compute(payroll_id)['vacaciones']
        return 0.0
    
    def _get_decimo_cuarto(self, cr, uid, payroll_id, **args):
        if payroll_id.employee_id.pago_provisiones:
            return self.compute(payroll_id)['decimo4to']
        return 0.0
    
    def _get_decimo_tercero(self, cr, uid, payroll_id, **args):
        if payroll_id.employee_id.pago_provisiones:
            if args.has_key('base_iess'):
                return self.compute(payroll_id, base_iess=args['base_iess'])['decimo3ro']
            return self._get_decimo_tercero
        return 0.0
    
    def compute(self, payroll_id, base_iess=0.0, base_fondos=0.0, base_renta=0.0):
        aux_days = sum([(DATE(contract.date_end) - DATE(contract.date_start)).days for contract in payroll_id.employee_id.contract_ids if contract.date_start < payroll_id.contract_id.date_start])
        contract_date = DATE(contract.date_start) - timedelta(days=aux_days)
        period_date = DATE(payroll_id.period_id.date_stop)
        diferencia = EDAD_ANIO(contract_date.strftime('%Y-%m-%d'), period_date.strftime('%Y-%m-%d'))
        proportion = 1 if diferencia >= 1 else 0
        if diferencia == 1 and contract_date.month == period_date.month:
            dias = DIAS_LABORADOS((period_date.strftime('%Y') + contract_date.strftime('-%m-%d'), None),
                                  (payroll_id.period_id.date_start, payroll_id.period_id.date_stop), DIAS_PERIODO=None)
            proportion = dias['dias_laborados'] / float(dias['dias_periodo'])

        diff = period_date - contract_date
        dias_mes = DATE(payroll_id.period_id.date_stop) - DATE(payroll_id.period_id.date_start)
        dias = min(15, (15.0/(dias_mes.days+1))*payroll_id.num_dias) + min(15, (round(diff.days / 365) - 5 if diff.days / 365 > 5 else 0))
        provision_dias_vacaciones = round(dias/12.0, 2)

        return {
            'decimo3ro': base_iess / 12.0,
            'decimo4to': payroll_id.period_id.fiscalyear_id.basic_salary / 12.0 / (dias_mes.days+1) * payroll_id.num_dias,
            'vacaciones': (base_iess / 30.0) * provision_dias_vacaciones,
            'fondo_reserva': proportion * base_fondos * 0.0833,
            'aporte_patronal': base_iess * 0.1115,
            'secap': base_iess * 0.005,
            'iece': base_iess * 0.005
        }
    
hr_provision()
