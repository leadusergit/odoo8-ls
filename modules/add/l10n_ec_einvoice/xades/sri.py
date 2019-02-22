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
from .xades import CheckDigit

SCHEMAS = {
    'out_invoice': 'schemas/factura.xsd',
    'out_refund': 'schemas/Notas_de_Credito_V1.1.0.xsd',
    'retention': 'schemas/Comprobante_de_Retención_V1.0.0.xsd',
    'delivery': 'schemas/delivery.xsd',
    'in_refund': 'schemas/nota_debito.xsd'
}

class DocumentXML(object):
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
    def send_receipt(self, document,access_key):
        """envia comprobante codificado para solicitar autorización""" 
        
        print"documento-sri-send=%s"%document
        """Se imprime el tipo  de ambiente en el que se genera el comprobante pruebas o producción"""
        ambiente_send = access_key[23:24] 
        print"  ambiente_send=%s"%ambiente_send
        
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
        #if not utils.check_service('prueba'):
        if not utils.check_service(a):
            raise osv.except_osv('Error SRI', 'Servicio SRI no disponible.')

        if a =='prueba':
           client = Client(SriService.get_active_ws()[0])
           #print"get_active_ws()[0] =%s"%get_active_ws()[0] 
           print"client-send-sri-pruebas=%s"%client
           result =  client.service.validarComprobante(buffer_xml)
           print"result-sri-pruebas=%s"%result
        else:
            client = Client(SriService.get_ws_prod()[0])
            #print"get_active_prod()[0] =%s"%get_active_prod()[0] 
            print"client-send-sri-prod=%s"%client
            result =  client.service.validarComprobante(buffer_xml)
            print"result-sri-prod=%s"%result
        
        
        if result.estado == 'RECIBIDA':
            return True
        else:
            raise osv.except_osv(u'Error SRI',result)
            #return False, result

    def request_authorization(self, access_key):
        messages = []
        
        """Se imprime el tipo  de ambiente en el que se genera el comprobante pruebas[1] o producción [2]"""
        ambiente_request= access_key[23:24]
        print" ambiente_request=%s"%ambiente_request
        
        """Se selecciona el web service de autorización según el ambiente"""
        if  ambiente_request =='1':
            client = Client(SriService.get_active_ws()[1])
            print" client-autorizacion-pruebas=%s"%client
            result =  client.service.autorizacionComprobante(access_key)
            print" result-autorizacion-pruebas=%s"%result
            autorizacion = result.autorizaciones[0][0]
            print" autorizacion-pruebas=%s"%autorizacion
        else:
            client = Client(SriService.get_ws_prod()[1])
            print" client-autorizacion-prod=%s"%client
            result =  client.service.autorizacionComprobante(access_key)
            print" result-autorizacion-prod=%s"%result
            autorizacion = result.autorizaciones[0][0]
            print" autorizacion-prod=%s"%autorizacion
        #for m in autorizacion.mensajes[0]:
        for m in autorizacion[0]:       
            print"autorizacion[0]=%s"%autorizacion[0]
            #messages.append([m.identificador, m.mensaje, m.tipo])--cerfificar para que sirve esta linea
        
        print" autorizacion.estado-114sri.py=%s"%autorizacion.estado
                
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
            #return False, messages, False
            raise osv.except_osv(u'Error SRI',messages )


class SriService(object):

    __AMBIENTE_PRUEBA = '1' #guardar tipo de ambiente en campo "ambiente" tabla account_invoice
    __AMBIENTE_PROD = '2'
    __WS_TEST_RECEIV = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
    __WS_TEST_AUTH = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'
    __WS_RECEIV = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
    __WS_AUTH = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'

    __WS_TESTING = (__WS_TEST_RECEIV, __WS_TEST_AUTH)
    __WS_PROD = (__WS_RECEIV, __WS_AUTH)
    __WS_ACTIVE = __WS_TESTING

    @classmethod
    def get_active_env(self):
         return self.get_env_test()
             
    @classmethod
    def get_env_test(self):
        return self.__AMBIENTE_PRUEBA

    @classmethod
    def get_env_prod(self):
        return self.__AMBIENTE_PROD

    @classmethod
    def get_ws_test(self):
        return self.__WS_TEST_RECEIV, self.__WS_TEST_AUTH
    
    @classmethod
    def get_ws_prod(self):
        return self.__WS_RECEIV, self.__WS_AUTH

    @classmethod
    def get_active_ws(self):
        return self.__WS_ACTIVE
    
    @classmethod
    def create_access_key(self, values):
        
        """ recibe una cadena estructurada de 48 posiciones, incluye tipo ambiente en tupla 0 posicion 3 
        (tabla 5 del SRI: pruebas=1, produccion=2) values: tuple ([], [])
        """        
        #dato = ''.join(values[0] + [env] + values[1]) #concatena una lista con un espacio vacio e intercala tipo ambiente
        dato = ''.join(values[0] + values[1])
        print "dato=%s"%dato
        #genera el verificador en modulo 11 y retorna con 49 posiciones
        modulo = CheckDigit.compute_mod11(dato)
        print "modulo=%s"%modulo
        access_key = ''.join([dato, str(modulo)])
        print"access_key-lin169-sri.py=%s"%access_key
        
        return access_key

