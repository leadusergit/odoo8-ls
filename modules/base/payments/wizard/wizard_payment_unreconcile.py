# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Asset work
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
#creador  *EG

import time
import datetime
from openerp.osv import osv
from openerp.osv import fields
from mx import DateTime
import openerp.netsvc
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime
import openerp.tools
from openerp.tools.translate import _
from openerp.tools import config
import calendar


class wizard_payment_unreconcile(osv.osv_memory):
    _name = "wizard.payment.unreconcile"
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    def _get_move_line(self, cr, uid, context={}):
        #print 'context',context
        res = []
        for item in self.pool.get('payment.cheque').browse(cr, uid, context.get('active_ids')):
            for line in item.cheque_det_ids:
                if line.line_id:
                    res.append(line.line_id.id)
        #print "res_move_line", res
        return res
    
    def act_unreconcile(self, cr, uid, ids, context=None):
        #print 'ids',ids
        #print 'context',context
        res = []
        unlink_ids = []
        for item in self.pool.get('payment.cheque').browse(cr, uid, context.get('active_ids')):
            for line in item.cheque_det_ids:
                if line.line_id:
                    res.append(line.line_id.id)
            #print "res_move_line", res
            if res:
                recs = self.pool.get('account.move.line').read(cr, uid, res, ['reconcile_id','reconcile_partial_id'])
                
                full_recs = filter(lambda x: x['reconcile_id'], recs)
                rec_ids = [rec['reconcile_id'][0] for rec in full_recs]
                
                part_recs = filter(lambda x: x['reconcile_partial_id'], recs)
                part_rec_ids = [rec['reconcile_partial_id'][0] for rec in part_recs]
            
                unlink_ids += rec_ids
                unlink_ids += part_rec_ids
            
            if len(unlink_ids):
                #print "entra", unlink_ids
                self.pool.get('account.move.reconcile').unlink(cr, uid, unlink_ids)
            #Pagos desde una linea directa del extracto
            self.pool.get('payment.cheque').write(cr, uid, item.id, {'state':'cancel'})
            for line in item.cheque_det_ids:
                self.pool.get('payment.cheque.detail').write(cr, uid, line.id, {'state':'cancel'})
            
        result = {'type': 'ir.actions.act_window_close'}
        return result
    
wizard_payment_unreconcile()

class wizard_transfer_unreconcile(osv.osv_memory):
    _name = "wizard.transfer.unreconcile"
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    def _get_move_line(self, cr, uid, context={}):
        #print 'context',context
        res = []
        for item in self.pool.get('payment.cheque').browse(cr, uid, context.get('active_ids')):
            for line in item.cheque_det_ids:
                if line.line_id:
                    res.append(line.line_id.id)
        #print "res_move_line", res
        return res
    
    def act_unreconcile(self, cr, uid, ids, context=None):
        #print 'ids',ids
        #print 'context',context
        res = []
        unlink_ids = []
        for item in self.pool.get('payment.transfer').browse(cr, uid, context.get('active_ids')):
            for line in item.transfer_ids:
                if line.line_id:
                    res.append(line.line_id.id)
            #print "res_move_line", res
            if res:
                recs = self.pool.get('account.move.line').read(cr, uid, res, ['reconcile_id','reconcile_partial_id'])
                
                full_recs = filter(lambda x: x['reconcile_id'], recs)
                rec_ids = [rec['reconcile_id'][0] for rec in full_recs]
                
                part_recs = filter(lambda x: x['reconcile_partial_id'], recs)
                part_rec_ids = [rec['reconcile_partial_id'][0] for rec in part_recs]
            
                unlink_ids += rec_ids
                unlink_ids += part_rec_ids
            
            if len(unlink_ids):
                #print "entra", unlink_ids
                self.pool.get('account.move.reconcile').unlink(cr, uid, unlink_ids)
            #Pagos desde una linea directa del extracto
            self.pool.get('payment.transfer').write(cr, uid, item.id, {'state':'cancel'})
            for line in item.transfer_ids:
                self.pool.get('payment.transfer.line').write(cr, uid, line.id, {'state':'cancel'})
            
            
        result = {'type': 'ir.actions.act_window_close'}
        return result
    
wizard_transfer_unreconcile()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: