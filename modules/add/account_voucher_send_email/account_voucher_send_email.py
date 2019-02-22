# -*- coding: utf-8 -*-


import time
import datetime
import base64
import openerp.addons.mail.mail_thread
import smtplib
import time, logging, openerp.modules as addons
import openerp.addons.decimal_precision as dp


from openerp import netsvc
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from openerp.addons.report.models import abstract_report 
from openerp.addons.hr_nomina import payroll_tools
from openerp.tools import config, email_send
from mako.template import Template
from openerp.report import report_sxw
import logging

_logger = logging.getLogger(__name__)




class account_voucher(osv.osv): #models.Model
    _inherit = 'account.voucher'
    
    _columns = {                
        'send_email': fields.boolean('Email Enviado?')
    }
    
    
    def action_voucher_sent(self, cr, uid, ids, context):
             
        for voucher in self.browse(cr, uid, ids):
            email = voucher.partner_id.email
            print"email =%s"%email 
            if not email:
                raise ValidationError(u'%s No tiene configurada direccion de correo' % voucher.partner_id.name)
                continue
        
        obj = self.browse(cr, uid, ids)[0]
        email_template_obj = self.pool.get('email.template')
        res_id = self.pool.get('mail.compose.message')
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher_send_email', 'email_template_edi_vchr')[1]
        
        ctx = dict(
            default_use_template=bool(template_id),
            default_template_id=template_id,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'target': 'new',
            'context': ctx,
        }
    
    
    
    def voucher_send_mail(self, cr, uid, ids, context=None):
        
        obj = self.browse(cr, uid, ids)[0]

        email_template_obj = self.pool.get('email.template')
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher_send_email', 'email_template_voucher')[1]
        #email_template_obj.write(cr, uid, template_id, {'attachment_ids': [(6, 0, [attachment_id])]})  
        email_template_obj.send_mail(cr, uid, template_id, obj.id, True)

        return True
    
 
account_voucher()

  
