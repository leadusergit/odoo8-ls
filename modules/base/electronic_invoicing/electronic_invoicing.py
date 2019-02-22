# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    Author: Israel Paredes Reyes <israelparedesreyes@gmail.com>
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
from suds.client import Client
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class electronic_invoicing_ws(osv.osv):
    _name = 'electronic.invoicing.ws'
    _columns = {
        'name': fields.char('Descripción', size=64, required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'company_id': fields.many2one('res.company', 'Compañia', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'host': fields.char('Host', size=128, required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'port': fields.integer('Puerto', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'user': fields.char('Usuario', size=64, required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'password': fields.char('Contraseña', size=64, required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'dbname': fields.char('Base de datos', size=64, required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'wsdl': fields.char('WSDL', size=512, required=True, help='Path de la localización del archivo WSDL', readonly=True, states={'draft':[('readonly',False)]}),
        'state': fields.selection([('draft', 'Borrador'), ('active', 'Activo')], 'Estado', required=True, readonly=True),
        'description': fields.function(lambda self, cr, uid, ids, *a: dict([(o.id, self.__get_description(o.wsdl)) for o in self.browse(cr, uid, ids)]),
                                       method=True, type='text', string='Descripción del servicio',
                                       store={_name: (lambda self, cr, uid, ids, *a: ids, ['wsdl', 'state'], 10)}),
    }
    _defaults = {
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, uid, ctx).company_id.id 
    }
    
    def get_ws(self, cr, uid, company_id, context=None):
        ids = self.search(cr, uid, [('state', '=', 'active'), ('company_id', '=', company_id)])
        ws_id = bool(ids) and ids[0]
        return self.browse(cr, uid, ws_id, context=context)
    
    def check_docs(self, cr, uid, docs_ids=[], context=None):
        date = datetime.today() - timedelta(days=14)
        if not docs_ids:
            for model in ['account.invoice', 'account.invoice.retention']:
                res = {}
                model_pool = self.pool.get(model)
                for args in ([('fe_state', 'in', ['draft', 'receive'])],
                             [('fe_id', '>', 0), ('fe_auth_date', '>', date.strftime('%Y-%m-%d'))]):
                    docs = model_pool.search(cr, uid, args)
                    res.update(dict.fromkeys(docs))
                docs_ids.extend([(aux, model) for aux in res.keys()])
        if not docs_ids:
            return
        _logger.info('F.E.: Start to check %s electronic documents.'%len(docs_ids))
        group = {}
        for doc_id, model in docs_ids:
            aux = self.pool.get(model).read(cr, uid, doc_id, ['fe_id', 'company_id'])
            doc_ids = group.get(aux['company_id'][0], {})
            doc_ids[aux['fe_id']] = (doc_id, model)
            group[aux['company_id'][0]] = doc_ids
        for company_id, doc_ids in group.iteritems():
            ws_id = self.get_ws(cr, uid, company_id, context)
            if not ws_id:
                _logger.warning(u'F.E.: No se ha encontrado una configuración para el S.W. del facturador electrónico')
                return
            client = Client(ws_id.wsdl)
            res = client.service.check_docs(ws_id.host, ws_id.port, ws_id.dbname, ws_id.user, ws_id.password, doc_ids.keys())
            try:
                res = eval(res)
            except:
                return
            for fe_id, (doc_id, model) in doc_ids.iteritems():
                if not res.has_key(fe_id):
                    _logger.info('F.E.: Documento electrónico (%s) no encontrado del modelo (%s)'%(fe_id, model))
                    fields = self.pool.get(model).fields_get(cr, uid).keys()
                    res[fe_id] = dict((field[3:], False) for field in fields if field.startswith('fe_'))
                self.pool.get(model).save_result(cr, uid, {doc_id: res[fe_id]}, context=context)
        _logger.info('F.E.: End the check task.')
        return
    
    def __get_description(self, wsdl):
        try:
            client = Client(wsdl)
            return str(client)
        except:
            return False
            
    def activate(self, cr, uid, ids, context=None):
        context = context or {}
        state = context.get('new_state', 'active')
        for config in self.read(cr, uid, ids, ['wsdl']):
            if state == 'active' and not self.__get_description(config['wsdl']):
                raise osv.except_osv('Error', 'No se puede obtener el esquema desde la dirección indicada')
        self.write(cr, uid, ids, {'state': state})
    
electronic_invoicing_ws()

class electronic_invoicing_send(osv.osv_memory):
    _name = 'electronic.invoicing.send'
    _columns = {
        'create_uid': fields.many2one('res.users', 'Usuario'),
        'ws_id': fields.many2one('electronic.invoicing.ws', 'Servicio', domain=[('state', '=', 'active')], required=True),
        'doc_model': fields.selection([('account.invoice', 'Facturas'), ('account.invoice.retention', 'Retenciones')],
                                string='Documento', type='char', size=64, required=True),
        'invoice_ids': fields.many2many('account.invoice', 'wiz_invoice_rel', 'wiz_id', 'invoice_id', 'Documentos',
                                        domain=[('state', 'in', ['open', 'paid']), ('type', 'in', ['out_invoice', 'out_refund']), ('fe_state', 'in', [False, 'delete'])]),
        'retention_ids': fields.many2many('account.invoice.retention', 'wiz_retention_rel', 'wiz_id', 'retention_id', 'Retenciones',
                                        domain=[('state', 'in', ['paid']), ('type', '=', 'retention'), ('fe_state', 'in', [False, 'delete'])]),
        'result': fields.text('Resultado'),
        'state': fields.selection([('draft', 'Borrador'), ('done', 'Realizado')], 'Estado', required=True)
    }
    
    def default_ws(self, cr, uid, context=None):
        ws_pool = self.pool.get('electronic.invoicing.ws')
        ws_id = ws_pool.search(cr, uid, [('state', '=', 'active')], limit=1)
        return ws_id and ws_id[0] or False
    
    _defaults = {  
        'create_uid': lambda self, cr, uid, *a: uid,
        'ws_id': default_ws,
        'doc_model': lambda self, *a: self.__get_defaults(*a).get('doc_model', 'account.invoice.retention'),
        'invoice_ids': lambda self, *a: self.__get_defaults(*a).get('invoice_ids', []),
        'retention_ids': lambda self, *a: self.__get_defaults(*a).get('retention_ids', []),
        'state': lambda *a: 'draft'
    }
    
    def __get_defaults(self, cr, uid, context):
        ctx = {}
        ctx['doc_model'] = context.get('default_doc_model', context.get('active_model'))
        if context.get('active_model') and context.get('active_ids'):
            doc_pool = self.pool.get(context['active_model'])
            args = [('id', 'in', context['active_ids']), ('fe_state', 'in', [False, 'delete'])]
            if context['active_model'] == 'account.invoice':
                args.extend([('state', 'in', ['open', 'paid']), ('type', 'in', ['out_invoice', 'out_refund'])])
                doc_ids = doc_pool.search(cr, uid, args, context=context)
                ctx['invoice_ids'] = doc_ids
            elif context['active_model'] == 'account.invoice.retention':
                args.extend([('state', 'in', ['paid']), ('type', '=', 'retention')])
                doc_ids = doc_pool.search(cr, uid, args, context=context)
                ctx['retention_ids'] = doc_ids
        return ctx
    
    def send(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        doc_pool = self.pool.get(obj.doc_model)
        if obj.doc_model == 'account.invoice':
            doc_ids = obj.invoice_ids
        elif obj.doc_model == 'account.invoice.retention':
            doc_ids = obj.retention_ids
        documents = doc_pool.get_datas(cr, uid, [aux.id for aux in doc_ids], context=context)
        res = 'No se pudo enviar los documentos'
        if documents:
            client = Client(obj.ws_id.wsdl)
            res = client.service.send_data(obj.ws_id.host, obj.ws_id.port, obj.ws_id.dbname, obj.ws_id.user, obj.ws_id.password, [str(doc) for doc in documents])
            try:
                data = eval(res)
            except:
                data = None
            if data:
                res = doc_pool.save_result(cr, uid, data, context)
        self.write(cr, uid, ids, {'result': res, 'state': 'done'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Resultado del envío de documentos electrónicos',
            'res_model': self._name,
            'res_id': ids[0],
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new'
        }
    
electronic_invoicing_send()
