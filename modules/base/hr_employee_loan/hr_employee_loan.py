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
from openerp.addons.hr_nomina.payroll_tools import PERIODOS, DATE
from dateutil.relativedelta import relativedelta

class hr_expense(models.Model):
    _inherit = 'hr.expense'
    
    def obtener_valor_prestamos(self, cr, uid, payroll):
        res = 0.0
        loan_ids = self.pool['hr.employee.loan.plan'].search(cr, uid, [('loan_id.employee_id', '=', payroll.employee_id.id),
                                                                       ('loan_id.contract_id', '=', payroll.contract_id.id),
                                                                       ('loan_id.state', '=', 'valid'),
                                                                       ('period_id', '=', payroll.period_id.id)])
        for loan in self.pool['hr.employee.loan.plan'].browse(cr, uid, loan_ids):
            res += loan.amount
            loan.payroll_id = payroll.id
        return res
        

class hr_employee_loan(models.Model):
    _name = 'hr.employee.loan'
    _description = u'Préstamos a colaboradores'
    #===========================================================================
    # Columns
    name = fields.Char('Código', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Colaborador', required=True, readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', 'Contrato', required=True, readonly=True, states={'draft': [('readonly', False)]})
    period_from = fields.Many2one('hr.contract.period', 'Periodo desde', required=True, readonly=True, states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one('account.journal', 'Diario de préstamos', domain=[('type', '=', 'bank')], required=True, readonly=True, states={'draft': [('readonly', False)]})
    account_id = fields.Many2one('account.account', 'Cuenta contable', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date('Fecha del asiento', required=True, readonly=True, states={'draft': [('readonly', False)]})
    move_id = fields.Many2one('account.move', 'Asiento contable', readonly=True)
    amount = fields.Float('Monto', required=True, readonly=True, states={'draft': [('readonly', False)]})
    time = fields.Integer('Tiempo', required=True, readonly=True, states={'draft': [('readonly', False)]})
    plan_ids = fields.One2many('hr.employee.loan.plan', 'loan_id', 'Plan de recaudo', readonly=True, states={'open': [('readonly', False)]})
    state = fields.Selection([('draft', 'Borrador'), ('open', 'Abierto'), ('valid', 'Validado')], 'Borrador', required=True, readonly=True, default='draft')
    #===========================================================================
    @api.constrains('time', 'amount')
    def validar_campos(self):
        if not self.time or self.time < 0:
            raise ValidationError(u'El tiempo del préstamo no puede ser negativo o cero.')
        if not self.amount or self.amount < 0:
            raise ValidationError(u'No puede registrar un préstamo negativo o sin valor.')
        return True
    
    @api.one
    def confirm(self):
        if round(self.amount, 2) != round(sum([aux.amount for aux in self.plan_ids]), 2):
            raise ValidationError(u'No se puede confirmar, revise que el valor del préstamo coincida con el plan de recaudo.')
        self.state = 'valid'
    
    @api.one
    def validar(self):
        if not self.name:
            self.name = self.env['ir.sequence'].get(code='hr.employee.loan')
        period_id = self.env['account.period'].find(self.date)
        vals = {'journal_id': self.journal_id.id,
                'date': self.date,
                'period_id': period_id.id,
                'ref': u'Préstamo a: %s'%self.employee_id.name,
                'name': u'Préstamo a: %s'%self.employee_id.name,
                'other_info': u'Préstamo a: %s'%self.employee_id.name,
                'no_comp': self.name,
                'line_id': [(0, 6, {'ref': u'Préstamo a: %s'%self.employee_id.name,
                                    'name': u'Préstamo a: %s'%self.employee_id.name,
                                    'account_id': self.account_id.id,
                                    'debit': self.amount,
                                    'journal_id': self.journal_id.id,
                                    'period_id': period_id.id}),
                            (0, 6, {'ref': u'Préstamo a: %s'%self.employee_id.name,
                                    'name': u'Préstamo a: %s'%self.employee_id.name,
                                    'account_id': self.journal_id.default_credit_account_id.id,
                                    'credit': self.amount,
                                    'journal_id': self.journal_id.id,
                                    'period_id': period_id.id})]}
        self.move_id = self.env['account.move'].create(vals).id
        self.state = 'open'
    
    @api.one
    def cancel(self):
        if self.move_id:
            self.move_id.button_cancel()
            self.move_id.unlink()
        self.state = 'draft'
        
    @api.one
    def edit(self):
        self.state = 'open'
    
    @api.one
    def create_plan(self):
        for line in self.plan_ids:
            if not line.payroll_id and not line.state=='locked':
                line.unlink()
        amount_paid = sum([aux.amount for aux in self.plan_ids])
        amount, plan = self.amount - amount_paid, []
        value = round((self.amount - amount_paid) / float(self.time - len(self.plan_ids)), 2)
        date_from = DATE(self.period_from.date_start)
        periodos = PERIODOS(date_from.strftime('%Y-%m-%d'), (date_from + relativedelta(months=self.time, days=-1)).strftime('%Y-%m-%d'))
        periodos = [period for period in periodos.keys() if period not in (aux.period_id.name for aux in self.plan_ids)]
        periodos = self.env['hr.contract.period'].search([('name', 'in', periodos)])
        if len(periodos) != (self.time - len(self.plan_ids)):
            raise ValidationError('No se encuentran configurados todos los periodos para el préstamo. Por favor créelos.')
        for period_id in periodos:
            plan.append({'period_id': period_id.id, 'amount': value})
            amount -= value
        if amount and plan:
            plan[-1]['amount'] += amount
        self.plan_ids = plan
        
    @api.one
    def lock_all(self):
        for line in self.plan_ids:
            line.state = 'locked'
        
    @api.one
    def unlock_all(self):
        for line in self.plan_ids:
            if not line.payroll_id:
                line.state = 'unlocked'
    
class hr_employee_loan_plan(models.Model):
    _name = 'hr.employee.loan.plan'
    _description = u'Plan de recaudación de préstamos'
    _order = 'period_id'
    #===========================================================================
    # Columns
    loan_id = fields.Many2one('hr.employee.loan', 'Préstamo', required=True, ondelete='cascade')
    period_id = fields.Many2one('hr.contract.period', 'Periodo', required=True, readonly=True, states={'unlocked': [('readonly', False)]})
    payroll_id = fields.Many2one('hr.payroll', 'Rol de pagos', readonly=True, ondelete='set null')
    amount = fields.Float('Monto', required=True, readonly=True, states={'unlocked': [('readonly', False)]})
    state = fields.Selection([('locked', 'Bloqueado'), ('unlocked', 'Desbloqueado')], 'Estado',
                             default='unlocked', required=True, readonly=True)
    #===========================================================================
    
    _sql_constraints = [
        ('plan_uniq', 'unique(loan_id,period_id)', 'Solo debe haber un descuento por periodo!')
    ]
    
    @api.multi
    def write(self, vals):
        for plan in self:
            if (vals.has_key('loan_id') and len(vals) == 1) or vals.get('state') == 'locked':
                continue
            if plan.payroll_id and 'payroll_id' not in vals.keys():
                raise ValidationError('No puede modificar un registro si ya fue tomado en cuenta en un rol de pagos.')
        return super(hr_employee_loan_plan, self).write(vals)
    
    @api.multi
    def change_state(self):
        for self in self:
            if not self.payroll_id:
                self.state = 'unlocked' if self.state=='locked' else 'locked'
    
    @api.multi
    def unlink(self):
        if self.payroll_id:
            raise ValidationError('No puede borrar registros que se encuentren en un rol de pagos.')
        return super(hr_employee_loan_plan, self).unlink()