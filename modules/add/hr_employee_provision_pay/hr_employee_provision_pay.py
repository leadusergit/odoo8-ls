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
from openerp import pooler
from datetime import date, datetime, timedelta, time
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.addons.hr_nomina.payroll_tools import DATE

 
class hr_employee_provision_pay(models.Model):
    _name = 'hr.employee.provision.pay'
    _description = u'Pago Decimos'
     
     
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        reads = self.browse(cr, uid, ids, context=context)
        for record in reads:
            #name = '%s - %s' % (record.id , record.codigo_orden_servicio)
            name = '%s' % (record.provision)
            res.append((record.id, name))
        return res
    #===========================================================================
    # Columns
    
    state = fields.Selection([('draft', 'Borrador'),('done', 'Validado'),('paid', 'Pagado')], 'Estado', required=True,readonly=True, default='draft')
    fiscalyear_id = fields.Many2one('hr.fiscalyear', 'Año',readonly=True, states={'draft': [('readonly', False)]})
    ppay_lines = fields.One2many('hr.employee.provision.pay.line','ppay_id', 'Lineas', readonly=True , copy=True)
    period_start = fields.Many2one('account.period', 'Desde',required=True,readonly=True, states={'draft': [('readonly', False)]},help='Periodo Inicial, se tomara como fecha inicial la fecha de inicio del periodo')
    period_end = fields.Many2one('account.period', 'Hasta',required=True,readonly=True, states={'draft': [('readonly', False)]},help='Periodo Final, se tomara como fecha final la fecha de fin del periodo')
    region = fields.Selection([('costa', 'Costa'),('sierra', 'Sierra'),('insular', 'Region Insular y Amazonia')], 'Región', required=True,readonly=True, states={'draft': [('readonly', False)]}, default='sierra')   
    provision = fields.Selection([('dt', 'Decimo Tercer Sueldo'),('dc', 'Decimo Cuarto Sueldo')], 'Provision', required=True,readonly=True, states={'draft': [('readonly', False)]}, default='dc')   
    journal_id=fields.Many2one('account.journal', 'Método de pago', domain=[('type', '=', 'bank')],help='Seleccionar el metodo con el que se generaran los vouchers de pago')

    dec3_amount = fields.Float('Decimo Tercer Sueldo',readonly=True)
    dec4_amount = fields.Float('Decimo Cuarto Sueldo',readonly=True,help='Monto Total a pagar')
    aux = fields.Float('Campo Auxiliar')
    aux1 = fields.Float('Campo Auxiliar 1')
    aux2 = fields.Float('Campo Auxiliar 2')
    subquery = fields.Text('Reporte',readonly=True)
    #===========================================================================
    _sql_constraints = [
        ('uniq_declaration', 'unique(period_start,period_end)', 'Formulario Generado!')
    ]
    
    
    @api.multi
    def clear_info(self,ppay_id):   
        self.env.cr.execute('DELETE FROM hr_employee_provision_pay_line WHERE ppay_id=%s', (ppay_id,))
    
    @api.multi
    def unlink(self):
        """"Método que controla borrado de registros"""
        for rdec in self:
            if rdec.state in ('done','paid'):
                 raise ValidationError('No puede borrar registro en estado validado')
        return super(hr_employee_provision_pay, self).unlink()
    
    

    @api.multi
    def done(self):
        
        self.write({'state': 'done'})
        return True
    
    @api.multi
    def pagar(self):
        
        if self.state=='done':
            self.ppay_lines.pago()
            self.write({'state': 'paid'})

        return True
    
    
    
    @api.multi
    def change_state(self):
        for self in self:
            self.state = 'draft' if self.state != 'draft' else 'valid'
    
    @api.one
    @api.depends('period_start','period_end')
    def get_values(self):
        
        #periodos_ids = self.env['hr.contract.period'].sudo().search([('fiscalyear_id', '=', self.fiscalyear_id.id)]).ids    

        #period_ids = self.env['account.period'].sudo().search([('fiscalyear_id', '=', self.fiscalyear_id.id)]).ids         
          
        payslip_ids= self.env['hr.payslip'].sudo().search([('state', 'not in', ['draft'])],
                                                           order='date_to desc')#, limit=12)                                            
                                                           
        
                                                 
        
        for payslip in payslip_ids:                      
                
            if payslip.period_id.date_start >=self.period_start.date_start and  payslip.period_id.date_stop <=self.period_end.date_stop and payslip.contract_id.state =='vigente':
           
                print" payslip.contract_id.state=%s"%payslip.contract_id.state
                if self.provision=='dt':
                    aux = sum([psl.amount for psl in payslip.line_ids if psl.code =='PROV DTERCERO' and  psl.salary_rule_id.acumula and psl.contract_id.state =='vigente'])
                    #print"aux=%s"%aux

                    self.aux += aux
                    self.dec3_amount = self.aux
                    
                if self.provision=='dc':
                    aux1 = sum([psl.amount for psl in payslip.line_ids if psl.code =='PROV DCUARTO' and  psl.salary_rule_id.acumula and psl.contract_id.state =='vigente'])
                    #print"aux1=%s"%aux1
               
                
                    self.aux1 += aux1
                    self.dec4_amount = self.aux1


            
    @api.multi
    def run_sql(self):        
       # self.env.cr.execute('''select sum(amount),employee_id from hr_employee_provision_pay_line group by employee_id''')            
        self.env.cr.execute('''select sum(pl.amount),pl.employee_id,empleado.name_related
                                from hr_employee_provision_pay_line pl,hr_employee empleado
                                where pl.employee_id=empleado.id
                                group by employee_id,empleado.name_related
                                order by 2''')
        
        res = self.env.cr.dictfetchall()
        cadena= "".join(str(res))
        self.subquery=cadena
        print"self.subquery=%s"%self.subquery
        
        return self.subquery

    @api.one
    @api.depends('period_start','period_end')   
    def load_rule(self):
        print"calculo decimos=%s"        
        self.clear_info(self.id)  
        #periodos_ids = self.env['hr.contract.period'].sudo().search([('fiscalyear_id', '=', self.fiscalyear_id.id)]).ids    
        #period_ids = self.env['account.period'].sudo().search([('fiscalyear_id', '=', self.fiscalyear_id.id)]).ids         
          
        payslip_ids= self.env['hr.payslip'].sudo().search([('state', 'not in', ['draft'])], order='date_to desc')#, limit=12)
        
        employee_ids= self.env['hr.employee'].sudo().search([('active', '=', True)]) 
                
        employee_lines= self.env['hr.payslip.line'].sudo().search([('code','=','PROV DCUARTO')])
        employee_lines1= self.env['hr.payslip.line'].sudo().search([('code','=','PROV DTERCERO')]) 
       

        lines_obj= self.env['hr.employee.provision.pay.line']
        
        if self.provision=='dc':

            for employee in employee_ids:
                for payslip in employee_lines:                  
                    if payslip.slip_id.period_id.date_start >=self.period_start.date_start and payslip.slip_id.period_id.date_stop <=self.period_end.date_stop and payslip.contract_id.state =='vigente':
                        empleado=payslip.employee_id.id 
                    else:
                        continue
                                   
                    if payslip.salary_rule_id.acumula and employee.id==empleado:
                        self.aux2 += payslip.amount                            
                        print"self.aux2 =%s"% self.aux2 
                        
                if self.aux2 >0:
                    vals ={'ppay_id':self.id,
                           'employee_id':employee.id,
                           'contract_id':payslip.contract_id.id,
                           'company_id':payslip.employee_id.company_id.id,
                           'partner_id':payslip.employee_id.address_home_id.id,
                           'currency_id':payslip.employee_id.company_id.currency_id.id,
                           'amount':self.aux2}
                    
                    lines_obj.create(vals)
                self.aux2 =0.00 
   
        if self.provision=='dt':
            
           for employee in employee_ids:
                for payslip in employee_lines1:                  
                    if payslip.slip_id.period_id.date_start >=self.period_start.date_start and payslip.slip_id.period_id.date_stop <=self.period_end.date_stop and payslip.contract_id.state =='vigente':
                        empleado=payslip.employee_id.id 
                    else:
                        continue
                                   
                    if payslip.salary_rule_id.acumula and employee.id==empleado:
                        self.aux2 += payslip.amount                            
                        print"self.aux2 =%s"% self.aux2 
                        
                if self.aux2 >0:
                    vals ={'ppay_id':self.id,
                           'employee_id':employee.id,
                           'contract_id':payslip.contract_id.id,
                           'company_id':payslip.employee_id.company_id.id,
                           'partner_id':payslip.employee_id.address_home_id.id,
                           'currency_id':payslip.employee_id.company_id.currency_id.id,
                           'amount':self.aux2}
                    
                    lines_obj.create(vals)
                self.aux2 =0.00  

            
        self.get_values()

class hr_employee_provision_pay_line(models.Model):
    _name = 'hr.employee.provision.pay.line'
    _description = u'Detalle de pago decimos'
    
    #===========================================================================
    # Columns
    ppay_id = fields.Many2one('hr.employee.provision.pay', string='Pago Provision',required=True, ondelete='cascade', readonly=True,select=True)
    fiscalyear_id= fields.Many2one('hr.fiscalyear',string='fiscal',related='ppay_id.fiscalyear_id',store=True, readonly=True)
    period_start= fields.Many2one('account.period',string='Desde',related='ppay_id.period_start',store=True, readonly=True)
    period_end= fields.Many2one('account.period',string='Hasta',related='ppay_id.period_end',store=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Empleado', readonly=True)
    company_id = fields.Many2one('res.company', 'Compañia', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Proveedor', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True)
    contract_id = fields.Many2one('hr.contract', 'Contrato', readonly=True)    
    amount = fields.Float('Valor')
    ##dpagado= fields.Many2one('account.voucher',string='Decimo Pagado',related='order_claim_id.company_id',store=True, readonly=True)
       
    
       
    @api.multi
    def pago(self):
        decimo_obj= self.env['hr.employee.provision.pay.line']
        
        for pdl in self:
            if pdl.ppay_id.provision=='dc':               
               pago=True
               pago1=False
            else:
               pago1=True
               pago=False
            
            print"pago,pago1=%s"%pago ,pago1 
            vals = dict(
                        pagod_ref=pdl.ppay_id.id,
                        reference='Pago decimos',
                        partner_id=pdl.employee_id.address_home_id.id,
                        amount= pdl.amount,
                        type='payment', 
                        date= date.today(),
                        company_id=pdl.company_id.id,
                        pre_line= True,
                        journal_id=pdl.ppay_id.journal_id.id,
                        account_id=pdl.ppay_id.journal_id.default_credit_account_id.id,
                        payment_option='without_writeoff',
                        pago_dc= pago,
                        pago_dt= pago1,
                        narration=pdl.ppay_id.provision,
                        transfers=[]
                        )
                        
            print"vals=%s"%vals    
            voucher =self.env['account.voucher'].create(vals)
            
            """se leen los registros del asiento contable """
            move_line_pool = self.env['account.move.line']
            account_move_lines = self.env['account.move.line'].search([("partner_id", "=", pdl.employee_id.address_home_id.id)])
            print" account_move_lines =%s"% account_move_lines
                
            for line in account_move_lines:
#                 print"line=%s"% line
#                 print"line.name =%s"%line.name 
#                 print"line.credit =%s"%line.credit                           
                   
                if 'decimo' in line.name or 'Decimo'in line.name and ('cuarto'in line.name or 'Cuarto'in line.name) and not line.reconcile_id and pago==True:


                    line_dr_ids = dict(reconcile= True,
                                        move_line_id = line.id,
                                        voucher_id =voucher.id, 
                                        amount_unreconciled= line.credit,
                                        amount=line.credit,
                                        amount_original=line.credit,
                                        account_id=line.account_id.id,
                                        type = 'dr')
                                       
                    print"line_dr_ids =%s"%line_dr_ids
                    

                    voucher_line =self.env['account.voucher.line'].create(line_dr_ids)
                if 'decimo' in line.name or 'Decimo'in line.name and ('tercero'in line.name or 'Tercero'in line.name) and not line.reconcile_id and pago1==True:


                    line_dr_ids = dict(reconcile= True,
                                        move_line_id = line.id,
                                        voucher_id =voucher.id, 
                                        amount_unreconciled= line.credit,
                                        amount=line.credit,
                                        amount_original=line.credit,
                                        account_id=line.account_id.id,
                                        type = 'dr')
                                       
                    print"line_dr_ids =%s"%line_dr_ids
                    

                    voucher_line =self.env['account.voucher.line'].create(line_dr_ids)    
        
   
   
   
   
   