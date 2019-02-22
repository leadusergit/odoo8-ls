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

import time
from datetime import datetime
import logging
import os
import base64
import subprocess
import StringIO

from lxml import etree

from openerp.osv import osv, fields
from openerp.tools import config
from openerp.tools.translate import _
from openerp.tools import ustr
from xml.dom.minidom import parse, parseString

import openerp.addons.decimal_precision as dp
import openerp.netsvc

try:
    from suds.client import Client
    from suds.transport import TransportError
except ImportError:
    raise ImportError('Instalar Libreria suds')

from .xades.sri import SriService, DocumentXML
#tabla 7 ficha tecnica SRI (tipo de Identificador)
tipoIdentificacion = {
    'r' : '04',
    'c' : '05',
    'p' : '06',
    #'venta_consumidor_final' : '07',
    #'identificacion_exterior' : '08',
    #'placa' : '09',
}
#tabla 17? ficha tecnica SRI
codigoImpuestoRetencion = {
    'ret_ir': '1',
    'ret_vat': '2',
    'ret_vat_srv': '2',
    'ice': '3',
}

class account_retention(osv.osv):
    
    _inherit = 'account.invoice.retention'
    __logger = logging.getLogger(_inherit)
    #48+1 posiciones (estructurado) para la clave de acceso (ultimo digito es generado por validacion para verficacion de unuicidad del numero)
	#37 posiciones (estructurado) para el numero que devuelve el SRI como autorizacion del documento
	#8 posiciones para generar un codigo de seguridad
    _columns = {
        'access_key': fields.char('Clave de Acceso', size=49, readonly=True, store=True),
        'authorization_number': fields.char('Número de Autorización', size=37, readonly=True),
        'authorization_date':  fields.datetime('Fecha y Hora de Autorización', readonly=True),
        'authorization_sri': fields.boolean('¿Autorizado SRI?', readonly=True),
        'security_code': fields.char('Código de Seguridad', size=8)
        }
        
    def get_code(self, cr, uid, retention):
        """
        TODO: revisar la generacion
        del codigo de 8 digitos, esta en ir.sequence?????
        """
        return self.pool.get('ir.sequence').get_id(cr, uid, 71)
    #genera el codigo de acceso de 49 posiciones
    def get_access_key(self, cr, uid, retention):

        """Relacion account_invoice/retention ----account_authorisation """
        auth= retention.autorization
        print "auth=%s"%auth
        
        """Relacion account_invoice/retention --account_journal--account_authorisation """
        auth_aux = retention.invoice_id.journal_id.auth_ret_id
        print "auth_aux=%s"%auth_aux
        
        #print"auth=%s"%auth #formatea la fecha almacenada en la retencion
        #ld = retention.fecha.split('-')
        ld = retention.invoice_id.date_invoice.split('-')

        ld.reverse()
        fecha = ''.join(ld)
        #
        ##tcomp = auth.type_id.code
        ##print"tcomp=%s"%tcomp     #quema el valor de la tabla 4 del SRI tipo de comprobante retencion = 07
        tcomp = '07'
        ruc = retention.company_id.partner_id.ident_num
        #print"ruc=%s"%ruc   #obtiene el pto emision y sucursal
        tipo_ambiente = retention.company_id.ambiente_code
        print"tipo_ambiente=%s"%tipo_ambiente
        serie = '{0}{1}'.format(auth.serie_entidad or auth_aux.serie_entidad, auth.serie_emision or auth_aux.serie_emision )
        #print"serie=%s"%serie
        numero = retention.name #retention.name[6:15] # FIX w/ number #en name tiene el numero de 9 posiciones
        #print"numero=%s"%numero  #de empresa obtiene el codigo de emision (tabla 2 SRI: Normal o por indisponibilidad)
        tipo_emision = retention.company_id.emission_code
        #print"tipo_emision=%s"%tipo_emision 
        #codigo_numero = self.get_code(cr, uid, retention) #este numero es una constante que figura fijo en todas las acces key
        codigo_numero = '11111126'
        #print"codigo_numero=%s"%codigo_numero  #al parecer lo que sigue estructura el codigo pero falta validarlo
        access_key = (
            [fecha, tcomp, ruc ,tipo_ambiente],
            [serie, numero, codigo_numero, tipo_emision]
            )
        return access_key
        
    def _get_tax_element(self, retention, access_key, emission_code):
        """ Es la cabecera definicion de impuestos y datos empresariales, asignacion de 
		    valores a las variables del esquema
        """
        company = retention.company_id
        
        """Relacion account_invoice/retention ----account_authorisation """
        auth= retention.autorization
        print "auth=%s"%auth
        
        """Relacion account_invoice/retention --account_journal--account_authorisation """
        auth_aux = retention.invoice_id.journal_id.auth_ret_id
        print "auth_aux=%s"%auth_aux
        
        
        infoTributaria = etree.Element('infoTributaria')
        etree.SubElement(infoTributaria, 'ambiente').text = company.ambiente_code 
        etree.SubElement(infoTributaria, 'tipoEmision').text = emission_code
        etree.SubElement(infoTributaria, 'razonSocial').text = company.name
        etree.SubElement(infoTributaria, 'nombreComercial').text = company.name
        etree.SubElement(infoTributaria, 'ruc').text = company.partner_id.ident_num
        etree.SubElement(infoTributaria, 'claveAcceso').text = access_key
        etree.SubElement(infoTributaria, 'codDoc').text = '07'#auth.type_id.code
        etree.SubElement(infoTributaria, 'estab').text = auth.serie_entidad or auth_aux.serie_entidad
        print"estab-eretention=%s"%auth.serie_entidad
        etree.SubElement(infoTributaria, 'ptoEmi').text = auth.serie_emision or auth_aux.serie_emision
        print"ptoEmi-eretention=%s"%auth.serie_emision
        etree.SubElement(infoTributaria, 'secuencial').text = retention.name #retention.name[6:15]
        etree.SubElement(infoTributaria, 'dirMatriz').text = company.street
        
        #ret = etree.tostring(infoTributaria, pretty_print=True)
        #print ret
        return infoTributaria
    
    def _get_retention_element(self, retention):
	""" Aca esta la definicion de la cabecera del dcto electronico (compbte retencion), asignacion de 
		    valores a las variables del esquema
        """
        company = retention.company_id
        partner = retention.invoice_id.partner_id
        infoCompRetencion = etree.Element('infoCompRetencion')
        etree.SubElement(infoCompRetencion, 'fechaEmision').text = time.strftime('%d/%m/%Y',time.strptime(retention.invoice_id.date_invoice, '%Y-%m-%d'))
        etree.SubElement(infoCompRetencion, 'dirEstablecimiento').text = company.street2
        
	if company.special_tax_contributor_number and company.partner_id.property_account_position.name=='CONTRIBUYENTE ESPECIAL':
	    print"company.partner_id.property_account_position.name=%s"%company.partner_id.property_account_position.name
            etree.SubElement(infoCompRetencion, 'contribuyenteEspecial').text = company.special_tax_contributor_number

        etree.SubElement(infoCompRetencion, 'obligadoContabilidad').text = 'SI'
        etree.SubElement(infoCompRetencion, 'tipoIdentificacionSujetoRetenido').text =tipoIdentificacion[partner.ident_type] # '04'        
        etree.SubElement(infoCompRetencion, 'razonSocialSujetoRetenido').text = partner.name
        etree.SubElement(infoCompRetencion, 'identificacionSujetoRetenido').text = partner.ident_num
        etree.SubElement(infoCompRetencion, 'periodoFiscal').text = time.strftime('%m/%Y',time.strptime(retention.invoice_id.date_invoice, '%Y-%m-%d'))
        
        #cret = etree.tostring(infoCompRetencion, pretty_print=True)
        #print cret
        
        return infoCompRetencion
        
    def _get_detail_element(self, retention):
        """Incluye el detalle del dcto electronico comprobante retencion, se asignan los valores
		nota solo esta calculando los detalles para retencion fact de productos y servicios de empresa a empresa
		o a personas que estan obligadas a llevar contabilidad
        """
        impuestos = etree.Element('impuestos')
         #relación account_invoice_retention-account_invoice_tax <-->-clave tax_code_id-account_tax_code
        for line in retention.tax_line:
            origen=retention.invoice_id.auth_inv_id.serie_entidad+retention.invoice_id.auth_inv_id.serie_emision+retention.invoice_id.factura
            #Impuesto
            impuesto = etree.Element('impuesto')
            etree.SubElement(impuesto, 'codigo').text = codigoImpuestoRetencion[line.tax_group]
            print"line.tax_group-175=%s"%line.tax_group 
            
            if line.tax_group in ['ret_vat', 'ret_vat_srv']:                               
                print"line.percent-176=%s"%line.percent    
                if line.percent==30:
                    print"line.percent-30=%s"%line.percent
                    etree.SubElement(impuesto, 'codigoRetencion').text = '1'
                elif line.percent == 70:
                    print"line.percent-70=%s"%line.percent
                    etree.SubElement(impuesto, 'codigoRetencion').text = '2'
                else:
                    print"line.percent-100=%s"%line.percent
                    etree.SubElement(impuesto, 'codigoRetencion').text = '3'
            else:
                print"line.base_code_id.code=%s"%line.base_code_id.code
                etree.SubElement(impuesto, 'codigoRetencion').text = line.base_code_id.code                
            etree.SubElement(impuesto, 'baseImponible').text = '%.2f' % (line.base)
            etree.SubElement(impuesto, 'porcentajeRetener').text = str(line.percent)
            etree.SubElement(impuesto, 'valorRetenido').text = '%.2f' % (abs(line.amount))
            etree.SubElement(impuesto, 'codDocSustento').text = retention.invoice_id.cod_sustento
            etree.SubElement(impuesto, 'numDocSustento').text = origen#origin #line.num_document
            etree.SubElement(impuesto, 'fechaEmisionDocSustento').text = time.strftime('%d/%m/%Y',time.strptime(retention.invoice_id.date_invoice, '%Y-%m-%d'))
            impuestos.append(impuesto)
            
        #imp = etree.tostring(impuestos, pretty_print=True)
        #print imp
        return impuestos
        
    def _generate_xml_retention(self, retention, access_key, emission_code):
        """rutina que realiza la construccion del XML en base a llamadas a los metodos
		correspondientes
        """
		# armado del XML de retencion
        comprobanteRetencion = etree.Element('comprobanteRetencion')
        comprobanteRetencion.set("id", "comprobante")
        comprobanteRetencion.set("version", "1.0.0")
        
        # Cabecera docto Empresa: generar infoTributaria
        infoTributaria = self._get_tax_element(retention, access_key, emission_code)
        comprobanteRetencion.append(infoTributaria)
        
        # Cabecera del documento: generar infoCompRetencion
        infoCompRetencion = self._get_retention_element(retention)
        comprobanteRetencion.append(infoCompRetencion)
        
        # Detalle del documento: Impuestos
        impuestos = self._get_detail_element(retention)
        comprobanteRetencion.append(impuestos)
        
        comprobante = etree.tostring(comprobanteRetencion, pretty_print=True)
        print comprobante
        return comprobanteRetencion
        
    def action_generate_eretention(self, cr, uid, ids, context=None):
        """ metodo que es llamado desde el boton de la vista forms de cmpnts de retencion
		la logica escrita a continuacion es: verifica que la retencion no pase de 24 horas de antiguedad; de se asi no se procesa
		caso contrario en base al numero del numero del comprobante en curso verifica que sea el ultimo a ser autorizado, no 
		permite que autorice un comprobante cuando existen otros anteriores que no han sido autorizados.
		Si todo va en orden y aun no tiene generada la acces key, la genera ademas obtiene codigo de emision (pruebas o produccion).
		Desde este punto , llama a las rutinas para armar los datos del comrpobante en las variables del esquema SRI para retencion
        """
        for obj in self.browse(cr, uid, ids):
            # Validar que el envío del comprobante electrónico se realice dentro de las 24 horas posteriores a su emisión
            if (datetime.now() - datetime.strptime(obj.fecha, '%Y-%m-%d')).days > 30:
                raise osv.except_osv(u'No se puede enviar el comprobante electrónico al SRI', u'Los comprobantes electrónicos deberán enviarse a las bases de datos del SRI para su autorización en un plazo máximo de 24 horas')
            else:
                # Validar que el envío de los comprobantes electrónicos sea secuencial. Referencia a datos en auth segun:
				# account_authorisation <--- account_journal <--- account_invoice_retention
                auth = obj.invoice_id.journal_id.auth_ret_id
                print"auth=%s"%auth
                numero = obj.name#obj.name[6:15] #obtengo el número de la retencion
                #numero = '{0}{1}{2}'.format(auth.serie_entidad, auth.serie_emision,obj.name)
                print"numeroret=%s"%numero
                numero_anterior = int(numero) - 1
                print"numero_anterior=%s"%numero_anterior
                #numero_comprobante_anterior = '{0}{1}{2}'.format(auth.serie_entidad, auth.serie_emision,str(numero_anterior).zfill(9))
                numero_comprobante_anterior = '{0}'.format(str(numero_anterior).zfill(9))              
                print"numero_comprobante_anterior=%s"%numero_comprobante_anterior
                anterior_ids = self.pool.get('account.invoice.retention').search(cr, uid, [('name','=',numero_comprobante_anterior)])
                print"anterior_ids=%s"%anterior_ids
                comprobante_anterior = self.browse(cr, uid, anterior_ids, context = context)

#                 if numero_anterior >= 2:#control envio desde el comprobante 000000003
#                     print"numero_anteriorifcontrol=%s"%numero_anterior 
#                     if not comprobante_anterior[0].authorization_sri:
#                         print"comprobante_anteriorifnot=%s"%comprobante_anterior[0].authorization_sri
#                         raise osv.except_osv(u'No se puede enviar el comprobante electrónico al SRI', u'Los comprobantes electrónicos deberán ser enviados al SRI para su autorización en orden cronológico y secuencial. Por favor enviar primero el comprobante inmediatamente anterior')
#                 #else:
                if numero_anterior >= 0: #Entra a ejecutar la rutina desde el comprobante 000000001
                    if not obj.access_key:
                        print"obj.access_key=%s"%obj.access_key
                        # Codigo de acceso, se estructura el codigo de 48 posiciones y lo valida en modulo 11 clase SriService
                        ak_temp = self.get_access_key(cr, uid, obj)
						#acces key generada
                        access_key = SriService.create_access_key(ak_temp) 
						#de empresa extrae el codigo de emision 1= pruebas, 2=produccion
                        emission_code = obj.company_id.emission_code
						#escribe los datos en los campos respectivos de la retencion en curso
                        self.write(cr, uid, [obj.id], {'access_key': access_key, 'emission_code': emission_code})
                    else:
                        access_key = obj.access_key
                        print"access_key=%s"%access_key
                        emission_code = obj.company_id.emission_code
                        print"emission_code=%s"%emission_code

                    #"""XML del comprobante electrónico: retención"""
                    comprobanteRetencion = self._generate_xml_retention(obj, access_key, emission_code)  
					
					#"""Validación del xml"""
                    inv_xml = DocumentXML(comprobanteRetencion, 'retention')
                    print"inv_xml=%s"%inv_xml
                    inv_xml.validate_xml()  
                    print"inv_xml.validate_xml()=%s"%inv_xml.validate_xml() 
					
                    #"""Grabación del xml en el disco, usa access key como nombre del archivo y el path recogido de empresa y deja en name"""
                    tree = etree.ElementTree(comprobanteRetencion)
                    ##name = '%s%s.xml' %('/home/leaduser/fee/comprobantes_retencion/comprobantes/', access_key)
                    name = '%s%s.xml' %(obj.company_id.vouchers_generated, access_key)
					# usa name guarda los datos y formate el xml 
                    tree.write(name,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml")
                    #print"name=%s"%name
                    # Firma electrónica del xml, usa una rutina java, pasa el path y el jar necesarios
                    firma_path = os.path.join(os.path.dirname(__file__), 'xades/firma/firmaodoo.jar')
                    #print"firma_path=%s"%firma_path  #recoge el nombre de la firma desde empresa
                    file_pk12 = obj.company_id.electronic_signature
                    #print"file_pk12=%s"%file_pk12  #recoge el pass del firmador desde empresa
                    password = obj.company_id.password_electronic_signature
                    #print"password=%s"%password
                    ##pathout='/home/leaduser/fee/comprobantes_retencion/firmados/' #recoge el path donde se guradaran cbte retencion firmado
                    pathout= obj.company_id.vouchers_signed
                    #print"pathout=%s"%pathout #arma el nombre del archivo firmado que se guardara en disco
                    nameout='%s.xml'%access_key
                    #print"nameout=%s"%nameout
                    
                    # Invocación del jar de la firma electrónica, firma. Pasa el xml no firmado, jar, path, firmador, pass, nombre xml luego de firmado
                    subprocess.call(['java', '-jar', firma_path, name, file_pk12, password,pathout,nameout])
                    #cadena recibe el archivo xml firmado en el path predeterminado, document obtiene la copia de este
                    ##cadena=open('%s%s.xml' %('/home/leaduser/fee/comprobantes_retencion/firmados/',access_key))
                    cadena=open('%s%s.xml' %(obj.company_id.vouchers_signed,access_key))
                    document=cadena.read()
                     # abre el canal al host y escribe el archivo en el path predeterminado                   
                    buf = StringIO.StringIO()
                    buf.write(document)
					# usa el mismo canal de conexion y transforma el contenido string del archivo cadena serial base64 y lo carga en xml
                    xml = base64.encodestring(buf.getvalue())
                    #print"xml=%s"%xml
 
                    """ Recepción de comprobantes electrónicos en el SRI, habilita el wsdl del web service y lo pone en url
					    crea la conexion cliente con la clase Client, ejecuta la validacion del cpbte retencion del archivo firmado
						y lo pone en result"""
 
                    url = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
                    urlp = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
                    
                    """Seleccionar Web Service según el tipo de ambiente"""
                    ambiente_cr = access_key[23:24] 
                    print"ambiente_cr=%s"%ambiente_cr
                    
                    if ambiente_cr == '1':
                     client = Client(url)
					 # pide la validacion al SRI
                     result =  client.service.validarComprobante(xml)
                     print"result-cr-pruebas=%s"%result
                    else:
                     client = Client(urlp)
                     # pide la validacion al SRI
                     result =  client.service.validarComprobante(xml)
                     print"result-cr-prod=%s"%result

                    self.__logger.info("RecepcionComprobantes: %s" % result)
                    mensaje_error = ""
                    if (result[0] == 'DEVUELTA'):
                        # Recepción fallida: en caso de rechazo se envía el arreglo con los motivos, concatena la lista de erores 
						# lo publica al video como log
                        comprobante = result[1].comprobante
                        mensaje_error += 'Clave de Acceso: ' + comprobante[0].claveAcceso
                        mensajes = comprobante[0].mensajes
                        i = 0
                        mensaje_error += "\nErrores:\n"
                        while i < len(mensajes):
                            mensaje = mensajes[i]
                            mensaje_error += 'Identificador: ' + mensaje[i].identificador + '\nMensaje: ' + mensaje[i].mensaje + '\nTipo: ' + mensaje[i].tipo
                            i += 1
                        raise osv.except_osv('Error SRI', mensaje_error)
                    else:
                        # Recepción exitosa
                        self.write(cr, uid, obj.id, {'security_code': self.get_code(cr, uid, obj)})
                        return {'warning':{'title':'Autorizado SRI', 'message':'Retención Autorizada por el SRI!'}}
                            
            return True
        
    def action_authorization_sri(self, cr, uid, ids,access_key,context=None):
        """
        """
        for obj in self.browse(cr, uid, ids):
            
            url = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'
            urlp = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'
                    
            """Seleccionar Web Service según el tipo de ambiente en ambiente pruebas:url ,en ambiente producción :urlp"""
            ambiente_aut_cr = obj.access_key[23:24] 
            print"ambiente_aut_cr=%s"%ambiente_aut_cr
                    
            if ambiente_aut_cr =='1':
                client_auto = Client(url)
                result_auto = client_auto.service.autorizacionComprobante(obj.access_key)
                print"result_auto_cr_pruebas=%s"%result_auto
            
            else:
                client_auto = Client(urlp)
                result_auto = client_auto.service.autorizacionComprobante(obj.access_key)
                print"result_auto_cr_prod=%s"%result_auto
            
            
            self.__logger.info("AutorizacionComprobantes: %s" % result_auto)
            if result_auto[2] == '':
                raise osv.except_osv('Error SRI', 'No existe comprobante')
            else:
                autorizaciones = result_auto[2].autorizacion
                i = 0
                autorizado = False
                mensaje_error = ''
                while i < len(autorizaciones):
                    autorizacion = autorizaciones[i]
                    estado = autorizacion.estado
                    fecha_autorizacion = autorizacion.fechaAutorizacion

                    if (estado == 'NO AUTORIZADO'):                        
                        mensajes = autorizacion.mensajes
                        j = 0
                        mensaje_error += "\nErrores:\n"
                        while j < len(mensajes):
                            mensaje = mensajes[j]
                            mensaje_error += 'Identificador: ' + mensaje[j].identificador + '\nMensaje: ' + mensaje[j].mensaje + '\nTipo: ' + mensaje[j].tipo + '\n'
                            j += 1
                    else:
                        autorizado = True
                        numero_autorizacion = autorizacion.numeroAutorizacion
                    i += 1
                    
        
           
        if autorizado == True:
            #print"autorizado=%s"%autorizado
            self.write(cr, uid, obj.id, {'authorization_sri': True, 'authorization_number': numero_autorizacion, 'authorization_date': fecha_autorizacion})
            autorizacion_xml = etree.Element('autorizacion')
            etree.SubElement(autorizacion_xml, 'estado').text = estado
            etree.SubElement(autorizacion_xml, 'numeroAutorizacion').text = numero_autorizacion
            etree.SubElement(autorizacion_xml, 'fechaAutorizacion').text = str(fecha_autorizacion.strftime("%d/%m/%Y %H:%M:%S"))
            etree.SubElement(autorizacion_xml, 'comprobante').text = etree.CDATA(autorizacion.comprobante)
                                      
            tree = etree.ElementTree(autorizacion_xml)
            ##name = '%s%s.xml' %('/home/leaduser/fee/comprobantes_retencion/autorizados/',obj.access_key)
            name = '%s%s.xml' %(obj.company_id.vouchers_authorized,obj.access_key)
            fichero=tree.write(name,pretty_print=True,xml_declaration=True,encoding='utf-8',method="xml")  
  
            #return autorizacion_xml   
            #self.send_mail(cr, uid, obj, obj.access_key, context)
        else:
            raise osv.except_osv('Error SRI', mensaje_error)
        #return True
        return False

    def send_mail(self, cr, uid, obj, access_key, context):
        ##name = '%s%s.xml' %('/home/leaduser/fee/comprobantes_retencion/autorizados/', access_key)
        name = '%s%s.xml' %(obj.company_id.vouchers_authorized, access_key)
        cadena = open(name, mode='rb').read()
        attachment_id = self.pool.get('ir.attachment').create(cr, uid,
            {
                'name': '%s.xml' % (access_key),
                'datas': base64.b64encode(cadena),
                'datas_fname': '%s.xml' % (access_key),
                'res_model': self._name,
                'res_id': obj.id,
                'type': 'binary'
            }, context=context)

        email_template_obj = self.pool.get('email.template')
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'l10n_ec_withdrawing', 'email_template_edi_retention')[1]
        email_template_obj.write(cr, uid, template_id, {'attachment_ids': [(6, 0, [attachment_id])]})
        email_template_obj.send_mail(cr, uid, template_id, obj.id, True)

        return True
