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

from openerp.osv import osv, fields
from openerp.tools.translate import _

class account_invoice_treeview(osv.osv):
    
    _inherit = 'account.invoice'
    _description = "Ruc tree view"
    
    _columns = {
        'ident_partner_num': fields.related('partner_id','ident_num',type='char', string='CI/Ruc',readonly=True,store=True), 
        }
    
    
class account_invoice_tax(osv.osv):
    
    _inherit = 'account.invoice.tax'
    _description = "Tax Graph view"
    
    _columns = {
        'date_invoice': fields.related('invoice_id','date_invoice',type='date', string='Fecha Fac',readonly=True,store=True),
        'state_fact': fields.related('invoice_id','state',type='char', string='Estado Fact',readonly=True,store=True),  
        #'date_retention': fields.related('ret_id','fecha',type='date', string='Fecha Ret',readonly=True,store=True), 

        }




    
          
