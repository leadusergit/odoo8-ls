# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    Author: Israel Paredes Reyes <israelparedesreyes@gmail.com>
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
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.addons.hr_nomina.payroll_tools import DATE

class hr_fiscalyear(models.Model):
    _inherit = 'hr.fiscalyear'
    #===========================================================================
    # Columns
    max_percentage = fields.Float('Porcentaje máximo de ingresos', required=True, default=0.5, digits=(8,4))
    basic_amount = fields.Float('Fracción básica', required=True)
    housing_max = fields.Float('Vivienda', required=True, default=0.325, digits=(8,4))
    housing_max_amount = fields.Float('Monto máximo de vivienda', compute='max_amount_housing')
    education_max = fields.Float('Educación', required=True, default=0.325, digits=(8,4))
    education_max_amount = fields.Float('Monto máximo de educación', compute='max_amount_education')
    food_max = fields.Float('Alimentación', required=True, default=0.325, digits=(8,4))
    food_max_amount = fields.Float('Monto máximo de alimentación', compute='max_amount_food')
    clothing_max = fields.Float('Vestimenta', required=True, default=0.325, digits=(8,4))
    clothing_max_amount = fields.Float('Monto máximo de vestimenta', compute='max_amount_clothing')
    health_max = fields.Float('Salud', required=True, default=1.3, digits=(8,4))
    health_max_amount = fields.Float('Monto máximo de salud', compute='max_amount_health')
    total_max = fields.Float('Total', required=True, default=1.3, digits=(8,4))
    total_max_amount = fields.Float('Monto máximo deducible', compute='max_amount_total')
    income_tax_table = fields.One2many('hr.income.tax.table', 'year_id', 'Tabla de impuesto a la renta')
    #===========================================================================
    
    @api.one
    @api.depends('basic_amount', 'housing_max')
    def max_amount_housing(self):
        self.housing_max_amount = self.basic_amount * self.housing_max
        
    @api.one
    @api.depends('basic_amount', 'education_max')
    def max_amount_education(self):
        self.education_max_amount = self.basic_amount * self.education_max
    
    @api.one
    @api.depends('basic_amount', 'food_max')
    def max_amount_food(self):
        self.food_max_amount = self.basic_amount * self.food_max
    
    @api.one
    @api.depends('basic_amount', 'clothing_max')
    def max_amount_clothing(self):
        self.clothing_max_amount = self.basic_amount * self.clothing_max
        
    @api.one
    @api.depends('basic_amount', 'health_max')
    def max_amount_health(self):
        self.health_max_amount = self.basic_amount * self.health_max
        
    @api.one
    @api.depends('basic_amount', 'total_max')
    def max_amount_total(self):
        self.total_max_amount = self.basic_amount * self.total_max
    
class hr_income_tax_table(models.Model):
    _name = 'hr.income.tax.table'
    _description = u'Tabla anual del impuesto a la renta'
    #===========================================================================
    # Columns
    year_id = fields.Many2one('hr.fiscalyear', 'Año de trabajo', required=True)
    base = fields.Float('Fracción básica')
    excess = fields.Float('Exceso hasta')
    base_tax = fields.Float('Impuesto fracción básica')
    excess_tax = fields.Float('Impuesto fracción excedente (%)')
    #===========================================================================
    
class hr_employee_personal_expenses(models.Model):
    _name = 'hr.employee.personal.expenses'
    _description = u'Gastos personales de los empleados'
    #===========================================================================
    # Columns
    name = fields.Char('Descripción', compute='_get_name')
    employee_id = fields.Many2one('hr.employee', 'Empleado', required=True, default=lambda self: self.env.user.employee_ids and self.env.user.employee_ids[0],
                                  states={'validated': [('readonly', True)]})
    contract_id = fields.Many2one('hr.contract', 'Contrato', required=True, states={'validated': [('readonly', True)]})
    fiscalyear_id = fields.Many2one('hr.fiscalyear', 'Año', required=True, states={'validated': [('readonly', True)]})
    type = fields.Selection([('proyected', 'Proyectado'), ('real', 'Real')], 'Tipo', required=False, states={'validated': [('readonly', True)]})
    other_incomes = fields.Float('Otros ingresos', states={'validated': [('readonly', True)]})
    housing = fields.Float('Vivienda', states={'validated': [('readonly', True)]})
    max_housing = fields.Float('Máximo de vivienda', related='fiscalyear_id.housing_max_amount')
    education = fields.Float('Educación', states={'validated': [('readonly', True)]})
    max_education = fields.Float('Máximo de vivienda', related='fiscalyear_id.education_max_amount')
    food = fields.Float('Alimentación', states={'validated': [('readonly', True)]})
    max_food = fields.Float('Máximo de vivienda', related='fiscalyear_id.food_max_amount')
    clothing = fields.Float('Vestimenta', states={'validated': [('readonly', True)]})
    max_clothing = fields.Float('Máximo de vivienda', related='fiscalyear_id.clothing_max_amount')
    health = fields.Float('Salud', states={'validated': [('readonly', True)]})
    max_health = fields.Float('Máximo de vivienda', related='fiscalyear_id.health_max_amount')
    incomes_amount = fields.Float('Total de ingresos', compute='_get_incomes_amount')
    max_expenses = fields.Float('Máximo deducible', compute='_get_max_expenses')
    expenses_amount = fields.Float('Total de gastos', compute='_get_expenses_amount')
    base_amount = fields.Float('Base imponible', compute='_get_base_amount')
    tax_id = fields.Many2one('hr.income.tax.table', compute='_get_tax_id')
    table_base_amount = fields.Float('Fracción básica', compute='_get_table_amounts')
    table_base_tax = fields.Float('Impuesto a la fracción básica', compute='_get_table_amounts')
    excess_amount = fields.Float('Excedente', compute='_get_table_amounts')
    excess_tax = fields.Float('Impuesto al excedente', compute='_get_table_amounts')
    tax_amount = fields.Float('Total del impuesto', compute='_get_table_amounts')
    tax_amount_monthy = fields.Float('Total del impuesto mensual', compute='_get_table_amounts')
    wage = fields.Float('Sueldos y salarios', compute='get_values', multi='values')
    collected_amount = fields.Float('Valor recaudado', compute='get_values', multi='values')
    state = fields.Selection([('draft', 'Borrador'),('validated', 'Validado')], 'Estado', required=True, readonly=True, default='draft')
    #===========================================================================
    _sql_constraints = [
        ('uniq_declaration', 'unique(contract_id,fiscalyear_id)', 'Ya ha declarado su formulario de impuesto a la renta!')
    ]
    
    @api.one
    @api.depends('contract_id', 'fiscalyear_id')
    def get_values(self):
        payroll = self.env['hr.payroll'].sudo().search([('contract_id', '=', self.contract_id.id),
                                                        ('period_id.fiscalyear_id', '=', self.fiscalyear_id.id),
                                                        ('state', 'not in', ['draft', 'calculated'])],
                                                       order='create_date desc', limit=1)
        excl_irenta = sum([expense.value for expense in payroll.expenses_ids if expense.expense_type_id.impuesto_renta])
        print"excl_irenta=%s"%excl_irenta
        base_renta = sum([income.value for income in payroll.incomes_ids if income.adm_id.impuesto_renta])
        #base_renta = sum([income.value for income in employee.incomes_ids if income.adm_id.impuesto_renta])
        print"base_renta=%s"%base_renta 
        base_imponible, recaudo = self.env['hr.expense'].sudo().base_imponible_IR(contract=self.contract_id,
                                                                                  period=payroll.period_id,
                                                                                  base_renta=base_renta,
                                                                                  excl_irenta=excl_irenta)
        self.wage = base_imponible - base_renta + excl_irenta
        print"self.wage_lin144=%s"%self.wage
        self.collected_amount = recaudo
    
    def get_table_amounts(self, tax_id, base_amount, fiscalyear_id):
        table_base_amount = table_base_tax = excess_amount = excess_tax = tax_amount = 0.0
        if tax_id:
            table_base_amount = tax_id.base
            table_base_tax = tax_id.base_tax
            excess_amount = max(0.0, base_amount - tax_id.base)
            excess_tax = excess_amount * tax_id.excess_tax
            tax_amount = table_base_tax + excess_tax
        return dict(
            table_base_amount = table_base_amount,
            table_base_tax = table_base_tax,
            excess_amount = excess_amount,
            excess_tax = excess_tax,
            tax_amount = tax_amount,
            tax_amount_monthy = tax_amount / (len(fiscalyear_id.period_ids) or 1)
        )
    
    @api.one
    @api.depends('tax_id')
    def _get_table_amounts(self):
        res = self.get_table_amounts(self.tax_id, self.base_amount, self.fiscalyear_id)
        self.table_base_amount = res['table_base_amount']
        self.table_base_tax = res['table_base_tax']
        self.excess_amount = res['excess_amount']
        self.excess_tax = res['excess_tax']
        self.tax_amount = res['tax_amount']
        self.tax_amount_monthy = res['tax_amount_monthy'] 
    
    @api.one
    def validate(self):
        if self.expenses_amount > self.max_expenses:
            print"self.expenses_amount=%s"%self.expenses_amount
            print"self.max_expenses=%s"%self.max_expenses
            raise ValidationError(u'El total deducible no puede ser mayor que %.2f'%self.max_expenses)
        self.state = 'validated'
        
    @api.one
    def return_draft(self):
        self.state = 'draft'
        
    @api.one
    @api.depends('fiscalyear_id', 'fiscalyear_id.income_tax_table', 'base_amount')
    def _get_name(self):
        TYPE = dict([('proyected', 'proyectada'), ('real', 'real')])
        self.name = u'Declaración para el ' + self.fiscalyear_id.name +' de ' + self.employee_id.name
    
    def get_tax_id(self, fiscalyear_id, base_amount):
        for tax in fiscalyear_id.income_tax_table:
            if tax.base <= base_amount < (tax.excess or (base_amount + 1)):
                return tax
        return False
    
    @api.one
    @api.depends('fiscalyear_id', 'fiscalyear_id.income_tax_table', 'base_amount')
    def _get_tax_id(self):
        tax_id = self.get_tax_id(self.fiscalyear_id, self.base_amount)
        self.tax_id = bool(tax_id) and tax_id.id
    
    @api.one
    @api.depends('wage', 'other_incomes')
    def _get_incomes_amount(self):
        self.incomes_amount = self.wage + self.other_incomes
        
    @api.one
    @api.depends('housing', 'education', 'food', 'clothing', 'health')
    def _get_expenses_amount(self):
        self.expenses_amount = self.housing + self.education + self.food + self.clothing + self.health
        
    @api.one
    @api.depends('fiscalyear_id', 'incomes_amount')
    def _get_max_expenses(self):
        max_expenses = self.fiscalyear_id.max_percentage * self.incomes_amount
        print"self.fiscalyear_id.max_percentage=%s"%self.fiscalyear_id.max_percentage
        print"self.incomes_amount=%s"%self.incomes_amount
        print"max_expenses=%s"%max_expenses
        self.max_expenses = min(max_expenses, self.fiscalyear_id.total_max_amount)
        
    @api.one
    @api.depends('incomes_amount', 'expenses_amount')
    def _get_base_amount(self):
        self.base_amount = self.incomes_amount - self.expenses_amount
        
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.contract_id = self.employee_id.contract_id and self.employee_id.contract_id.id
    
    @api.onchange('housing')
    def onchange_housing(self):
        if self.housing > self.max_housing:
            self.housing = self.max_housing
            return {'warning': {'title': 'ValidationError', 'message': 'El valor deducible para Vivienda no puede pasar lo %.2f'%self.max_housing}}
    
    @api.onchange('education')
    def onchange_education(self):
        if self.education > self.max_education:
            self.education = self.max_education
            return {'warning': {'title': 'ValidationError', 'message': 'El valor deducible para Vivienda no puede pasar lo %.2f'%self.max_education}}
    
    @api.onchange('food')
    def onchange_food(self):
        if self.food > self.max_food:
            self.food = self.max_food
            return {'warning': {'title': 'ValidationError', 'message': 'El valor deducible para Vivienda no puede pasar lo %.2f'%self.max_food}}
        
    @api.onchange('clothing')
    def onchange_clothing(self):
        if self.clothing > self.max_clothing:
            self.clothing = self.max_clothing
            return {'warning': {'title': 'ValidationError', 'message': 'El valor deducible para Vivienda no puede pasar lo %.2f'%self.max_clothing}}
        
    @api.onchange('health')
    def onchange_health(self):
        if self.health > self.max_health:
            self.health = self.max_health
            return {'warning': {'title': 'ValidationError', 'message': 'El valor deducible para Vivienda no puede pasar lo %.2f'%self.max_health}}

class hr_expense(models.Model):
    _inherit = 'hr.expense'
    
    def base_imponible_IR(self, cr, uid, contract, period, base_renta, excl_irenta):
        ir_cobrado = 0.0
        # Obtengo el valor sin exclusiones
        base_renta -= excl_irenta
        # Proyecto en base al mes de cálculo
        MONTH = DATE(period.date_start).month
        base_renta *= (13 - MONTH)
        # Obtengo los roles anteriores
        payroll_ids = self.pool['hr.payroll'].search(cr, uid, [('contract_id', '=', contract.id),
                                                               ('state', 'not in', ['draft', 'calculated'])])
        # Sumo y resto los valores imponibles de los anteriores roles
        for payroll in self.pool['hr.payroll'].browse(cr, uid, payroll_ids):
            base_renta += sum([income.value for income in payroll.incomes_ids if income.adm_id.impuesto_renta])
            base_renta -= sum([expense.value for expense in payroll.expenses_ids if expense.expense_type_id.impuesto_renta])
            ir_cobrado += sum([expense.value for expense in payroll.expenses_ids if expense.expense_type_id.code == 'IMREN'])
        # Obtengo el valor de las utilidades si existen
        utility = self.pool['hr.employee.utilities'].search(cr, uid, [('contract_id', '=', contract.id),
                                                                      ('year_id.fiscalyear_id', '=', period.fiscalyear_id.id)],
                                                            limit=1)
        utility = self.pool['hr.employee.utilities'].browse(cr, uid, utility)
        base_renta += utility[0].amount if utility else 0.0
        #Retorno el valor de la base imponible
        return base_renta, ir_cobrado
    
    def calcular_impuesto_renta(self, cr, uid, payroll, **args):
        if not args.has_key('excl_irenta'):
            return self.calcular_impuesto_renta
        base_renta = args['base_renta']
        excl_irenta = args['excl_irenta']
        pe_env = self.pool['hr.employee.personal.expenses']
        #=======================================================================
        # OBTENER LA DEDUCCIÓN DE GASTOS PERSONALES
        personal_expense = pe_env.search(cr, uid, [('employee_id', '=', payroll.employee_id.id),
                                                   ('contract_id', '=', payroll.contract_id.id),
                                                   ('fiscalyear_id', '=', payroll.period_id.fiscalyear_id.id)],
                                         order='create_date desc', limit=1)
        personal_expense = pe_env.browse(cr, uid, personal_expense)
        expense_value = bool(personal_expense) and personal_expense[0].expenses_amount or 0.0
        #=======================================================================
        # OBTENER LA BASE IMPONIBLE
        BASE_IMPONIBLE, IR_COBRADO = self.base_imponible_IR(cr, uid, payroll.contract_id, payroll.period_id, base_renta, excl_irenta)
        BASE_IMPONIBLE -= expense_value
        #=======================================================================
        tax = pe_env.get_tax_id(payroll.period_id.fiscalyear_id, BASE_IMPONIBLE)
        values = pe_env.get_table_amounts(tax, BASE_IMPONIBLE, payroll.period_id.fiscalyear_id)
        MONTH = 13 - DATE(payroll.period_id.date_start).month
        return (values['tax_amount'] - IR_COBRADO) / float(MONTH)