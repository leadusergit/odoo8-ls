# -*- coding: utf-8 -*-
###################################################
#
#    Accounting Module Ecuador
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
import time


from openerp.tools.translate import _

import datetime
from openerp.osv import osv
from openerp.osv import fields
from mx import DateTime
# import netsvc
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime
from openerp import tools

# from tools import config
import calendar
from lxml import etree

#CLASE HEREDADA DEL MODULO ACCOUNT VOUCHER

# class account_statement_from_invoice_inherit(osv.osv_memory):
#     """
#     Generate Entries by Statement from Invoices
#     """
#     _inherit = "account.statement.from.invoice"
#     
#     def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
#         ##print 'herencia del account_statement_from_invoice_inherit',context
#         res = super(account_statement_from_invoice_inherit, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
#         if context and 'line_ids' in context:
#             view_obj = etree.XML(res['arch'])
#             child = view_obj.getchildren()[0]
#             domain = '[("id", "in", '+ str(context['line_ids'])+')]'
#             field = etree.Element('field', attrib={'domain': domain, 'name':'line_ids', 'colspan':'4', 'height':'300', 'width':'800', 'nolabel':"1"})
#             child.addprevious(field)
#             res['arch'] = etree.tostring(view_obj)
#         return res
#     
#     
# account_statement_from_invoice_inherit()