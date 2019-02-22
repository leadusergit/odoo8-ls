# -*- coding: utf-8 -*-
##############################################################################
#
#    E-Invoice Module - Ecuador
#    Copyright (C) 2014 VIRTUALSAMI CIA. LTDA. All Rights Reserved
#    alcides@virtualsami.com.ec
#    $Id$
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv
from openerp.tools.translate import _

class account_invoice_send(osv.osv_memory):

    _name = "account.invoice.send"
    _description = "Send selected invoices"

    def invoice_send(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        proxy = self.pool['account.invoice']
        for recordf in proxy.browse(cr, uid, active_ids, context=context):
            if recordf.state not in ('open') or recordf.autorizado_sri == True:
                raise osv.except_osv(_('Warning!'), _("Los comprobantes electrónicos deben estar en estado abierto y no autorizadas"))
            recordf.action_generate_einvoice()
            
        return {'type': 'ir.actions.act_window_close'}
    

class account_invoice_retention_send(osv.osv_memory):

    _name = "account.invoice.retention.send"
    _description = "Send selected invoices"

    def invoice_retention_send(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        proxy = self.pool['account.invoice.retention']
        for record in proxy.browse(cr, uid, active_ids, context=context):
            if record.state not in ('paid') or record.authorization_sri == True:
                raise osv.except_osv(_('Warning!'), _("Los comprobantes electrónicos deben estar en estado realizado y no autorizadas"))
            
            
            record.action_generate_eretention()
            acceskey= record.access_key
            record.action_authorization_sri(acceskey)
            
        return {'type': 'ir.actions.act_window_close'}
    
    
"""class account_invoice_retention_auth(osv.osv_memory):

    _name = "account.invoice.retention.auth"
    _description = "Auth selected invoices"

    def invoice_retention_auth(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        proxy = self.pool['account.invoice.retention']
        for rd in proxy.browse(cr, uid, active_ids, context=context):
            if rd.authorization_sri == True:
                raise osv.except_osv(_('Warning!'), _("Los comprobantes electrónicos deben estar en estado realizado y no autorizados"))     
          
            acceskey= rd.access_key
            rd.action_authorization_sri(acceskey)
        
        return {'type': 'ir.actions.act_window_close'} """  
    
    
          
