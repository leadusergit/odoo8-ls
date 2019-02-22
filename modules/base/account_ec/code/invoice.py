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
from openerp.osv import osv

class invoice(osv.osv):
    """
    Herencia para pagar factura desde Extracto
    Bancario.
    """
    _inherit = 'account.invoice'
    
    def pagar_factura(self, cr, uid, ids, context=None):
        if not ids: return []
        factura = self.browse(cr, uid, ids[0], context=context)
        return {
            'name': 'Pagar Factura',
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.bank.statement',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': {
                'name': 'Pago Factura %s' % (factura.number),
            }                
        }
    
#     def _refund_cleanup_lines(self, cr, uid, lines):
#         fields_line = self.pool.get('ir.model.fields').search(cr, 1, [('model', '=', 'account.invoice.line'), ('ttype', '=', 'many2one')])
#         fields = self.pool.get('ir.model.fields').read(cr, 1, fields_line)
#         for line in lines:
#             del line['id']
#             del line['invoice_id']
#             for field in (aux['name'] for aux in fields):
#                 line[field] = line.get(field, False) and line[field][0]
#             if 'invoice_line_tax_id' in line:
#                 line['invoice_line_tax_id'] = [(6,0, line.get('invoice_line_tax_id', [])) ]
#         return map(lambda x: (0,0,x), lines)
    
    
        
invoice()