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

from openerp import models, fields, api, _
from openerp.tools.translate import _

class hr_payslip_line(models.Model):
    
    _inherit = 'hr.payslip.line'
    _description = "Estado de Lineas de Rol"
    
    line_state = fields.Selection('hr.payslip',related='slip_id.state',store=True,readonly=True)
    
    

    @api.onchange('slip_id','line_state')
    def _onchange_state(self):
        if slip_id.state:
            self.line_state = self.slip_id.state           
        else:           
            self.line_state = 'draft'





    
          
