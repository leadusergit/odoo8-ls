# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    
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
from openerp.osv import osv

def not_null_fields(self, cr, uid, ids, fields):
    model_id = self.pool.get('ir.model').search(cr, 1, [('model', '=', self._name)], limit=1)[0]
    fields_ids = self.pool.get('ir.model.fields').search(cr, 1, [('name', 'in', fields), ('model_id', '=', model_id)])
    fields_obj = self.pool.get('ir.model.fields').read(cr, 1, fields_ids)
    for obj in self.read(cr, uid, ids, fields):
        for field in fields_obj:
            if not obj[field['name']]:
                raise osv.except_osv('Error al validar', 'Por favor llene el campo ' + field['field_description'])
    return True

def fnct_search(self, cr, uid, obj, name, args, context):
    ids = []
    for arg in args:
        if arg[0] == name:
            res_ids = self.search(cr, uid, [arg for arg in args if arg[0] != name], context={'active_test': False})
            for id, value in obj._columns[name]._fnct(self, cr, uid, res_ids).iteritems():
                if arg[1] == '=':
                    val = eval('value '+ '==' +' arg[2]', locals())
                elif arg[1] in ['<', '>', 'in', 'not in', '<=', '>=', '<>']:
                    val = eval('value '+ arg[1] + ' arg[2]', locals())
                elif arg[1] in ['ilike']:
                    val = (str(value).find(str(arg[2])) != -1)
                if val:
                    ids.append(id)
    return [('id', 'in', ids)]