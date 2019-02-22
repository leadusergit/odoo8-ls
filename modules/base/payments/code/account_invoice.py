# -*- coding: utf-8 -*-
##############################################################################
#
#    Payments Ecuador
#    Copyright (C) 2010-2010 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
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
import time
import openerp.netsvc
from openerp.osv import osv, fields
from openerp.tools.misc import currency
from openerp.tools.translate import _
import datetime
# import openerp.tools
#Aumento libreria
from openerp.addons.decimal_precision import decimal_precision as dp

"""
Hereda la clase de la factura
"""
class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    """
    Se aumenta el metodo para cambiar de estado la factura de pagada a abierta
    """
    def change_state_paid_to_open(self, cr, uid, ids, context):
        if context is None:
            context = {}
            
        if 'invoice_ids' in context:
            data_invs = self.browse(cr, uid, context['invoice_ids'], context=context)
            for data_inv in data_invs:
                if data_inv.reconciled:
                    raise osv.except_osv(_('Warning'), _('Invoice is already reconciled'))
            for data_inv in data_invs:    
                wf_service = netsvc.LocalService("workflow")
                res = wf_service.trg_validate(uid, 'account.invoice', data_inv.id, 'open_test', cr)
    
        
account_invoice()        

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
    def get_comprobante_pago(self, cr, uid, ids, field, args, context=None):
        res = dict.fromkeys(ids)
        vouchers_ids = self.browse(cr, uid, ids)
        for voucher_id in vouchers_ids:
            origin = 'PAGO #%s (%s)'%(voucher_id.number, voucher_id.id)
            for model in ['payment.cheque', 'payment.transfer']:
                args = [('origin', '=', origin), ('state', '!=', 'cancel')]
                comprobante_id = self.pool.get(model).search(cr, uid, args, limit=1)
                if comprobante_id:
                    res[voucher_id.id] = '%s,%s'%(model, comprobante_id[0])
        return res
    
    _columns = {
        'comprobante_id': fields.function(get_comprobante_pago, method=True, string='Forma de pago', type='reference', size=128,
                                          selection=[('payment.cheque', 'Cheque'), ('payment.transfer', 'Transferencia')]),
    }
    
    def button_proforma_voucher(self, cr, uid, ids, context=None):
        self.signal_workflow(cr, uid, ids, 'proforma_voucher')
        mod_obj = self.pool.get('ir.model.data')
        if 'type' in context:
            if context.get('type') == 'receipt':
                res = mod_obj.get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_form')
                return {
                        'name': 'Pago de Cliente',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'view_id': [res and res[1] or False],
                        'res_model': 'account.voucher',
                        'context': context,
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'current',
                        'res_id': ids and ids[0]  or False,##please replace record_id and provide the id of the record to be opened
                        }
            else:
                res = mod_obj.get_object_reference(cr, uid, 'account_voucher', 'view_vendor_payment_form')
                return {
                        'name': 'Pago de Proveedor',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'view_id': [res and res[1] or False],
                        'res_model': 'account.voucher',
                        'context': context,
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'current',
                        'res_id': ids and ids[0]  or False,##please replace record_id and provide the id of the record to be opened
                        }
        
    def cancel_voucher(self, cr, uid, ids, context=None):
        vouchers_ids = self.browse(cr, uid, ids)
        for comprobante in [aux.comprobante_id for aux in vouchers_ids]:
            if comprobante:
                model_pool = self.pool.get(comprobante._name)
                new_state = 'cancel' if comprobante.state in ['printed', 'cancel'] else 'draft'
                valor = False
                if 'reverse' in context and context.get('reverse', False):
                    valor = True
                model_pool.write(cr, uid, [comprobante.id], {'state': new_state,'has_reverso':valor})
                if new_state == 'draft':
                    model_pool.unlink(cr, uid, [comprobante.id])
        return super(account_voucher, self).cancel_voucher(cr, uid, ids, context)
    
account_voucher()

class account_conciliation_line(osv.osv):
    _inherit = "account.conciliation.line"
    
    def _get_nro(self, cr, uid, ids, field, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            move_id = obj.aml_id and obj.aml_id.move_id.id
            nro = ''
            for comprobante_model in ['payment.cheque', 'payment.transfer']:
                comprobante_pool = self.pool.get(comprobante_model)
                comprobante_id = comprobante_pool.search(cr, uid, [('move', '=', move_id), ('state', 'in', ['done', 'printed'])], limit=1)
                if comprobante_id:
                    comprobante_id = comprobante_pool.browse(cr, uid, comprobante_id[0])
                    nro = comprobante_model == 'payment.cheque' and 'CH. ' or 'TRF. '
                    nro += (comprobante_model == 'payment.cheque' and comprobante_id.num_cheque or comprobante_id.num_exit_voucher) or 'S/N'
                    break
            res[obj['id']] = nro
        return res
    
    _columns = {
        'nro': fields.function(_get_nro, method=True, string='Nro. Comprobante', type='char', size=64)
    }
account_conciliation_line()