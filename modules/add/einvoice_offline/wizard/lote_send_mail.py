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

class account_invoice_lote_send_mail(osv.osv_memory):

    _name = "account.invoice.lote.send.mail"
    _description = "Send mail selected invoices"

    def lote_invoice_send_mail(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        proxy = self.pool['account.invoice']
        for recordf in proxy.browse(cr, uid, active_ids, context=context):
            if recordf.state in ('draft') :#or recordf.autorizado_sri == False:
                raise osv.except_osv(_('Warning!'), _("Los comprobantes electrónicos deben estar en estado Abierto"))
            if recordf.partner_id.email:
                recordf.action_einvoice_send_mail()
            else:
                raise osv.except_osv(_('Warning!'), _(u'%s no tiene configurado email'% recordf.partner_id.name))
                        
        return {'type': 'ir.actions.act_window_close'}
       
    
class retention_lote_send_mail(osv.osv_memory):

    _name = "retention.lote.send.mail"
    _description = "Send mail selected retentions"

    def lote_retention_send_mail(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        proxy = self.pool['account.invoice.retention']
        for recordc in proxy.browse(cr, uid, active_ids, context=context):
            if recordc.state not in ('paid') :#recordc.authorization_sri == False:
                raise osv.except_osv(_('Warning!'), _("Los comprobantes electrónicos deben estar en estado Realizados"))
            if recordc.partner_id.email:
                recordc.retention_send_mail()
            else:
                raise osv.except_osv(_('Warning!'), _(u'%s no tiene configurado email'% recordf.partner_id.name))
                        
        return {'type': 'ir.actions.act_window_close'}
          
