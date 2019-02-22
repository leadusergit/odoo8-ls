# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
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
from openerp import models, fields, api
from openerp.exceptions import ValidationError
import time

class wizard_pay_payroll(models.TransientModel):
    _name = 'wizard.pay.payroll'
    #===========================================================================
    # Columns
    journal_id = fields.Many2one('account.journal', 'Método de pago', required=True, domain=[('type', '=', 'bank')])
    date = fields.Date('Fecha', default=time.strftime('%Y-%m-%d'))
    period_id = fields.Many2one('account.period', 'Periodo', required=True)
    ref = fields.Char('Referencia', required=True)
    payroll_ids = fields.Many2many('hr.payroll', required=True, domain=[('state', '=', 'calculated')],
                                   default=lambda self: self._context.get('active_ids', []))
    #===========================================================================
    
    @api.onchange('date')
    def onchange_date(self):
        period_id = self.env['account.period'].find(self.date)
        self.period_id = period_id

    def get_move_pay_data(self, payroll):
        res = dict(
                journal_id = self.journal_id.id,
                ref = self.ref,
                date = self.date,
                period_id = self.period_id.id,
                tipo_comprobante = 'Egreso',
                other_info = self.ref,
                line_id = [(0, 0, dict(period_id = self.period_id.id,
                                       date = self.date,
                                       name = payroll.employee_id.name,
                                       ref = self.ref,
                                       account_id = self.journal_id.default_credit_account_id.id,
                                       credit = payroll.total)),
                           (0, 0, dict(period_id = self.period_id.id,
                                       date = self.date,
                                       name = payroll.employee_id.name,
                                       ref = self.ref,
                                       account_id = payroll.employee_id.credit_account.id,
                                       debit = payroll.total))]
                )
        return res
    
    @api.one
    def pay(self):
        for payroll in [aux for aux in self.payroll_ids if aux.state == 'calculated']:
            move = self.env['account.move'].create(self.get_move_pay_data(payroll))
            move.post()
            payroll.state = 'paid'
            payroll.pay_move_id = move.id
             
class wizard_cash_payroll(models.TransientModel):
    _name = 'wizard.cash.payroll'
    _description = u'Generador del cash de la nómina'
    #===========================================================================
    # Columns
    name = fields.Char('Descripción', required=True)
    journal_id = fields.Many2one('account.journal', 'Diario', required=True, domain=[('type', '=', 'bank')])
    bank_account_id = fields.Many2one('res.partner.bank', 'Cuenta de banco', required=True, domain=[('partner_id.is_provider', '=', True)])
    date = fields.Date('Fecha', default=time.strftime('%Y-%m-%d'), required=True)
    payroll_ids = fields.Many2many('hr.payroll', required=True, domain=[('state', '=', 'paid')],
                                   default=lambda self: self._context.get('active_ids', []))
    #===========================================================================
    
    @api.multi
    def generate(self):
        self = self[0]
        vals = dict(name=self.name, journal_id=self.journal_id.id, amount=0.0,
                    bank_account_id=self.bank_account_id.id, date=self.date,
                    transfers=[])
        for payroll in self.payroll_ids:
            if payroll.state == 'paid' and payroll.pay_move_id \
                and payroll.pay_move_id.journal_id.id == self.journal_id.id and payroll.employee_id.modo_pago == 'transferencia':
                vals['transfers'].append((0, 0, dict(move=payroll.pay_move_id.id,
                                                     name=payroll.employee_id.name,
                                                     ident_type = payroll.employee_id.tipoid,
                                                     ident_num = payroll.employee_id.identification_id,
                                                     email = payroll.employee_id.work_email,
                                                     amount=payroll.pay_move_id.amount,
                                                     bank_account_dest_id=self.bank_account_id.id,
                                                     bank_account_id=payroll.employee_id.bank_account_id and payroll.employee_id.bank_account_id.id)))
                vals['amount'] += payroll.total
        if not vals['amount']:
            raise ValidationError(u'No se ha generado ningún cash.\nRevise que los roles estén pagados.\nPosiblemente eliminó el asiento de pago de un rol manualmente.\n¿Está seguro de haber seleccionado el diario con el que canceló los roles?')
        cash = self.env['payment.cash.management'].create(vals)
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payment.cash.management',
            'res_id': cash.id,
        }