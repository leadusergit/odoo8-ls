# -*- coding: utf-8 -*-
#############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
############################################################################
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from openerp import SUPERUSER_ID
from openerp import models, fields, api, _
from openerp.osv import osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import workflow
from openerp.exceptions import ValidationError,except_orm, Warning, RedirectWarning

 
class laundry_management(models.Model):

    _name = 'laundry.management'
    _description = "Orden Servicio Lavanderia"
    
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        reads = self.browse(cr, uid, ids, context=context)
        for record in reads:
            #name = '%s - %s' % (record.id , record.codigo_orden_servicio)
            name = '%s' % (record.tag_asignado)
            res.append((record.id, name))
        return res
    
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('laundry.management.line').browse(cr, uid, ids, context=context):
            result[line.order_laundry_id.id] = True
        return result.keys()
    
    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        return company_id
    
    def _get_default_warehouse(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        warehouse_ids = self.pool.get('stock.warehouse').search(cr, uid, [('company_id', '=', company_id)], context=context)
        if not warehouse_ids:
            return False
        return warehouse_ids[0]
    

    @api.one
    @api.depends('service_lines.price_subtotal')
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.service_lines)
        
        if self.porcentaje_iva_aplicado  == 'auto' or self.porcentaje_iva_aplicado  == 'iva14':
           self.amount_tax = self.amount_untaxed * 0.14
        if self.porcentaje_iva_aplicado  == 'iva12' or self.clean_start_time>='2017-06-01':
           self.amount_tax = self.amount_untaxed * 0.12
        
        self.amount_total = self.amount_untaxed + self.amount_tax
    
    @api.one
    @api.depends('service_lines')
    def _compute_total_prendas(self):
        self.total_prendas = sum(line.product_uom_qty*line.cantp for line in self.service_lines)
    
    
    @api.one
    @api.depends('service_lines')
    def _compute_max_dias(self):     
        """Se obtiene el maximo numero de dias (tiempo configurado en cada item de servicio)"""
        self.aux=1
        for line in self.service_lines:
            dias=line.tiempo 
            if dias >self.aux:
               self.aux=dias
            else:
               self.aux=self.aux              
            
    
    @api.one
    @api.depends('clean_start_time','service_lines')
    def _compute_fecha_entrega(self):
        """Se añade el maximo numero de dias a la fecha de entrega de la OS"""       
        self.clean_end_time= str(datetime.now() + relativedelta.relativedelta(days=+self.aux))   
        
                      
    company_id = fields.Many2one('res.company', 'Compañia', required=True, readonly=True, states={'R': [('readonly', False)]}, select=True)
    user_id = fields.Many2one('res.users', 'Encargado', required=True, readonly=True, states={'R': [('readonly', False)]}, select=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', change_default=True,
        required=True, readonly=True, states={'R': [('readonly', False)]},track_visibility='always')    
    fiscal_position=fields.Many2one('account.fiscal.position', 'Fiscal Position')
    tag_asignado = fields.Char('Secuencial', required=True, copy=False,readonly=True, select=True)
    codigo_orden_servicio = fields.Char('Etiqueta', required=True, readonly=True, states={'R': [('readonly', False)]})
    clean_start_time = fields.Datetime('Fecha Recepcion',required=True, readonly=True, states={'R': [('readonly', False)]})
    clean_end_time = fields.Datetime('Fecha Entrega', required=True, readonly=True, states={'R': [('readonly', False)]},compute='_compute_fecha_entrega')
    #so_ref_id = fields.Many2one('sale.order','Nº Pre-Factura',readonly=True)
    invoice_ref_id = fields.Many2one('account.invoice','Nº Factura', ondelete='cascade',readonly=True)
    service_lines = fields.One2many('laundry.management.line','order_laundry_id', 'Lineas de Servicio', readonly=True, states={'R': [('readonly', False)]},copy=True)
    state = fields.Selection([('R','Recibido'), 
                              ('ENV','Enviado'), 
                              ('EP','En proceso'), 
                              ('ET','En tránsito'), 
                              ('L','Listo'), 
                              ('E','Entregado'),
                              ('RCL','Reclamo')], 'Estado', select=True,
                                required=True, readonly=True,default=lambda *a: 'R')
    pricelist_id=fields.Many2one('product.pricelist', 'Tarifa', required=True, readonly=True,states={'R': [('readonly', False)]})
    currency_id=fields.Many2one('res.currency',strin='curency',related='pricelist_id.currency_id', store=True, readonly=True)
    informacion = fields.Text('Observación',readonly=True, states={'R': [('readonly', False)]})
    porcentaje_iva_aplicado= fields.Selection([('auto', 'Automatico'),
                                               ('iva12', 'IVA 12%'),
                                               ('iva14', 'IVA 14%')], '%IVA aplicado', select=True,copy=True,required=True,readonly=True,states={'R': [('readonly', False)]})
    amount_untaxed = fields.Float(string='Subtotal', digits=dp.get_precision('Account'),
        store=True,readonly=True, compute='_compute_amount', track_visibility='always')
    amount_tax = fields.Float(string='Impuestos', digits=dp.get_precision('Account'),
        store=True,readonly=True, compute='_compute_amount')
    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),
        store=True,readonly=True, compute='_compute_amount')
    total_prendas = fields.Integer(string='Prendas', store=True,readonly=True, compute='_compute_total_prendas', track_visibility='always')
    delivery_guide_ref= fields.Many2one('laundry.delivery.guide','Guia Entrega',readonly=True)    
    dispatch_guide_ref= fields.Many2one('laundry.dispatch.guide','Guia Despacho',readonly=True)    
    claim_ref= fields.Many2one('laundry.claim','Nº.Reclamo',readonly=True)    
    aux = fields.Integer('Max ndias',store=True,readonly=True, compute='_compute_max_dias')
    planta_id = fields.Many2one('stock.warehouse', 'Planta/PA', required=False)
    facturado= fields.Boolean('Factura Generada')
    reclamo= fields.Boolean('Reclamo')
    estado_rcl=fields.Char('Estado de Reclamo')
    invoice_ids= fields.Many2many('account.invoice', 'laundry_order_invoice_rel', 'order_laundry_id', 'invoice_id', 'Invoice', readonly=True, copy=False)
        
    
    
    _defaults = {
        'tag_asignado':lambda obj, cr, uid, context: '/',
        'clean_start_time':lambda self, cr, uid, context={}: context.get('clean_start_time', time.strftime("%Y-%m-%d %H:%M:%S")),
        #'clean_end_time': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
        'user_id': lambda obj, cr, uid, context: uid,
        'company_id': _get_default_company,
        'planta_id': _get_default_warehouse,
        'porcentaje_iva_aplicado':'auto',
        'facturado':False,
        'reclamo':False,
        'estado_rcl':'ep'
    } 
    _sql_constraints = [
        ('name_uniq', 'unique(tag_asignado, company_id)', 'Orden Referencia debe ser unico por Compania!'),
    ]
    _order = 'clean_start_time desc, id desc'                 
      
        
    
    def create(self, cr, uid, vals, context=None):
        """Secuencial de la Orden de Servicio se genera automatica de acuerdo a la configuracion 
        (configuracion/tecnico/secuencias)"""
        if context is None:
            context = {}
        if vals.get('tag_asignado', '/') == '/':
            vals['tag_asignado'] = self.pool.get('ir.sequence').get(cr, uid, 'laundry.management', context=context) or '/'
        new_id = super(laundry_management, self).create(cr, uid, vals, context=context)
        return new_id
    
    
    def button_dummy(self, cr, uid, ids, context=None):
        return True
    

    @api.multi
    def unlink(self):
        """"Método que controla borrado de registros"""
        for laundry in self:
            if laundry.state not in ('R'):
                 raise ValidationError('No puede borrar Ordenes de Servicio en estado diferente a "Recibido"')
        return super(laundry_management, self).unlink()
    
    
    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, service_lines, context=None):
        context = context or {}
        if not pricelist_id:
            return {}
        value = {
            'currency_id': self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context).currency_id.id
        }
        if not service_lines or service_lines == [(6, 0, [])]:
            return {'value': value}
       
        return {'value': value}
    
    
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        if not part:
            return {'value': {'fiscal_position': False}}

        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
        val = {}
        if pricelist:
            val['pricelist_id'] = pricelist
       
        return {'value': val}
    
    @api.constrains('clean_start_time', 'clean_end_time')
    def check_clean_start_time(self):
        '''
        Método usado para validar la fecha incial < fecha final
        ---------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        if self.clean_start_time >= self.clean_end_time:
            raise ValidationError(_('Fecha recepción deberia ser menor que la fecha entrega!'))
            
    """@api.multi
    def action_set_to_recibido(self):
        
        #This method is used to change the state
        #to R 
        #@param self: object pointer
        
        self.write({'state': 'R'})
        for laundry_keep_id in self.ids:
            workflow.trg_create(self._uid, self._name, laundry_keep_id, self._cr)
        return True

    @api.multi
    def laundry_cancel(self):
        #This method is used to change the state
        #to cancel 
        #@param self: object pointer
        self.write({'state': 'C'})
        return True"""

    @api.multi
    def laundry_entransito(self):
        #Método usado para cambiar a estado en tránsito
        #@param self: object pointer
        
        self.write({'state': 'ET'})
        return True

    @api.multi
    def laundry_enproceso(self):
        
        #Método usado para cambiar a estado en proceso
        #@param self: object pointer
        if self.state=='ENV':
            self.write({'state': 'EP'})
        return True
    
    @api.multi
    def laundry_listo(self):
        
        #Método usado para cambiar a estado listo
        #@param self: object pointer
        if self.state=='ET':
            self.write({'state': 'L'})
        return True
    
    @api.multi
    def laundry_entregado(self):
        
        #Método usado para cambiar a estado en entregado
        #@param self: object pointer
        if self.state=='L' or self.state=='RCL':
             self.write({'state': 'E'})
        """if self.claim_ref: 
           if self.state=='RCL'and self.claim_ref.state=='L' :
              self.write({'state': 'E'})"""
              
        return True
    
    @api.multi
    def laundry_reclamo(self):
        
        #Método usado para cambiar a estado reclamo
        #@param self: object pointer
        self.write({'state': 'RCL'})
        return True
    
    @api.multi
    def set_to_l(self):
        
        #Método usado para cambiar a estado entregado
        #@param self: object pointer
        if self.state=='RCL':        
            self.write({'state': 'L'})
        return True

    @api.multi
    def laundry_enviado (self):
        
        #Método usado para cambiar a estado enviado
        #@param self: object pointer
        #if self.so_ref_id:
        self.write({'state': 'ENV'})
        return True
    
    
    
    def view_invoice(self, cr, uid, ids, context=None):
        """Crea factura de orden de servicio en estado borrador"""        
        ir_property_obj = self.pool.get('ir.property')
        fiscal_obj = self.pool.get('account.fiscal.position')
        inv_ids = context.get('active_ids', [])
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        laundry_obj = self.browse(cr,uid,ids[0])
        
        if context is None:
            context = dict(context or {})
                       
        if laundry_obj.invoice_ref_id:
            raise ValidationError('No puede generar otra Factura,el ticket ya esta vinculado a una Factura')
            
        active_ids = context.get('active_ids', []) or []        
        mod_obj = self.pool.get('ir.model.data')
      
        partner=self.pool.get('laundry.management').browse(cr ,uid, ids ,context=context).partner_id.id
        fecha_inicio=self.pool.get('laundry.management').browse(cr ,uid, ids ,context=context).clean_start_time
        fecha_fin=self.pool.get('laundry.management').browse(cr ,uid, ids ,context=context).clean_end_time
        fiscal=self.pool.get('res.partner').browse(cr ,uid, partner ,context=context).property_account_position.id
        cuenta=self.pool.get('res.partner').browse(cr ,uid, partner ,context=context).property_account_receivable.id
        codigo_orden_servicio=self.pool.get('laundry.management').browse(cr ,uid, ids ,context=context).codigo_orden_servicio
        info=self.pool.get('laundry.management').browse(cr ,uid, ids ,context=context).informacion
        vendedor=self.pool.get('laundry.management').browse(cr ,uid, ids ,context=context).user_id.id    
        company=self.pool.get('laundry.management').browse(cr ,uid, ids ,context=context).company_id.id
        wh_company=self.pool.get('laundry.management').browse(cr ,uid, ids ,context=context).planta_id.id
        
        id_journal = self.pool.get('account.journal').search(cr, uid, [('company_id', '=', company),('type', '=', 'sale')])
        journal=self.pool.get('account.journal').browse(cr ,uid, id_journal ,context=context).auth_id.id

        print"company=%s"%company
        print"journal=%s"%journal,id_journal
        
        
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
        res_id = res and res[1] or False                
        form_res = mod_obj.get_object_reference(cr, uid,'account','invoice_form')
        form_id = form_res and form_res[1] or False
        tree_res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_tree')
        tree_id = tree_res and tree_res[1] or False
           
        
        vals = dict(partner_id=partner,
                    fiscal_position=fiscal,
                    date_invoice=fecha_inicio,
                    laundry_id=laundry_obj.id,
                    saleer_id=vendedor,
                    user_id= laundry_obj.user_id.id,                
                    type='out_invoice',
                    account_id=cuenta,
                    amount_tax=laundry_obj.amount_tax,
                    comment=codigo_orden_servicio,
                    auth_ret_id= journal)
        
        invoice =self.pool.get('account.invoice').create(cr,uid,vals,context=None)
        print"invoice=%s"%invoice
        invoice_id=self.pool.get('account.invoice').browse(cr ,uid, invoice ,context=context).id
        print"invoice_id=%s"%invoice_id
        
        for laundry in laundry_obj:           
            for lines in laundry_obj.service_lines:
                
                product= lines.product_id.id
                cantidad=lines.product_uom_qty
                uos_id=self.pool.get('product.product').browse(cr ,uid, product ,context=context).uom_id.id
                result = []
                val = inv_line_obj.product_id_change(cr, uid, inv_ids, product,
                                                    False, partner_id=partner, fposition_id=fiscal,company_id=company)
                res = val['value']
                # determine taxes
                """Se obtiene lista de impuestos de cada producto"""
                if res.get('invoice_line_tax_id'):
                    res['invoice_line_tax_id'] = [(6, 0, res.get('invoice_line_tax_id'))]
                else:
                    res['invoice_line_tax_id'] = False
                print"res['invoice_line_tax_id']=%s"%res
                
                vals1 = dict(invoice_id=invoice_id,
                             product_id=product,
                             quantity=cantidad,
                             product_uom=1,
                             uos_id=uos_id,
                             price_unit=lines.price_unit,
                             price_subtotal=lines.price_subtotal,
                             invoice_line_tax_id=res['invoice_line_tax_id'],
                             name='Servicio de Lavanderia',
                            )
                print"vals1=%s"%vals1

                invoiceline =self.pool.get('account.invoice.line').create(cr,uid,vals1,context=None)

        res1 = {'invoice_ref_id':invoice_id,'facturado':True}
        self.write(cr, uid, ids, res1)
        """Retora la vista de la factura"""
        return {
                'name': 'Factura Lavanderia',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'view_id': [res_id],
                'view_name':'view_invoice_form',
                'res_model': 'account.invoice',
                'context': {'id':invoice_id},
                #'context': {'partner_id':partner,'partner_invoice_id':partner,
                #            'partner_shipping_id':partner,'fiscal_position':fiscal,
                #            'pricelist_id':1},
                #'nodestroy': True,
                #'target': 'current',
                'views': [(form_id, 'form'), (tree_id, 'tree')],
                'res_id': invoice_id ,
                'type': 'ir.actions.act_window',
        }


    def crear_reclamo(self, cr, uid, ids, context=None):
        """Crea Registro de reclamo vinculado a orden de servicio en estado recibido"""  
        
        laundry_obj = self.browse(cr,uid,ids[0])
        laundry_claim= self.pool.get('laundry.claim')
        
        if context is None:
            context = dict(context or {})
            
        self.laundry_reclamo(cr, uid, ids, context=None)
        
        active_ids = context.get('active_ids', []) or []        
        mod_obj = self.pool.get('ir.model.data') 
        
        partner=self.pool.get('laundry.management').browse(cr ,uid, ids ,context=context).partner_id.id
        company=self.pool.get('laundry.management').browse(cr ,uid, ids ,context=context).company_id.id       
        fiscal=self.pool.get('res.partner').browse(cr ,uid, partner ,context=context).property_account_position.id

        
        res = mod_obj.get_object_reference(cr, uid, 'laundry_management', 'view_laundry_claim_form')
        res_id = res and res[1] or False                
        form_res = mod_obj.get_object_reference(cr, uid,'laundry_management','view_laundry_claim_form')
        form_id = form_res and form_res[1] or False
        tree_res = mod_obj.get_object_reference(cr, uid, 'laundry_management', 'view_laundry_claim_tree')
        tree_id = tree_res and tree_res[1] or False
           
        
        vals = dict(partner_id=laundry_obj.partner_id.id,
                    fiscal_position=fiscal,
                    pricelist_id=1,
                    clean_start_time=laundry_obj.clean_start_time,
                    clean_end_time=laundry_obj.clean_end_time,
                    user_id=laundry_obj.user_id.id  ,
                    codigo_orden_reclamo = laundry_obj.tag_asignado+'R',
                    invoice_ref_id = laundry_obj.invoice_ref_id.id,
                    state = 'R',
                    currency_id=laundry_obj.currency_id.id,
                    informacion = laundry_obj.informacion,
                    porcentaje_iva_aplicado= laundry_obj.porcentaje_iva_aplicado,
                    amount_untaxed = laundry_obj.amount_untaxed,
                    amount_tax = laundry_obj.amount_tax,
                    amount_total = laundry_obj.amount_total,
                    total_prendas = laundry_obj.total_prendas, 
                    lorder_id= laundry_obj.id)          
        
        order =self.pool.get('laundry.claim').create(cr,uid,vals,context=None)
        print"reclamo=%s"%order
        order_id=self.pool.get('laundry.claim').browse(cr ,uid, order ,context=context).id
        print"reclamoid=%s"%order_id
        
        for laundry in laundry_obj:           
            for lines in laundry_obj.service_lines:

                    vals1 = dict(order_claim_id =order_id,
                                 product_id = lines.product_id.id,
                                 name =lines.name,
                                 color=lines.color,
                                 discount=lines.discount,
                                 company_id= lines.company_id.id,
                                 order_laundry_id=lines.order_laundry_id.id,
                                 product_uom_qty=lines.product_uom_qty,
                                 observacion=lines.observacion)
                    print"vals1=%s"%vals1

                    orderline =self.pool.get('laundry.claim.line').create(cr,uid,vals1,context=None)

        res = {'claim_ref':order_id,'reclamo':True,'estado_rcl':'ep'}
        self.write(cr, uid, ids, res)
        
        """return-- permite visualizar el registro creado en el formulario"""
        return {
                'name': 'OrdenReclamo',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'view_id': [res_id],
                'view_name':'view_laundry_claim_form',
                'res_model': 'laundry.claim',
                'context': {'id':order_id},
                #'context': {'partner_id':partner,'partner_invoice_id':partner,
                #            'partner_shipping_id':partner,'fiscal_position':fiscal,
                #            'pricelist_id':1},
                #'nodestroy': True,
                #'target': 'current',
                'views': [(form_id, 'form'), (tree_id, 'tree')],
                'res_id': order_id ,
                'type': 'ir.actions.act_window',
        }
   
    def desvincular(self, cr, uid, ids, context=None):                   
        self.set_to_l(cr, uid, ids, context=None)
        res = {'reclamo':False}
        self.write(cr, uid, ids, res)
        
        
    def confirmar(self, cr, uid, ids, context=None):
        """Modifica el estado de la orden de servicio y el reclamo vinculado si este existe"""
        laundry_obj = self.browse(cr,uid,ids)
        claim= self.pool.get('laundry.claim')
        
        if laundry_obj.invoice_ref_id:
            self.laundry_entregado(cr, uid, ids, context=None)
            
            if laundry_obj.claim_ref:
                claim_id= laundry_obj.claim_ref.id
                claim.laundry_claim_entregado(cr, uid, claim_id, context=None)
        else:
            raise ValidationError('Orden de Servicio no puede ser Entregada si no ha sido Facturada')

    
    def _inv_get(self, cr, uid, order, context=None):
        return {}
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepara datos para generar factura de OS agrupadas"""

        if context is None:
            context = {}
        journal_id = self.pool['account.invoice'].default_get(cr, uid, ['journal_id'], context=context)['journal_id']
        if not journal_id:
            raise ValidationError('Defina un diario para esta compañia')

        invoice_vals = {
            'name': order.tag_asignado or '',
            'origin': order.tag_asignado ,
            'type': 'out_invoice',
            'reference': order.codigo_orden_servicio,
            'account_id': order.partner_id.property_account_receivable.id,
            'partner_id': order.partner_id.id,
            #'journal_id': journal_id,
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.informacion,
            #'payment_term': order.payment_term and order.payment_term.id or False,
            'fiscal_position': order.fiscal_position.id ,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'user_id': order.user_id.id
            #'section_id' : order.section_id.id
        }

        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals
    
    
    def _make_invoice(self, cr, uid, order, lines, context=None):
        print"order=%s"%order
        print"lines=%s"%lines
        inv_obj = self.pool.get('account.invoice')
        obj_invoice_line = self.pool.get('account.invoice.line')
        if context is None:
            context = {}
        invoiced_sale_line_ids = self.pool.get('laundry.management.line').search(cr, uid, [('order_laundry_id', '=', order.id), ('invoiced', '=', False)], context=context)
        from_line_invoice_ids = []
        for invoiced_sale_line_id in self.pool.get('laundry.management.line').browse(cr, uid, invoiced_sale_line_ids, context=context):
            for invoice_line_id in invoiced_sale_line_id.invoice_lines:
                if invoice_line_id.invoice_id.id not in from_line_invoice_ids:
                    from_line_invoice_ids.append(invoice_line_id.invoice_id.id)
        for preinv in order.invoice_ids:
            if preinv.state not in ('cancel',) and preinv.id not in from_line_invoice_ids:
                for preline in preinv.invoice_line:
                    inv_line_id = obj_invoice_line.copy(cr, uid, preline.id, {'invoice_id': False, 'price_unit': -preline.price_unit})
                    lines.append(inv_line_id)
        inv = self._prepare_invoice(cr, uid, order, lines, context=context)
        inv_id = inv_obj.create(cr, uid, inv, context=context)
        data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], [2], time.strftime(DEFAULT_SERVER_DATE_FORMAT))
        if data.get('value', False):
            inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        #self.write(cr, uid,order.id,{'invoice_ref_id':inv_id,'facturado':True}) 
        #print"inv_id=%s"%inv_id      
        
        return inv_id
    
    
    def action_invoice_create(self, cr, uid, ids, grouped=False, states=None, date_invoice = False, context=None):
        if states is None:
            states = ['L']
        res = False
        invoices = {}
        invoice_ids = []
        invoice = self.pool.get('account.invoice')
        obj_laundry_order_line = self.pool.get('laundry.management.line')
        partner_currency = {}

        if date_invoice:
            context = dict(context or {}, date_invoice=date_invoice)
        for o in self.browse(cr, uid, ids, context=context):
            currency_id = o.pricelist_id.currency_id.id
            if (o.partner_id.id in partner_currency) and (partner_currency[o.partner_id.id] <> currency_id):
                raise ValidationError('xxxx')
           
            partner_currency[o.partner_id.id] = currency_id
            lines = []
            for line in o.service_lines:
                lines.append(line.id)                            
                created_lines = obj_laundry_order_line.invoice_line_create(cr, uid, lines)
                print"created_lines=%s"%created_lines
                
            if created_lines:
                invoices.setdefault(o.partner_id.id, []).append((o, created_lines))
        if not invoices:
            for o in self.browse(cr, uid, ids, context=context):
                for i in o.invoice_ids:
                    if i.state == 'draft':
                        return i.id 
        for val in invoices.values():
            if grouped:
                res = self._make_invoice(cr, uid, val[0][0], reduce(lambda x, y: x + y, [l for o, l in val], []), context=context)
                invoice_ref = ''
                origin_ref = ''
                for o, l in val:
                    invoice_ref += (o.tag_asignado) + '|'
                    origin_ref += (o.tag_asignado) + '|'
                    ##self.write(cr, uid, [o.id], {'state': 'RC'})
                    cr.execute('insert into laundry_order_invoice_rel (order_laundry_id,invoice_id) values (%s,%s)', (o.id, res))
                    self.invalidate_cache(cr, uid, ['invoice_ids'], [o.id], context=context)
                    print"if grouped"
                    self.write(cr, uid,o.id,{'invoice_ref_id':res,'facturado':True})
                #remove last '|' in invoice_ref
                if len(invoice_ref) >= 1:
                    invoice_ref = invoice_ref[:-1]
                if len(origin_ref) >= 1:
                    origin_ref = origin_ref[:-1]
                invoice.write(cr, uid, [res], {'origin': origin_ref, 'name': invoice_ref,'laundry_grouped':True})

            else:
                for order, il in val:
                    res = self._make_invoice(cr, uid, order, il, context=context)
                    invoice_ids.append(res)
                    ##self.write(cr, uid, [order.id], {'state': 'RC'})
                    cr.execute('insert into laundry_order_invoice_rel (order_laundry_id,invoice_id) values (%s,%s)', (order.id, res))
                    self.invalidate_cache(cr, uid, ['invoice_ids'], [order.id], context=context)
                    invoice.write(cr, uid, [res], {'laundry_id':order.id})
                    self.write(cr, uid,order.id,{'invoice_ref_id':res,'facturado':True})
        return res



class laundry_management_line(models.Model):  
    
    def _get_uom_id(self, cr, uid, *args):
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            return result[1]
        except Exception, ex:
            return False
        
                
    @api.one
    @api.depends('price_unit', 'discount', 'tax_id', 'product_uom_qty',
        'product_id', 'order_laundry_id.partner_id', 'order_laundry_id.currency_id')
    def _compute_price(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.tax_id.compute_all(price, self.product_uom_qty, product=self.product_id, partner=self.order_laundry_id.partner_id)
        self.price_subtotal = taxes['total']
        #print"self.price_subtotal=%s"%self.price_subtotal
        if self.order_laundry_id:
            self.price_subtotal = self.order_laundry_id.currency_id.round(self.price_subtotal)
            #print"self.price_subtotal//=%s"%self.price_subtotal
    
    def _fnct_line_invoiced(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids, False)
        for this in self.browse(cr, uid, ids, context=context):
            res[this.id] = this.invoice_lines and \
                all(iline.invoice_id.state != 'cancel' for iline in this.invoice_lines) 
        return res   
    
    def _order_lines_from_invoice(self, cr, uid, ids, context=None):
        # direct access to the m2m table is the less convoluted way to achieve this (and is ok ACL-wise)
        cr.execute("""SELECT DISTINCT sol.id FROM laundry_order_line_invoice_rel rel JOIN
                                                  laundry_management_line sol ON (sol.order_laundry_id = rel.order_laundry_id)
                                    WHERE rel.invoice_id = ANY(%s)""", (list(ids),))
        return [i[0] for i in cr.fetchall()]
    
         
    
    _name = 'laundry.management.line'
    _description = "Lavanderia Lineas"
    
    
    order_laundry_id = fields.Many2one('laundry.management', string='Pedido',required=True, ondelete='cascade', readonly=True,select=True)
    #service_name = fields.Many2one('laundry.service',string='Servicio',required=True)
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', 'Prenda', change_default=True, readonly=False)
    name = fields.Text('Descripcion', required=True, readonly= False)
    color = fields.Selection([('amarillo','amarillo'),('blue','azul'),('beige','beige'),
                              ('white','blanco'),('brown','cafe'),('gris','gris'),
                              ('mostaza','mostaza'),('black','negro'),('perla','perla'),
                              ('red','rojo'),('green','verde'),('red1','vino'),
                              ('otros','otros')], 'Color', select=True,required=True,default=lambda *a: 'otros')
    price_unit =fields.Float('Precio Unitario',digits_compute= dp.get_precision('Precio producto'), required=True,readonly=False)
    price_subtotal=fields.Float(string='Subtotal',digits_compute= dp.get_precision('Account'),compute='_compute_price')
    tax_id=fields.Many2many('account.tax', 'laundry_management_line_tax', 'laundry_management_line_id', 'tax_id', 'Impuestos', readonly=False)
    product_uom_qty=fields.Float('Cantidad', digits_compute= dp.get_precision('Cantidad'), required=True, readonly=False)
    product_uom=fields.Many2one('product.uom', 'Unidad de Medida', required=True, readonly=True)
    product_uos_qty=fields.Float('Cantidad(UoS)' ,digits_compute= dp.get_precision('Producto UoS'), readonly=False)
    product_uos=fields.Many2one('product.uom', 'Product UoS')
    discount=fields.Float('Descuento(%)', digits_compute= dp.get_precision('Descuento'), readonly=False)
    method_id = fields.Many2one('laundry.method.catalogue', string='Método Lavado',readonly=True)
    tiempo=fields.Char('Tiempo Entrega',readonly=True)
    cantp=fields.Integer('NºPrendas',store=True,readonly=True)
    method_type_id=fields.Many2many('laundry.method.type.catalogue', 'laundry_method_type_catalogue_line', 'laundry_method_type_catalogue_id', 'method_type_id', 'Bandera', readonly=False)
    #method_type_id = fields.Many2one('laundry.method.type.catalogue', string='Bandera')
    partner_id= fields.Many2one('res.partner',string='Cliente',related='order_laundry_id.partner_id',store=True, readonly=True)
    company_id= fields.Many2one('res.company',string='Empresa',related='order_laundry_id.company_id',store=True, readonly=True)
    claim_id= fields.Many2one('laundry.claim',string='Reclamo',related='order_laundry_id.claim_ref',store=True, readonly=True)
    observacion=fields.Char('Observación')
    invoice_lines= fields.Many2many('account.invoice.line', 'laundry_order_line_invoice_rel', 'order_laundry_line_id', 'invoice_line_id', 'Invoice Lines', readonly=True, copy=False)
    invoiced=fields.Boolean( string='Invoiced',compute='_fnct_line_invoiced',
            store={
                'account.invoice': (_order_lines_from_invoice, ['state'], 10),
                'laundry.management.line': (lambda self,cr,uid,ids,ctx=None: ids, ['invoice_lines'], 10)
            })



    _order = 'order_laundry_id desc, sequence, id'
    _defaults = {
        'product_uom' : _get_uom_id,
        'discount': 0.0,
        'product_uom_qty': 1,
        'product_uos_qty': 1,
        'sequence': 10,
        'price_unit': 0.0,
    }

    def create(self, cr, uid, values, context=None):
        if values.get('order_laundry_id') and values.get('product_id') and  any(f not in values for f in ['name', 'price_unit', 'product_uom_qty', 'product_uom','method_id','tiempo','num_prendas_servicio']):
            order = self.pool['laundry.management'].read(cr, uid, values['order_laundry_id'], ['pricelist_id', 'partner_id', 'clean_start_time', 'fiscal_position'], context=context)
            defaults = self.product_id_change(cr, uid, [], order['pricelist_id'][0], values['product_id'],
                qty=float(values.get('product_uom_qty', False)),
                uom=values.get('product_uom', False),
                qty_uos=float(values.get('product_uos_qty', False)),
                uos=values.get('product_uos', False),
                name=values.get('name', False),
                partner_id=order['partner_id'][0],
                clean_start_time=order['clean_start_time'],
                fiscal_position=order['fiscal_position'][0] if order['fiscal_position'] else False,
                flag=False,  # Force name update
                method_id=values.get('method_id', False),
                tiempo=values.get('tiempo', False),
                cantp=values.get('num_prendas_servicio', False),
                context=dict(context or {}, company_id=values.get('company_id')))['value']
            if defaults.get('tax_id'):
                defaults['tax_id'] = [[6, 0, defaults['tax_id']]]
            values = dict(defaults, **values)
        return super(laundry_management_line, self).create(cr, uid, values, context=context)
    
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, clean_start_time=False, packaging=False, fiscal_position=False, flag=False,method_id=False,tiempo=False,cantp=False, context=None):
        context = context or {}
        lang = lang or context.get('lang', False)
        """if not partner_id:
            raise osv.except_osv(_('No Customer Defined!'), _('Before choosing a product,\n select a customer in the sales form.'))
        warning = False"""
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        partner = partner_obj.browse(cr, uid, partner_id)
        lang = partner.lang
        context_partner = context.copy()
        context_partner.update({'lang': lang, 'partner_id': partner_id})

        if not product:
            return {'value': {'product_uos_qty': qty}, 'domain': {'product_uom': [],'product_uos': []}}
        if not clean_start_time:
            clean_start_time = time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        result = {}
        warning_msgs = ''
        product_obj = product_obj.browse(cr, uid, product, context=context_partner)

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False

        fpos = False
        if not fiscal_position:
            fpos = partner.property_account_position or False
        else:
            fpos = self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position)
        if update_tax: #The quantity only have changed
            # The superuser is used by website_sale in order to create a sale order. We need to make
            # sure we only select the taxes related to the company of the partner. This should only
            # apply if the partner is linked to a company.
            if uid == SUPERUSER_ID and context.get('company_id'):
                taxes = product_obj.taxes_id.filtered(lambda r: r.company_id.id == context['company_id'])
            else:
                taxes = product_obj.taxes_id
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes)

        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            if product_obj.description_sale:
                result['name'] += '\n'+product_obj.description_sale
                
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                result['method_id'] = product_obj.product_tmpl_id.method_id.id
                result['tiempo'] = product_obj.product_tmpl_id.tiempo
                result['cantp'] = product_obj.product_tmpl_id.num_prendas_servicio
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                result['method_id'] = product_obj.product_tmpl_id.method_id.id
                result['tiempo'] = product_obj.product_tmpl_id.tiempo
                result['cantp'] = product_obj.product_tmpl_id.num_prendas_servicio
                uos_category_id = False
            #result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['method_id'] = product_obj.product_tmpl_id.method_id.id
            result['tiempo'] = product_obj.product_tmpl_id.tiempo
            result['cantp'] = product_obj.product_tmpl_id.num_prendas_servicio
            #result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                result['method_id'] = product_obj.product_tmpl_id.method_id.id
                result['tiempo'] = product_obj.product_tmpl_id.tiempo
                result['cantp'] = product_obj.product_tmpl_id.num_prendas_servicio
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                result['method_id'] = product_obj.product_tmpl_id.method_id.id
                result['tiempo'] = product_obj.product_tmpl_id.tiempo
                result['cantp'] = product_obj.product_tmpl_id.num_prendas_servicio
            #result['th_weight'] = q * product_obj.weight        # Round the quantity up

        if not uom2:
            uom2 = product_obj.uom_id
        # get unit price

        if not pricelist:
            warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                    'Please set one before choosing a product.')
            warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
        else:
            ctx = dict(
                context,
                uom=uom or result.get('product_uom'),
                clean_start_time=clean_start_time,
            )
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                    product, qty or 1.0, partner_id, ctx)[pricelist]
            if price is False:
                warn_msg = _("Cannot find a pricelist line matching this product and quantity.\n"
                        "You have to change either the product, the quantity or the pricelist.")

                warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
            else:
                if update_tax:
                    price = self.pool['account.tax']._fix_tax_included_price(cr, uid, price, taxes, result['tax_id'])
                result.update({'price_unit': price})
                if context.get('uom_qty_change', False):
                    values = {'price_unit': price}
                    if result.get('product_uos_qty'):
                        values['product_uos_qty'] = result['product_uos_qty']
                    return {'value': values, 'domain': {}, 'warning': False}
        """if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }"""
        return {'value': result, 'domain': domain}#, 'warning': warning}
    

    def product_uom_change(self, cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, clean_start_time=False,method_id= False,tiempo=False,cantp=False, context=None):
        context = context or {}
        lang = lang or ('lang' in context and context['lang'])
        if not uom:
            return {'value': {'price_unit': 0.0, 'product_uom' : uom or False}}
        return self.product_id_change(cursor, user, ids, pricelist, product,
                qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                partner_id=partner_id, lang=lang, update_tax=update_tax,
                clean_start_time=clean_start_time,method_id=method_id,tiempo=tiempo,cantp=cantp,context=context)
  
    
    def _get_line_qty(self, cr, uid, line, context=None):
        if line.product_uos:
            return line.product_uos_qty or 0.0
        return line.product_uom_qty

    def _get_line_uom(self, cr, uid, line, context=None):
        if line.product_uos:
            return line.product_uos.id
        return line.product_uom.id
    
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):

        res = {}
        if not line.invoiced:
            if not account_id:
                if line.product_id:
                    account_id = line.product_id.property_account_income.id
                    if not account_id:
                        account_id = line.product_id.categ_id.property_account_income_categ.id
                    if not account_id:
                        raise ValidationError('Defina cuenta de ingreso para este producto')
                else:
                    prop = self.pool.get('ir.property').get(cr, uid,
                            'property_account_income_categ', 'product.category',
                            context=context)
                    account_id = prop and prop.id or False
            uosqty = self._get_line_qty(cr, uid, line, context=context)
            uos_id = self._get_line_uom(cr, uid, line, context=context)
            pu = 0.0
            if uosqty:
                pu = round(line.price_unit * line.product_uom_qty / uosqty,
                        self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Price'))
            fpos = line.order_laundry_id.fiscal_position or False
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
            if not account_id:
                raise osv.except_osv(_('Error!'),
                            _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
            res = {
                'name': line.name,
                'sequence': line.sequence,
                'origin': line.order_laundry_id.tag_asignado,
                'account_id': account_id,
                'price_unit': pu,
                'quantity': uosqty,
                'discount': line.discount,
                'uos_id': uos_id,
                'product_id': line.product_id.id or False,
                'invoice_line_tax_id': [(6, 0, [x.id for x in line.tax_id])],
                #'account_analytic_id': line.order_id.project_id and line.order_id.project_id.id or False,
            }

        return res
    
    def invoice_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        create_ids = []
        sales = set()
        for line in self.browse(cr, uid, ids, context=context):
            vals = self._prepare_order_line_invoice_line(cr, uid, line, False, context)
            print"vals=%s"%vals
            if vals:
                inv_id = self.pool.get('account.invoice.line').create(cr, uid, vals, context=context)
                self.write(cr, uid, [line.id], {'invoice_lines': [(4, inv_id)]}, context=context)
                sales.add(line.order_laundry_id.id)
                create_ids.append(inv_id)
                #self.write(cr, uid,[line.id],{'invoiced':True})
        # Trigger workflow events
        #for sale_id in sales:
         #   workflow.trg_write(uid, 'sale.order', sale_id, cr)
        return create_ids  





class account_invoice(models.Model):
    _inherit ='account.invoice'
    _description = "Factura Lavanderia"
    
    laundry_id= fields.Many2one('laundry.management','Nº Orden Servicio',readonly=True) 
    laundry_grouped= fields.Boolean('Facturas agrupadas')  
   
    
    @api.multi
    def unlink(self):
        for invoice in self:
            if invoice.state not in ('draft', 'cancel'):
                raise Warning(_('You cannot delete an invoice which is not draft or cancelled. You should refund it instead.'))
            elif invoice.internal_number:
                raise Warning(_('You cannot delete an invoice after it has been validated (and received a number).  You can set it back to "Draft" state and modify its content, then re-confirm it.'))
            if invoice.laundry_id or invoice.laundry_grouped:
                raise Warning(_('Factura no puede ser borrada Orden de Servicio ya ha sido procesada'))
                
        return super(account_invoice, self).unlink()
    


