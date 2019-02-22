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

class hr_payslip_wizard(osv.osv_memory):

    _name = "hr.payslip.wizard"
    _description = "Confirmar Payslips"

    def confirm_payslip(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        proxy = self.pool['hr.payslip']
        for recordp in proxy.browse(cr, uid, active_ids, context=context):
            if recordp.state not in ('draft','verify'):
                raise osv.except_osv(_('Warning!'), _("Estado del Rol Incorrecto al Contabilizar el Rol"))
            recordp.process_sheet()
            
        return {'type': 'ir.actions.act_window_close'}
        
    
          
