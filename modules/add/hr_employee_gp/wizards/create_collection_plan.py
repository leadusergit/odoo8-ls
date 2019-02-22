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
from openerp.addons.hr_nomina.payroll_tools import PERIODOS

class create_collection_plan(models.TransientModel):
    _name = 'create.collection.plan'
    _description = 'Crear un plan de recaudación'
    #===========================================================================
    # Columns
    declaration_id = fields.Many2one('hr.employee.personal.expenses', required=True, ondelete='cascade')
    fiscalyear_id = fields.Many2one('hr.fiscalyear', related='declaration_id.fiscalyear_id')
    period_start = fields.Many2one('hr.contract.period')
    period_end = fields.Many2one('hr.contract.period')
    #===========================================================================
    
    @api.one
    def create_plan(self):
        periods = PERIODOS(self.period_start.date_start, self.period_end.date_stop)
        amount = (self.declaration_id.tax_amount - self.declaration_id.collected_amount) / (len(periods) or 1)
        periods = self.env['hr.contract.period'].search([('name', 'in', periods.keys())])
        self.declaration_id.collection_plan.unlink()
        for period in periods:
            self.env['hr.income.tax.collection.plan'].create(dict(
                declaration_id = self.declaration_id.id,
                period_id = period.id,
                amount = max(0.0, amount)
            ))