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
from openerp.addons.base_ec.tools.xls_tools import *
from cStringIO import StringIO
from base64 import encodestring
from xlwt import Workbook
import time

def style(bold=False, font_name='Calibri', size=11, font_color='black',
          rotation=0, align='left', vertical='center', wrap=False,
          border=False, color=None, format=None):
    return get_style(bold, font_name, size, font_color, rotation, align, vertical, wrap, border, color, format)

STYLES = {
    'company': style(True, size=14, font_color='dark_red_ega'),
    'header': style(True, size=12),
    'title': style(True, size=12, font_color='dark_yellow', align='center'),
}

class wizard_common_xls_report(osv.osv_memory):
    _name = 'wizard.common.xls.report'
#     _inherit = 'ir.wizard.screen'
    _description = 'Reporte excel'
    _columns = {
        'file': fields.binary('Archivo', readonly=True),
        'filename': fields.char('Nombre del acrchivo', size=512, readonly=True),
        'state': fields.selection([('draft', 'Borrador'), ('done', 'Generado')], 'Estado', required=True, readonly=True)
    }
    _defaults = {
        'state': lambda *a: 'draft'
    }
    
    def get_encabezado(self, cr, uid, sheet, width):
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        sheet.write(0, 0, company.name, STYLES['company'])
        sheet.write(1, 0, company.rml_header1, STYLES['header'])
        sheet.write(2, 0, company.rml_footer1, STYLES['header'])
        sheet.write(3, 0, company.rml_footer2, STYLES['header'])
        sheet.write_merge(5, 5, 0, width-1, self._description, STYLES['title'])
        return 8
    
    def preprint_xls(self, cr, uid, width=15):
        book = Workbook(encoding='utf-8')
        sheet = book.add_sheet('Hoja 1')
        row = self.get_encabezado(cr, uid, sheet, width)
        return book, sheet, row
    
    def print_report_xls(self, cr, uid, ids, context):
        raise ('Error', 'No implementado')
    
    def save_book(self, book):
        buf = StringIO()
        book.save(buf)
        outfile = encodestring(buf.getvalue())
        buf.close()
        return {'state': 'done', 'file': outfile, 'filename': self._description + time.strftime(' (%Y%b%d %H:%M:%S)').upper() + '.xls'}
    
wizard_common_xls_report()