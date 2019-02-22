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
from datetime import datetime
from dateutil.relativedelta import relativedelta

class hr_fiscalyear(osv.osv):
    _name = "hr.fiscalyear"
    _description = "Fiscal Year"
    _order = "date_start"
    _columns = {
        'name': fields.char('Año Fiscal', size=64, required=True),
        'code': fields.char('Codigo', size=6, required=True),
        'company_id': fields.many2one('res.company', 'Empresa'),
        'date_start': fields.date('Fecha Inicial', required=True),
        'date_stop': fields.date('Fecha Final', required=True),
        'period_ids': fields.one2many('hr.contract.period', 'fiscalyear_id', 'Periodos'),
        'state': fields.selection([('draft','Borrador'), ('done','Terminado')], 'Estado', readonly=True),
        'basic_salary': fields.float('Salario Básico', digits=(8,2),
                                     help='Es el Salario Básico establecido del año fiscal.', required=True),
    }
    _defaults = {
        'state': lambda *a: 'draft',
    }

    def _check_duration(self,cr,uid,ids):
        obj_fy=self.browse(cr,uid,ids[0])
        if obj_fy.date_stop < obj_fy.date_start:
            return False
        return True

    _constraints = [
        (_check_duration, 'Error ! The duration of the Fiscal Year is invalid. ', ['date_stop'])
    ]
    _sql_constraints = [
        ('rule_fiscalyear', 'UNIQUE (name)', 'Solo puede definir un Salario Básico por año.' )
    ]

    def create_period3(self,cr, uid, ids, context={}):
        return self.create_period(cr, uid, ids, context, 3)

    def create_period(self,cr, uid, ids, context={}, interval=1):
        for fy in self.browse(cr, uid, ids, context):
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            while ds.strftime('%Y-%m-%d')<fy.date_stop:
                de = ds + relativedelta(months=interval, days=-1)

                if de.strftime('%Y-%m-%d')>fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

                self.pool.get('hr.contract.period').create(cr, uid, {
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                })
                ds = ds + relativedelta(months=interval)
        return True

    def find(self, cr, uid, dt=None, exception=True, context={}):
        if not dt:
            dt = datetime.strftime('%Y-%m-%d')
        ids = self.search(cr, uid, [('date_start', '<=', dt), ('date_stop', '>=', dt)])
        if not ids:
            if exception:
                raise osv.except_osv('Error !', 'No hay un año fiscal para este periodo!\nPor favor crear uno.')
            else:
                return False
        return ids[0]
hr_fiscalyear()