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
from openerp.addons.l10n_ec_einvoice.xades.sri import SriService, DocumentXML
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
    #'venta_consumidor_final' : '07',
    #'identificacion_exterior' : '08',
    #'placa' : '09',
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


class Company(osv.osv):
    _inherit = 'res.company'
    
    _columns = {
        'factura_parent': fields.boolean('Facturación Empresa Principal', help="Al marcar este campo las facturas seran generadas con datos de la empresa pprincipal"),
        'parent_name':fields.char('Nombre Empresa Principal'),
        'parent_street':fields.char('Dirección Empresa Principal'),
        'parent_num':fields.char('Identificación Empresa Principal'),
    }
    

class account_invoice(osv.osv):
    _inherit ='account.invoice'
    
  
  
    def _get_tax_element(self, invoice, access_key, emission_code):
        """ Se obtienen los elementos del tag InfoTributaria para Factura y NC"""
        
        if invoice.company_id.parent_id and invoice.company_id.factura_parent:
            nombre= invoice.company_id.parent_name
            num=invoice.company_id.parent_num
            direccion=invoice.company_id.parent_street
        else:
            nombre= invoice.company_id.name
            num=invoice.company_id.partner_id.ident_num
            direccion=invoice.company_id.street
            
        
        company = invoice.company_id        
        """Relacion account_invoice ----account_authorisation """
        auth= invoice.auth_ret_id
        print "auth=%s"%auth
        
        """Relacion account_invoice --account_journal--account_authorisation """
        auth_aux = invoice.journal_id.auth_id 
        print "auth_aux=%s"%auth_aux
        
        """Tabla 7 SRI: Se toma el código según el tipo de doc Factura:01, Nota de Crèdito:04"""
        type=invoice.type
        if type =='out_invoice':
         tipodoc= '01'
        if type=='out_refund':
         tipodoc= '04'
         
        
        infoTributaria = etree.Element('infoTributaria')        
        etree.SubElement(infoTributaria, 'ambiente').text = company.ambiente_code
        #print"ambiente-einvoicelin107=%s"%SriService.get_active_env()
        etree.SubElement(infoTributaria, 'tipoEmision').text = emission_code
        #print"tipoEmision-einvoice=%s"%emission_code
        etree.SubElement(infoTributaria, 'razonSocial').text = nombre
        etree.SubElement(infoTributaria, 'nombreComercial').text = nombre
        #print"nombreComercial-einvoice=%s"%company.name
        etree.SubElement(infoTributaria, 'ruc').text = num
        #print"ruc-einvoice=%s"%company.partner_id.ced_ruc
        etree.SubElement(infoTributaria, 'claveAcceso').text = access_key
        #print"claveAcceso-einvoice=%s"%access_key
        etree.SubElement(infoTributaria, 'codDoc').text = tipodoc #tipoDocumento[auth.type_id.code]
        print"tipodoc=%s"%tipodoc
        etree.SubElement(infoTributaria, 'estab').text = auth.serie_entidad or auth_aux.serie_entidad
        print"estab-einvoice=%s"%auth.serie_entidad
        etree.SubElement(infoTributaria, 'ptoEmi').text =auth.serie_emision or auth_aux.serie_emision
        print"ptoEmi-einvoice=%s"%auth.serie_emision
        etree.SubElement(infoTributaria, 'secuencial').text = invoice.number[6:15]
        print"secuencial-einvoice=%s"%invoice.number[6:15]
        etree.SubElement(infoTributaria, 'dirMatriz').text = direccion
        #print"dirMatriz-einvoicelin129=%s"%company.street
        ##print" infoTributaria=%s"% infoTributaria
        s = etree.tostring(infoTributaria, pretty_print=True)
        print s
        return infoTributaria
    
    
    def get_access_key(self, cr, uid, invoice):
        
        """Relacion account_invoice ----account_authorisation """
        auth= invoice.auth_ret_id
        print "authk=%s"%auth
        
        """Relacion account_invoice --account_journal--account_authorisation """
        auth_aux = invoice.journal_id.auth_id 
        print "auth_auxk=%s"%auth_aux
        
        ld = invoice.date_invoice.split('-')
        ld.reverse()
        fecha = ''.join(ld)
        #modificado codigo de doc en tabla account_ats_doc
        #var=auth.type_id.code
        """Se toma el código del tipo de comprobante Factura:01, NC:04"""
        #tcomp = tipoDocumento[auth.type_id.code]
        if invoice.type=='out_invoice':
         tcomp= '01'
        if invoice.type=='out_refund':
         tcomp= '04'     
        print"tcomp=%s"%tcomp
        
        if invoice.company_id.parent_id and invoice.company_id.factura_parent:
            ruc = invoice.company_id.parent_num
            tipo_ambiente=invoice.company_id.ambiente_code
        else:
            ruc = invoice.company_id.partner_id.ident_num
            tipo_ambiente=invoice.company_id.ambiente_code
        
        
       
        serie = '{0}{1}'.format(auth.serie_entidad or auth_aux.serie_entidad , auth.serie_emision or auth_aux.serie_emision)
        numero = invoice.number[6:15]
        print"numero.lin316-einvoice=%s"%numero
        #TODO: security code
        codigo_numero = '11111126'#'12345678'
        tipo_emision = invoice.company_id.emission_code
        print"tipo_emision =%s"%tipo_emision 
        access_key = (
            [fecha, tcomp, ruc, tipo_ambiente],
            [serie, numero, codigo_numero, tipo_emision]
            )
        return access_key