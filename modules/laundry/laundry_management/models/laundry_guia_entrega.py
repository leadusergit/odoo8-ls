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

   
class laundry_delivery_guide(models.Model):

    _name = 'laundry.delivery.guide'
    _description = "Guia de entrega de lavanderia"
    
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        reads = self.browse(cr, uid, ids, context=context)
        for record in reads:
            name = '%s' % (record.codigo_auto)
            res.append((record.id,name))
        return res
    
    
    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        return company_id
    
    @api.one
    @api.depends('guia_lines')
    def _compute_prendas_ge(self):
        self.num_prendas_ge = sum(line.num_prendas for line in self.guia_lines)
        
        
    company_id = fields.Many2one('res.company', 'Empresa', required=True,readonly=True,select=True)
    companypl_id = fields.Many2one('res.company', 'EmprPL',select=True)
    planta_id = fields.Many2one('stock.warehouse', 'Planta', required=True, readonly=True, states={'draft': [('readonly', False)]}, select=True)
    user_id = fields.Many2one('res.users','Encargado', required=True, readonly=True, states={'draft': [('readonly', False)]}, select=True)
    partner_id = fields.Many2one('res.partner','Transportista', required=True, readonly=True, states={'draft': [('readonly', False)]}, select=True)  
    codigo_auto = fields.Char('Secuencial',  required=True, copy=False, select=True, readonly=True)
    guia_lines = fields.One2many('laundry.delivery.guide.lines','e_list_id', 'Detalle guia de entrega', requerid=True,readonly=False, states={'recept': [('readonly', True)]}, copy=True)
    codigo_guia_entrega = fields.Char('Guia', required=False, readonly=True, states={'draft': [('readonly', False)]})
    fecha_recepcion = fields.Date('Fecha Elaboracion',required=True, readonly=True, states={'draft': [('readonly', False)]})
    fecha_entrega = fields.Date('Fecha Entrega', readonly=True, states={'draft': [('readonly', False)]})
    num_prendas_ge = fields.Integer('Prendas',store=True,readonly=True, compute='_compute_prendas_ge',track_visibility='always')
    state = fields.Selection([('draft','Borrador'),
                              ('send','Enviado'),
                              ('partial','Parcialmente Recibido'),
                              ('recept','Recibido')],'Estado', select=True,required=True, readonly=True,default=lambda *a: 'draft')

   
    _defaults = {
        'codigo_auto':lambda obj, cr, uid, context: '/',
        'fecha_recepcion':lambda self, cr, uid, context={}: context.get('fecha_recepcion', time.strftime("%Y-%m-%d %H:%M:%S")),
        'fecha_entrega': lambda *a: str(datetime.now() + relativedelta.relativedelta(days=+2)),
        'planta_id':lambda obj, cr, uid, context: uid,
        'user_id': lambda obj, cr, uid, context: uid,
        'company_id': _get_default_company
    } 
    
    
    _sql_constraints = [
        ('name_uniq', 'unique(codigo_auto, company_id)', 'Guia de entrega debe ser unica por Compania!'),
    ]
    
    _order = 'fecha_recepcion desc, id desc'                 
    
   
   
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('codigo_auto', '/') == '/':
            vals['codigo_auto'] = self.pool.get('ir.sequence').get(cr, uid, 'laundry.delivery.guide', context=context) or '/'
        new_id = super(laundry_delivery_guide, self).create(cr, uid, vals, context=context)
        return new_id
    
    
    @api.multi
    def unlink(self):
        """"Método que controla borrado de registros"""
        for delivery in self:
            if delivery.state not in ('draft'):
                 raise ValidationError('No puede borrar Guias de Entrega en estado diferente a "Borrador"')
        return super(laundry_delivery_guide, self).unlink()
    
    
    @api.constrains('fecha_recepcion', 'fecha_entrega')
    def check_fecha_recepcion(self):
        '''
        This method is used to validate the clean_start_time and
        clean_end_time.
        ---------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        if self.fecha_recepcion >= self.fecha_entrega:
            raise ValidationError(_('Start Date Should be \less than the End Date!'))
            
    @api.multi
    def action_set_to_recept(self): 
        
        if self.state=='partial':       
            self.write({'state': 'recept'})
        return True
    
    @api.multi
    def laundry_delivery_borrador(self):
        #This method is used to change the state
        
        self.write({'state': 'draft'})
        return True
    
    @api.multi
    def laundry_delivery_enviado(self):
        #This method is used to change the state
        
        if self.state=='draft':
            self.write({'state': 'send'})
        return True
    

    @api.multi
    def laundry_delivery_recibido(self):
        
        #This method is used to change the state

        if self.state=='send':
            self.write({'state': 'recept'})
        return True
    
    @api.multi
    def laundry_delivery_parcial(self):
        
        #This method is used to change the state

        if self.state=='send':
            self.write({'state': 'partial'})
        return True
    
    
    def confirmar_ge_lines(self, cr, uid, ids, context=None):
        
        delivery_guide_obj = self.browse(cr,uid,ids[0])
        laundry= self.pool.get('laundry.management')
        claim= self.pool.get('laundry.claim')
        
        if context is None:
            context = dict(context or {})
      
        if not delivery_guide_obj.guia_lines:
            raise ValidationError('El detalle no puede estar vacio(Seleccionar Orden de Servicio)')

        """Modifica estados de OS(orde servicio) vinculadas a GE(guia entrega)"""
        for lines in delivery_guide_obj.guia_lines:
        
            laundry_id=lines.service_order_id.id
            claim_id=lines.service_claim_id.id
        
            print"confirmar_ge_lines"
            print"laundry_id=%s"%laundry_id  
                      
            """Si se ha generado RCL(claim_id) de OS se modifica estado de RCL y OS(continua en estado RCL)
               caso contrario se modifica estado de OS a Enviado"""
            if claim_id: 
                claim.laundry_claim_enviado(cr, uid, claim_id, context=None)
                laundry.laundry_reclamo(cr, uid, laundry_id, context=None)
                res = {'estado_rcl':'e'}
                laundry.write(cr,uid,laundry_id,res,context=None)
            else:
                laundry.laundry_enviado(cr, uid, laundry_id, context=None)
                
        
            """Actualiza registro referencia a GE en laundry_management"""
            ge_id=lines.e_list_id.id#      
            print"ge_id=%s"%ge_id
            
            """Si se ha generado RCL(claim_id) de OS se registra referencia a GE en RCL
               caso contario se registra referencia a GE en OS"""
            if claim_id:
                res = {'delivery_guide_ref':ge_id}
                claim.write(cr,uid,claim_id,res,context=None)               
            else:
                res = {'delivery_guide_ref':ge_id}
                laundry.write(cr,uid,laundry_id,res,context=None)
                
        
        """Modifica estado de GE """
        self.laundry_delivery_enviado(cr, uid, ids, context=None)    
        
        
        
    def confirmar(self, cr, uid, ids, context=None):
        
        delivery_guide_obj = self.browse(cr,uid,ids)
        delivery_lines= self.pool.get('laundry.delivery.guide.lines')
        laundry= self.pool.get('laundry.management')
        claim= self.pool.get('laundry.claim')
        
        if context is None:
            context = dict(context or {})
            
        """Modifica estados de OS(orden servicio) vinculadas a GE(guia entrega)"""
        for lines in delivery_guide_obj.guia_lines:
            laundry_id=lines.service_order_id.id
            claim_id=lines.service_claim_id.id
            
            t=0
            p=0
            if lines.check:
               t=t+1
               print"total=%s"%t
               if claim_id:
                  claim.laundry_claim_enproceso(cr, uid, claim_id, context=None)
                  laundry.laundry_reclamo(cr, uid, laundry_id, context=None)
                  res = {'estado_rcl':'ep'}
                  laundry.write(cr,uid,laundry_id,res,context=None)
               else:
                  laundry.laundry_enproceso(cr, uid, laundry_id, context=None)                  
            else:
               p=p+1 
               print"parcial=%s"%p
               res = {'partial':True}
               delivery_lines.write(cr,uid,lines.id,res,context=None)
               
        recibidas=t-p  
        if t == recibidas :
            self.laundry_delivery_recibido(cr, uid, ids,context=None)
            print"recibidas=%s"%recibidas 
        else:
            self.laundry_delivery_parcial(cr, uid, ids,context=None)

    
                
                
    def recibir(self, cr, uid, ids, context=None):
        
        delivery_guide_obj = self.browse(cr,uid,ids)
        delivery_lines= self.pool.get('laundry.delivery.guide.lines')
        laundry= self.pool.get('laundry.management')
        claim= self.pool.get('laundry.claim')
        
        if context is None:
            context = dict(context or {})
            
        """Modifica estados de OS(orden servicio) vinculadas a GE(guia entrega)"""
        for lines in delivery_guide_obj.guia_lines:
            laundry_id=lines.service_order_id.id
            claim_id=lines.service_claim_id.id
            
            if lines.partial and lines.check :
                if claim_id:
                  claim.laundry_claim_enproceso(cr, uid, claim_id, context=None)
                  laundry.laundry_reclamo(cr, uid, laundry_id, context=None)
                  res = {'estado_rcl':'ep'}
                  laundry.write(cr,uid,laundry_id,res,context=None)
                else:
                  laundry.laundry_enproceso(cr, uid, laundry_id, context=None)

            
            res = {'partial':False}
            delivery_lines.write(cr,uid,lines.id,res,context=None)
            
        """Modifica estado de GE"""    
        self.action_set_to_recept(cr, uid, ids,context=None)           
        
        
        
        
class laundry_delivery_guide_lines(models.Model):
    

    @api.one
    @api.depends('service_order_id')
    def _compute_amount(self):
        #self.amount_untaxed = sum(line.price_subtotal for line in self.service_lines)
        self.total = self.service_order_id.amount_total
        self.num_prendas = self.service_order_id.total_prendas
        self.service_claim_id = self.service_order_id.claim_ref.id
        self.company_id=self.service_order_id.company_id.id
        
        if self.service_claim_id:
            self.total = 0.00
            self.num_prendas = self.service_order_id.claim_ref.total_prendas
               
    _name = 'laundry.delivery.guide.lines'
    _description = "Detalle guia de entrega lavanderia"
              
    e_list_id = fields.Many2one('laundry.delivery.guide', string='Lineas Guia Entrega',required=True, ondelete='cascade', readonly=True,select=True)
    service_order_id = fields.Many2one('laundry.management',string='Orden Nº',required=True)
    service_claim_id = fields.Many2one('laundry.claim',string='Reclamo')
    num_prendas = fields.Integer('Prendas',store=True,readonly=True, compute='_compute_amount')
    company_id = fields.Many2one('res.company',string='Punto de Atención')
    #company_id= fields.Many2one('res.company',string='Punto de Atención',related='e_list_id.company_id',store=True, readonly=True)
    planta_id= fields.Many2one('stock.warehouse',string='Planta',related='e_list_id.planta_id',store=True, readonly=True)
    total = fields.Float(string='Total', digits=dp.get_precision('Account'),store=True,readonly=True, compute='_compute_amount')
    observacion=fields.Char('Observación')
    check=fields.Boolean('Listo',default= True)
    partial=fields.Boolean('Parcial',default= False)
    

    @api.multi
    def unlink(self):
        """"Método que controla borrado de registros"""
        for delivery_lines in self:
            if delivery_lines.e_list_id.state not in ('draft'):
                 raise ValidationError('No puede borrar Detalle Guias de Entrega')
        return super(laundry_delivery_guide_lines, self).unlink()

