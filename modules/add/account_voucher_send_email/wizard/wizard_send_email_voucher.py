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
from openerp.tools.translate import _

# from openerp import models, fields, api
# from openerp.exceptions import ValidationError
# import time



class voucher_lote_send_mail(osv.osv_memory):

    _name = "voucher.lote.send.mail"
    _description = "Send mail selected vouchers"

    def lote_voucher_send_mail(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        proxy = self.pool['account.voucher']
        for voucher in proxy.browse(cr, uid, active_ids, context=context):
            if voucher.state not in ('posted') :#recordc.authorization_sri == False:
                raise osv.except_osv(_('Warning!'), _("El cobro/pago debe estar contabilizado"))
            if voucher.partner_id.email:
                voucher.voucher_send_mail()
            else:
                raise osv.except_osv(_('Warning!'), _(u'%s No tiene configurado email'% voucher.partner_id.name))
                        
        return {'type': 'ir.actions.act_window_close'}
    
