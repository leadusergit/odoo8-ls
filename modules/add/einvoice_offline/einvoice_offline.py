# -*- coding: utf-8 -*-
##############################################################################
#
#    E-Invoice Module - Ecuador
#    Copyright (C) 2014 VIRTUALSAMI CIA. LTDA. All Rights Reserved
#    alcides@virtualsami.com.ec
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


import os
import hashlib
import subprocess
import time
from datetime import datetime
import logging
import base64
import urllib2
import httplib
import StringIO

from lxml import etree
from xml.dom.minidom import parse, parseString
from socket import error as SocketError

from openerp.osv import osv, fields
from openerp.tools import config
from openerp.tools.translate import _
from openerp.tools import ustr
import openerp.addons.decimal_precision as dp
import openerp.netsvc
import openerp.addons.l10n_ec_einvoice.utils
import glob
from lxml import etree #import añadido
from openerp.addons.l10n_ec_einvoice.xades.sri import SriService
from openerp.addons.einvoice_offline.sri_add import DocumentXMLOL,DocumentXMLOFFL
from openerp.addons.l10n_ec_einvoice.xades.xades import Xades
from ubuntu_sso.utils.ipc import LOCALHOST
from __builtin__ import True
from atom import Feed

try:
    from suds.client import Client
    from suds.transport import TransportError
except ImportError:
    raise ImportError('Instalar Libreria suds')

tipoDocumento = {
    '01': '01',
    '04': '04',
    '05': '05',
    '06': '06',
    '07': '07',
    '18': '01',
}

tipoIdentificacion = {
    'r' : '04',
    'c' : '05',
    'p' : '06',
    'venta_consumidor_final' : '07',
    'identificacion_exterior' : '08',
    'placa' : '09',
}

codigoImpuesto = {
    'vat': '2',
    'vat0': '2',
    'ice': '3',
    'other': '5'
}

tarifaImpuesto = {
    'vat0': '0',
    'vat': '2',
    'novat': '6',
    'other': '7',
}

class res_company(osv.osv):
    _inherit ='res.company'
    
    
    _columns = {
    'is_offline': fields.boolean('Facturación Offline',default=lambda *a: False),
    'recepcion_online': fields.char('URL Recepción Online'),
    'autorizacion_online': fields.char('URL Autorización Online'),
    'recepcion_offline': fields.char('URL Recepción Offline'),
    'autorizacion_offline': fields.char('URL Autorización Offline'),
    'recepcion_pruebas_online': fields.char('URL Recepción pruebas Online'),
    'autorizacion_pruebas_online': fields.char('URL Autorización pruebas Online'),
    'recepcion_pruebas_offline': fields.char('URL Recepción pruebas Offline'),
    'autorizacion_pruebas_offline': fields.char('URL Autorización pruebas Offline'),
    }

class account_invoice(osv.osv):
    _inherit ='account.invoice'
    
    
    _columns = {
    'numero_autorizacion_offline': fields.char('Número de Autorización Offline', size=49, readonly=True),
    'is_offline': fields.related('company_id','is_offline',type='boolean', string='Offline',readonly=True), 

    }

    
    def action_generate_einvoice(self, cr, uid, ids, context=None):

        LIMIT_TO_SEND = 5
        WAIT_FOR_RECEIPT = 3
        TITLE_NOT_SENT = u'No se puede enviar el comprobante electrónico al SRI'
        MESSAGE_SEQUENCIAL = u'Los comprobantes electrónicos deberán ser enviados al SRI para su autorización en orden cronológico y secuencial. Por favor enviar primero el comprobante inmediatamente anterior'
        MESSAGE_TIME_LIMIT = u'Los comprobantes electrónicos deberán enviarse a las bases de datos del SRI para su autorización en un plazo máximo de 24 horas'
        
        for obj in self.browse(cr, uid, ids):
           
            if not obj.type in [ 'out_invoice', 'out_refund']:
                print "no disponible para otros documentos"
                continue

            """"Validar que el envío del comprobante electrónico se realice dentro de las 24 horas posteriores a su emisión"""
            if (datetime.now() - datetime.strptime(obj.date_invoice, '%Y-%m-%d')).days > LIMIT_TO_SEND:
                raise osv.except_osv(TITLE_NOT_SENT, MESSAGE_TIME_LIMIT)
            
            """"Validar que el envío de los comprobantes electrónicos sea secuencial"""
            if not self.check_before_sent(cr, uid, obj):
                raise osv.except_osv(TITLE_NOT_SENT, MESSAGE_SEQUENCIAL)
            ak_temp = self.get_access_key(cr, uid, obj)
            access_key = SriService.create_access_key(ak_temp)
            emission_code = obj.company_id.emission_code

            """"Move write. Completa datos de acces key y del tipo de emision en el registro concurrente"""
            self.write(cr, uid, [obj.id], {'clave_acceso': access_key, 'emission_code': emission_code})

            if obj.type == 'out_invoice':
                """ XML del comprobante electrónico: factura"""
                factura = self._generate_xml_invoice(obj, access_key, emission_code)    
                          
                if obj.company_id.is_offline:
                    """validación del xml"""
                    inv_xml = DocumentXMLOFFL(factura, 'out_invoice')
                    inv_xml.validate_xml()  
                else:
                    """validación del xml"""
                    inv_xml = DocumentXMLOL(factura, 'out_invoice')
                    inv_xml.validate_xml() 
                
                """Generar Factura impresa en el path dado con la clave de acceso como nombre"""
                
                tree = etree.ElementTree(factura)
                facxml = '%s%s.xml' %(obj.company_id.bills_generated,access_key)
                tree.write(facxml,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml") 
                
                """parametros para generar factura firmada"""
                xades = Xades()
                ##pathxml='%s%s.xml' %('/home/leaduser/fee/facturas/facturas/',access_key)
                pathxml='%s%s.xml' %(obj.company_id.bills_generated,access_key)
                file_pk12 = obj.company_id.electronic_signature
                password = obj.company_id.password_electronic_signature    
                pathout=obj.company_id.bills_signed
                nameout='%s.xml'%access_key
                
                """generar factura firmada"""      
               
                signed_document = xades.apply_digital_signature(pathxml,file_pk12, password,pathout,nameout)                            
              
                """enviar comprobante electrónico"""                             
                #fac=open('%s%s.xml' %('/home/leaduser/fee/facturas/firmadas/',access_key))
                fac=open('%s%s.xml' %(obj.company_id.bills_signed,access_key))
                facr=fac.read()
                #print "leer factura =%s"%facr               
                """tipofe 0 online 1 offline ambiente 1 pruebas 2 produccion"""
                tipofe=obj.company_id.is_offline
                print"tipofe-fac=%s"%tipofe                
                ambiente=obj.company_id.ambiente_code
                print"ambiente-fac=%s"%ambiente
                
                
                if not tipofe and ambiente=='2':
                    inv_xml.send_receipt(facr,access_key,obj.company_id.recepcion_online)
                    time.sleep(WAIT_FOR_RECEIPT)
                if not tipofe and ambiente=='1':
                    print"recepcion_pruebas_online_fac=%s"%obj.company_id.recepcion_pruebas_online
                    inv_xml.send_receipt(facr,access_key,obj.company_id.recepcion_pruebas_online)
                    time.sleep(WAIT_FOR_RECEIPT)
                
                if tipofe and ambiente=='2':
                    inv_xml.send_receipt(facr,access_key,obj.company_id.recepcion_offline)
                    time.sleep(WAIT_FOR_RECEIPT)
                if tipofe and ambiente=='1':
                    print"recepcion_pruebas_offline_fac=%s"%obj.company_id.recepcion_pruebas_offline
                    inv_xml.send_receipt(facr,access_key,obj.company_id.recepcion_pruebas_offline)
                    time.sleep(WAIT_FOR_RECEIPT)

                """solicitud de autorización del comprobante electrónico"""
                if not tipofe and ambiente=='2':
                    doc_xml, m, auth = inv_xml.request_authorization(access_key,obj.company_id.autorizacion_online)
                if not tipofe and ambiente=='1':
                    doc_xml, m, auth = inv_xml.request_authorization(access_key,obj.company_id.autorizacion_pruebas_online)
                    print"autorizacion_pruebas_online_fac=%s"%obj.company_id.autorizacion_pruebas_online
                
                if tipofe and ambiente=='2':
                    doc_xml, m, auth = inv_xml.request_authorization(access_key,obj.company_id.autorizacion_offline)
                if tipofe and ambiente=='1':
                    doc_xml, m, auth = inv_xml.request_authorization(access_key,obj.company_id.autorizacion_pruebas_offline)
                    print"autorizacion_pruebas_offline_fac=%s"%obj.company_id.autorizacion_pruebas_offline
                ##fact_aut = etree.tostring(doc_xml, pretty_print=True)
                ##print " fact_aut =%s"%fact_aut """
                
                """Imprimir factura autorizada y guardar en carpeta"""
                tree = etree.ElementTree(doc_xml)
                autorizada ='%s%s.xml'%(obj.company_id.bills_authorized,access_key)
                print"obj.company_id.bills_authorized=%s"%obj.company_id.bills_authorized
                tree.write(autorizada,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml")                        
                print"faut.write=%s"%tree.write    
                                     
                if doc_xml is None:
                    msg = ' '.join(m)
                    raise m            
                """Se obtiene id de factura y se llama metodo actualizacion de datos"""
                idfac=obj.id
                
                
                if obj.company_id.is_offline:
                    self.datos_autorizacion_offline(cr, uid, auth, idfac,access_key)
                else:
                    self.datos_autorizacion(cr, uid, auth, idfac)
                """enviar factura a correo de cliente """
                #self.send_mail_invoice(cr, uid, obj, doc_xml, auth, context)
                
            else: # Cuando el doc electrónico es una Nota de Crédito
                
                if not obj.origin:
                    raise osv.except_osv('Error de Datos', u'Falta el motivo de la devolución')
                invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('number','=',obj.name)])
                factura_origen = self.browse(cr, uid, invoice_ids, context = context)
                print"factura_origen = %s "%factura_origen
                
                """"XML del comprobante electrónico: nota de crédito"""
                notacredito = self._generate_xml_refund(obj, factura_origen, access_key, emission_code)
                ##notacred = etree.tostring(notacredito, pretty_print=True)
                ##print "notacredito-else=%s"%notacred
                
                if obj.company_id.is_offline:
                    """validación del xml NC"""
                    inv_xml = DocumentXMLOFFL(notacredito, 'out_refund')
                    inv_xml.validate_xml()  
                else:
                    """validación del xml NC"""
                    inv_xml = DocumentXMLOL(notacredito, 'out_refund')
                    inv_xml.validate_xml() 
                
                              
                """Imprimir NC en ubicación dada con la clave de acceso como nombre"""                                            
                tree = etree.ElementTree(notacredito)
                ncxml = '%s%s.xml' %(obj.company_id.credit_note_generated,access_key)
                tree.write(ncxml,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml")
               
                """Parametros para generar nota de crédito firmada"""
                xades = Xades()
                pathxml='%s%s.xml' %(obj.company_id.credit_note_generated,access_key)
                file_pk12 = obj.company_id.electronic_signature
                password = obj.company_id.password_electronic_signature    
                pathout=obj.company_id.credit_note_signed
                nameout='%s.xml'%access_key
                
                """generar nota de crédito firmada"""      
               
                signed_document = xades.apply_digital_signature(pathxml,file_pk12, password,pathout,nameout) 
                
                """enviar comprobante electrónico al SRI"""                             
                nc=open('%s%s.xml' %(obj.company_id.credit_note_signed,access_key))
                ncr=nc.read()              
                
                
                """tipofe 0 online 1 offline ambiente 1 pruebas 2 produccion"""
                
                tipofe=obj.company_id.is_offline
                print"tipofe-nc=%s"%tipofe                
                ambiente=obj.company_id.ambiente_code
                print"ambiente-nc=%s"%ambiente
                
                
                if not tipofe and ambiente=='2':
                    inv_xml.send_receipt(ncr,access_key,obj.company_id.recepcion_online)
                    time.sleep(WAIT_FOR_RECEIPT)
                if not tipofe and ambiente=='1':
                    print"recepcion_pruebas_online_nc=%s"%obj.company_id.recepcion_pruebas_online
                    inv_xml.send_receipt(ncr,access_key,obj.company_id.recepcion_pruebas_online)
                    time.sleep(WAIT_FOR_RECEIPT)
                
                if tipofe and ambiente=='2':
                    inv_xml.send_receipt(ncr,access_key,obj.company_id.recepcion_offline)
                    time.sleep(WAIT_FOR_RECEIPT)
                if tipofe and ambiente=='1':
                    print"recepcion_pruebas_offline_nc=%s"%obj.company_id.recepcion_pruebas_offline
                    inv_xml.send_receipt(ncr,access_key,obj.company_id.recepcion_pruebas_offline)
                    time.sleep(WAIT_FOR_RECEIPT)
                

                """solicitud de autorización del comprobante electrónico"""
                if not tipofe and ambiente=='2':
                    doc_xml, m, auth = inv_xml.request_authorization(access_key,obj.company_id.autorizacion_online)
                if not tipofe and ambiente=='1':
                    doc_xml, m, auth = inv_xml.request_authorization(access_key,obj.company_id.autorizacion_pruebas_online)
                    print"autorizacion_pruebas_on-nc=%s"%obj.company_id.autorizacion_pruebas_online
                
                if tipofe and ambiente=='2':
                    doc_xml, m, auth = inv_xml.request_authorization(access_key,obj.company_id.autorizacion_offline)
                if tipofe and ambiente=='1':
                    doc_xml, m, auth = inv_xml.request_authorization(access_key,obj.company_id.autorizacion_pruebas_offline)
                    print"autorizacion_pruebas_off-nc=%s"%obj.company_id.autorizacion_pruebas_offline
                
                
                """Imprimir nota de crèdito autorizada y guardar en carpeta"""
                tree = etree.ElementTree(doc_xml)
                autorizada ='%s%s.xml'%(obj.company_id.credit_note_authorized,access_key)
                tree.write(autorizada,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml")                          
                                     
                if doc_xml is None:
                    msg = ' '.join(m)
                    raise m        
                    
                """Se obtiene id de factura y se llama metodo actualizacion de datos"""
                idfac=obj.id
                
                if obj.company_id.is_offline:
                    self.datos_autorizacion_offline(cr, uid, auth, idfac,access_key)
                else:
                    self.datos_autorizacion(cr, uid, auth, idfac)
                
                """envío del correo electrónico de nota de crédito al cliente"""
                #self.send_mail_refund(cr, uid, obj, access_key, context)
                
    
    
    def action_generate_einvoice_offline(self, cr, uid, ids, context=None):

        for obj in self.browse(cr, uid, ids):
           
            if not obj.type in [ 'out_invoice', 'out_refund']:
                print "no disponible para otros documentos"
                continue

            ak_temp = self.get_access_key(cr, uid, obj)
            access_key = SriService.create_access_key(ak_temp)
            emission_code = obj.company_id.emission_code

            """"Move write. Completa datos de acces key y del tipo de emision en el registro concurrente"""
            self.write(cr, uid, [obj.id], {'clave_acceso': access_key, 'emission_code': emission_code,'numero_autorizacion_offline':access_key})

            if obj.type == 'out_invoice':
                """ XML del comprobante electrónico: factura"""
                factura = self._generate_xml_invoice(obj, access_key, emission_code)    
                          
                if obj.company_id.is_offline:
                    """validación del xml"""
                    inv_xml = DocumentXMLOFFL(factura, 'out_invoice')
                    inv_xml.validate_xml()  
                else:
                    """validación del xml"""
                    inv_xml = DocumentXMLOL(factura, 'out_invoice')
                    inv_xml.validate_xml() 
                
                """Generar Factura impresa en el path dado con la clave de acceso como nombre"""
                
                tree = etree.ElementTree(factura)
                facxml = '%s%s.xml' %(obj.company_id.bills_generated,access_key)
                tree.write(facxml,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml") 
                
                """parametros para generar factura firmada"""
                xades = Xades()
                ##pathxml='%s%s.xml' %('/home/leaduser/fee/facturas/facturas/',access_key)
                pathxml='%s%s.xml' %(obj.company_id.bills_generated,access_key)
                file_pk12 = obj.company_id.electronic_signature
                password = obj.company_id.password_electronic_signature    
                pathout=obj.company_id.bills_signed
                nameout='%s.xml'%access_key
                
                """generar factura firmada"""      
               
                signed_document = xades.apply_digital_signature(pathxml,file_pk12, password,pathout,nameout)                            
              
            else: # Cuando el doc electrónico es una Nota de Crédito
                
                if not obj.origin:
                    raise osv.except_osv('Error de Datos', u'Falta el motivo de la devolución')
                invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('number','=',obj.name)])
                factura_origen = self.browse(cr, uid, invoice_ids, context = context)
                print"factura_origen = %s "%factura_origen
                
                """"XML del comprobante electrónico: nota de crédito"""
                notacredito = self._generate_xml_refund(obj, factura_origen, access_key, emission_code)
                ##notacred = etree.tostring(notacredito, pretty_print=True)
                ##print "notacredito-else=%s"%notacred
                
                if obj.company_id.is_offline:
                    """validación del xml NC"""
                    inv_xml = DocumentXMLOFFL(notacredito, 'out_refund')
                    inv_xml.validate_xml()  
                else:
                    """validación del xml NC"""
                    inv_xml = DocumentXMLOL(notacredito, 'out_refund')
                    inv_xml.validate_xml() 
                
                              
                """Imprimir NC en ubicación dada con la clave de acceso como nombre"""                                            
                tree = etree.ElementTree(notacredito)
                ncxml = '%s%s.xml' %(obj.company_id.credit_note_generated,access_key)
                tree.write(ncxml,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml")
               
                """Parametros para generar nota de crédito firmada"""
                xades = Xades()
                pathxml='%s%s.xml' %(obj.company_id.credit_note_generated,access_key)
                file_pk12 = obj.company_id.electronic_signature
                password = obj.company_id.password_electronic_signature    
                pathout=obj.company_id.credit_note_signed
                nameout='%s.xml'%access_key
                
                """generar nota de crédito firmada"""      
               
                signed_document = xades.apply_digital_signature(pathxml,file_pk12, password,pathout,nameout) 
                
                
    def action_send_einvoice_offline(self, cr, uid, ids, context=None):

        LIMIT_TO_SEND = 5
        WAIT_FOR_RECEIPT = 3
        TITLE_NOT_SENT = u'No se puede enviar el comprobante electrónico al SRI'
        MESSAGE_SEQUENCIAL = u'Los comprobantes electrónicos deberán ser enviados al SRI para su autorización en orden cronológico y secuencial. Por favor enviar primero el comprobante inmediatamente anterior'
        MESSAGE_TIME_LIMIT = u'Los comprobantes electrónicos deberán enviarse a las bases de datos del SRI para su autorización en un plazo máximo de 24 horas'
        
        for obj in self.browse(cr, uid, ids):
           
            if not obj.type in [ 'out_invoice', 'out_refund']:
                print "no disponible para otros documentos"
                continue

            """"Validar que el envío del comprobante electrónico se realice dentro de las 24 horas posteriores a su emisión"""
            if (datetime.now() - datetime.strptime(obj.date_invoice, '%Y-%m-%d')).days > LIMIT_TO_SEND:
                raise osv.except_osv(TITLE_NOT_SENT, MESSAGE_TIME_LIMIT)
            
            """"Validar que el envío de los comprobantes electrónicos sea secuencial"""
            if not self.check_before_sent(cr, uid, obj):
                raise osv.except_osv(TITLE_NOT_SENT, MESSAGE_SEQUENCIAL)                        
              
            if obj.type == 'out_invoice':

                """enviar comprobante electrónico"""                             
                #fac=open('%s%s.xml' %('/home/leaduser/fee/facturas/firmadas/',access_key))
                fac=open('%s%s.xml' %(obj.company_id.bills_signed,obj.clave_acceso))
                facr=fac.read()
                print "leer factura =%s"%facr   
                
                if obj.company_id.is_offline:
                    """validación del xml"""
                    inv_xml = DocumentXMLOFFL(facr, 'out_invoice')
                else:
                    """validación del xml"""
                    inv_xml = DocumentXMLOL(facr, 'out_invoice')
                                
                """tipofe 0 online 1 offline ambiente 1 pruebas 2 produccion"""
                tipofe=obj.company_id.is_offline
                print"tipofe-fac=%s"%tipofe                
                ambiente=obj.company_id.ambiente_code
                print"ambiente-fac=%s"%ambiente
                
                
                if not tipofe and ambiente=='2':
                    inv_xml.send_receipt(facr,obj.clave_acceso,obj.company_id.recepcion_online)
                    time.sleep(WAIT_FOR_RECEIPT)
                if not tipofe and ambiente=='1':
                    print"recepcion_pruebas_online_fac=%s"%obj.company_id.recepcion_pruebas_online
                    inv_xml.send_receipt(facr,obj.clave_acceso,obj.company_id.recepcion_pruebas_online)
                    time.sleep(WAIT_FOR_RECEIPT)
                
                if tipofe and ambiente=='2':
                    inv_xml.send_receipt(facr,obj.clave_acceso,obj.company_id.recepcion_offline)
                    time.sleep(WAIT_FOR_RECEIPT)
                if tipofe and ambiente=='1':
                    print"recepcion_pruebas_offline_fac=%s"%obj.company_id.recepcion_pruebas_offline
                    inv_xml.send_receipt(facr,obj.clave_acceso,obj.company_id.recepcion_pruebas_offline)
                    time.sleep(WAIT_FOR_RECEIPT)

                """solicitud de autorización del comprobante electrónico"""
                if not tipofe and ambiente=='2':
                    doc_xml, m, auth = inv_xml.request_authorization(obj.clave_acceso,obj.company_id.autorizacion_online)
                if not tipofe and ambiente=='1':
                    doc_xml, m, auth = inv_xml.request_authorization(obj.clave_acceso,obj.company_id.autorizacion_pruebas_online)
                    print"autorizacion_pruebas_online_fac=%s"%obj.company_id.autorizacion_pruebas_online
                
                if tipofe and ambiente=='2':
                    doc_xml, m, auth = inv_xml.request_authorization(obj.clave_acceso,obj.company_id.autorizacion_offline)
                if tipofe and ambiente=='1':
                    doc_xml, m, auth = inv_xml.request_authorization(obj.clave_acceso,obj.company_id.autorizacion_pruebas_offline)
                    print"autorizacion_pruebas_offline_fac=%s"%obj.company_id.autorizacion_pruebas_offline
                ##fact_aut = etree.tostring(doc_xml, pretty_print=True)
                ##print " fact_aut =%s"%fact_aut """
                
                """Imprimir factura autorizada y guardar en carpeta"""
                tree = etree.ElementTree(doc_xml)
                autorizada ='%s%s.xml'%(obj.company_id.bills_authorized,obj.clave_acceso)
                print"obj.company_id.bills_authorized=%s"%obj.company_id.bills_authorized
                tree.write(autorizada,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml")                        
                print"faut.write=%s"%tree.write    
                                     
                if doc_xml is None:
                    msg = ' '.join(m)
                    raise m            
                """Se obtiene id de factura y se llama metodo actualizacion de datos"""
                idfac=obj.id
                
                
                if obj.company_id.is_offline:
                    self.datos_autorizacion_offline(cr, uid, auth, idfac,obj.clave_acceso)
                else:
                    self.datos_autorizacion(cr, uid, auth, idfac)
                """enviar factura a correo de cliente """
                #self.send_mail_invoice(cr, uid, obj, doc_xml, auth, context)
                
            else: # Cuando el doc electrónico es una Nota de Crédito
                
                if not obj.origin:
                    raise osv.except_osv('Error de Datos', u'Falta el motivo de la devolución')
                invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('number','=',obj.name)])
                factura_origen = self.browse(cr, uid, invoice_ids, context = context)
                print"factura_origen = %s "%factura_origen
                
                """enviar comprobante electrónico al SRI"""                             
                nc=open('%s%s.xml' %(obj.company_id.credit_note_signed,obj.clave_acceso))
                ncr=nc.read()              
                
                if obj.company_id.is_offline:
                    """validación del xml"""
                    inv_xml = DocumentXMLOFFL(ncr, 'out_invoice')
                else:
                    """validación del xml"""
                    inv_xml = DocumentXMLOL(ncr, 'out_invoice')
                
                """tipofe 0 online 1 offline ambiente 1 pruebas 2 produccion"""
                
                tipofe=obj.company_id.is_offline
                print"tipofe-nc=%s"%tipofe                
                ambiente=obj.company_id.ambiente_code
                print"ambiente-nc=%s"%ambiente
                
                
                if not tipofe and ambiente=='2':
                    inv_xml.send_receipt(ncr,obj.clave_acceso,obj.company_id.recepcion_online)
                    time.sleep(WAIT_FOR_RECEIPT)
                if not tipofe and ambiente=='1':
                    print"recepcion_pruebas_online_nc=%s"%obj.company_id.recepcion_pruebas_online
                    inv_xml.send_receipt(ncr,obj.clave_acceso,obj.company_id.recepcion_pruebas_online)
                    time.sleep(WAIT_FOR_RECEIPT)
                
                if tipofe and ambiente=='2':
                    inv_xml.send_receipt(ncr,obj.clave_acceso,obj.company_id.recepcion_offline)
                    time.sleep(WAIT_FOR_RECEIPT)
                if tipofe and ambiente=='1':
                    print"recepcion_pruebas_offline_nc=%s"%obj.company_id.recepcion_pruebas_offline
                    inv_xml.send_receipt(ncr,obj.clave_acceso,obj.company_id.recepcion_pruebas_offline)
                    time.sleep(WAIT_FOR_RECEIPT)
                

                """solicitud de autorización del comprobante electrónico"""
                if not tipofe and ambiente=='2':
                    doc_xml, m, auth = inv_xml.request_authorization(obj.clave_acceso,obj.company_id.autorizacion_online)
                if not tipofe and ambiente=='1':
                    doc_xml, m, auth = inv_xml.request_authorization(obj.clave_acceso,obj.company_id.autorizacion_pruebas_online)
                    print"autorizacion_pruebas_on-nc=%s"%obj.company_id.autorizacion_pruebas_online
                
                if tipofe and ambiente=='2':
                    doc_xml, m, auth = inv_xml.request_authorization(obj.clave_acceso,obj.company_id.autorizacion_offline)
                if tipofe and ambiente=='1':
                    doc_xml, m, auth = inv_xml.request_authorization(obj.clave_acceso,obj.company_id.autorizacion_pruebas_offline)
                    print"autorizacion_pruebas_off-nc=%s"%obj.company_id.autorizacion_pruebas_offline
                
                
                """Imprimir nota de crèdito autorizada y guardar en carpeta"""
                tree = etree.ElementTree(doc_xml)
                autorizada ='%s%s.xml'%(obj.company_id.credit_note_authorized,obj.clave_acceso)
                tree.write(autorizada,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml")                          
                                     
                if doc_xml is None:
                    msg = ' '.join(m)
                    raise m        
                    
                """Se obtiene id de factura y se llama metodo actualizacion de datos"""
                idfac=obj.id
                
                if obj.company_id.is_offline:
                    self.datos_autorizacion_offline(cr, uid, auth, idfac,obj.clave_acceso)
                else:
                    self.datos_autorizacion(cr, uid, auth, idfac)
                
                """envío del correo electrónico de nota de crédito al cliente"""
                #self.send_mail_refund(cr, uid, obj, access_key, context)
                
                    
    def datos_autorizacion_offline(self,cr, uid,auth,idfac,access_key):
        """metodo que actualiza datos de autorización en account_invoice"""
       
        cr.execute('UPDATE account_invoice SET ambiente=%s, numero_autorizacion_offline=%s , '\
                    'fecha_autorizacion=%s , estado_autorizacion=%s , autorizado_sri=%s '\
                    'WHERE id=%s ',
                    (auth.ambiente,access_key,auth.fechaAutorizacion,auth.estado,True,idfac))
        return True 
