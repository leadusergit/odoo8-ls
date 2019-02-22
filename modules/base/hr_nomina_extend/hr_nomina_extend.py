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
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from openerp import SUPERUSER_ID
from openerp import models, fields, api, _
from openerp.osv import osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import workflow
from openerp.exceptions import ValidationError,except_orm, Warning, RedirectWarning

    
class hr_utilities(models.Model):
    _name = 'hr.utilities'
    _description = u'Utilidades de un año'
       
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        reads = self.browse(cr, uid, ids, context=context)
        for record in reads:
            name = 'Utilidades'
            res.append((record.id, name))
        return res
    
    @api.one
    @api.depends('amount')
    def _compute_amount(self):
        self.amount15 = self.amount*0.15       
        self.amount10 = self.amount*0.10   
        self.amount5 =  self.amount*0.05 
              
           
    #===========================================================================
    # Columns
    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Año', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date('Desde',required=True, readonly=True, states={'draft': [('readonly', False)]})
    date_end = fields.Date('Hasta', required=True, readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Text('Descripción', readonly=True, states={'draft': [('readonly', False)]})
    employee_utilities = fields.One2many('hr.employee.utilities', 'ut_id', 'Utilidades de los colaboradores', readonly=True)
    state = fields.Selection([('draft', 'Borrador'), ('valid', 'Validado')], 'Estado', required=True, readonly=True, default='draft')
    amount = fields.Float('Monto Total')
    amount15 = fields.Float('Monto(15%)',digits=dp.get_precision('Account'),
        store=True,readonly=True, compute='_compute_amount', track_visibility='always')
    amount10 = fields.Float('Monto(10%)',digits=dp.get_precision('Account'),
        store=True,readonly=True, compute='_compute_amount', track_visibility='always')
    amount5 = fields.Float('Monto(5%)',digits=dp.get_precision('Account'),
        store=True,readonly=True, compute='_compute_amount', track_visibility='always')
    num_employee = fields.Float('Nº Empleados',readonly=True)
    aux = fields.Float('Calculos')
    aux1 = fields.Float('Calculos1')
    aux2 = fields.Float('Calculos2')
    value_dias = fields.Float('Total Dias Laborados(Todos los empleados)')
    ponderado = fields.Float('Ponderado 10%',readonly=True)
    value_10 = fields.Float('Valor del 10%')
    value_5 = fields.Float('Valor del 5%')
    total_dias5 = fields.Float('Total dias5',compute='_get_diast5')
    #===========================================================================
    _sql_constraints = [
        ('uniq_declaration', 'unique(fiscalyear_id,date_start,date_end)', 'Utilidades Generadas!')
    ]
    
    
    _defaults = {
        'date_start':lambda self, cr, uid, context={}: context.get('self.fiscalyear_id.date_start', time.strftime("%Y-%m-%d")),
        'date_end':lambda self, cr, uid, context={}: context.get('self.fiscalyear_id.date_stop', time.strftime("%Y-%m-%d")),
    }
    
    
    @api.multi
    def unlink(self):
        """"Método que controla borrado de registros"""
        for util in self:
            if util.state=='valid' :
                 raise ValidationError('No puede borrar registro en estado Borrador')
        return super(hr_utilities, self).unlink()
    
    @api.multi
    def clear_info(self,ut_id):   
        self.env.cr.execute('DELETE FROM hr_employee_utilities WHERE ut_id=%s', (ut_id,))
        self._compute_amount()
        
    @api.multi
    def change_state(self):
        for self in self:
            self.state = 'draft' if self.state != 'draft' else 'valid'
            
    
    @api.one
    @api.depends('date_start,date_end')
    def get_values(self):
        print"self.id=%s"%self.id
        self.clear_info(self.id)
        
        employee_ids = self.env['hr.employee'].sudo().search([('manager', '=', False)]).ids
        num=len(employee_ids)
        print"num=%s"%num         
        self.num_employee=num       
        
        period_ids = self.env['account.period'].sudo().search([('fiscalyear_id', '=', self.fiscalyear_id.id)]).ids  
        print"period_ids=%s"%period_ids
        payslip_ids= self.env['hr.payslip'].sudo().search([('state', 'not in', ['draft']),('period_id','in',period_ids)])          
        print"payslip_ids=%s"%payslip_ids
        contract_ids= self.env['hr.contract'].sudo().search([('employee_id', 'in', employee_ids)])
        lines_obj= self.env['hr.employee.utilities'] 
    
        for payslip in payslip_ids:            
            if 'Gerente' not in payslip.employee_id.job_id.name and payslip.contract_id.state=='vigente':                
                aux = sum([td.number_of_days for td in payslip.worked_days_line_ids if payslip.id==td.payslip_id.id])                    
                self.aux += aux         
                self.value_dias = self.aux
                print"self.value_dias total dias=%s"%self.value_dias
                
                   
                                                                                            
        for contract in contract_ids:            
  
            if 'Gerente' not in contract.employee_id.job_id.name and contract.state=='vigente' or (self.date_end <= contract.date_end > self.date_start):                
                
                payslip_days= self.env['hr.payslip'].sudo().search([('state', 'not in', ['draft']),('period_id','in',period_ids),('employee_id','=',contract.employee_id.id)])             
                print"payslip_days=%s"%payslip_days
                
                for payslipd in payslip_days:
                    aux1 = sum([wd.number_of_days for wd in payslipd.worked_days_line_ids if wd.contract_id.id==contract.id]) 
                    self.aux1 += aux1         
                    print"self.aux1=%s"%self.aux1
                                    
                """if contract.employee_id.marital=='married':
                    cargas=1
                else:
                    cargas=0"""
                cargas=0
                    
                if contract.employee_id.children:                    
                    for family in contract.employee_id.cargas_ids:
                        print"family =%s"%family 
                        fecha2 = datetime.strptime(family.birth,"%Y-%m-%d")
                        fecha1 = datetime.strptime(str(date.today()),"%Y-%m-%d") 
                        edad_dias= fecha1-fecha2
                        edad=(edad_dias.days/365)
                        print"edad=%s"%edad
                       

                        if family.discapacidad :
                            cargas=cargas+2
                        else:
                            if (edad <=18 and family.parentezco != 'hb_wife') or (edad >18 and family.parentezco == 'hb_wife'):
                               cargas=cargas+1
                        
                       
  
                    if self.value_dias > 0:
                        self.ponderado=self.aux1/self.value_dias
                    else:
                        self.ponderado=1
                        
                    num= self.aux1
                    self.aux1=0                    
                    self.value_10 = self.ponderado*self.amount10
                    #self.ponderado=0
                                   
                    vals ={'ut_id':self.id,
                           'employee_id':contract.employee_id.id,
                           'contract_id':contract.id,
                            'value_10':self.value_10,
                            'num_dias10':num,
                            'num_cargas':cargas}
                    
                    lines_obj.create(vals)
                    
                else:                  
                    
                    if self.value_dias > 0:
                        self.ponderado=self.aux1/self.value_dias
                    else:
                        self.ponderado=1
                        
                    num= self.aux1
                    self.aux1=0                    
                    self.value_10 = self.ponderado*self.amount10
                    #self.ponderado=0
                                   
                    vals ={'ut_id':self.id,
                           'employee_id':contract.employee_id.id,
                           'contract_id':contract.id,
                           'value_10':self.value_10,
                           'num_dias10':num,
                           'num_cargas':0}
                    
                    lines_obj.create(vals)
                        
    @api.one
    @api.depends('employee_utilities')
    def _get_diast5(self):    
                    
        self.total_dias5 = sum(d.num_dias5 for d in self.employee_utilities)
        print"self.total_dias5=%s"%self.total_dias5
    


class hr_employee_utilities(models.Model):
    _name = 'hr.employee.utilities'
    _description = u'Utilidades de los empleados'
    
    #===========================================================================
    # Columns
    employee_id = fields.Many2one('hr.employee', 'Empleado', required=True)
    contract_id = fields.Many2one('hr.contract', 'Contrato', required=True)
    ut_id = fields.Many2one('hr.utilities', 'Utilidades', required=True, ondelete='cascade')
    value_10 = fields.Float('Valor del 10%', required=True)
    value_5 = fields.Float('Valor del 5%',compute='_get_amount5')
    amount = fields.Float('Total', compute='_get_amount')
    num_dias10 = fields.Float('Dias Laborados')
    num_dias5 = fields.Float('Dias Laborados',compute='_get_dias')
    num_cargas = fields.Float('Nº Cargas')
    total_dias5 = fields.Float('Total dias5')
    #===========================================================================
    
    @api.one
    @api.depends('num_dias10','num_cargas')
    def _get_dias(self):

        if self.num_cargas:            
            self.num_dias5= self.num_dias10*self.num_cargas
        else:
            self.num_dias5= 0
    
    @api.one
    @api.depends('num_dias5','total_dias5','ut_id')
    def _get_amount5(self):
        
        if self.num_cargas: 
            self.value_5= (self.num_dias5/self.ut_id.total_dias5)*self.ut_id.amount5
        else:
            self.value_5= 0.00
        
        
    @api.one
    @api.depends('value_10','value_5')
    def _get_amount(self):
        
        self.amount = self.value_10 + self.value_5
        
        
