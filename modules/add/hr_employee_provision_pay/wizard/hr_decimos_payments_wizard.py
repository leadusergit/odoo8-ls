# -*- coding: utf-8 -*-

import time
from openerp import netsvc

import datetime
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.addons.hr_nomina import payroll_tools
from openerp import models, fields, api
from openerp.exceptions import ValidationError
import logging
from docutils.nodes import line_block
       
class hr_payment_decimos_employee_wizard(models.TransientModel):
    
    """Genera voucher para pago de decimos de los empleados seleccionados opcion Generar Decimos(hr.payslip)"""
    _name = 'hr.payments.decimos.employee.wizard'

    
    journal_id=fields.Many2one('account.journal', 'Método de pago', required=True, domain=[('type', '=', 'bank')])
    date=fields.Date('Fecha', default=time.strftime('%Y-%m-%d'),required=True)
    ref=fields.Char('Referencia', required=True)
    employee_ids = fields.Many2many('hr.employee', 'employee_nomina_rel', 'address_home_id', 'employee_id', 'Employees')

    pago_dt=fields.Boolean('Pago Decimo Tercero', default= False, readonly=False,)
    pago_dc= fields.Boolean('Pago Decimo Cuarto', default= True , readonly=False)

          
                
    @api.multi
    def compute_sheet_decimos(self):
        self = self[0]
        
        print"self.employee_ids=%s"%self.employee_ids
        for employee in self.employee_ids:
                       
            provision =employee.pago_provisiones
            print"employee.pago_provisiones=%s"%employee.pago_provisiones
            partner=employee.address_home_id.id
            account=self.journal_id.default_credit_account_id.id
            company= employee.company_id.id,
            currency=employee.company_id.currency_id.id
            journal=self.journal_id.id
            print"partner=%s"%partner
            print"account=%s"%account
            print"company=%s"%company
            print"currency=%s"%currency
            print"journal=%s"%journal            
                
            vals = dict(
                        reference=self.ref,
                        partner_id=partner,
                        journal_id=self.journal_id.id, 
                        amount=0.0,
                        currency_id=currency,
                        type='payment', 
                        date=self.date,
                        company_id=company,
                        account_id=account,
                        pre_line= True,
                        payment_option='without_writeoff',
                        pago_dc=self.pago_dc,
                        pago_dt=self.pago_dt,
                        narration=self.ref,
                        transfers=[]
                        )
                        
                 
            voucher =self.env['account.voucher'].create(vals)

       