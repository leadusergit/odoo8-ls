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

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    def unlink(self, cr, uid, ids, context=None):
        invoices = self.browse(cr, uid, ids, context=context)
        for invoice in invoices:
            if invoice.fe_id > 0:
                raise osv.except_osv('ValidationError', 'No puede eliminar facturas que ya poseen un documento electrónico generado.')
        return super(account_invoice, self).unlink(cr, uid, ids, context)
        
    def _zfill (self, cr, uid, ids, field_name, args, context):
        res = {}
        invoices = self.browse(cr, uid, ids)
        for invoice in invoices:
            nro_factura =  invoice.fe_nro_comprobante
            if invoice.type in ('in_invoice', 'in_refund'):
                nro_factura = invoice.number_inv_supplier
            res[invoice.id] = str(nro_factura).zfill(9) if nro_factura else ''
        return res
    
    _columns = {
        'factura': fields.function(_zfill, method=True, type='char', size=16, string='Nro. Factura',
                                   store={'account.invoice': (lambda self, cr, uid, ids, *a: ids, None, 10)}),
        'fe_id': fields.integer('ID del documento', readonly=True),
        'fe_auth_key': fields.char('Autorización S.R.I.', size=37, readonly=True),
        'fe_auth_date': fields.date('Fecha de autorización', readonly=True),
        'fe_subtotal_untaxed': fields.float('Subtotal sin impuestos', readonly=True),
        'fe_subtotal_12': fields.float('Subtotal 12%', readonly=True),
        'fe_subtotal_0': fields.float('Subtotal 0%', readonly=True),
        'fe_sub_no_obj_iva': fields.float('Subtotal no objeto de IVA', readonly=True),
        'fe_total_descuentos': fields.float('Total descuentos', readonly=True),
        'fe_valor_ice': fields.float('Valor ICE', readonly=True),
        'fe_iva_12': fields.float('IVA 12%', readonly=True),
        'fe_valor_total': fields.float('Valor total', readonly=True),
        'fe_contingencia': fields.boolean('Contingencia'),
        'fe_nro_comprobante': fields.integer('Nro de comprobante', readonly=True),
        'fe_state': fields.char('Estado', size=32, readonly=True),
    }
    
    def check_docs(self, cr, uid, ids, context=None):
        ws_pool = self.pool.get('electronic.invoicing.ws')
        ids = self.search(cr, uid, [('id', 'in', ids), ('state', 'in', ['open', 'paid']), ('type', 'in', ['out_invoice', 'out_refund']), ('fe_state', '!=', False)])
        if not ids:
            raise osv.except_osv('Error', u'El (los) documento(s) que intenta chequear no se encuentran generados como electrónicos.')
        doc_ids = [(id, 'account.invoice') for id in ids]
        ws_pool.check_docs(cr, uid, doc_ids, context=None)
        return True
    
    def get_datas(self, cr, uid, ids, context=None):
        IDENT_TYPE = dict([('c', '05'), ('p', '06'), ('r', '04'), ('s', '07')])
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        documents = []
        for invoice_id in self.browse(cr, uid, ids, context=context):
            if not invoice_id.invoice_line:
                continue
            document = dict(
                id = invoice_id.id,
                tipo_comprobante = '01',
                pos_id = company_id.num_sucursal.zfill(3),
                fecha_emision = invoice_id.date_invoice,
                cons_final = invoice_id.partner_id.ident_num == '9999999999999',
                razon_social_cliente = dict(
                    ruc = invoice_id.partner_id.ident_num,
                    tdoc_comprador = IDENT_TYPE[invoice_id.partner_id.ident_type],
                    nombre_comercial = invoice_id.partner_id.name,
                    name = invoice_id.partner_id.name,
                    street = invoice_id.partner_id.street,
                    street2 = invoice_id.partner_id.street2,
                    phone = invoice_id.partner_id.phone,
                    email = invoice_id.partner_id.email or 'sinmail@openconsulting.com.ec'
                ),
                invoice_line_ids = []
            )
            if invoice_id.type == 'out_refund' and invoice_id.origin:
                origin_inv_id = invoice_id.origin.split('(')[1][:-1]
                origin_inv_id = self.pool.get('account.invoice').browse(cr, uid, int(origin_inv_id))
                if not origin_inv_id.fe_id:
                    continue
                document['tipo_comprobante'] = '04'
                document['import_nc'] = invoice_id.amount_total
                document['facturas_nc'] = origin_inv_id.fe_id
                document['motivo_nc'] = invoice_id.comment
            for line_id in invoice_id.invoice_line:
                line_tax_id = None
                for tax in line_id.invoice_line_tax_id:
                    if tax.tax_group in ['vat', 'vat0', 'novat']:
                        line_tax_id = tax.tax_code_id.electronic_code
                        break
                document['invoice_line_ids'].append(dict(
                    main_code = line_id.product_id.default_code,
                    product_type = line_id.product_id.type if line_id.product_id.type == 'service' else 'goods',
                    description = line_id.name,
                    quantity = line_id.quantity,
                    unit_price = line_id.price_unit,
                    discount = line_id.discount,
                    line_tax_id = line_tax_id,
                    ice_tax_id = None
                ))
            documents.append(document)
        return documents
    
    def save_result(self, cr, uid, data={}, context=None):
        res = ''
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        for invoice_id, vals in data.iteritems():
            invoice = self.browse(cr, uid, invoice_id, context=context)
            if not isinstance(vals, dict):
                res += u'No se pudo crear la factura %s: %s.\n'%(invoice.factura or invoice.name, vals)
                continue
            vals = dict(('fe_' + key, value) for key, value in vals.iteritems())
            if vals.get('fe_state') == invoice.fe_state:
                continue
            if vals.get('fe_auth_key'):
                company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
                auth_pool = self.pool.get('account.authorisation')
                auth_vals = {
                    'name': vals['fe_auth_key'],
                    'serie_entidad' : company_id.num_establecimiento,
                    'serie_emision' : company_id.num_sucursal,
                    'expiration_date' : vals['fe_auth_date'],
                    'resolucion_date': vals['fe_auth_date'],
                    'active' : True,
                    'type' : 'out_invoice',
                    'partner_id' : company_id.partner_id.id,
                    'doc_type': 'electronic'
                }
                auth_id = auth_pool.search(cr, uid, [(key, '=', value) for key, value in auth_vals.iteritems()], limit=1)
                vals['nro_factura'] = ('%s'%vals['fe_nro_comprobante']).zfill(9)
                vals['factura'] = ('%s'%vals['fe_nro_comprobante']).zfill(9)
                vals['num_retention'] = vals['fe_nro_comprobante']
                vals['auth_ret_id'] = auth_id[0] if auth_id else auth_pool.create(cr, uid, auth_vals, context=context)
            self.write(cr, uid, invoice_id, vals)
        return res or 'Respuesta exitosa desde la Facturación electrónica.'
        
account_invoice()

class account_invoice_retention(osv.osv):
    _inherit = 'account.invoice.retention'
    
    def _get_name(self, cr, uid, ids, field, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = obj.fe_nro_comprobante and ('%s'%obj.fe_nro_comprobante).zfill(9) or ''
        return res
    
    _columns = {
        'name': fields.function(_get_name, method=True, string='Nombre', type='char', size=16),
        'fe_auth_key': fields.char('Autorización S.R.I.', size=37, readonly=True),
        'fe_auth_date': fields.date('Fecha de autorización', readonly=True),
        'fe_id': fields.integer('ID del documento', readonly=True),
        'fe_state': fields.char('Estado', size=32, readonly=True),
#         'fe_subtotal_untaxed': fields.float('Subtotal sin impuestos', readonly=True),
#         'fe_subtotal_12': fields.float('Subtotal 12%', readonly=True),
#         'fe_subtotal_0': fields.float('Subtotal 0%', readonly=True),
#         'fe_sub_no_obj_iva': fields.float('Subtotal no objeto de IVA', readonly=True),
#         'fe_total_descuentos': fields.float('Total descuentos', readonly=True),
#         'fe_valor_ice': fields.float('Valor ICE', readonly=True),
#         'fe_iva_12': fields.float('IVA 12%', readonly=True),
#         'fe_valor_total': fields.float('Valor total', readonly=True),
        'fe_contingencia': fields.boolean('Contingencia'),
        'fe_nro_comprobante': fields.integer('Nro de comprobante', readonly=True),
    }
    
    def unlink(self, cr, uid, ids, context=None):
        retentions = self.browse(cr, uid, ids, context=context)
        for retention in retentions:
            if retention.fe_id > 0:
                raise osv.except_osv('ValidationError', 'No puede eliminar retenciones que ya poseen un documento electrónico generado.')
        return super(account_invoice_retention, self).unlink(cr, uid, ids, context)
    
    def get_datas(self, cr, uid, ids, context=None):
        IDENT_TYPE = dict([('c', '05'), ('p', '06'), ('r', '04'), ('s', '07')])
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        documents = []
        for retention_id in self.browse(cr, uid, ids, context=context):
            tax_line = [tax for tax in retention_id.tax_line if tax.amount]
            if not tax_line:
                continue
            if not retention_id.invoice_id.auth_ret_id:
                raise osv.except_osv('Error', u'La factura no posee una autorización.')
            auth = retention_id.invoice_id.auth_inv_id
            document = dict(
                id = retention_id.id,
                tipo_comprobante = '07',
                pos_id = company_id.num_sucursal,
                fecha_emision = retention_id.fecha,
                cons_final = retention_id.partner_id.ident_num == '9999999999999',
                pf_nro = retention_id.fecha.split('-')[1],
                pf_year = retention_id.fecha.split('-')[0],
                razon_social_cliente = dict(
                    ruc = retention_id.partner_id.ident_num,
                    tdoc_comprador = IDENT_TYPE[retention_id.partner_id.ident_type],
                    nombre_comercial = retention_id.partner_id.name,
                    name = retention_id.partner_id.name,
                    email = retention_id.invoice_id.partner_id.email or 'notificacionesfe1@gmail.com'
                ),
                facturas_reten_padre_id_cod = '01',
                facturas_reten_padre_id = auth.serie_entidad + auth.serie_emision + retention_id.invoice_id.factura.rjust(9, '0')[:9],
                facturas_reten_padre_fecha = retention_id.invoice_id.date_invoice,
                facturas_reten_ids = []
            )
            for line_id in tax_line:
                document['facturas_reten_ids'].append(dict(
                    facturas_imp_reten = line_id.tax_code_id.electronic_code,
                    facturas_imp_reten_porc = abs(round(line_id.percent, 2)) * 100,
                    valor_total = abs(line_id.base),
                    valor_total_reten = abs(line_id.amount),
                ))
            documents.append(document)
        return documents
    
    def save_result(self, cr, uid, data={}, context=None):
        res = ''
        for retention_id, vals in data.iteritems():
            retention = self.browse(cr, uid, retention_id, context=context)
            if not isinstance(vals, dict):
                res += u'No se pudo crear la retención %s: %s.\n'%(retention.name, vals)
                continue
            vals = dict(('fe_' + key, value) for key, value in vals.iteritems())
            if vals.get('fe_state') == retention.fe_state:
                continue
            if vals.get('fe_auth_key'):
                company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
                auth_pool = self.pool.get('account.authorisation')
                auth_vals = {
                    'name': vals['fe_auth_key'],
                    'serie_entidad' : company_id.num_establecimiento,
                    'serie_emision' : company_id.num_sucursal,
                    'expiration_date' : vals['fe_auth_date'],
                    'resolucion_date': vals['fe_auth_date'],
                    'active' : True,
                    'type' : 'retention',
                    'partner_id' : company_id.partner_id.id,
                    'doc_type': 'electronic'
                }
                auth_id = auth_pool.search(cr, uid, [(key, '=', value) for key, value in auth_vals.iteritems()], limit=1)
                vals['name'] = ('%s'%vals['fe_nro_comprobante']).zfill(9)
                vals['num_comprobante'] = vals['fe_nro_comprobante']
                vals['autorization'] = auth_id[0] if auth_id else auth_pool.create(cr, uid, auth_vals, context=context)
            self.write(cr, uid, retention_id, vals)
        return res or 'Respuesta exitosa desde la Facturación electrónica.'
    
account_invoice_retention()