# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution.
#    Account module for basic payroll in Ecuador.
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

from openerp.osv import fields, osv
from string import index
import re

class hr_payroll(osv.osv):
    _inherit = 'hr.payroll'
    _columns = {
        'account_move_id': fields.many2one('account.move', 'Movimiento Contable', readonly=True),
        'account_move_provisions_id': fields.many2one('account.move', 'Movimiento contable de las provisiones', readonly=True),
        'analitic_move_id': fields.many2one('account.analytic.line', 'Cuenta Analitica', readonly=True),
        'pay_move_id': fields.many2one('account.move', 'Movimiento contable del pago', readonly=True),
        'state' : fields.selection([('draft', 'Borrador'),
                                    ('calculated', 'Calculado'),
                                    ('paid', 'Pagado'),
                                    ('validate', 'Validado')], 'Estado', readonly=True),
    }

    def _obtener_cuenta(self, cr, income_adm, payroll):
        res = {}
        if income_adm.debit_account:
            res['id'] = income_adm.debit_account.id
            res['nombre'] = income_adm.debit_account.name
            return res
        elif income_adm.income_account_ids:
            employee = payroll.employee_id
            employee_category = payroll.employee_id.category_id
            if not employee_category:
                raise osv.except_osv("Error", 'El empleado ' + employee.name + ' no tiene configurado una categoria en su ficha! ')
            infos = income_adm.income_account_ids
            for info in infos:
                category = info.category_id
                if category.id == employee_category.id:
                    if info.debit_account_id:
                        res['id'] = info.debit_account_id.id
                        res['nombre'] = info.debit_account_id.name
                        return res
                    else:
                        raise osv.except_osv("Error", 'El departamento ' + category.name + ' no tiene configurado una cuenta para el ingreso ' + income.name)
                elif employee_category and employee_category.parent_id.id == category.id:
                    if info.debit_account_id:
                        res['id'] = info.debit_account_id.id
                        res['nombre'] = info.debit_account_id.name
                        return res
                    else:
                        raise osv.except_osv("Error", 'El departamento ' + category.name + ' no tiene configurado una cuenta para el ingreso ' + income.name)   
        elif income_adm.credit_account:
            res['id'] = income_adm.credit_account.id
            res['nombre'] = income_adm.credit_account.name
            res['tipo'] = 'credit'
            return res
        else:
            raise osv.except_osv("Error", 'El ingreso ' + income_adm.name + ' no tiene configurado ninguna cuenta contable ')
            
    def validar_registro(self, cr, uid, ids, context=None):
        """Change states in income, expense, and payroll, then asociate account properties """
        context = context or {}
        context['write_vals'] = {}
        try:
            diario_id = self.pool.get('ir.model.data')._get_id(cr, uid, 'hr_nomina_account', 'nomina_journal')
            diario_id = self.pool.get('ir.model.data').read(cr, uid, diario_id, ['res_id'])['res_id']
        except ValueError:
            raise osv.except_osv("Error Contable", u'No existe el diario de nómina, cargue nuevamente el módulo contable de la nómina.')
        account_move_line_obj = self.pool.get('account.move.line')
        account_valuation = self.pool['hr.employee.category'].account_valuation
        for this in self.browse(cr, uid, ids):
            if this.total < 0:
                raise osv.except_osv("Error de Uso", "No se pueden validar Roles con valores negativos a pagar.")
            texto = 'Rol '
            category = bool(this.employee_id.category_ids) and this.employee_id.category_ids[0]
            cuenta = account_valuation(cr, uid, category, this.employee_id.credit_account)
            if not cuenta:
                raise osv.except_osv("Error contable", u'No se encuentra configurada la cuenta principal de pagos de nómina, verifique la sección de contabilidad en la ficha del empleado.')
            account_period_data = self.transformar_contract_period_to_account_period(cr, uid, this.period_id.id)
            fecha_asiento = account_period_data['date_stop']
            vals = {'ref': texto + account_period_data['name'] + ' ' + this.employee_id.identification_id,
                    'journal_id': diario_id,
                    'date': fecha_asiento,
                    'period_id': account_period_data['id'],
                    'tipo_comprobante': 'ComproDiario',
                    'nro_comp': texto + this.employee_id.identification_id}
            account_move_id = self.pool.get('account.move').create(cr, uid, vals)        
            debit = credit = 0
            vals.update({'move_id': account_move_id,
                         'employee_id': this.employee_id.id,
                         'type_hr': 'payrol'})
            for expense in this.expenses_ids:
                if not expense.expense_type_id.credit_account:
                    raise osv.except_osv('Error contable', u'No se encuentra configurado las cuentas contables del egreso "%s".'%expense.expense_type_id.name)
                vals.update({'name': expense.expense_type_id.credit_account.name,
                             'account_id': account_valuation(cr, uid, category, expense.expense_type_id.credit_account).id,
                             'analytic_account_id': self._get_analitic_account(cr, uid, this, expense.expense_type_id.credit_account.id),
                             'credit': round(expense.value, 2),
                             'debit': 0.0})
                account_move_line_obj.create(cr, uid, vals)
                credit += expense.value or 0.00                                
            for income in this.incomes_ids:
                res = self._obtener_cuenta(cr, income.adm_id, this)
                vals.update({'name': res['nombre'],
                             'account_id': account_valuation(cr, uid, category, income.adm_id.debit_account).id,
                             'analytic_account_id': self._get_analitic_account(cr, uid, this, res['id']),
                             'credit': 0.0,
                             'debit': round(income.value, 2) or 0.0})
                account_move_line_obj.create(cr, uid, vals)
                credit += res.has_key('tipo') and income.value or 0.00
                debit += not res.has_key('tipo') and income.value or 0.00
            
            res = debit - credit
            res = abs(res)
            
            vals.update({'name': '[' + str(cuenta.id) + ']' + cuenta.name,
                         'account_id': cuenta.id,
                         'analytic_account_id': self._get_analitic_account(cr, uid, this, cuenta.id),
                         'credit': round(res, 2),
                         'debit': 0.00})
            ids_move_line = account_move_line_obj.create(cr, uid, vals)
            vals_account = vals.copy()
            vals.update({'ref': 'Provi ' + account_period_data['name'] + ' ' + this.employee_id.identification_id,
                         'nro_comp': texto + this.employee_id.identification_id})
            account_move_id_provisions = self.pool.get('account.move').create(cr, uid, vals)
            types_provisions_ids = self._get_provision_ids(cr, uid, this.id)
            types_provisions = self.pool.get('hr.provision.type').browse(cr, uid, types_provisions_ids)
            for type_provision in types_provisions:
                value = this.provisiones_id[0][type_provision.field_name.name]
                if value:
                    if not type_provision.debit_account_id:
                        raise osv.except_osv('Error contable', u'La provisión "%s" no posee una cuenta contable de débito asociada a ella.'%type_provision.name)
                    if not type_provision.credit_account_id:
                        raise osv.except_osv('Error contable', u'La provisión "%s" no posee una cuenta contable de crédito asociada a ella.'%type_provision.name)
                    vals.update({'name': type_provision.credit_account_id.name,
                                 'account_id': account_valuation(cr, uid, category, type_provision.credit_account_id).id,
                                 'analytic_account_id': self._get_analitic_account(cr, uid, this, type_provision.credit_account_id.id),
                                 'move_id': account_move_id_provisions,
                                 'credit': round(value, 2),
                                 'debit': 0.0})
                    account_move_line_obj.create(cr, uid, vals)
                    vals.update({'name': type_provision.debit_account_id.name,
                                 'account_id': account_valuation(cr, uid, category, type_provision.debit_account_id).id,
                                 'analytic_account_id': self._get_analitic_account(cr, uid, this, type_provision.debit_account_id.id),
                                 'credit': 0.0,
                                 'debit': round(value, 2),})
                    account_move_line_obj.create(cr, uid, vals)
            self.pool.get('account.move').post(cr, uid, [account_move_id, account_move_id_provisions])
            context['write_vals'][this.id] = {'account_move_id': account_move_id, 'account_move_provisions_id': account_move_id_provisions}
        return super(hr_payroll, self).validar_registro(cr, uid, ids, context)
    
    def _get_analitic_account(self, cr, uid, this, account_id):
        analytic_id = this.employee_id.department_id and this.employee_id.department_id.analytic_id
        if not analytic_id:
            raise osv.except_osv('Error', u'No se a configurado ningún centro de costos. Asegurese que %s pertenezca a un departamento y éste a su vez posee un centro de costos.'%this.employee_id.name)
        account_code = self.pool.get('account.account').read(cr, uid, account_id, ['code'])['code']
        return re.match('[4-6]\.', account_code) and analytic_id.id or False
        
    def transformar_contract_period_to_account_period(self, cr, uid, contract_period_id):
        hr_contract_period = self.pool.get('hr.contract.period')
        data_contract_period = hr_contract_period.read(cr, uid, contract_period_id)
        account_period = self.pool.get('account.period')
        account_period_id = account_period.search(cr, uid, [('name', '=', str(data_contract_period['name']))])
        if not account_period_id:
            raise osv.except_osv('Error contable', u'No existe el periodo contable %s.'%data_contract_period['name'])
        account_period_data = account_period.read(cr, uid, account_period_id)
        return  account_period_data[0]

    def from_validated_to(self, cr, uid, ids, context=None):
        context = context or {}
        write_vals = context.get('write_vals', {})
        account_move_obj = self.pool.get('account.move')
        for item in self.browse(cr, uid, ids):
            write_vals[item.id] = dict(write_vals.get(item.id, {}), **{'state': 'paid'})
            if not item.state == 'validate':
                raise osv.except_osv('ValidationError', 'El rol seleccionado no se encuentra en estado validado.')
            for move_id in [item.account_move_id, item.account_move_provisions_id]:
                if move_id:
                    account_move_obj.button_cancel(cr, uid, [move_id.id])
                    move_ids = [aux.id for aux in move_id.line_id if aux.analytic_account_id]
                    cr.execute('DELETE FROM account_analytic_line WHERE move_id=ANY(%s)', (move_ids,))
                    cr.execute('UPDATE account_move_line SET analytic_account_id=null WHERE id=ANY(%s)', (move_ids,))
                    account_move_obj.unlink(cr, uid, [move_id.id])
        context['write_vals'] = write_vals
        return super(hr_payroll, self).from_validated_to(cr, uid, ids, context)
    
    def action_pay(self, cr, uid, ids, context=None):
        context = context or {}
        context['active_ids'] = ids
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','wizard_pay_payroll_form_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.pay.payroll',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
    
    def from_paid_to(self, cr, uid, ids, context=None):
        payrolls = self.browse(cr, uid, ids)
        for payroll in payrolls:
            if payroll.pay_move_id:
                payroll.pay_move_id.button_cancel()
                payroll.pay_move_id.unlink()
            payroll.state = 'calculated'
            
hr_payroll()

class hr_account_move_line(osv.osv):
    _inherit = 'account.move.line' 
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Empleado'),
    }
hr_account_move_line()

class hr_expense_type(osv.osv):
    _inherit = 'hr.expense.type'
    _columns = {
        'debit_account': fields.many2one('account.account', 'Cuenta contable al debe'),
        'credit_account': fields.many2one('account.account', 'Cuenta contable al haber'),
    }
hr_expense_type()

class hr_expense(osv.osv):
    _inherit = "hr.expense"
    _columns = {
        'in_invoice':fields.many2one('account.invoice', 'Factura Compras', domain=[('type', '=', 'in_invoice'), ('state', 'in', ('open', 'paid')), ('tipo_factura', '=', 'invoice')]),
        'out_invoice':fields.many2one('account.invoice', 'Factura Ventas', domain=[('type', '=', 'out_invoice'), ('state', 'in', ('open', 'paid')), ('tipo_factura', '=', 'invoice')]),
    }
    
    def transformar_account_period_to_hr_period(self, account_period_id, cr, uid):
        #print "account_period_id", account_period_id
        account_period_obj = self.pool.get('account.period')
        hr_contract_period_obj = self.pool.get('hr.contract.period')
        account_period_data = account_period_obj.read(cr, uid, account_period_id)
        if not account_period_data:
             raise osv.except_osv("Error", 'Defina el Periodo en Gestion Financiera/Configuracion/Contabilidad Financiera/Periodos')
        hr_period_id = hr_contract_period_obj.search(cr, uid, [('name', '=', account_period_data['name'])])
        if not hr_period_id:
             raise osv.except_osv("Error", 'Defina el Periodo en Recursos Humanos/Configuracion/Administracion de Periodos/Año de Trabajo')
        return hr_period_id[0]

hr_expense()

class hr_provision_type(osv.osv):
    _inherit = 'hr.provision.type'
    _columns = {
        'debit_account_id': fields.many2one('account.account', 'Cuenta contable al Debe'),
        'credit_account_id': fields.many2one('account.account', 'Cuenta contable al Haber'),
    }
hr_provision_type()

class hr_adm_incomes(osv.osv):
    _inherit = "hr.adm.incomes"
    _columns = {
        'debit_account': fields.many2one('account.account', 'Cuenta contable al debe'),
        'credit_account': fields.many2one('account.account', 'Cuenta contable al haber'),
        'income_account_ids':fields.one2many('hr.adm.incomes.account', 'adm_income_id', 'Cuentas Contable', readonly=False),
    }
hr_adm_incomes()

class hr_adm_incomes_account(osv.osv):
    _name = "hr.adm.incomes.account"
    _description = "Administracion de la parte contable de los ingresos"
    
    _columns = {
        'name' : fields.char('Descripcion', size=128),
        'debit_account_id': fields.many2one('account.account', 'Cuenta contable al debe'),
        'credit_account_id': fields.many2one('account.account', 'Cuenta contable al haber'),
        'category_id':fields.many2one('hr.department', 'Departamento'),
        'adm_income_id':fields.many2one('hr.adm.incomes', 'Ingresos'),
    }
hr_adm_incomes_account()

class hr_employee_category(osv.osv):
    _inherit = "hr.employee.category"
    _columns = {
        'account_valuation_ids': fields.one2many('hr.employee.category.account.valuation', 'category_id', 'Mapeo de cuentas')
    }
    
    def account_valuation(self, cr, uid, category_id, account_id, context=None):
        if category_id:
            for map in category_id.account_valuation_ids:
                if map.account_id.id == account_id:
                    return map.account_dest_id
        return account_id
    
hr_employee_category()

class hr_employee_category_account_valuation(osv.osv):
    _name = 'hr.employee.category.account.valuation'
    _columns = {
        'category_id': fields.many2one('hr.employee.category', 'Categoría', required=True, ondelete='cascade'),
        'account_id': fields.many2one('account.account', 'Cuenta contable', required=True),
        'account_dest_id': fields.many2one('account.account', 'Cuenta contable destino', required=True),
        'company_id': fields.many2one('res.company', 'Compañia', required=True)
    }
    _defaults = {  
        'company_id': lambda self, cr, uid, ctx: self.pool['res.users'].browse(cr, uid, uid).company_id.id,  
    }
    _sql_constraints = [
        ('name_uniq', 'unique(category_id, account_id)', 'The Name of the OpenERPModel must be unique !'),      ]
hr_employee_category_account_valuation()