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
from openerp.exceptions import ValidationError

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


class account_invoice(osv.osv):
    _inherit ='account.invoice'
    
  
    def _get_invoice_element(self, invoice):
        
        """infoFactura: Elementos cabecera de la factura"""
        print"einvoice_add module"
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
        
        if partner.ident_type and partner.ident_num:
            etree.SubElement(infoFactura, 'tipoIdentificacionComprador').text =tipoIdentificacion[partner.ident_type] #04#
            print"tipoIdentificacionComprador-einvoice=%s"%tipoIdentificacion[partner.ident_type]            
            etree.SubElement(infoFactura, 'razonSocialComprador').text = partner.name
            print"razonSocialComprador-einvoice=%s"%partner.name
            etree.SubElement(infoFactura, 'identificacionComprador').text = partner.ident_num
            print"identificacionComprador-einvoice=%s"%partner.ident_num
            
        else:
            raise ValidationError(u'Verificar configuración de %s,datos de ficha cliente incompletos'%partner.name)

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
                
                """Codigo de porcentaje 3 cuando se aplica iva =14%"""
                print"invoice.porcentaje_iva_aplicado=%s"%invoice.porcentaje_iva_aplicado
                if invoice.porcentaje_iva_aplicado in ['iva14']:
                    etree.SubElement(totalImpuesto, 'codigoPorcentaje').text = '3'
                else:
                    etree.SubElement(totalImpuesto, 'codigoPorcentaje').text = tarifaImpuesto[tax.tax_group]
                    print"codigoPorcentaje-einvoice12=%s"%tarifaImpuesto[tax.tax_group]
                
                etree.SubElement(totalImpuesto, 'baseImponible').text = '{:.2f}'.format(tax.base_amount)
                print"baseImponible-einvoice=%s"%'{:.2f}'.format(tax.base_amount)
                etree.SubElement(totalImpuesto, 'valor').text = '{:.2f}'.format(tax.tax_amount)
                print"valor-einvoice=%s"%'{:.2f}'.format(tax.tax_amount)
                totalConImpuestos.append(totalImpuesto)
                
        infoFactura.append(totalConImpuestos)
        
        etree.SubElement(infoFactura, 'propina').text = '0.00'
        etree.SubElement(infoFactura, 'importeTotal').text = '{:.2f}'.format(invoice.amount_pay)
        etree.SubElement(infoFactura, 'moneda').text = 'DOLAR'
        
        pagos = etree.Element('pagos')
        pago = etree.Element('pago')
        
        if invoice.payment_type.code:
            etree.SubElement(pago, 'formaPago').text = invoice.payment_type.code
        else:
            etree.SubElement(pago, 'formaPago').text = '20'
            
        etree.SubElement(pago, 'total').text = '{:.2f}'.format(invoice.amount_pay)
        etree.SubElement(pago, 'plazo').text ='30'
        etree.SubElement(pago, 'unidadTiempo').text ='dias'
        pagos.append(pago)
        infoFactura.append(pagos)
        
       # print"infoFactura=%s"%infoFactura
        #s1 = etree.tostring(infoFactura, pretty_print=True)
        #print s1
            
        return infoFactura


    def _get_refund_element(self, refund, invoice):
        """Nota de Crédito: Registra valores a favor de los clientes, generalmente se conoce como correctivos a factura
        normalmente debe referenciar a una factura, su aplicacion a factura debe restar por el monto de NC al saldo de la factura
        esto hay que verificar en funcionamiento de usuario al momento de generar refund en una factura"""        
       
       # print"refund=%s"%refund       
        company = refund.company_id
        partner = refund.partner_id
        
        infoNotaCredito = etree.Element('infoNotaCredito')
        etree.SubElement(infoNotaCredito, 'fechaEmision').text = time.strftime('%d/%m/%Y',time.strptime(refund.date_invoice, '%Y-%m-%d'))
        #print"fechaEmision=%s"%time.strftime('%d/%m/%Y',time.strptime(refund.date_invoice, '%Y-%m-%d'))
        etree.SubElement(infoNotaCredito, 'dirEstablecimiento').text = company.street2
        #print"dirEstablecimiento=%s"%company.street2
        etree.SubElement(infoNotaCredito, 'tipoIdentificacionComprador').text = tipoIdentificacion[partner.ident_type]#'04'#
        etree.SubElement(infoNotaCredito, 'razonSocialComprador').text = partner.name
        #print"razonSocialComprador=%s"%partner.name
        etree.SubElement(infoNotaCredito, 'identificacionComprador').text = partner.ident_num
        #print"identificacionComprador=%s"%partner.ident_num
        if company.special_tax_contributor_number:
            etree.SubElement(infoNotaCredito, 'contribuyenteEspecial').text = company.special_tax_contributor_number #company.company_registry
            #print"contribuyenteEspecial=%s"%company.special_tax_contributor_number
        etree.SubElement(infoNotaCredito, 'obligadoContabilidad').text = 'SI'
        etree.SubElement(infoNotaCredito, 'codDocModificado').text = '01'
       
        if refund.name:
         """Se crea el secuencial del documento modificado con guiones intermedios"""
         numdocmod=refund.number[:3] + '-' + refund.number[3:6] +'-'+ refund.origin[9:18]
         #print"ndm=%s"%numdocmod       
         etree.SubElement(infoNotaCredito, 'numDocModificado').text = refund.origin[:3] + '-' + refund.origin[3:6] +'-'+ refund.origin[6:15] #numdocmod
         """Se toma la fecha de emisión del documento modificado  """
         etree.SubElement(infoNotaCredito, 'fechaEmisionDocSustento').text = refund.origin[24:26] + '/' + refund.origin[21:23] +'/'+ refund.origin[16:20]      
         #print"fechaEmisionDocSustento=%s"%time.strftime('%d/%m/%Y',time.strptime(refund.date_invoice, '%Y-%m-%d'))        
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
                #print"tax.tax_group=%s"%tax.tax_group 
                totalImpuesto = etree.Element('totalImpuesto')
                etree.SubElement(totalImpuesto, 'codigo').text = codigoImpuesto[tax.tax_group]
                #print"codigo=%s"%codigoImpuesto[tax.tax_group]
                
                """Codigo de porcentaje 3 cuando se aplica iva =14%"""
                #print"invoice.porcentaje_iva_aplicado=%s"%invoice.porcentaje_iva_aplicado
                if invoice.porcentaje_iva_aplicado in ['iva14']:
                    etree.SubElement(totalImpuesto, 'codigoPorcentaje').text = '3'
                else:
                    etree.SubElement(totalImpuesto, 'codigoPorcentaje').text = tarifaImpuesto[tax.tax_group]
                    #print"codigoPorcentaje12=%s"%tarifaImpuesto[tax.tax_group]

                etree.SubElement(totalImpuesto, 'baseImponible').text = '{:.2f}'.format(abs(tax.base_amount))
                #print"baseImponible=%s"%'{:.2f}'.format(abs(tax.base_amount))
                etree.SubElement(totalImpuesto, 'valor').text = '{:.2f}'.format(abs(tax.tax_amount))
                #print"valor=%s"%'{:.2f}'.format(abs(tax.tax_amount)) 
                totalConImpuestos.append(totalImpuesto)
                
        infoNotaCredito.append(totalConImpuestos)
        etree.SubElement(infoNotaCredito, 'motivo').text = refund.name
        
        #inc = etree.tostring(infoNotaCredito, pretty_print=True)
        #print inc
        
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
                    
                    """Codigo de porcentaje 3 cuando se aplica iva =14%"""
                    print"invoice.porcentaje_iva_aplicado=%s"%invoice.porcentaje_iva_aplicado
                    if invoice.porcentaje_iva_aplicado in ['iva14']:
                        etree.SubElement(impuesto, 'codigoPorcentaje').text = '3'
                    else:
                        etree.SubElement(impuesto, 'codigoPorcentaje').text = tarifaImpuesto[tax_line.tax_group]
                        print"codigoPorcentaje-einvoice12=%s"%tarifaImpuesto[tax_line.tax_group]
                        
                    if invoice.porcentaje_iva_aplicado in ['iva12','auto'] and tarifaImpuesto[tax_line.tax_group]=='2':
                        etree.SubElement(impuesto, 'tarifa').text = '12'
                    else:
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
            #etree.SubElement(detalle, 'codigoInterno').text = line.product_id.default_code.replace(u'%',' ').replace(u'º', ' ').replace(u'Ñ', 'N').replace(u'ñ','n')
            #print"codigoInterno=%s"%line.product_id.default_code.replace(u'%',' ').replace(u'º', ' ').replace(u'Ñ', 'N').replace(u'ñ','n')
            
            #if line.product_id.manufacturer_pref:
            #    etree.SubElement(detalle, 'codigoAdicional').text = line.product_id.manufacturer_pref.replace(u'%',' ').replace(u'º', ' ').replace(u'Ñ', 'N').replace(u'ñ','n')
            if line.product_id.default_code:
                etree.SubElement(detalle, 'codigoAdicional').text = line.product_id.default_code.replace(u'%',' ').replace(u'º', ' ').replace(u'Ñ', 'N').replace(u'ñ','n')
            else:
                etree.SubElement(detalle, 'codigoAdicional').text = '999'

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
                    
                    """Codigo de porcentaje 3 cuando se aplica iva =14%"""
                    print"invoice.porcentaje_iva_aplicado=%s"%invoice.porcentaje_iva_aplicado
                    if invoice.porcentaje_iva_aplicado in ['iva14']:
                        etree.SubElement(impuesto, 'codigoPorcentaje').text = '3'
                    else:
                        etree.SubElement(impuesto, 'codigoPorcentaje').text = tarifaImpuesto[tax_line.tax_group]

                    if invoice.porcentaje_iva_aplicado in ['iva12','auto'] and tarifaImpuesto[tax_line.tax_group]=='2':
                        etree.SubElement(impuesto, 'tarifa').text = '12'
                    else:
                        etree.SubElement(impuesto, 'tarifa').text = tax_line.percent_comp
                        print"tarifa-einvoice=%s"%tax_line.percent_comp#porcentaje de impuesto guardar sin %
                    #etree.SubElement(impuesto, 'tarifa').text = '%.2f' % (tax_line.amount * 100)
                    
                    etree.SubElement(impuesto, 'baseImponible').text = '%.2f' % (line.price_subtotal)
                    etree.SubElement(impuesto, 'valor').text = '%.2f' % (line.price_subtotal * tax_line.amount)#'%.2f' % (line.amount_tax)
                    impuestos.append(impuesto)
            detalle.append(impuestos)
            detalles.append(detalle)
            
       #dnc= etree.tostring(detalles, pretty_print=True)
        #print dnc    
        
        return detalles

        
    
                


    
  
