# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution.
#    Module for basic payroll in Ecuador.
#    Copyright (C) 2010-2013 Israel Paredes Reyes. All Rights Reserved.
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
from openerp.osv import osv, fields
from cStringIO import StringIO
import time, base64, csv

class wizard_load_csv(osv.osv_memory):
    _name = 'wizard.load.csv'
    _columns = {
        'date': fields.date('Fecha', required=True),
        'period_id': fields.many2one('hr.contract.period', 'Periodo', required=True),
        'tipo': fields.many2one('hr.expense.type', 'Tipo de Egreso', required=True),
        'data': fields.binary('Archivo', required=True),
        'wrong_values': fields.text('Cédulas con valores Erróneos', readonly=True),
        'num_registros': fields.char('Numero de Registros Cargados', size=16, readonly=True),
        'state': fields.selection([('init', 'init'), ('done', 'done')], 'Estado'),
    }
    _defaults = {
        'state': lambda * a: 'init',
        'date': lambda * a: time.strftime('%Y-%m-%d'),
    }
    
    def __get_datas(self, reader):
        res = []
        for index, data in enumerate(reader):
            if not index:
                fields = data
                continue
            aux = {}
            for i, field in enumerate(fields):
                if fields:
                    aux[field] = len(data) > i and data[i] or None
            res.append(aux)
        return res

    def load_csv_aaa(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids):
            wrong_values = []
            num_reg = num_total = 0
            for reg in self.__get_datas(csv.reader(StringIO(base64.decodestring(obj.data)))):
                num_total += 1
                employee_id = self.pool.get('hr.employee').search(cr, uid, [('identification_id', '=', reg.get('identification_id', None))], limit=1)
                employee_id = employee_id and employee_id[0]
                if not employee_id:
                    wrong_values.append(u'El dato %s de la columna "identification_id" es erroneo'%reg.get('identification_id'))
                    continue
                employee = self.pool.get('hr.employee').browse(cr, uid, employee_id)
                if not employee.contract_id:
                    wrong_values.append(u'%s no posee un contrato válido'%employee.name)
                    continue
                if not reg.get('value'):
                    wrong_values.append(u'No hay un valor para %s'%employee.name)
                    continue
                partner_id = self.pool.get('res.partner').search(cr, uid, [('name', '=', reg.get('partner_id', None))], limit=1)
                self.pool.get('hr.expense').create(cr, uid, dict(employee_id=employee.id,
                                                                 expense_type_id=obj.tipo.id,
                                                                 contract_id=employee.contract_id.id,
                                                                 value=float(reg['value']),
                                                                 date=time.strftime('%Y/%m/%d : %H:%M'),
                                                                 period_id=obj.period_id.id,
                                                                 state='draft',
                                                                 res_partner=partner_id and partner_id[0] or False))
                num_reg += 1
            self.write(cr, uid, [obj.id], dict(num_registros='%s de %s'%(num_reg, num_total),
                                               wrong_values='\n'.join(wrong_values),
                                               state='done'))
        return True
    
wizard_load_csv()