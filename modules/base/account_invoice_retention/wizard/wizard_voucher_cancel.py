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
from openerp import models, fields, api
import time
from openerp import tools

class move_line(models.Model):
    _inherit = 'account.move.line'
    #===========================================================================
    # Columns
    is_reverse = fields.Boolean('Reverso', help=u'Este campo me identifica la lineas que se generan un reverso desde los pagos a proveedores y desde el boton anular de pagos cheques',copy=False)
    
    #===========================================================================

class account_move(models.Model):
    _inherit = 'account.move' 
    #Do not touch _name it must be same as _inherit
    #_name = 'account.move'
    #===========================================================================
    # Columns
    to_reverse=fields.Boolean('Es Reverso', help="Ponga un check si este asiento esta utilizando como reverso de cheque anulado. "\
                                                 "Solo hace falta este check en los asientos que genera un reverso manual", copy=False)
    origen_reverso = fields.Char('Origen Reverso', help="Este campo se llenara con la informacon que cheque origen que genero el reverso", copy=False)
    #===========================================================================

class wizard_account_voucher_cancel(models.TransientModel):
    _name = 'wizard.account.voucher.cancel'
    _description = 'Asistente para cancelar un voucher'
     #===========================================================================
    # Columns
    move_date= fields.Date('Fecha del asiento', help='Deje en blanco para usar la fecha actual')
    period_id= fields.Many2one('account.period', 'Periodo', help='Deje en blanco para usar el periodo actual')
    reverse= fields.Boolean('Asiento de reversa')
    #===========================================================================
    
    def onchange_move_date(self, cr, uid, ids, date):
        period_id = self.pool.get('account.period').find(cr, uid, date)
        return {'value': {'period_id': period_id}}
    
    def btn_ok(self, cr, uid, ids, context=None):
        context = context or {}
        if not context.get('active_model') or not context.get('active_ids'):
            raise osv.except_osv('Error', 'Debe proporcionar el modelo y los ids del objeto a ejecutar.')
        obj = self.read(cr, uid, ids[0])
        context['reverse'] = obj['reverse']
        model = self.pool.get(context['active_model'])
        new_move_ids = []
        if obj['reverse']:
            move_date = obj['move_date'] or time.strftime('%Y-%m-%d')
            period_id = obj['period_id'] or self.pool.get('account.period').find(cr, uid, move_date)
            period_id = isinstance(period_id, tuple) and period_id[0] or period_id
            period_id = isinstance(period_id, list) and period_id[0] or period_id
            move_ids = [aux['move_id'][0] for aux in model.read(cr, uid, context['active_ids'], ['move_id'])]
            info = model.browse(cr, uid, context['active_ids'])
            if info:
                cheque = info[0].comprobante_id or False
            if move_ids:
                for move_id in self.pool.get('account.move').read(cr, uid, move_ids):
                    lines_ids = move_id['line_id']
                    vals = {'date': move_date, 'period_id': period_id, 'state': 'draft'}
                    move_id = dict((key, isinstance(val, tuple) and val[0] or val) for key, val in move_id.iteritems())
                    move_id.update(dict(vals, **{'no_comp': False, 'line_id': []}))
                    if cheque:
                        move_id.update(dict(vals, **{'ref':'CHQ-ANU-'+str(cheque.num_cheque),'other_info':'*REVERSO* '+tools.ustr(cheque.observation),'to_reverse':True,'origen_reverso':str(cheque.num_cheque)}))
                    for line_id in self.pool.get('account.move.line').read(cr, uid, lines_ids):
                        line_id = dict((key, isinstance(val, tuple) and val[0] or val) for key, val in line_id.iteritems())
                        line_id.update(dict(vals, **{'credit': line_id['debit'], 'debit': line_id['credit'], 'reconcile_id': False, 'reconcile_partial_id': False,'x_conciliado':False}))
                        if cheque:
                            line_id.update(dict(vals, **{'ref':'CHQ-ANU-'+str(cheque.num_cheque),'is_reverse': True}))
                        move_id['line_id'].append((0, 0, line_id))
                    new_move_ids.append(self.pool.get('account.move').create(cr, uid, move_id))
                self.pool.get('account.move').post(cr, uid, new_move_ids)
        model.cancel_voucher(cr, uid, context['active_ids'], context)
        return {'type': 'ir.actions.act_window_close'}
    
wizard_account_voucher_cancel()