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

   
class laundry_dispatch_guide(models.Model):

    _name = 'laundry.dispatch.guide'
    _description = "Guia de despacho lavanderia"
    
    
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
    @api.depends('despacho_lines')
    def _compute_prendas_gd(self):
        self.num_prendas_gd = sum(line.num_prendas for line in self.despacho_lines)
        
        
    company_id = fields.Many2one('res.company', 'Destino', required=True,readonly=True, states={'draft': [('readonly', False)]}, select=True)
    companypl_id = fields.Many2one('res.company', 'EmprPL',select=True)
    planta_id = fields.Many2one('stock.warehouse', 'Origen', required=True, readonly=True, states={'draft': [('readonly', False)]}, select=True)
    user_id = fields.Many2one('res.users','Encargado', required=True, readonly=True, states={'draft': [('readonly', False)]} ,select=True)
    partner_id = fields.Many2one('res.partner','Transportista', required=True, readonly=True, states={'draft': [('readonly', False)]}, select=True)  
    codigo_auto = fields.Char('Secuencial',  required=True, copy=False, select=True, readonly=True)
    despacho_lines = fields.One2many('laundry.dispatch.guide.lines','d_list_id', 'Detalle guia despacho', requerid=True,readonly=False, states={'recept': [('readonly', True)]}, copy=True)
    codigo_guia_despacho= fields.Char('Guia', required=False, readonly=True, states={'draft': [('readonly', False)]})
    fecha_recepcion = fields.Date('Fecha',required=True, readonly=True, states={'draft': [('readonly', False)]})
    fecha_entrega = fields.Date('Fecha Recepción', readonly=True, states={'draft': [('readonly', False)]})
    num_prendas_gd = fields.Integer('Prendas',store=True,readonly=True, compute='_compute_prendas_gd',track_visibility='always')
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
        ('name_uniq', 'unique(codigo_auto, company_id)', 'Guia de despacho debe ser unica por Compania!'),
    ]
    
    _order = 'fecha_recepcion desc, id desc'                 
    
   
   
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('codigo_auto', '/') == '/':
            vals['codigo_auto'] = self.pool.get('ir.sequence').get(cr, uid, 'laundry.dispatch.guide', context=context) or '/'
        new_id = super(laundry_dispatch_guide, self).create(cr, uid, vals, context=context)
        
        return new_id
    
    @api.multi
    def unlink(self):
        """"Método que controla borrado de registros"""
        for dispatch in self:
            if dispatch.state not in ('draft'):
                 raise ValidationError('No puede borrar Guias de Despacho en estado diferente a "Borrador"')
        return super(laundry_dispatch_guide, self).unlink()
    
    
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
        #This method is used to change the state       
        if self.state=='partial':       
            self.write({'state': 'recept'})
            
        return True
    
    @api.multi
    def laundry_dispatch_enviado(self):
        #This method is used to change the state        
        if self.state=='draft':
            self.write({'state': 'send'})
        return True
    

    @api.multi
    def laundry_dispatch_recibido(self):
        
        #This method is used to change the state
        if self.state=='send':
            self.write({'state': 'recept'})
        return True
    
    @api.multi
    def laundry_dispatch_parcial(self):
        
        #This method is used to change the state
        if self.state=='send':
            self.write({'state': 'partial'})
        return True
    
    
    def confirmar_gd_lines(self, cr, uid, ids, context=None):
        
        dispatch_guide_obj = self.browse(cr,uid,ids[0])
        laundry= self.pool.get('laundry.management')
        claim= self.pool.get('laundry.claim')
        
        if context is None:
            context = dict(context or {})
                       
        if not dispatch_guide_obj.despacho_lines:
            raise ValidationError('El detalle no puede estar vacio(Seleccionar Orden de Servicio)')
        
        """Modifica estados de OS(orde servicio) y Reclamos vinculadas a GD(guia despacho)"""
        for lines in dispatch_guide_obj.despacho_lines:
            laundry_id=lines.service_order_id.id
            claim_id=lines.service_claim_id.id
            
            print"confirmar_gd_lines"
            print"laundry_id claim_id=%s"%laundry_id,claim_id
                                   
            if claim_id:
                claim.laundry_claim_entransito(cr, uid, claim_id, context=None)
                laundry.laundry_reclamo(cr, uid, laundry_id, context=None)
                res = {'estado_rcl':'et'}
                laundry.write(cr,uid,laundry_id,res,context=None)
            else:
                laundry.laundry_entransito(cr, uid, laundry_id, context=None)

                
            """Actualiza registro referencia a GD en laundry_management y laudry_claim"""
            gd_id=lines.d_list_id.id       
            print"gd_id=%s"%gd_id

            if claim_id: 
                res = {'dispatch_guide_ref':gd_id}
                claim.write(cr,uid,claim_id,res,context=None)
            else:
                res = {'dispatch_guide_ref':gd_id}
                laundry.write(cr,uid,laundry_id,res,context=None)   
        
        """Modifica estado de GD """
        self.laundry_dispatch_enviado(cr, uid, ids, context=None)
        
        
        
    def confirmar(self, cr, uid, ids, context=None):
        
        dispatch_guide_obj = self.browse(cr,uid,ids)
        dispatch_lines= self.pool.get('laundry.dispatch.guide.lines')
        laundry= self.pool.get('laundry.management')
        claim=self.pool.get('laundry.claim')
        
        if context is None:
            context = dict(context or {})
            
        """Modifica estados de OS(orde servicio) y Reclamos vinculadas a GD(guia despacho)"""
        for lines in  dispatch_guide_obj.despacho_lines:
            laundry_id=lines.service_order_id.id
            claim_id=lines.service_claim_id.id
            
            t=0
            p=0
            if lines.check:
               t=t+1
               print"despacho-total=%s"%t    
               if claim_id:
                   claim.laundry_claim_listo(cr, uid, claim_id, context=None)
                   laundry.laundry_reclamo(cr, uid, laundry_id, context=None)
                   res = {'estado_rcl':'l'}
                   laundry.write(cr,uid,laundry_id,res,context=None)
               else:
                   laundry.laundry_listo(cr, uid, laundry_id, context=None)
            else:
               p=p+1 
               print"despacho-parcial=%s"%p
               res = {'partial':True}
               dispatch_lines.write(cr,uid,lines.id,res,context=None)

        """Modifica estado de GD"""
        recibidas=t-p  
        if t == recibidas :
            self.laundry_dispatch_recibido(cr, uid, ids,context=None)
            print"recibidas=%s"%recibidas 
        else:
            self.laundry_dispatch_parcial(cr, uid, ids,context=None)
        
    
    
    def recibir(self, cr, uid, ids, context=None):
        
        dispatch_guide_obj = self.browse(cr,uid,ids)
        dispatch_lines= self.pool.get('laundry.dispatch.guide.lines')
        laundry= self.pool.get('laundry.management')
        claim= self.pool.get('laundry.claim')
        
        if context is None:
            context = dict(context or {})
            
        """Modifica estados de OS(orden servicio) vinculadas a GD(guia despacho)"""
        for lines in dispatch_guide_obj.despacho_lines:
            laundry_id=lines.service_order_id.id
            claim_id=lines.service_claim_id.id
            
            if lines.partial and lines.check:
                if claim_id:
                  claim.laundry_claim_listo(cr, uid, claim_id, context=None)
                  laundry.laundry_reclamo(cr, uid, laundry_id, context=None)
                  res = {'estado_rcl':'l'}
                  laundry.write(cr,uid,laundry_id,res,context=None)
                else:
                  laundry.laundry_listo(cr, uid, laundry_id, context=None)

            
            res = {'partial':False}
            dispatch_lines.write(cr,uid,lines.id,res,context=None)
            
        """Modifica estado de GD"""
        self.action_set_to_recept(cr, uid, ids,context=None)  
        
        
        
class laundry_dispatch_guide_lines(models.Model):   

    @api.one
    @api.depends('service_order_id')
    def _compute_amount(self):
        #self.amount_untaxed = sum(line.price_subtotal for line in self.service_lines)
        self.total = self.service_order_id.amount_total
        self.num_prendas = self.service_order_id.total_prendas
        self.ge_id = self.service_order_id.delivery_guide_ref.codigo_auto
        self.service_claim_id = self.service_order_id.claim_ref.id
        self.company_id=self.service_order_id.company_id.id        
        
        if self.service_claim_id:
            self.total = 0.00
            self.num_prendas = self.service_order_id.claim_ref.total_prendas
        
    _name = 'laundry.dispatch.guide.lines'
    _description = "Detalle guia de despacho lavanderia" 
               
                
    d_list_id = fields.Many2one('laundry.dispatch.guide', string='Lineas Guia Despacho',required=True, ondelete='cascade', readonly=True,select=True)
    service_order_id = fields.Many2one('laundry.management',string='Nº Orden',required=True )
    service_claim_id = fields.Many2one('laundry.claim',string='Reclamo')
    num_prendas = fields.Integer('Prendas',store=True,readonly=True, compute='_compute_amount')
    total = fields.Float(string='Total', digits=dp.get_precision('Account'),store=True,readonly=True, compute='_compute_amount')
    #company_id= fields.Many2one('res.company',string='Punto de Atención',related='d_list_id.company_id',store=True, readonly=True)
    company_id = fields.Many2one('res.company',string='Punto de Atención')
    planta_id= fields.Many2one('stock.warehouse',string='Planta',related='d_list_id.planta_id',store=True, readonly=True)
    ge_id=fields.Char('Guia Entrega',store=True,readonly=True, compute='_compute_amount')
    observacion=fields.Char('Observación')
    check=fields.Boolean('Listo',default= True)
    partial=fields.Boolean('Parcial',default= False)
    
    
    @api.multi
    def unlink(self):
        """"Método que controla borrado de registros"""
        for dispatch_lines in self:
            if dispatch_lines.d_list_id.state not in ('draft'):
                 raise ValidationError('No puede borrar Detalle Guias de Despacho')
        return super(laundry_dispatch_guide_lines, self).unlink()

