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
import time

class base_file_report(osv.osv_memory):
    """Modelo en memoria para almacenar temporalmente los archivos generados al cargar un reporte.
    Todos los asistentes que generen un archivo (xls, xml, etc.) deben devolver la función show()"""
    _name = 'base.file.report'
    _columns = {
        'file': fields.binary('Archivo generado', readonly=True, required=True),
        'filename': fields.char('Archivo generado', required=True)
    }
    
    def show(self, cr, uid, file, filename, context=None):
        id = self.create(cr, uid, {'file': file, 'filename': filename}, context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': filename + time.strftime(' (%Y-%m-%d %H:%M:%S)'),
            'res_model': self._name,
            'res_id': id,
            'view_mode': 'form',
            'target': 'new'
        }
base_file_report()