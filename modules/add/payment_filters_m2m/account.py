# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    All Rights Reserved.
#    info skype: german_442 email: (german.ponce@outlook.com)
############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import pooler, tools

class account_voucher(osv.osv):
    _name = 'account.voucher'
    _inherit ='account.voucher'
    _columns = {

        'invoice_filters_cr_ids': fields.many2many('account.invoice',
            'voucher_id','invoice_id','voucher_invoice_rel', 'Facturas'),

        'invoice_filters_dr_ids': fields.many2many('account.invoice',
            'voucher_id','invoice_id','voucher_invoice_rel', 'Facturas'),

        }

    _defaults = {
        }

    def barrido_facturas_cr(self, cr, uid, ids, context=None):
        self_br = self.browse(cr, uid, ids, context=None)[0]
        voucher_line_obj = self.pool.get('account.voucher.line')
        if self_br.invoice_filters_cr_ids:
            if self_br.state == 'draft':
                filters_names = [str(x.number) for x in self_br.invoice_filters_cr_ids]
                voucher_line_ids = voucher_line_obj.search(cr, uid, 
                    [('voucher_id','=',ids[0]),('name','not in',tuple(filters_names)),
                    ('type','=','cr')])
                if voucher_line_ids:
                    voucher_line_obj.unlink(cr, uid, voucher_line_ids, context)
        return True

    def barrido_facturas_dr(self, cr, uid, ids, context=None):
        self_br = self.browse(cr, uid, ids, context=None)[0]
        voucher_line_obj = self.pool.get('account.voucher.line')
        if self_br.invoice_filters_dr_ids:
            if self_br.state == 'draft':
                filters_names = [str(x.number) for x in self_br.invoice_filters_dr_ids]
                voucher_line_ids = voucher_line_obj.search(cr, uid, 
                    [('voucher_id','=',ids[0]),('name','not in',tuple(filters_names)),
                    ('type','=','dr')])
                if voucher_line_ids:
                    voucher_line_obj.unlink(cr, uid, voucher_line_ids, context)
        return True
    # def reset_lines(self, cr, uid, ids, context=None):
    #     self_br = self.browse(cr, uid, ids, context=None)[0]
    #     res = self.onchange_journal(cr, uid, ids, self_br.journal_id.id,
    #     self_br.line_cr_ids, False, self_br.partner_id.id, self_br.date,
    #     self_br.amount, self_br.type, self_br.company_id.id ,context)
    #     print "###################### RES >>>>>>>>>>>>>>> ", res['value']['line_cr_ids']
    #     self_br.write({'line_cr_ids': res['value']['line_cr_ids']})
    #     return res