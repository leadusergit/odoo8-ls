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

import utils

import glob
from lxml import etree #import añadido

from .xades.sri import SriService, DocumentXML
from .xades.xades import Xades
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

class AccountInvoice(osv.osv):
    """ para su generacion: modelo de datos centrado en account_invoice, tablas maestras product_product, res_parner, account_jurnal
        account_autorisation, res_company. Tablas hijas, account_invoice_line, account_invoice_tax; tablas hijas de account_invoice_line
        account_invoice_line_tax (many2many con account_tax), dependencia en transitiva de acount_tax_code.
        Logica: Desde la vista el boton action_generate_einvoice crea el acces key mas tipo de emision, 
        crea el xml segun SRI factura, NC para ello accesa al modelo explicado; valida el xml, firma el xml, guarda en disco, verifica comunicacion 
     """
    _inherit = 'account.invoice'
    __logger = logging.getLogger(_inherit)
    
    _columns = {
        'clave_acceso': fields.char('Clave de Acceso', size=49, readonly=True),
        'numero_autorizacion': fields.char('Número de Autorización', size=37, readonly=True),
        'estado_autorizacion': fields.char('Estado de Autorización', size=64, readonly=True),
        'fecha_autorizacion':  fields.datetime('Fecha Autorización', readonly=True),
        'ambiente': fields.char('Ambiente', size=64, readonly=True),
        'autorizado_sri': fields.boolean('¿Autorizado SRI?', readonly=True),
        'security_code': fields.char('Código de Seguridad', size=8),
	    'emission_code': fields.char('Tipo de Emisión', size=1),   
        'fee_view': fields.related('company_id','fee_view',type='boolean', size=5, string='Doc Electrónico',readonly=True), 
        }
    _defaults = {

    }    
    
    
    def _get_tax_element(self, invoice, access_key, emission_code):
        """ Se obtienen los elementos del tag InfoTributaria para Factura y NC"""
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
        etree.SubElement(infoTributaria, 'razonSocial').text = company.name
        #print"razonSocial-einvoice=%s"%company.name
        etree.SubElement(infoTributaria, 'nombreComercial').text = company.name
        #print"nombreComercial-einvoice=%s"%company.name
        etree.SubElement(infoTributaria, 'ruc').text = company.partner_id.ident_num
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
        etree.SubElement(infoTributaria, 'dirMatriz').text = company.street
        #print"dirMatriz-einvoicelin129=%s"%company.street
        
        ##print" infoTributaria=%s"% infoTributaria
        s = etree.tostring(infoTributaria, pretty_print=True)
        print s
        return infoTributaria

    def _get_invoice_element(self, invoice):
        
        """infoFactura: Elementos cabecera de la factura"""
        
        company = invoice.company_id
        partner = invoice.partner_id

        infoFactura = etree.Element('infoFactura')
        etree.SubElement(infoFactura, 'fechaEmision').text = time.strftime('%d/%m/%Y',time.strptime(invoice.date_invoice, '%Y-%m-%d'))
        print"fechaEmision-einvoice=%s"%time.strftime('%d/%m/%Y',time.strptime(invoice.date_invoice, '%Y-%m-%d'))
        etree.SubElement(infoFactura, 'dirEstablecimiento').text = company.street2
        print"dirEstablecimiento-einvoice=%s"%company.street2
        if company.special_tax_contributor_number:
            etree.SubElement(infoFactura, 'contribuyenteEspecial').text = company.special_tax_contributor_number #company.company_registry
            print"contribuyenteEspecial-einvoice=%s"%company.company_registry
        
        etree.SubElement(infoFactura, 'obligadoContabilidad').text = 'SI'
        etree.SubElement(infoFactura, 'tipoIdentificacionComprador').text =tipoIdentificacion[partner.ident_type] #"04"#
        print"tipoIdentificacionComprador-einvoice=%s"%tipoIdentificacion[partner.ident_type]
        etree.SubElement(infoFactura, 'razonSocialComprador').text = partner.name
        print"razonSocialComprador-einvoice=%s"%partner.name
        etree.SubElement(infoFactura, 'identificacionComprador').text = partner.ident_num
        print"identificacionComprador-einvoice=%s"%partner.ident_num
        etree.SubElement(infoFactura, 'totalSinImpuestos').text = '%.2f' % (invoice.amount_untaxed)
        print"totalSinImpuestos-einvoicelin156=%s"%'%.2f' % (invoice.amount_untaxed)
        etree.SubElement(infoFactura, 'totalDescuento').text = '%.2f' % (invoice.amount_discount)#'0.00'#'%.2f' % (invoice.discount_total)
        #totalConImpuestos. Este campo es la suma de impuestos
        #totalConImpuestos
        totalConImpuestos = etree.Element('totalConImpuestos')
        print"totalConImpuestos=%s"%totalConImpuestos
		# desde modelo padre toma referencia one2many: tax_line, para referir a account_invoice_tax usando invoice_id
        for tax in invoice.tax_line:

            if tax.tax_group in ['vat', 'vat0', 'ice', 'other']:
                totalImpuesto = etree.Element('totalImpuesto')
                etree.SubElement(totalImpuesto, 'codigo').text = codigoImpuesto[tax.tax_group]
                print"codigo-einvoicelin166=%s"%codigoImpuesto[tax.tax_group]
                etree.SubElement(totalImpuesto, 'codigoPorcentaje').text = tarifaImpuesto[tax.tax_group]
                print"codigoPorcentaje-einvoice=%s"%tarifaImpuesto[tax.tax_group]
                etree.SubElement(totalImpuesto, 'baseImponible').text = '{:.2f}'.format(tax.base_amount)
                print"baseImponible-einvoice=%s"%'{:.2f}'.format(tax.base_amount)
                etree.SubElement(totalImpuesto, 'valor').text = '{:.2f}'.format(tax.tax_amount)
                print"valor-einvoice=%s"%'{:.2f}'.format(tax.tax_amount)
                totalConImpuestos.append(totalImpuesto)
                
        infoFactura.append(totalConImpuestos)
        
        etree.SubElement(infoFactura, 'propina').text = '0.00'
        etree.SubElement(infoFactura, 'importeTotal').text = '{:.2f}'.format(invoice.amount_pay)
        etree.SubElement(infoFactura, 'moneda').text = 'DOLAR'
        
       # print"infoFactura=%s"%infoFactura
        #s1 = etree.tostring(infoFactura, pretty_print=True)
        #print s1
            
        return infoFactura

    def _get_refund_element(self, refund, invoice):
        """Nota de Crédito: Registra valores a favor de los clientes, generalmente se conoce como correctivos a factura
		normalmente debe referenciar a una factura, su aplicacion a factura debe restar por el monto de NC al saldo de la factura
		esto hay que verificar en funcionamiento de usuario al momento de generar refund en una factura"""        
       
        print"refund=%s"%refund       
        company = refund.company_id
        partner = refund.partner_id
        
        infoNotaCredito = etree.Element('infoNotaCredito')
        etree.SubElement(infoNotaCredito, 'fechaEmision').text = time.strftime('%d/%m/%Y',time.strptime(refund.date_invoice, '%Y-%m-%d'))
        print"fechaEmision=%s"%time.strftime('%d/%m/%Y',time.strptime(refund.date_invoice, '%Y-%m-%d'))
        etree.SubElement(infoNotaCredito, 'dirEstablecimiento').text = company.street2
        print"dirEstablecimiento=%s"%company.street2
        etree.SubElement(infoNotaCredito, 'tipoIdentificacionComprador').text = tipoIdentificacion[partner.ident_type]#'04'#
        etree.SubElement(infoNotaCredito, 'razonSocialComprador').text = partner.name
        print"razonSocialComprador=%s"%partner.name
        etree.SubElement(infoNotaCredito, 'identificacionComprador').text = partner.ident_num
        print"identificacionComprador=%s"%partner.ident_num
        etree.SubElement(infoNotaCredito, 'contribuyenteEspecial').text = company.special_tax_contributor_number 
        print"contribuyenteEspecial=%s"%company.special_tax_contributor_number
        etree.SubElement(infoNotaCredito, 'obligadoContabilidad').text = 'SI'
        etree.SubElement(infoNotaCredito, 'codDocModificado').text = '01'
       
        if refund.name:
         """Se crea el secuencial del documento modificado con guiones intermedios"""
         numdocmod=refund.number[:3] + '-' + refund.number[3:6] +'-'+ refund.origin[9:18]
         print"ndm=%s"%numdocmod       
         etree.SubElement(infoNotaCredito, 'numDocModificado').text = numdocmod
         """Se toma la fecha de emisión del documento modificado  """
         etree.SubElement(infoNotaCredito, 'fechaEmisionDocSustento').text = time.strftime('%d/%m/%Y',time.strptime(refund.date_invoice, '%Y-%m-%d'))        
         print"fechaEmisionDocSustento=%s"%time.strftime('%d/%m/%Y',time.strptime(refund.date_invoice, '%Y-%m-%d'))
         
         etree.SubElement(infoNotaCredito, 'totalSinImpuestos').text = '%.2f' % (abs(refund.amount_untaxed))
         etree.SubElement(infoNotaCredito, 'valorModificacion').text = '%.2f' % (abs(refund.amount_pay))
         etree.SubElement(infoNotaCredito, 'moneda').text = 'DOLAR'
     
        """Si NC no depende de factura""" 
        """else:           
         numdocmod=refund.number[:3] + '-' + refund.number[3:6] +'-'+ refund.number[6:15]
         etree.SubElement(infoNotaCredito, 'numDocModificado').text =numdocmod
         etree.SubElement(infoNotaCredito, 'fechaEmisionDocSustento').text = time.strftime('%d/%m/%Y',time.strptime(refund.date_invoice, '%Y-%m-%d'))
         #time.strftime('%d/%m/%Y',time.strptime(refund.reference_invoice_date, '%Y-%m-%d'))
         etree.SubElement(infoNotaCredito, 'totalSinImpuestos').text = '%.2f' % (abs(refund.amount_untaxed))
         etree.SubElement(infoNotaCredito, 'valorModificacion').text = '%.2f' % (abs(refund.amount_pay))
         etree.SubElement(infoNotaCredito, 'moneda').text = 'DOLAR'"""
        
        totalConImpuestos = etree.Element('totalConImpuestos')
        for tax in refund.tax_line:

            if tax.tax_group in ['vat', 'vat0', 'ice', 'other']:
                print"tax.tax_group=%s"%tax.tax_group 
                totalImpuesto = etree.Element('totalImpuesto')
                etree.SubElement(totalImpuesto, 'codigo').text = codigoImpuesto[tax.tax_group]
                print"codigo=%s"%codigoImpuesto[tax.tax_group]
                etree.SubElement(totalImpuesto, 'codigoPorcentaje').text = tarifaImpuesto[tax.tax_group]
                print"codigoPorcentaje=%s"%tarifaImpuesto[tax.tax_group]
                etree.SubElement(totalImpuesto, 'baseImponible').text = '{:.2f}'.format(abs(tax.base_amount))
                print"baseImponible=%s"%'{:.2f}'.format(abs(tax.base_amount))
                etree.SubElement(totalImpuesto, 'valor').text = '{:.2f}'.format(abs(tax.tax_amount))
                print"valor=%s"%'{:.2f}'.format(abs(tax.tax_amount)) 
                totalConImpuestos.append(totalImpuesto)
                
        infoNotaCredito.append(totalConImpuestos)
        etree.SubElement(infoNotaCredito, 'motivo').text = refund.origin
        
        inc = etree.tostring(infoNotaCredito, pretty_print=True)
        print inc
        
        return infoNotaCredito
        
    def _get_detail_element(self, invoice):
        
        """Elementos Detalle de Factura, requiere accesar a las lineas de  detalle de la factura y segun
		   sea el servicio y/o producto debe accesar a los impuestos para llenar los datos sobre estos y sus codigos """          

        def fix_chars(code):
            if code:
                code.replace(u'%',' ').replace(u'º', ' ').replace(u'Ñ', 'N').replace(u'ñ','n')
                return code
            return '1'
            
        detalles = etree.Element('detalles')
		# itera sobre el detalle account_invoice_line; usa invoice_line del modelo padre para referenciarlo
        for line in invoice.invoice_line:
            detalle = etree.Element('detalle')
            etree.SubElement(detalle, 'codigoPrincipal').text = fix_chars(line.product_id.default_code)
            print"codigoPrincipal-einvoicelin236=%s"%fix_chars(line.product_id.default_code)
            etree.SubElement(detalle, 'descripcion').text = fix_chars(line.product_id.name)
            print"descripcion-einvoice=%s"%fix_chars(line.product_id.name)
            etree.SubElement(detalle, 'cantidad').text = '%.6f' % (line.quantity)
            print"cantidad-einvoice=%s"%'%.6f' % (line.quantity)
            etree.SubElement(detalle, 'precioUnitario').text = '%.6f' % (line.price_unit)
            print"precioUnitario-einvoice=%s"%'%.6f' % (line.price_unit)
            etree.SubElement(detalle, 'descuento').text ='%.2f' % (line.discount)#0.00'#'
            etree.SubElement(detalle, 'precioTotalSinImpuesto').text = '%.2f' % (line.price_subtotal)
            print"precioTotalSinImpuesto-einvoice=%s"%'%.2f' % (line.price_subtotal)
            impuestos = etree.Element('impuestos')
			#desde account_invoice_line va contra account_invoice_line_tax (hija) que tambien lo es de account_tax, 
			#lo referencia con invoice_line_tax_id del modelo (tipico de many2many) entre account_invoice_line y account_tax
			#cualquier campo que se requiera desde la instancia account_invoice_line al account_tax esta al alcance del primero
            for tax_line in line.invoice_line_tax_id:
                if tax_line.tax_group in ['vat', 'vat0', 'ice', 'other']:
                    impuesto = etree.Element('impuesto')
                    etree.SubElement(impuesto, 'codigo').text = codigoImpuesto[tax_line.tax_group]
                    print"codigo-einvoicelin250=%s"%codigoImpuesto[tax_line.tax_group]
                    etree.SubElement(impuesto, 'codigoPorcentaje').text = tarifaImpuesto[tax_line.tax_group]
                    print"codigoPorcentaje-einvoice=%s"%tarifaImpuesto[tax_line.tax_group]                       
                    etree.SubElement(impuesto, 'tarifa').text = tax_line.percent_comp
                    print"tarifa-einvoice=%s"%tax_line.percent_comp#porcentaje de impuesto guardar sin %
                    etree.SubElement(impuesto, 'baseImponible').text = '%.2f' % (line.price_subtotal)
                    print"baseImponibl-einvoice=%s"%'%.2f' % (line.price_subtotal)
                    etree.SubElement(impuesto, 'valor').text = '%.2f' % (line.price_subtotal * tax_line.amount)
                    print"valor-einvoice=%s"%'%.2f' % (line.price_subtotal * tax_line.amount)
                    impuestos.append(impuesto)
            detalle.append(impuestos)
            detalles.append(detalle)
            
            #print"detalles=%s"%detalles
            #s2 = etree.tostring(detalles, pretty_print=True)
            #print s2
        return detalles

    def _get_detail_element_refund(self, invoice):
        
        """ Detalle de Nota de Crèdito. Todas las referencias a las tablas son las mismas que se documento en facturas"""
        
        detalles = etree.Element('detalles')
        for line in invoice.invoice_line:
            detalle = etree.Element('detalle')
            etree.SubElement(detalle, 'codigoInterno').text = line.product_id.default_code.replace(u'%',' ').replace(u'º', ' ').replace(u'Ñ', 'N').replace(u'ñ','n')
            print"codigoInterno=%s"%line.product_id.default_code.replace(u'%',' ').replace(u'º', ' ').replace(u'Ñ', 'N').replace(u'ñ','n')
            
            #if line.product_id.manufacturer_pref:
            #    etree.SubElement(detalle, 'codigoAdicional').text = line.product_id.manufacturer_pref.replace(u'%',' ').replace(u'º', ' ').replace(u'Ñ', 'N').replace(u'ñ','n')
            etree.SubElement(detalle, 'descripcion').text = line.product_id.name.replace(u'%',' ').replace(u'º', ' ').replace(u'Ñ', 'N').replace(u'ñ','n')
            etree.SubElement(detalle, 'cantidad').text = '%.6f' % (line.quantity)
            etree.SubElement(detalle, 'precioUnitario').text = '%.6f' % (line.price_unit)
            etree.SubElement(detalle, 'descuento').text = '%.2f' % (line.discount)
            etree.SubElement(detalle, 'precioTotalSinImpuesto').text = '%.2f' % (line.price_subtotal)
            impuestos = etree.Element('impuestos')
            for tax_line in line.invoice_line_tax_id:
                if tax_line.tax_group in ['vat', 'vat0', 'ice', 'other']:
                    impuesto = etree.Element('impuesto')
                    etree.SubElement(impuesto, 'codigo').text = codigoImpuesto[tax_line.tax_group]
                    etree.SubElement(impuesto, 'codigoPorcentaje').text = tarifaImpuesto[tax_line.tax_group]
                    etree.SubElement(impuesto, 'tarifa').text = '%.2f' % (tax_line.amount * 100)
                    etree.SubElement(impuesto, 'baseImponible').text = '%.2f' % (line.price_subtotal)
                    etree.SubElement(impuesto, 'valor').text = '%.2f' % (line.price_subtotal * tax_line.amount)#'%.2f' % (line.amount_tax)
                    impuestos.append(impuesto)
            detalle.append(impuestos)
            detalles.append(detalle)
            
        dnc= etree.tostring(detalles, pretty_print=True)
        print dnc    
        
        return detalles

    def _generate_xml_invoice(self, invoice, access_key, emission_code):
        
        """Genera Factura"""
        
        factura = etree.Element('factura')
        factura.set("id", "comprobante")
        factura.set("version", "1.1.0")
        
        # generar infoTributaria
        infoTributaria = self._get_tax_element(invoice, access_key, emission_code)
        factura.append(infoTributaria)
        
        # generar infoFactura
        infoFactura = self._get_invoice_element(invoice)
        factura.append(infoFactura)
        
        #generar detalles
        detalles = self._get_detail_element(invoice)
        
        factura.append(detalles)
        

        #fac = etree.tostring(factura, pretty_print=True)
        #print fac
        return factura
    
    def _generate_xml_refund(self, refund, invoice, access_key, emission_code):
        
        """  Genera Nota de Credito   """
       
        print"refund=%s"%refund
        print"invoice=%s"%invoice
        print"access_key=%s"%access_key
        print"emission_code=%s"%emission_code
        
        notaCredito = etree.Element('notaCredito')
        notaCredito.set("id", "comprobante")
        notaCredito.set("version", "1.1.0")
        
        """ generar infoTributaria"""
        infoTributaria = self._get_tax_element(refund, access_key, emission_code)
        notaCredito.append(infoTributaria)
        
        
        """generar infoNotaCredito"""
        infoNotaCredito = self._get_refund_element(refund, invoice)
        notaCredito.append(infoNotaCredito)
        
        """generar detalles"""
        detalles = self._get_detail_element_refund(refund)
        notaCredito.append(detalles)
        
        #notaC = etree.tostring(notaCredito, pretty_print=True)
        #print notaC
        
        return notaCredito
    
    def get_access_key(self, cr, uid, invoice):
        
        """Relacion account_invoice ----account_authorisation """
        auth= invoice.auth_ret_id
        print "auth=%s"%auth
        
        """Relacion account_invoice --account_journal--account_authorisation """
        auth_aux = invoice.journal_id.auth_id 
        print "auth_aux=%s"%auth_aux
        
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
        
        ruc = invoice.company_id.partner_id.ident_num
        print"ruc=%s"%ruc
        tipo_ambiente=invoice.company_id.ambiente_code
        print"tipo_ambiente=%s"%tipo_ambiente
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
    
    
    def check_before_sent(self, cr, uid, obj):
        
        print "obj.number-einvoicelin325=%s"%obj.number 
        sql = "select autorizado_sri, number from account_invoice where state='open' and number <'%s' order by number desc limit 1" % obj.number
        cr.execute(sql)
        """estado="open"
        cr.execute('select autorizado_sri, number from account_invoice '\
                   'where state= %s and number < %s order by number desc limit 1',
                   (estado,obj.number)) """         
        res = cr.fetchone()
        return (res, {}) and True or False
       #return res[0] and True or False   
       
        
    def action_generate_einvoice(self, cr, uid, ids, context=None):
        """ desde el boton "Factura Electrónica" dentro de la vista account.invoice_form del archivo einvoice_view.xml
		este metodo es disparado. Solo es posible ejecutarse siempre que se haya registrado sin problemas una factura o NC con
		los impuestos bien configurados y establecidos en cada producto que paticipen en la factura.
		Las reglas de aplicacion sobre impuestos esta considerando desde el 2016 para ECUADOR
        """
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
                          
                """validación del xml"""
                inv_xml = DocumentXML(factura, 'out_invoice')
                inv_xml.validate_xml()  
                
                """Generar Factura impresa en el path dado con la clave de acceso como nombre"""
                
                ##imprimir factura en pantalla
                ##fac = etree.tostring(factura, pretty_print=True)
                ##print "fac=%s"%fac   # tree recupera el xml formateado y parseado
                tree = etree.ElementTree(factura)
                facxml = '%s%s.xml' %(obj.company_id.bills_generated,access_key)
                tree.write(facxml,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml") 
                
                # firma de XML, now what ??
                # TODO: zip, checksum, save, send_mail
                """parametros para generar factura firmada"""
                xades = Xades()
                ##pathxml='%s%s.xml' %('/home/leaduser/fee/facturas/facturas/',access_key)
                pathxml='%s%s.xml' %(obj.company_id.bills_generated,access_key)
                file_pk12 = obj.company_id.electronic_signature
                password = obj.company_id.password_electronic_signature    
                ##pathout='/home/leaduser/fee/facturas/firmadas/'
                pathout=obj.company_id.bills_signed
                nameout='%s.xml'%access_key
                
                """generar factura firmada"""      
               
                signed_document = xades.apply_digital_signature(pathxml,file_pk12, password,pathout,nameout)
                            
              
                """enviar comprobante electrónico"""                             
                #fac=open('%s%s.xml' %('/home/leaduser/fee/facturas/firmadas/',access_key))
                fac=open('%s%s.xml' %(obj.company_id.bills_signed,access_key))
                facr=fac.read()
                #print "leer factura =%s"%facr               
                inv_xml.send_receipt(facr,access_key)
                time.sleep(WAIT_FOR_RECEIPT)

                """solicitud de autorización del comprobante electrónico"""
                doc_xml, m, auth = inv_xml.request_authorization(access_key)
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
                
                """validación del xml de la NC"""
                inv_xml = DocumentXML(notacredito, 'out_refund')
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
                inv_xml.send_receipt(ncr,access_key)
                time.sleep(WAIT_FOR_RECEIPT)

                """solicitud de autorización del comprobante electrónico"""
                doc_xml, m, auth = inv_xml.request_authorization(access_key)
                
                """Imprimir nota de crèdito autorizada y guardar en carpeta"""
                tree = etree.ElementTree(doc_xml)
                autorizada ='%s%s.xml'%(obj.company_id.credit_note_authorized,access_key)
                tree.write(autorizada,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml")                          
                                     
                if doc_xml is None:
                    msg = ' '.join(m)
                    raise m            
                """Se obtiene id de factura y se llama metodo actualizacion de datos"""
                idfac=obj.id
                self.datos_autorizacion(cr, uid, auth, idfac)
                
                """envío del correo electrónico de nota de crédito al cliente"""
                #self.send_mail_refund(cr, uid, obj, access_key, context)
                
                
    
    def datos_autorizacion(self,cr, uid,auth,idfac):
        """metodo que actualiza datos de autorización en account_invoice"""
       
        cr.execute('UPDATE account_invoice SET ambiente=%s, numero_autorizacion=%s , '\
                    'fecha_autorizacion=%s , estado_autorizacion=%s , autorizado_sri=%s '\
                    'WHERE id=%s ',
                    (auth.ambiente,auth.numeroAutorizacion,auth.fechaAutorizacion,auth.estado,True,idfac))
        return True
    
    def action_einvoice_send_mail(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids)[0]
        #name = '%s%s.xml' %('/home/leaduser/fee/facturas/autorizadas/', obj.clave_acceso)
        name = '%s%s.xml' %(obj.company_id.bills_authorized, obj.clave_acceso)
        cadena = open(name, mode='rb').read()
        attachment_id = self.pool.get('ir.attachment').create(cr, uid, 
            {
                'name': '%s.xml' % (obj.clave_acceso),
                'datas': base64.b64encode(cadena),
                'datas_fname':  '%s.xml' % (obj.clave_acceso),
                'res_model': self._name,
                'res_id': obj.id,
                'type': 'binary'
            }, context=context)
                            
        email_template_obj = self.pool.get('email.template')
        res_id = self.pool.get('mail.compose.message')
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'email_template_edi_invoice')[1]
        email_template_obj.write(cr, uid, template_id, {'attachment_ids': [(6, 0, [attachment_id])]})  
        #email_template_obj.send_mail(cr, uid, template_id, obj.id, True)
        
        ctx = dict(
            default_use_template=bool(template_id),
            default_template_id=template_id,
            mark_invoice_as_sent=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'target': 'new',
            'context': ctx,
        }
        
       
    
        """def send_mail_invoice(self, cr, uid, obj, xml_element, auth, context=None):
        self.write(cr, uid, [obj.id], {
            'numero_autorizacion': auth.numeroAutorizacion,
            'estado_autorizacion': auth.estado,
            'ambiente': auth.ambiente,
            'fecha_autorizacion': auth.fechaAutorizacion.strftime("%d/%m/%Y %H:%M:%S"),
            'autorizado_sri': True
        })
        einvoice_xml = etree.tostring(xml_element, pretty_print=True, encoding='iso-8859-1')
        buf = StringIO.StringIO()
        buf.write(einvoice_xml)
        einvoice = base64.encodestring(buf.getvalue())
        buf.close()
        attachment_id = self.pool.get('ir.attachment').create(cr, uid, 
            {
                'name': '{0}.xml'.format(obj.clave_acceso),
                'datas': einvoice,
                'datas_fname':  '{0}.xml'.format(obj.clave_acceso),
                'res_model': self._name,
                'res_id': obj.id,
                'type': 'binary'
            }, context=context)
                            
        email_template_obj = self.pool.get('email.template')
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'l10n_ec_einvoice', 'email_template_einvoice')[1]
#        email_template_obj.write(cr, uid, template_id, {'attachment_ids': [(6, 0, [attachment_id])]})
        email_template_obj.send_mail(cr, uid, template_id, obj.id, True)
        
        return True
    
    def send_mail_refund(self, cr, uid, obj, access_key, context=None):
        name = '%s%s.xml' %('/opt/facturas/', access_key)
        cadena = open(name, mode='rb').read()
        attachment_id = self.pool.get('ir.attachment').create(cr, uid,
            {
                'name': '%s.xml' % (access_key),
                'datas': base64.b64encode(cadena),
                'datas_fname':  '%s.xml' % (access_key),
                'res_model': self._name,
                'res_id': obj.id,
                'type': 'binary'
            }, context=context)

        email_template_obj = self.pool.get('email.template')
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'email_template_edi_refund')[1]
        email_template_obj.write(cr, uid, template_id, {'attachment_ids': [(6, 0, [attachment_id])]})
        email_template_obj.send_mail(cr, uid, template_id, obj.id, True)

        return True"""
        
   
    def invoice_print(self, cr, uid, ids, context=None):

        '''
        Redefinicion para imprimir RIDE
        '''
        res = super(AccountInvoice, self).invoice_print(cr, uid, ids, context)
        res['report_name'] = 'account_print_invoice'
        return res
