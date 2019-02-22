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
from openerp.exceptions import ValidationError


 
"""class laundry_claim_catalogue(models.Model):
 
    _name = 'laundry.claim.catalogue'
    _description = "Catalogo reclamos lavanderia"
 
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        reads = self.browse(cr, uid, ids, context=context)
        for record in reads:
            name = '%s' % (record.descripcion_reclamo)
            res.append((record.id, name))
        return res

    _rec_name = 'descripcion_reclamo'
    
    codigo = fields.Char('Código')
    descripcion_reclamo = fields.Char('Descripción')"""
    

class laundry_claim(models.Model):

    _name = 'laundry.claim'
    _description = "Orden Reclamo Lavanderia"
    
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        reads = self.browse(cr, uid, ids, context=context)
        for record in reads:
            name = '%s' % (record.codigo_orden_reclamo)
            res.append((record.id, name))
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('laundry.claim.line').browse(cr, uid, ids, context=context):
            result[line.order_laundry_id.id] = True
        return result.keys()
    
    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        return company_id
    

    @api.one
    @api.depends('service_claim_lines.price_subtotal')
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.service_claim_lines)
        
        if self.porcentaje_iva_aplicado  == 'auto' or self.porcentaje_iva_aplicado  == 'iva14':
           self.amount_tax = self.amount_untaxed * 0.14
        if self.porcentaje_iva_aplicado  == 'iva12' or self.clean_start_time>='2017-06-01':
           self.amount_tax = self.amount_untaxed * 0.12
        
        self.amount_total = self.amount_untaxed + self.amount_tax
    
    @api.one
    @api.depends('service_claim_lines')
    def _compute_total_prendas(self):
        self.total_prendas = sum(line.product_uom_qty for line in self.service_claim_lines)
        
       
                
    company_id = fields.Many2one('res.company', 'Compañia', required=True, readonly=True, states={'R': [('readonly', False)]}, select=True)
    user_id = fields.Many2one('res.users', 'Encargado', required=True, readonly=True, states={'R': [('readonly', False)]}, select=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', change_default=True,
        required=True, readonly=True, states={'R': [('readonly', False)]},track_visibility='always')    
    fiscal_position=fields.Many2one('account.fiscal.position', 'Fiscal Position')
    cod_asignado = fields.Char('Secuencial', required=True, copy=False,readonly=True, select=True)
    codigo_orden_reclamo = fields.Char('Etiqueta', required=True, readonly=True, states={'R': [('readonly', False)]})
    clean_start_time = fields.Datetime('Fecha Recepcion',required=False, readonly=True, states={'R': [('readonly', False)]})
    clean_end_time = fields.Datetime('Fecha Entrega', required=False, readonly=True, states={'R': [('readonly', False)]})
    so_ref_id = fields.Many2one('sale.order','SO(Pre-Factura)',readonly=True)
    service_claim_lines = fields.One2many('laundry.claim.line','order_claim_id', 'Lineas de Reclamo', readonly=True, states={'R': [('readonly', False)]},copy=True)
    state = fields.Selection([('R','Recibido'), 
                              ('ENV','Enviado'), 
                              ('EP','En proceso'), 
                              ('ET','En tránsito'), 
                              ('L','Listo'), 
                              ('E','Entregado')], 'Estado', select=True,
                                required=True, readonly=True,default=lambda *a: 'R')
    pricelist_id=fields.Many2one('product.pricelist', 'Tarifa', required=False, readonly=True,states={'R': [('readonly', False)]})
    currency_id=fields.Many2one('res.currency',strin='curency',related='pricelist_id.currency_id', store=True, readonly=True)
    informacion = fields.Text('Observación',readonly=True, states={'R': [('readonly', False)]})
    porcentaje_iva_aplicado= fields.Selection([('auto', 'Automatico'),
                                               ('iva12', 'IVA 12%'),
                                               ('iva14', 'IVA 14%')], '%IVA aplicado', select=True,copy=True,required=False,readonly=True,states={'R': [('readonly', False)]})
    amount_untaxed = fields.Float(string='Subtotal', digits=dp.get_precision('Account'),
        store=True,readonly=True, compute='_compute_amount', track_visibility='always')
    amount_tax = fields.Float(string='Impuestos', digits=dp.get_precision('Account'),
        store=True,readonly=True, compute='_compute_amount')
    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),
        store=True,readonly=True, compute='_compute_amount')
    total_prendas = fields.Integer(string='Total Prendas', store=True,readonly=True, compute='_compute_total_prendas', track_visibility='always')
    delivery_guide_ref= fields.Many2one('laundry.delivery.guide','Guia Entrega',readonly=True)    
    dispatch_guide_ref= fields.Many2one('laundry.dispatch.guide','Guia Despacho',readonly=True)    
    lorder_id= fields.Many2one('laundry.management',string='Orden Servicio',required=False,readonly=True)    

    
    _defaults = {
        'cod_asignado':lambda obj, cr, uid, context: '/',
        'clean_start_time':lambda self, cr, uid, context={}: context.get('clean_start_time', time.strftime("%Y-%m-%d %H:%M:%S")),
        'clean_end_time': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
        'user_id': lambda obj, cr, uid, context: uid,
        'company_id': _get_default_company,
        'porcentaje_iva_aplicado':'auto'
    } 
    _sql_constraints = [
        ('name_uniq', 'unique(cod_asignado, company_id)', 'Orden Referencia debe ser unico por Compania!'),
    ]
    _order = 'clean_start_time desc, id desc'                 
      
        
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('cod_asignado', '/') == '/':
            vals['cod_asignado'] = self.pool.get('ir.sequence').get(cr, uid, 'laundry.claim', context=context) or '/'
        new_id = super(laundry_claim, self).create(cr, uid, vals, context=context)
        return new_id
    
    
    def desvincular(self, cr, uid, ids, context=None):
        
        claim_obj = self.browse(cr,uid,ids[0])
        laundry= self.pool.get('laundry.management')
        
        laundry_id= claim_obj.lorder_id.id
        laundry.desvincular(cr, uid, laundry_id, context=None)
        
        
    @api.multi
    def unlink(self):
        """"Método que controla borrado de registros"""
        for claim in self:
            if claim.state not in ('R'):
                 raise ValidationError('No puede borrar Reclamos en estado diferente a "Recibido"')
        self.desvincular()
        return super(laundry_claim, self).unlink()
    
    
    def button_dummy(self, cr, uid, ids, context=None):
        return True
    
    
    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, service_claim_lines, context=None):
        context = context or {}
        if not pricelist_id:
            return {}
        value = {
            'currency_id': self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context).currency_id.id
        }
        if not service_claim_lines or service_claim_lines == [(6, 0, [])]:
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
        This method is used to validate the clean_start_time and
        clean_end_time.
        ---------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        if self.clean_start_time >= self.clean_end_time:
            raise ValidationError(_('Start Date Should be \
            less than the End Date!'))
            
    @api.multi
    def laundry_claim_entransito(self):
        #This method is used to change the state
        #to done
        #@param self: object pointer
        if self.state=='EP':
            self.write({'state': 'ET'})
        return True

    @api.multi
    def laundry_claim_enproceso(self):
        
        #This method is used to change the state
        #to inspect
        #@param self: object pointer
        if self.state=='ENV':
            self.write({'state': 'EP'})
        return True
    
    @api.multi
    def laundry_claim_listo(self):
        
        #This method is used to change the state
        if self.state=='ET':
            self.write({'state': 'L'})
        return True
    
    @api.multi
    def laundry_claim_entregado(self):
        
        #This method is used to change the state
        if self.state=='L':
            self.write({'state': 'E'})
        return True
       

    @api.multi
    def laundry_claim_enviado (self):
        
        #This method is used to change the state
        self.write({'state': 'ENV'})
        return True
    
    
    def confirmar(self, cr, uid, ids, context=None):
        
        claim_obj = self.browse(cr,uid,ids)
        laundry= self.pool.get('laundry.management')
        
        laundry_id= claim_obj.lorder_id.id
        laundry.confirmar(cr, uid, laundry_id, context=None)
        self.laundry_claim_entregado(cr, uid, ids, context=None)

        

class laundry_claim_line(models.Model):  
    
    def _get_uom_id(self, cr, uid, *args):
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            return result[1]
        except Exception, ex:
            return False
                
    @api.one
    @api.depends('price_unit', 'discount', 'tax_id', 'product_uom_qty',
        'product_id', 'order_claim_id.partner_id', 'order_claim_id.currency_id')
    def _compute_price(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.tax_id.compute_all(price, self.product_uom_qty, product=self.product_id, partner=self.order_claim_id.partner_id)
        self.price_subtotal = taxes['total']
        #print"self.price_subtotal=%s"%self.price_subtotal
        if self.order_claim_id:
            self.price_subtotal = self.order_claim_id.currency_id.round(self.price_subtotal)
            #print"self.price_subtotal//=%s"%self.price_subtotal
            
    
    _name = 'laundry.claim.line'
    _description = "Detalle Reclamo"
    
    
    order_claim_id = fields.Many2one('laundry.claim', string='Reclamo',required=True, ondelete='cascade', readonly=True,select=True)
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', 'Prenda', change_default=True, readonly=False)
    name = fields.Text('Descripcion', required=False, readonly=True)
    color = fields.Selection([('black','negro'),('gris','gris'),('blue','azul'),
                              ('brown','cafe'),('green','verde'),('red1','vino'),
                              ('beige','beige'),('perla','perla'),('white','blanco'),                              
                              ('red','rojo'),('amarillo','amarillo'),('mostaza','mostaza'),
                              ('otros','otros')], 'Color', select=True,required=False,default=lambda *a: 'otros')
    price_unit =fields.Float('Precio Unitario',digits_compute= dp.get_precision('Precio producto'), required=False,readonly=False)
    price_subtotal=fields.Float(string='Subtotal',digits_compute= dp.get_precision('Account'),compute='_compute_price')
    tax_id=fields.Many2many('account.tax', 'laundry_claim_line_tax', 'laundry_claim_line_id', 'tax_id', 'Impuestos', readonly=False)
    product_uom_qty=fields.Float('Cantidad', digits_compute= dp.get_precision('Cantidad'), required=False, readonly=False)
    product_uom=fields.Many2one('product.uom', 'Unidad de Medida', required=False, readonly=True)
    product_uos_qty=fields.Float('Cantidad(UoS)' ,digits_compute= dp.get_precision('Producto UoS'), readonly=False)
    product_uos=fields.Many2one('product.uom', 'Product UoS')
    discount=fields.Float('Descuento(%)', digits_compute= dp.get_precision('Descuento'), readonly=False)
    method_id = fields.Many2one('laundry.method.catalogue', string='Método Lavado', select=True)
    tiempo=fields.Char('Tiempo Entrega')
    claim_type_id = fields.Many2one('laundry.claim.catalogue', string='Tipo Reclamo', select=True)
    company_id= fields.Many2one('res.company',string='Empresa',related='order_claim_id.company_id',store=True, readonly=True)
    order_laundry_id= fields.Many2one('laundry.management',string='Orden Servicio',related='order_claim_id.lorder_id',store=True, readonly=True)    
    observacion=fields.Char('Observación')


    _order = 'order_claim_id desc, sequence, id'
    _defaults = {
        'product_uom' : _get_uom_id,
        'discount': 0.0,
        'product_uom_qty': 1,
        'product_uos_qty': 1,
        'sequence': 10,
        'price_unit': 0.0,
    }

    """def create(self, cr, uid, values, context=None):
        if values.get('order_claim_id') and values.get('product_id') and  any(f not in values for f in ['name', 'price_unit', 'product_uom_qty', 'product_uom','method_id','tiempo']):
            order = self.pool['laundry.claim'].read(cr, uid, values['order_claim_id'], ['pricelist_id', 'partner_id', 'clean_start_time', 'fiscal_position'], context=context)
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
                context=dict(context or {}, company_id=values.get('company_id')))['value']
            if defaults.get('tax_id'):
                defaults['tax_id'] = [[6, 0, defaults['tax_id']]]
            values = dict(defaults, **values)
        return super(laundry_claim_line, self).create(cr, uid, values, context=context)"""
    
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, clean_start_time=False, packaging=False, fiscal_position=False, flag=False,method_id=False,tiempo=False, context=None):
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
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                result['method_id'] = product_obj.product_tmpl_id.method_id.id
                result['tiempo'] = product_obj.product_tmpl_id.tiempo
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
            #result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                result['method_id'] = product_obj.product_tmpl_id.method_id.id
                result['tiempo'] = product_obj.product_tmpl_id.tiempo
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                result['method_id'] = product_obj.product_tmpl_id.method_id.id
                result['tiempo'] = product_obj.product_tmpl_id.tiempo
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
            lang=False, update_tax=True, clean_start_time=False,method_id= False,tiempo=False, context=None):
        context = context or {}
        lang = lang or ('lang' in context and context['lang'])
        if not uom:
            return {'value': {'price_unit': 0.0, 'product_uom' : uom or False}}
        return self.product_id_change(cursor, user, ids, pricelist, product,
                qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                partner_id=partner_id, lang=lang, update_tax=update_tax,
                clean_start_time=clean_start_time,method_id=method_id,tiempo=tiempo, context=context)

      
