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
from openerp.osv import osv
from openerp.report import report_sxw
from openerp import models, fields, api
from lxml import etree
from xml.dom.minidom import parse, parseString
import base64
import StringIO

class wizard_generate_rdep(models.TransientModel):
    _name = "wizard.generate.rdep"

    fiscalyear_id = fields.Many2one('hr.fiscalyear', 'Año Fiscal', required=True)
    employee_id = fields.Many2many('hr.employee', string='Empleados')

    @api.multi
    def generar_rdep_xml(self):
        if self.employee_id:
            self.env.cr.execute('SELECT employee_id FROM hr_payslip p '
                                ' WHERE company_id = %s AND period_id = ANY (%s) AND employee_id = ANY (%s) GROUP BY employee_id ',
                                (self.env.user.company_id.id, self.fiscalyear_id.period_ids.ids, self.employee_id.ids))
        else:
            self.env.cr.execute('SELECT employee_id FROM hr_payslip p '
                       ' WHERE company_id = %s AND period_id = ANY (%s) GROUP BY employee_id ', (self.env.user.company_id.id, self.fiscalyear_id.period_ids.ids))
        value = self.env.cr.fetchall()

        employees = self.env['hr.employee'].search([('id', '=', value)])

        fiscalyear = self.env['hr.fiscalyear'].search([('date_start', '<', self.fiscalyear_id.date_start)], order='date_start desc', limit=1)
        
        template = self.env.ref('hr_payslip_rdep.rdep_xml')
        
        return self.env['base.file.report'].show(
                base64.encodestring(template.render({'employees': employees,
                                                     'company': self.env.user.company_id,
                                                     'fiscalyear_before': fiscalyear,
                                                     'fiscalyear': self.fiscalyear_id
                                                    })),'FormularioRDEP.xml')