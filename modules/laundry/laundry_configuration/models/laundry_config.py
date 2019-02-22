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


 
class laundry_method_type_catalogue(models.Model):
 
    _name = 'laundry.method.type.catalogue'
    _description = "Catalogo metodo tipos de lavado"
 
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        reads = self.browse(cr, uid, ids, context=context)
        for record in reads:
            name = '%s-%s' % (record.codigo,record.descripcion_tipo_metodo)
            res.append((record.id, name))
        return res

    _rec_name = 'descripcion_tipo_metodo'
    
    codigo = fields.Char('Código')
    descripcion_tipo_metodo = fields.Char('Descripción')
    
    
class laundry_method_catalogue(models.Model):
 
    _name = 'laundry.method.catalogue'
    _description = "Catalogo metodo de lavado"
 
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        reads = self.browse(cr, uid, ids, context=context)
        for record in reads:
            name = '%s-%s' % (record.codigo_mtd,record.descripcion_mtd)
            res.append((record.id, name))
        return res

    _rec_name = 'descripcion_mtd'
    
    codigo_mtd = fields.Char('Código')
    descripcion_mtd = fields.Char('Descripción')
    
    
    
class product_template(models.Model):
 
    _name = 'product.template'
    _inherit = 'product.template'
    _description = "Lavanderia producto template"
 

    laundry=fields.Boolean('Producto/Lavanderia',default=lambda *a: False)
    method_id = fields.Many2one('laundry.method.catalogue', string='Método de Lavado', select=True)
    tiempo=fields.Char('Tiempo de Entrega')
    num_prendas_servicio=fields.Integer('NºPiezas')
    
    _defaults = {
        'tiempo':'2',
        'num_prendas_servicio':1
    }
    
class ProductCategory(models.Model):

    _inherit = "product.category"
    _description = "Lavanderia producto categoria"

    isservicetype = fields.Boolean('Es actividad de Lavanderia',default=lambda *a: False)


class laundry_claim_catalogue(models.Model):
 
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
    descripcion_reclamo = fields.Char('Descripción')