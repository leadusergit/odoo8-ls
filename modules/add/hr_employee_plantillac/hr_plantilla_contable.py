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
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.addons.hr_nomina.payroll_tools import DATE
import openerp.addons.decimal_precision as dp

class hr_salary_rule(models.Model):
    _inherit = 'hr.salary.rule' 
    
    acumula= fields.Boolean('Provision Acumulada')
    descuento_iess= fields.Boolean('Descuento(IESS/SRI)')
    
class hr_employee_plantilla(models.Model):
    _name = 'hr.employee.plantilla'
    _description = u'Plantilla gastos nomina mensual'
     
     
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        reads = self.browse(cr, uid, ids, context=context)
        for record in reads:
            #name = '%s - %s' % (record.id , record.codigo_orden_servicio)
            name = '%s' % (record.period_id.code)
            res.append((record.id, name))
        return res
        
    
    #===========================================================================
    # Columns
    subquery = fields.Text('Detalle Gasto',readonly=True)
    subquery1 = fields.Text('Detalle Retencion',readonly=True)
   #subquery = fields.Text('Detalle Ingresos',store=True,readonly=True, compute='_subquery')
    plantilla_lines = fields.One2many('hr.employee.plantilla.line','plantilla_id', 'Lineas', readonly=True,copy=True)
    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Año',required=True,readonly=True, states={'draft': [('readonly', False)]})
    period_id = fields.Many2one('account.period', 'Periodo',required=True,readonly=True, states={'draft': [('readonly', False)]})
    incomes_amount = fields.Float('Total Gasto Personal', digits=dp.get_precision('Account'),compute='get_values')
    expenses_amount = fields.Float('Descuentos', compute='get_values')
    dec3_amount = fields.Float('Decimo Tercer Sueldo', compute='get_values')
    dec4_amount = fields.Float('Decimo Cuarto Sueldo', compute='get_values')
    fr_amount = fields.Float('Fondos de Reserva', compute='get_values')
    vacacion_amount= fields.Float('Provisión Vacaciones', compute='get_values')
    wage = fields.Float('Sueldos(a pagar)', compute='get_values')
    retenciones = fields.Float('Total Retenciones(IESS/SRI)', digits=dp.get_precision('Account'),compute='get_values')
    other_expenses = fields.Float('Otros Descuentos' , compute='get_values')
    total_prov_ret = fields.Float('Total(Retenciones+Provisiones)',compute='get_values')
    anticipos_remuneracion = fields.Float('Anticipos de Remuneración',compute='get_values')
    aux = fields.Float('Campo Auxiliar')
    aux1 = fields.Float('Campo Auxiliar 1')
    aux2 = fields.Float('Campo Auxiliar 2')
    aux3 = fields.Float('Campo Auxiliar 3')
    aux4 = fields.Float('Campo Auxiliar 4')
    aux5 = fields.Float('Campo Auxiliar 5')
    aux6 = fields.Float('Campo Auxiliar 6')
    aux7 = fields.Float('Campo Auxiliar 7')
    
    aux8 = fields.Float('Campo Auxiliar 8')
    auxiliar = fields.Float('Calculos')
    aux_total = fields.Float('CalculosTotal')
    amount_aux = fields.Float('MontoAux',readonly=True)
    patronal=fields.Float('Aux')
    detalle= fields.Boolean('Detalle Generado')
    state = fields.Selection([('draft','Creado'), 
                              ('done','Generado')], 'Estado', select=True,
                                required=True, readonly=True,default=lambda *a: 'draft')
    #===========================================================================

    _sql_constraints = [
        ('uniq_declaration', 'unique(fiscalyear_id,period_id)', 'Formulario Generado!')
    ]

        
    @api.multi
    def unlink(self):
        """"Método que controla borrado de registros"""
        for plt in self:
            if plt.state=='done' :
                 raise ValidationError('No puede borrar plantilla en estado Generado')
        return super(hr_employee_plantilla, self).unlink()
    
    
    @api.multi
    def done(self):
        
        self.write({'state': 'done'})
        return True
    
    @api.one
    @api.depends('period_id','fiscalyear_id')
    def get_values(self):
        
        #periodos_ids = self.env['hr.contract.period'].sudo().search([('fiscalyear_id', '=', self.fiscalyear_id.id)]).ids    

        fiscalyear = self.env['account.fiscalyear'].sudo().search([('id', '=', self.fiscalyear_id.id)]).id
        print" fiscalyear=%s"%fiscalyear
        period_ids = self.env['account.period'].sudo().search([('fiscalyear_id', '=', fiscalyear)]).ids         
          
        print" period_ids=%s"%period_ids
        payslip_ids= self.env['hr.payslip'].sudo().search([('period_id', 'in', period_ids),                                                        
                                                           ('state', 'not in', ['draft'])],
                                                           order='date_to desc')#, limit=12)
        
                                                 
        print" payslip_ids=%s"%payslip_ids
        print" self.period_id.code=%s"%self.period_id.code
        
        for payslip in payslip_ids:                      
                
            if payslip.period_id.fiscalyear_id.id==self.fiscalyear_id.id and payslip.period_id.code==self.period_id.code:
                
                # aporte patronal
                if payslip.struct_id.name =='PASANTIA' or 'GERENTE' in payslip.struct_id.name :
                   auxiliar=0
                else:
                    auxiliar  = sum([psl.amount for psl in payslip.line_ids if psl.code =='SUBT_INGRESOS'])
                    auxiliar  = auxiliar*0.1215
                ##auxiliar  = sum([psl.amount for psl in payslip.line_ids if 'IESSPATRONAL' in psl.code ]) # no se puede sumar ya que esta regla no es visible en el rol
                #total ingresos
                aux  = sum([psl.amount for psl in payslip.line_ids if psl.code =='SUBT_TOTINGRESOS']) + auxiliar
                #total descuentos
                aux1 = sum([psl.amount for psl in payslip.line_ids if psl.code =='SUBT_EGRESOS'])
                #total otros descuentos
                auxiliar1=sum([psl.amount for psl in payslip.line_ids if psl.salary_rule_id.category_id.code=='EGRESOS' and not psl.salary_rule_id.descuento_iess])
                #total descuentos iess-sri
                aux7 = sum([psl.amount for psl in payslip.line_ids if psl.salary_rule_id.category_id.code=='EGRESOS' and psl.salary_rule_id.descuento_iess]) + auxiliar          
                #total decimo tercero provisionado
                aux2 = sum([psl.amount for psl in payslip.line_ids if psl.code =='PROV DTERCERO' and psl.salary_rule_id.acumula])
                #total decimo cuarto provisionado
                aux3 = sum([psl.amount for psl in payslip.line_ids if psl.code =='PROV DCUARTO' and  psl.salary_rule_id.acumula])
                #total fondos de reserva provisionado
                aux4 = sum([psl.amount for psl in payslip.line_ids if psl.code =='PROV FOND RESERV' and psl.salary_rule_id.acumula])
                #total provision vacaciones
                aux5 = sum([psl.amount for psl in payslip.line_ids if psl.code =='SUBT_INGRESOS'])
                aux5=aux5/12
                #total sueldos a pagar
                aux6 = sum([psl.amount for psl in payslip.line_ids if psl.code =='SUBT_NET'])
                aux8 = sum([psl.amount for psl in payslip.line_ids if psl.code =='ANTI'])
              
                self.aux += aux
                self.aux1 += aux1
                self.aux2 += aux2
                self.aux3 += aux3
                self.aux4 += aux4
                self.aux5 += aux5
                self.aux6 += aux6
                self.aux7 += aux7
                self.aux8 += aux8
                self.auxiliar += auxiliar1
                self.aux_total += aux2 + aux3 + aux4 + aux5 + aux7 
                
                self.incomes_amount = self.aux
                self.expenses_amount = self.aux1
                self.dec3_amount = self.aux2
                self.dec4_amount = self.aux3
                self.fr_amount = self.aux4
                self.vacacion_amount = self.aux5
                self.wage = self.aux6
                self.retenciones= self.aux7
                self.other_expenses = self.auxiliar
                self.total_prov_ret= self.aux_total
                self.anticipos_remuneracion= self.aux8
                
                print"self.incomes_amount=%s"%self.incomes_amount
                print"self.expenses_amount=%s"%self.expenses_amount 
                print"self.retenciones=%s"%self.retenciones             


    
    
    @api.multi
    def _run_sql(self,anio,periodo):
        
        self.env.cr.execute('''SELECT pl.rule_name,sum(pl.amount) 
                                FROM hr_employee_plantilla_line pl
                                where pl.fiscalyear_id= %s and pl.period_id= %s
                                group by pl.rule_name order by 1 desc'''%(anio,periodo))            
        res = self.env.cr.dictfetchall()
        cadena= "".join(str(res))

        cadena0=cadena.replace("[{'rule_name': None, 'sum': None",'')
        cadena1=cadena0.replace("[{'rule_name': u'",'')
        cadena2=cadena1.replace("}, {'rule_name': u'",'\r\n')
        cadena3=cadena2.replace("', 'sum'",'')
        cadena4=cadena3.replace("}]",'')
        #cadena5=cadena4.replace(":",'  :')
        self.subquery=cadena4
        print"self.subquery=%s"%self.subquery
        return self.subquery
    
    @api.multi
    def _run_sql_ret(self,anio,periodo):
        
        self.env.cr.execute('''SELECT pl.rule_namer,sum(pl.amountr) 
                                FROM hr_employee_plantilla_line pl
                                where pl.fiscalyear_id= %s and pl.period_id= %s
                                group by pl.rule_namer order by 1 desc'''%(anio,periodo))
                    
        res = self.env.cr.dictfetchall()
        cadena= "".join(str(res))
        
        cadena0=cadena.replace("[{'rule_namer': None, 'sum': None",'')
        cadena1=cadena0.replace("[{'rule_namer': u'",'')
        cadena2=cadena1.replace("}, {'rule_namer': u'",'\r\n')
        cadena3=cadena2.replace("', 'sum'",'')
        cadena4=cadena3.replace("}]",'')
        #cadena5=cadena4.replace(":",'  :')
        self.subquery1=cadena4
        print"self.subquery1=%s"%self.subquery1
        return self.subquery1
    
    @api.multi
    @api.depends('period_id','fiscalyear_id')    
    def load_rule(self):
        print"rubros=%s"        
          
        #periodos_ids = self.env['hr.contract.period'].sudo().search([('fiscalyear_id', '=', self.fiscalyear_id.id)]).ids    

        fiscalyear = self.env['account.fiscalyear'].sudo().search([('id', '=', self.fiscalyear_id.id)]).id
        period_ids = self.env['account.period'].sudo().search([('fiscalyear_id', '=', fiscalyear)]).ids         
          
        payslip_ids= self.env['hr.payslip'].sudo().search([('period_id', 'in', period_ids),                                                        
                                                           ('state', 'not in', ['draft'])],
                                                           order='date_to desc')#, limit=12)
        
        
        ing_ids= self.env['hr.salary.rule'].sudo().search([('category_id', '=', 11)])
        oing_ids= self.env['hr.salary.rule'].sudo().search([('category_id', '=', 14)])
        lines_obj= self.env['hr.employee.plantilla.line']

        for payslip in payslip_ids:
            if payslip.period_id.fiscalyear_id.id==self.fiscalyear_id.id and payslip.period_id.code==self.period_id.code:
                for psl in payslip.line_ids:
                    if payslip.struct_id.name =='PASANTIA' or 'GERENTE' in payslip.struct_id.name:
                        auxiliar =0
                    else:
                        if psl.code =='SUBT_INGRESOS':
                            auxiliar  = sum([psl.amount])
                            auxiliar  = round(auxiliar*0.1215,2)
                        
                vals ={'plantilla_id':self.id,
                        'rule_name':'Aporte Patronal Iess',
                        'rule_namer':'Aporte Patronal Iess',
                        'rule_id':17,
                        'ruler_id':17,
                        'amount':auxiliar,
                        'amountr':auxiliar
                        }
                        
                 
                lines =self.env['hr.employee.plantilla.line'].create(vals)
                    
        for payslip in payslip_ids:                  
            if payslip.period_id.code==self.period_id.code:
                for psl in payslip.line_ids:                   
                    nplnt=[]
                    if psl.salary_rule_id.category_id.code in ('INGRESOS','OINGRESOS') or (psl.salary_rule_id.category_id.code in ('PROVISION','PROVISION1','PROVISION11') and not psl.salary_rule_id.acumula):
                    #if psl.salary_rule_id.category_id.code in ('INGRESOS','OINGRESOS','COMPANIA','PROVISION','PROVISION1','PROVISION11')  
                        
                        nplnt=psl.name
                        monto=psl.amount
                        rid=psl.salary_rule_id.id
                        
                    
                    if nplnt:
                        if psl.name==nplnt and psl.amount > 0:
                            
                            self.amount_aux = monto
                                                        
                            vals ={'plantilla_id':self.id,
                                   'rule_name':nplnt,
                                   'rule_id':rid,
                                   'amount':self.amount_aux
                                   }
                            lines =self.env['hr.employee.plantilla.line'].create(vals)                                    
                  
                    nret=[]            
                    if psl.salary_rule_id.category_id.code=='EGRESOS' and psl.salary_rule_id.descuento_iess:
                        nret=psl.name
                        monto=psl.amount
                        ret_id=psl.salary_rule_id.id    
                        
                    if psl.name==nret and psl.amount > 0:
                            
                            self.amount_aux = monto
                                                        
                            vals ={'plantilla_id':self.id,
                                   'rule_namer':nret,
                                   'ruler_id':ret_id,
                                   'amountr':self.amount_aux
                                   }
                            lines =self.env['hr.employee.plantilla.line'].create(vals)                
                            
        self._run_sql(self.period_id.fiscalyear_id.id,self.period_id.id)
        self._run_sql_ret(self.period_id.fiscalyear_id.id,self.period_id.id)            

        self.write({'detalle':True}) 

                           

                    

class hr_employee_plantilla_line(models.Model):
    _name = 'hr.employee.plantilla.line'
    _description = u'Detalle de plantilla'
    
    #===========================================================================
    # Columns
    plantilla_id = fields.Many2one('hr.employee.plantilla', string='Plantilla',required=True, ondelete='cascade', readonly=True,select=True)
    fiscalyear_id= fields.Many2one('account.fiscalyear',string='fiscal',related='plantilla_id.fiscalyear_id',store=True, readonly=True)
    period_id= fields.Many2one('account.period',string='periodo',related='plantilla_id.period_id',store=True, readonly=True)
    rule_name= fields.Text('Descripción Gasto')
    rule_id= fields.Integer('Id Regla')
    amount = fields.Float('Valor')
    rule_namer= fields.Text('Descripción Retencion')
    ruler_id= fields.Integer('Id Regla')
    amountr = fields.Float('Valor')
    
    

        
       
   
        
   