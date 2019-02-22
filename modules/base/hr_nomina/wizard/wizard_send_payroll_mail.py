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

class hr_payroll(models.Model):
    _inherit = 'hr.payroll'
    #===========================================================================
    # Columns
    send_mail = fields.Boolean('Mensaje enviado', readonly=True)
    #===========================================================================

class wizard_send_payroll_mail(models.TransientModel):
    _name = 'wizard.send.payroll.mail'
    #===========================================================================
    # Columns
    include_dispatched = fields.Boolean('Reenviar', help='Permite re-enviar los roles ya enviados.')
    #===========================================================================
    
    def __send_mail(self, include_dispatched):
        payroll_ids = self._context['active_ids']
        if not self._context['active_model'] == 'hr.payroll':
            raise ValidationError('Los modelos no son roles de pagos')
        send_ids = []
        for payroll in self.env['hr.payroll'].browse(payroll_ids):
            if payroll.send_mail:
                if not include_dispatched: continue
            send_ids.append(payroll.id)
        self.pool['hr.payroll'].send_email(self._cr, self._uid, send_ids, self._context)
        return self.pool['hr.payroll'].write(self._cr, self._uid, send_ids, {'send_mail': True})
    
    @api.multi
    def send_email(self):
        for obj in self:
            obj.__send_mail(self.include_dispatched)
        return True
