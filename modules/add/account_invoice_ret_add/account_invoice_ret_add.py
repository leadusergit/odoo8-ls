# -*- coding: utf-8 -*-

import time
import datetime
import base64
from datetime import date
from datetime import datetime
from openerp import api, tools
from openerp.osv import fields , osv 
from openerp.tools.translate import _
import openerp.addons.mail.mail_thread
from openerp.exceptions import ValidationError
import smtplib

class account_invoice_retention(osv.osv): #models.Model
    _name = 'account.invoice.retention'
    _inherit = ['account.invoice.retention', 'mail.thread']
    #__logger = logging.getLogger(_inherit) 
    
    
    def action_cr_sent(self, cr, uid, ids, context):
        #template = addons.get_module_resource('l10n_ec_einvoice', 'report', 'account_print_retention.rml')
             
        for retention in self.browse(cr, uid, ids):
            email = retention.partner_id.email
            print"email =%s"%email 
            if not email:
                raise ValidationError(u'%s no tiene configurada direccion de correo' % retention.partner_id.name)
                continue
        
        obj = self.browse(cr, uid, ids)[0]
        name = '%s%s.xml' %(obj.company_id.vouchers_authorized, obj.access_key)
        cadena = open(name, mode='rb').read()
        attachment_id = self.pool.get('ir.attachment').create(cr, uid, 
            {
                'name': '%s.xml' % (obj.access_key),
                'datas': base64.b64encode(cadena),
                'datas_fname':  '%s.xml' % (obj.access_key),
                'res_model': self._name,
                'res_id': obj.id,
                'type': 'binary'
            }, context=context)
                            
        email_template_obj = self.pool.get('email.template')
        res_id = self.pool.get('mail.compose.message')
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_invoice_ret_add', 'email_template_edi_cr')[1]
        email_template_obj.write(cr, uid, template_id, {'attachment_ids': [(6, 0, [attachment_id])]})  
        ##email_template_obj.send_mail(cr, uid, template_id, obj.id, True)
        
        ctx = dict(
            default_use_template=bool(template_id),
            default_template_id=template_id,
            mark_invoice_as_sent=True,
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
        """return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            #'nodestroy': False,
            'res_model': 'mail.compose.message',
            #'views': [(compose_form.id, 'form')],
            #'view_id': compose_form.id,
            'target': 'new',#presenta wizard para envio de email
            #'context': ctx,
        }"""
      
    

    
account_invoice_retention()

  
