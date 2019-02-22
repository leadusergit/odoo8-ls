# -*- coding: utf-8 -*-

import time
import datetime
from datetime import date
from datetime import datetime
from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging
import openerp.addons.decimal_precision as dp


class asset_asset_confirm(osv.osv_memory):

    _name = "asset.asset.confirm"
    _description = "Procesar Activos Fijos"

    def confirm_asset(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        proxy = self.pool['account.asset.asset']
        for asset in proxy.browse(cr, uid, active_ids, context=context):
            if asset.state not in ('draft'):
                raise osv.except_osv(_('Warning!'), _("Estado Incorrecto"))
            asset.validate()
            
        return {'type': 'ir.actions.act_window_close'}
    
    def draft_asset(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        proxy = self.pool['account.asset.asset']
        for asset in proxy.browse(cr, uid, active_ids, context=context):
            if asset.state not in ('open'):
                raise osv.except_osv(_('Warning!'), _("Estado Incorrecto"))
            asset.set_to_draft()
            
        return {'type': 'ir.actions.act_window_close'}
    
    
    def close_asset(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        proxy = self.pool['account.asset.asset']
        for asset in proxy.browse(cr, uid, active_ids, context=context):
            if asset.state not in ('open'):
                raise osv.except_osv(_('Warning!'), _("Estado Incorrecto"))
            asset.set_to_close()
            
        return {'type': 'ir.actions.act_window_close'}