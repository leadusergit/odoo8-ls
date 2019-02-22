# -*- coding: utf-8 -*-
##############################################################################
#
#    XADES 
#    Copyright (C) 2014 Cristian Salamea All Rights Reserved
#    cristian.salamea@gmail.com
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

import logging
import os
import StringIO
import base64

from lxml import etree
from lxml.etree import DocumentInvalid
from base64 import decodestring

try:
    from suds.client import Client
    from suds.transport import TransportError
except ImportError:
    raise ImportError('Instalar Libreria suds')

from openerp.osv import osv
from openerp.addons.l10n_ec_einvoice import utils
from openerp.addons.l10n_ec_einvoice.xades.xades import CheckDigit

SCHEMAS = {
    'out_invoice': 'schemas/factura.xsd',
    'out_refund': 'schemas/Notas_de_Credito_V1.1.0.xsd',
    'retention': 'schemas/Comprobante_de_Retención_V1.0.0.xsd',
    'delivery': 'schemas/delivery.xsd',
    'in_refund': 'schemas/nota_debito.xsd'
}

class DocumentXMLOL(object):
    _schema = False
    document = False
      
    @classmethod
    def __init__(self, document, type='out_invoice'):
        """
        document: XML representation
        type: determinate schema
        """
        self.document = document
        self.type_document = type
        self._schema = SCHEMAS[self.type_document]
        self.signed_document = False
    
    @classmethod
    def validate_xml(self):
        """
        """
        MSG_SCHEMA_INVALID = u"El sistema generó el XML pero el comprobante electrónico no pasa la validación XSD del SRI."
        file_path = os.path.join(os.path.dirname(__file__), self._schema)
        print"file_path=%s"%file_path
        schema_file = open(file_path)
        print"schema_file=%s"%schema_file
        xmlschema_doc = etree.parse(schema_file)
        print"xmlschema_doc=%s"%xmlschema_doc
        xmlschema = etree.XMLSchema(xmlschema_doc)
        print"xmlschema=%s"%xmlschema
        try:
            print"document11=%s"%xmlschema.assertValid(self.document)
            xmlschema.assertValid(self.document)
            print"document22 =%s"%xmlschema.assertValid(self.document)
        except DocumentInvalid as e:
            print e
            raise osv.except_osv('Error de Datos', MSG_SCHEMA_INVALID)

          
    @classmethod
    def send_receipt(self, document,access_key,url_recepcion):
        """envia comprobante codificado para solicitar autorización""" 
        
        print"documento-sri-send=%s"%document
        """Se imprime el tipo  de ambiente en el que se genera el comprobante pruebas o producción"""
        ambiente_send = access_key[23:24] 
        print"  ambiente_send=%s"%ambiente_send
        
        buf = StringIO.StringIO()
        buf.write(document)
        buffer_xml = base64.encodestring(buf.getvalue())
        print"  buffer_xml=%s"%buffer_xml

       
        """Se imprime el ambiente"""
        if ambiente_send=='1':
            a='prueba'
        if ambiente_send=='2':
            a='produccion'       
        print"   a=%s"%a

        if not utils.check_service(a):
            raise osv.except_osv('Error SRI', 'Servicio SRI no disponible.')

        client = Client(url_recepcion)#Client(SriService.get_active_ws()[0])
        print"client-send-sri-online=%s"%client
        result =  client.service.validarComprobante(buffer_xml)       
        
        if result.estado == 'RECIBIDA':
            return True
        else:
            return False, result

    def request_authorization(self, access_key,url_autorizacion):
        messages = []
        
        """Se imprime el tipo  de ambiente en el que se genera el comprobante pruebas[1] o producción [2]"""
        ambiente_request= access_key[23:24]
        print" ambiente_request-online=%s"%ambiente_request


        client = Client(url_autorizacion) #Client(SriService.get_active_ws()[1])
        print" client-autorizacion=%s"%client
        result =  client.service.autorizacionComprobante(access_key)
        print" result-autorizacion=%s"%result
        autorizacion = result.autorizaciones[0][0]
        print" autorizacion=%s"%autorizacion
       
        #for m in autorizacion.mensajes[0]:
        for m in autorizacion[0]:       
            print"autorizacion[0]=%s"%autorizacion[0]
            #messages.append([m.identificador, m.mensaje, m.tipo])--cerfificar para que sirve esta linea
        
        print" autorizacion.estado-142sri_add.py=%s"%autorizacion.estado
                
        if autorizacion.estado == 'AUTORIZADO':
            print "autorizacion.estado=%s "%autorizacion.estado
            autorizacion_xml = etree.Element('autorizacion')
            etree.SubElement(autorizacion_xml, 'estado').text = autorizacion.estado
            print "autorizacion.estado=%s "%autorizacion.estado
            etree.SubElement(autorizacion_xml, 'numeroAutorizacion').text = autorizacion.numeroAutorizacion
            print "autorizacion.numeroAutorizacion=%s "%autorizacion.numeroAutorizacion
            #etree.SubElement(autorizacion_xml, 'ambiente').text = autorizacion.ambiente
            #print "autorizacion.ambiente=%s "%autorizacion.ambiente
            etree.SubElement(autorizacion_xml, 'fechaAutorizacion').text = str(autorizacion.fechaAutorizacion.strftime("%d/%m/%Y %H:%M:%S"))
            print "fechaAutorizacion=%s "%str(autorizacion.fechaAutorizacion.strftime("%d/%m/%Y %H:%M:%S"))
            etree.SubElement(autorizacion_xml, 'comprobante').text = etree.CDATA(autorizacion.comprobante)
            print "comprobante=%s "%etree.CDATA(autorizacion.comprobante)

            #print"autorizacion_xml=%s"%autorizacion_xml
            #print"messages=%s"%messages
            #print"autorizacion=%s"%autorizacion

            tree = etree.ElementTree(autorizacion_xml)
            ##facxml = '%s%s.xml' %('/home/leaduser/fee/facturas/autorizadas/',access_key)          
            ##tree.write(facxml,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml")           
                                           
            return autorizacion_xml, messages, autorizacion   
                 
            #autorizado = etree.tostring(autorizacion_xml, messages, autorizacion, pretty_print=True) 

        else:
            return False, messages, False

class DocumentXMLOFFL(object):
    _schema = False
    document = False
      
    @classmethod
    def __init__(self, document, type='out_invoice'):
        """
        document: XML representation
        type: determinate schema
        """
        self.document = document
        self.type_document = type
        self._schema = SCHEMAS[self.type_document]
        self.signed_document = False
    
    @classmethod
    def validate_xml(self):
        """
        """
        MSG_SCHEMA_INVALID = u"El sistema generó el XML pero el comprobante electrónico no pasa la validación XSD del SRI."
        file_path = os.path.join(os.path.dirname(__file__), self._schema)
        print"file_path=%s"%file_path
        schema_file = open(file_path)
        print"schema_file=%s"%schema_file
        xmlschema_doc = etree.parse(schema_file)
        print"xmlschema_doc=%s"%xmlschema_doc
        xmlschema = etree.XMLSchema(xmlschema_doc)
        print"xmlschema=%s"%xmlschema
        try:
            print"document11=%s"%xmlschema.assertValid(self.document)
            xmlschema.assertValid(self.document)
            print"document22 =%s"%xmlschema.assertValid(self.document)
        except DocumentInvalid as e:
            print e
            raise osv.except_osv('Error de Datos', MSG_SCHEMA_INVALID)

          
    @classmethod
    def send_receipt(self, document,access_key,url_recepcion):
        """envia comprobante codificado para solicitar autorización""" 
        
        print"documento-sri-send=%s"%document
        """Se imprime el tipo  de ambiente en el que se genera el comprobante pruebas o producción"""
        ambiente_send = access_key[23:24] 
        print"  ambiente_send-off=%s"%ambiente_send
        
        buf = StringIO.StringIO()
        buf.write(document)
        buffer_xml = base64.encodestring(buf.getvalue())
        print"  buffer_xml=%s"%buffer_xml
        
        """Se selecciona el web service según el ambiente"""
        if ambiente_send=='1':
            a='prueba'
        if ambiente_send=='2':
            a='produccion'       
        print"   a=%s"%a

        if not utils.check_service(a):
            raise osv.except_osv('Error SRI', 'Servicio SRI no disponible.')

        client = Client(url_recepcion)#Client(SriService.get_active_ws()[0])
        print"client-send-sri-off=%s"%client
        result =  client.service.validarComprobante(buffer_xml)       
        
        if result.estado == 'RECIBIDA':
            return True
        else:
            return False, result
        

    def request_authorization(self, access_key,url_autorizacion):
        messages = []
        
        """Se imprime el tipo  de ambiente en el que se genera el comprobante pruebas[1] o producción [2]"""
        ambiente_request= access_key[23:24]
        print" ambiente_request-off=%s"%ambiente_request


        client = Client(url_autorizacion) #Client(SriService.get_active_ws()[1])
        print" client-autorizacion-off=%s"%client
        result =  client.service.autorizacionComprobante(access_key)
        print" result-autorizacion-off=%s"%result
        autorizacion = result.autorizaciones[0][0]
        print" autorizacion-off=%s"%autorizacion
       
        #for m in autorizacion.mensajes[0]:
        for m in autorizacion[0]:       
            print"autorizacion[0]=%s"%autorizacion[0]
            #messages.append([m.identificador, m.mensaje, m.tipo])--cerfificar para que sirve esta linea
        
        #print" autorizacion.estado-264sri_add.py=%s"%autorizacion.estado
                
        if autorizacion.estado == 'AUTORIZADO':
            print "autorizacion.estado=%s "%autorizacion.estado
            autorizacion_xml = etree.Element('autorizacion')
            etree.SubElement(autorizacion_xml, 'estado').text = autorizacion.estado
            print "autorizacion.estado=%s "%autorizacion.estado
            etree.SubElement(autorizacion_xml, 'numeroAutorizacion').text = autorizacion.numeroAutorizacion
            print "autorizacion.numeroAutorizacion=%s "%autorizacion.numeroAutorizacion
            #etree.SubElement(autorizacion_xml, 'ambiente').text = autorizacion.ambiente
            #print "autorizacion.ambiente=%s "%autorizacion.ambiente
            etree.SubElement(autorizacion_xml, 'fechaAutorizacion').text = str(autorizacion.fechaAutorizacion.strftime("%d/%m/%Y %H:%M:%S"))
            print "fechaAutorizacion=%s "%str(autorizacion.fechaAutorizacion.strftime("%d/%m/%Y %H:%M:%S"))
            etree.SubElement(autorizacion_xml, 'comprobante').text = etree.CDATA(autorizacion.comprobante)
            print "comprobante=%s "%etree.CDATA(autorizacion.comprobante)

            #print"autorizacion_xml=%s"%autorizacion_xml
            #print"messages=%s"%messages
            #print"autorizacion=%s"%autorizacion

            tree = etree.ElementTree(autorizacion_xml)
            ##facxml = '%s%s.xml' %('/home/leaduser/fee/facturas/autorizadas/',access_key)          
            ##tree.write(facxml,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml")           
                                           
            return autorizacion_xml, messages, autorizacion   
                 
            #autorizado = etree.tostring(autorizacion_xml, messages, autorizacion, pretty_print=True) 

        else:
            return False, messages, False
