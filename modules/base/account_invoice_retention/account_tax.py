# -*- coding: utf-8 -*-
###################################################
#
#    BUILDING CRM Module
#    Copyright (C) 2012 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
#    $autor: Dairon Medina Caro <dairon.medina@gmail.com>
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
###################################################

from openerp.osv import osv, fields

class account_tax(osv.osv):
    _name = "account.tax"
    _inherit = "account.tax"
    
    _columns = {
        'tax_group' : fields.selection([('vat','IVA no 0%'),('other','Other'),
                                        ('rete', 'Retencion'),('iva0','IVA 0%'),('noiva','No IVA')], "Grupo"),
        
        }
account_tax()