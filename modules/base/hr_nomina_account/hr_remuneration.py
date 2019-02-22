# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution.
#    Account module for basic payroll in Ecuador.
#    Copyright (C) 2010-2013 Israel Paredes Reyes. All Rights Reserved.
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
from openerp.osv import osv, fields

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    _columns = {
        'type_hr':fields.selection([('quincena', 'Quincena'),
                                    ('payrol', 'Rol Pagos'),
                                    ('anticipo', 'Anticipo'),
                                    ('prestamo', 'Prestamo'),
                                    ],
                                   'TipoHR', size=9),
    }
account_move_line()