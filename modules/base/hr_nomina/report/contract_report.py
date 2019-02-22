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
import openerp.modules as addons, re, base64, StringIO
from docx import *
from mako.template import Template

def _replace(texto, **args):
    res = []
    pun = texto.find('${')
    if pun >= 0:
        aux = texto[pun:texto.find('}')+1]
        res.append((re.escape(aux), Template(aux).render_unicode(**args)))
        res.extend(_replace(texto[texto.find('}')+1:], **args))
    return res

class contract_report(osv.osv_memory):
    _name = 'contract.report'
    
    def __generate(self, cr, uid, contract_id):
        contract_id = self.pool.get('hr.contract').browse(cr, uid, contract_id)
        document = StringIO.StringIO()
        if not contract_id.type_id.template:
            raise osv.except_osv('Error', u'El tipo de contrato "%s" no posee una plantilla para generar el reporte.'%contract_id.type_id.name)
        document.write(base64.decodestring(contract_id.type_id.template))
        document = opendocx(document)
                
        for paratext in getdocumenttext(document):
            for orig, new in _replace(paratext, o=contract_id):
                document = advReplace(document, orig, new)
                
        coreprops = coreproperties(title='Contrato o nombramiento de %s'%contract_id.employee_id.name,
                                   subject='Contrato de tipo %s del empleado %s'%(contract_id.name, contract_id.employee_id.name),
                                   creator='Israel Paredes Reyes',
                                   keywords=['OpenERP', 'Contrato', 'Israel'])
        
        out_doc_path = addons.get_module_resource('hr_nomina', 'report') + '/out_file'
        savedocx(document, coreprops, appproperties(), contenttypes(), websettings(),
                 wordrelationships(relationshiplist()), out_doc_path)
        
        file = open(out_doc_path) 
        file_data = "" 
        while 1: 
            line = file.readline() 
            file_data += line 
            if not line: 
                break 

        file.close()
        out = base64.b64encode(file_data)
        os.unlink(out_doc_path)
        return {'file': out, 'file_name': 'Contrato para %s.docx'%contract_id.employee_id.name}
    
    def view_init(self, cr, uid, fields_name, context):
        if context.get('active_model') == 'hr.contract':
            vals = self.__generate(cr, uid, context.get('active_id'))
            context.update(dict(default_file=vals['file'],
                                default_file_name=vals['file_name']))
            
    _columns = {
        'file': fields.binary('Archivo generado'),
        'file_name': fields.char('Nombre del archivo', size=512)
    }
    
contract_report()