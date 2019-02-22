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

class region(osv.osv):
    """
    Regiones
    """
    _name = 'res.region'
    _description = 'region'
    _columns = {
        'name': fields.char('Nombre', size=64,
            help='Nombre completo de la Region.', required=True, translate=True),
        'code': fields.char('Codigo', size=2,
            help='Código de la Region.', required=True),
    }
    _sql_constraints = [
        ('name_uniq', 'unique (name)',
            'El nombre de la región debe ser único!'),
        ('code_uniq', 'unique (code)',
            'El código de la región debe ser único!')
    ]

    def name_search(self, cr, user, name='', args=None, operator='ilike',
            context=None, limit=100):
        if not args:
            args=[]
        if not context:
            context={}
        ids = False
        if len(name) == 2:
            ids = self.search(cr, user, [('code', 'ilike', name)] + args,
                    limit=limit, context=context)
        if not ids:
            ids = self.search(cr, user, [('name', operator, name)] + args,
                    limit=limit, context=context)
        return self.name_get(cr, user, ids, context)
    _order='name'

    def create(self, cursor, user, vals, context=None):
        if 'code' in vals:
            vals['code'] = vals['code'].upper()
        return super(region, self).create(cursor, user, vals,
                context=context)

    def write(self, cursor, user, ids, vals, context=None):
        if 'code' in vals:
            vals['code'] = vals['code'].upper()
        return super(region, self).write(cursor, user, ids, vals,
                context=context)
        
region()

class regionZone(osv.osv):
    _description='res.region.state'
    _name = 'res.region.state'
    _columns = {
        'region_id': fields.many2one('res.region', 'Region', required=False),
        'name': fields.char('Nombre de la Zona', size=64, required=True),
        'code': fields.char('Código de la Zona', size=3, required=True),
    }
    def name_search(self, cr, user, name='', args=None, operator='ilike',
            context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}
        ids = self.search(cr, user, [('code', 'ilike', name)] + args, limit=limit,
                context=context)
        if not ids:
            ids = self.search(cr, user, [('name', operator, name)] + args,
                    limit=limit, context=context)
        return self.name_get(cr, user, ids, context)

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
            'El nombre de la zona debe ser único!'),
        ('code_uniq', 'unique (code)',
            'El código de la zona debe ser único!')
    ]

    _order = 'name'

regionZone()

class city(osv.osv):
    """
    Ciudad
    """
    _name = 'city.city'
    _description = 'City'

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        res = []
        for line in self.browse(cr, uid, ids):
            state = line.state_id.name
            region = line.state_id.region_id.name        
            country = line.state_id.country_id.name    
            location = "%s, %s, %s, %s" %(line.name, state, region, country)
            res.append((line['id'], location))
        return res

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        res = super(city, self).search(cr, uid, args, offset, limit, order, context, count)
        if not res and args:
            args = [('zipcode', 'ilike', args[0][2])]
            res = super(city, self).search(cr, uid, args, offset, limit, order, context, count)
        return res

    _columns = {
        'state_id': fields.many2one('res.country.state', 'Estado', required=True, select=1),
        'region_id': fields.many2one('res.region.state', 'Region', required=False, select=1),
        'name': fields.char('Ciudad', size=64, required=True, select=1),
        'zipcode': fields.char('Codigo Postal', size=64, required=True, select=1),
    }
city()

class CountryState(osv.osv):
    """
    Provincia
    """
    _inherit = 'res.country.state'
    _columns = {
        'city_ids': fields.one2many('city.city', 'state_id', 'Ciudades'),
        'region_id': fields.many2one('res.region', 'Region'),
    }
CountryState()

class res_partner(osv.osv):    
    _inherit = "res.partner"
    _columns = {
        'location': fields.many2one('city.city', 'Locacion'),
    }
    
    def onchange_location(self, cr, uid, ids, location_id):
        res = {'value': {}}
        if location_id:
            location_id = self.pool.get('city.city').browse(cr, uid, location_id)
            res['value']['city'] = location_id.name
            res['value']['zip'] = location_id.zipcode
            res['value']['state_id'] = location_id.state_id.id
            res['value']['country_id'] = location_id.state_id.country_id.id
        return res
    
res_partner()