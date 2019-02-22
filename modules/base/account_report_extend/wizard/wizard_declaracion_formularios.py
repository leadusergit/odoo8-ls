# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Module
#    Copyright (C) 2010 Atikasoft  All Rights Reserved
#    info@atikasoft.com.ec
#    $Id$
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import wizard
import base64
import pooler
from time import strftime
from openerp.osv import osv, fields
from xml.dom.minidom import Document


init_form = """<?xml version="1.0"?>
<form string="Asistente para el archivo Reporte Estado de las vallas">
      <field name="company" required="1"  colspan="4"/>
      <field name="formulario" required="1"  colspan="4"/>
      <field name="version" required="1"  colspan="4"/>
</form>
"""

form_finish = """<?xml version="1.0"?>
<form string="Generar Formulario 103">
    <image name="gtk-dialog-info" colspan="2"/>
    <group colspan="2" col="4">
        <separator string="Archivo Generado" colspan="4"/>
        <field name="data" readonly="1" colspan="3"/>
    </group>
</form>"""


init_fields = {
    'formulario':{'string':"Formulario:",'type':'selection','selection':[('103','103'),('104','104')]},
    'company' : {'string':'Compania', 'type':'many2one', 'relation':'res.company'}, 
    'version': {'string':'Version Formulario', 'type':'char', 'size': 20,},   
}

finish_fields = {
    'data': {'string':'Archivo', 'type':'binary', 'readonly': True, },
    'name': {'string':'Nombre', 'type':'string', 'readonly': True, },
}

class wizard_declaracion_formularios(wizard.interface):
 
    
     def _generate_file(self, cr, uid, data, context):
        #print "DATA: ", data
        id_header = data['id']
        #print "id_header:",id_header
        id_formulario = data['form']['formulario']
        #print"id_formulario:",id_formulario
        version = data['form']['version']
        #print"version:",version
        
        # Obtener Informacion de la compania
        compania = data['form']['company']
        #print "compania:",compania
        lineas = pooler.get_pool(cr.dbname).get('res.company').browse(cr, uid, [compania])[0]
        empresa = lineas.partner_id.name
        #print"empresa:",empresa
        ruc_empresa = lineas.partner_id.ident_num
        #print "RUC: ", ruc_empresa
        
        # Obtener fechas
        fechas = pooler.get_pool(cr.dbname).get('account.tax.header').browse(cr, uid, [id_header])[0]
        
        anio, mes, dia,  = str(fechas.inicio).split("-")
        #print "dia: ", dia
        #print "mes: ", mes
        #print "anio: ", anio
        
        doc = Document()
        
#        xml = doc.createElement("xml")
#        doc.appendChild(xml)
        
        mainform = doc.createElement("formulario")
        mainform.setAttribute("version", "0.2")
        doc.appendChild(mainform)
        
        cabecera = doc.createElement("cabecera")
        mainform.appendChild(cabecera)        
        
        codversion = doc.createElement("codigo_version_formulario")
        cabecera.appendChild(codversion)
        pversion = doc.createTextNode(str(version))
        codversion.appendChild(pversion)
        
        ruc = doc.createElement("ruc")
        cabecera.appendChild(ruc)
        pruc = doc.createTextNode(str(ruc_empresa))
        ruc.appendChild(pruc)
        
        moneda = doc.createElement("codigo_moneda")
        cabecera.appendChild(moneda)
        pmoneda = doc.createTextNode("1")
        moneda.appendChild(pmoneda)
        
        detalle = doc.createElement("detalle")
        mainform.appendChild(detalle)  
        
        campo = doc.createElement("campo")
        campo.setAttribute("numero", "31")
        detalle.appendChild(campo)
        pvalor = doc.createTextNode("O")
        campo.appendChild(pvalor)
        
        campo = doc.createElement("campo")
        campo.setAttribute("numero", "101")
        detalle.appendChild(campo)
        pvalor = doc.createTextNode(str(mes))
        campo.appendChild(pvalor)   

        campo = doc.createElement("campo")
        campo.setAttribute("numero", "102")
        detalle.appendChild(campo)
        pvalor = doc.createTextNode(str(anio))
        campo.appendChild(pvalor)    
        
        campo = doc.createElement("campo")
        campo.setAttribute("numero", "104")
        detalle.appendChild(campo)
        
        campo = doc.createElement("campo")
        campo.setAttribute("numero", "198")
        detalle.appendChild(campo)
        pvalor = doc.createTextNode("1707779961")
        campo.appendChild(pvalor)  

        campo = doc.createElement("campo")
        campo.setAttribute("numero", "199")
        detalle.appendChild(campo)   
        
        campo = doc.createElement("campo")
        campo.setAttribute("numero", "201")
        detalle.appendChild(campo)
        pvalor = doc.createTextNode(str(ruc_empresa))
        campo.appendChild(pvalor)   
        
        campo = doc.createElement("campo")
        campo.setAttribute("numero", "202")
        detalle.appendChild(campo)
        pvalor = doc.createTextNode(str(empresa))
        campo.appendChild(pvalor)                               
                  
        
        sql = """ select code from account_tax_code where formulario  = '""" + str(id_formulario) + """' order by code """   
        cr.execute(sql)     
        res = cr.dictfetchall() 
        for codigos in res:
            det_ids = pooler.get_pool(cr.dbname).get('account.tax.type').search(cr, uid, [('header_id', '=', id_header), ('code', '=', str(codigos['code'])), ('formulario', '=', str(id_formulario) )])
            #print "det_ids: ", det_ids
            if det_ids:
                lineas = pooler.get_pool(cr.dbname).get('account.tax.type').browse(cr, uid, det_ids)
                for item in lineas: 
                    campo = doc.createElement("campo")
                    campo.setAttribute("numero", str(item.code))
                    detalle.appendChild(campo)
                    pvalor = doc.createTextNode(str(item.b_total))
                    campo.appendChild(pvalor)  
            else:
                #print "SIN VALOR"
                campo = doc.createElement("campo")
                campo.setAttribute("numero", str(codigos['code']))
                detalle.appendChild(campo)
                pvalor = doc.createTextNode("0.00")
                campo.appendChild(pvalor)  
                
        #print doc.toprettyxml(indent="  ") 
         
        out = base64.encodestring(doc.toprettyxml(indent="  "))
        if (id_formulario=='103'):
            return {'data' : out, 'name' : 'Formulario_103.xml'}
        elif (id_formulario=='104'):
            return {'data' : out, 'name' : 'Formulario_104.xml'}
        

     states = {
        'init' : {
            'actions' : [],
            'result' : {'type':'form', 'arch': init_form, 'fields' : init_fields, 'state' : [('end', 'Cancelar', 'gtk-cancel', True), ('generate', 'Generar Archivo')]},
            },
        'generate' : {
            'actions' : [_generate_file],
            'result' : {'type': 'form', 'arch' : form_finish, 'fields' : finish_fields, 'state' : [('end', 'Cerrar', 'gtk-ok', True)]}
            }
        }
    
wizard_declaracion_formularios('wizard.declaracion.formularios')
