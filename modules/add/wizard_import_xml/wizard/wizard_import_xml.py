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
import logging
import os
import StringIO
import base64
import time
from lxml import etree
from lxml.etree import DocumentInvalid
from base64 import decodestring
from openerp import models, fields, api
from openerp.exceptions import ValidationError,except_orm, Warning, RedirectWarning
try:
    from suds.client import Client
    from suds.transport import TransportError
except ImportError:
    raise ImportError('Instalar Libreria suds')

import xml.etree.ElementTree as ET
import unicodedata
from xml.dom import minidom
from os.path import join as pjoin


"""
tree = ET.parse(r"/home/leaduser/test.xml")
root = tree.getroot()
doc = minidom.parse(r"/home/leaduser/test/comprobante.xml")
for child in root:
    tag=child.tag
    texto= child.text
    #print(child.tag, child.attrib ,child.text)
    print(tag,texto)
   
    if tag=='comprobante':
                
        print"////doc////=%s"%doc
        path='/home/leaduser/test/'  
        filename="comprobante.xml" 
        file = open(os.path.join(path,filename),"w")  
        file.write(texto)  
        file.close()
"""
        
       
class wizard_load_xml(models.Model):
    _name = 'wizard.load.xml'
        
    date= fields.Date('Fecha', required=True)
    period_id =fields.Many2one('account.period', 'Periodo', required=True)
    path_import =fields.Char('Path Importación',help='Especificar path de ubicacion de archivo XML', required=False)
    data =fields.Binary('Archivo', required=False)

    
    _defaults = {
        'date': lambda * a: time.strftime('%Y-%m-%d'),
        'path_import': '/home/leaduser/test/test.xml',
    }
  

    def get_partner(self, cr, uid, ids,context=None):   
        
        load_xml= self.browse(cr,uid,ids[0])
        print"path_import=%s"%load_xml.path_import
        if context is None:
            context = dict(context or {})
            
        #tree=ET.parse(load_xml.path_import)
        buf = StringIO.StringIO()
        buf.write(load_xml.data)
        tree = base64.decodestring(buf.getvalue())
        print"tree=%s"%tree

        
        root = ET.fromstring(tree)
        for child in root:
            print"child=%s"%child
            tag=child.tag
            texto= child.text
            #print(child.tag, child.attrib ,child.text)
            print(tag,texto)
   
            if tag=='comprobante':
                """Elimina Tildes"""
                docc=''.join((c for c in unicodedata.normalize('NFD', texto ) if unicodedata.category(c) != 'Mn'))
                doc = minidom.parseString(docc)
                print"doc=%s"%doc
                

        
        def getNodeText(node):
    
            nodelist = node.childNodes
            result = []
            for node in nodelist:
                if node.nodeType == node.TEXT_NODE:
                    result.append(node.data)
            return ''.join(result)
        

        def getText(nodelist):
            rc = []
            for node in nodelist:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data)
            return ''.join(rc)

        
        claveAcceso = doc.getElementsByTagName("claveAcceso")[0]
        print("Node 1 : %s \n" % getNodeText(claveAcceso))
        razonSocial = doc.getElementsByTagName("razonSocial")[0]
        print("Node 2 : %s \n" % getNodeText(razonSocial))
        ruc = doc.getElementsByTagName("ruc")[0]
        print("Node 3 : %s \n" % getNodeText(ruc))
        estab  = doc.getElementsByTagName("estab")[0]
        print("Node 4 : %s \n" % getNodeText(estab))
        ptoEmi  = doc.getElementsByTagName("ptoEmi")[0]
        print("Node 5 : %s \n" % getNodeText(ptoEmi))
        secuencial  = doc.getElementsByTagName("secuencial")[0]
        print("Node 6 : %s \n" % getNodeText(secuencial))
        dirMatriz  = doc.getElementsByTagName("dirMatriz")[0]
        print("Node 7 : %s \n" % getNodeText(dirMatriz)) 
        
             
             
        
        partner=self.pool('res.partner').search(cr, uid,[('ident_num', '=',getNodeText(ruc))],context=context)
        
        if partner:
            aux=partner[0]
            print"/////aux/////=%s"%aux
            fiscal = self.pool('res.partner').browse(cr ,uid, aux ,context=None).property_account_position.id
            cuenta = self.pool.get('res.partner').browse(cr ,uid, aux ,context=context).property_account_receivable.id
            pago = self.pool.get('res.partner').browse(cr ,uid, aux ,context=context).property_account_receivable.id
            company = self.pool.get('res.partner').browse(cr ,uid, aux ,context=context).company_id.id
            id_journal = self.pool.get('account.journal').search(cr, uid, [('company_id', '=', company),('type', '=', 'purchase')])
            retencion_id =self.pool.get('account.journal').browse(cr ,uid, id_journal ,context=context).auth_ret_id.id
        
        
            inputs = dict(doc_type = 'electronic',
                          name=getNodeText(claveAcceso),
                          partner_id= aux,
                          serie_entidad= getNodeText(estab),
                          serie_emision=getNodeText(ptoEmi),
                          type='in_invoice',
                          expiration_date=load_xml.date,
                          num_start=1,
                          num_end=1000
                          )
        
        
            authorisation_obj = self.pool.get('account.authorisation')
            autorizacion = authorisation_obj.create(cr, uid, inputs,context=None)
            autorizacion_id = authorisation_obj.browse(cr ,uid, autorizacion ,context=None).id
            print"autorizacion=%s"%autorizacion_id
            """Commit a la creacion en account.authorisation"""
            cr.commit()
            
            
            """CREAR CABECERA DE FACTURA"""
            numero= int(getNodeText(secuencial))
            vals = dict(type='in_invoice',
                        tipo_factura ='invoice',                                        
                        partner_id= aux,
                        fiscal_position=fiscal,
                        date_invoice = load_xml.date,
                        auth_inv_id = autorizacion_id,
                        auth_ret_id = retencion_id,                    
                        origin = getNodeText(secuencial),
                        number_inv_supplier = numero,                    
                        account_id = cuenta,
                        payment_type=1,
                        comment='test'
                        )
        
            print"vals=%s"%vals
            inv_obj = self.pool.get('account.invoice')
            factura = inv_obj.create(cr, uid, vals,context=None)
            inv_id = inv_obj.browse(cr ,uid, factura ,context=None).id
            
            cr.commit()
            
            """CREAR LINEAS DE FACTURA"""
            detalles = doc.getElementsByTagName("detalles")
            for det in detalles:
                detn= det.getElementsByTagName("detalle")
                for tagd in detn:
                    codigoPrincipal = tagd.getElementsByTagName("codigoPrincipal")[0]
                    descripcion= tagd.getElementsByTagName("descripcion")[0]
                    cantidad= tagd.getElementsByTagName("cantidad")[0]
                    precioUnitario= tagd.getElementsByTagName("precioUnitario")[0]
                    descuento= tagd.getElementsByTagName("descuento")[0]
                    precioTotalSinImpuesto= tagd.getElementsByTagName("precioTotalSinImpuesto")[0]
                
                    print("codigoP:%s,desc:%s,cant:%s,precio:%s,descto:%s,tsinimp:%s" %
                      (codigoPrincipal.firstChild.data,descripcion.firstChild.data,cantidad.firstChild.data,
                       precioUnitario.firstChild.data,descuento.firstChild.data,precioTotalSinImpuesto.firstChild.data))
        
                    """impuestos = doc.getElementsByTagName("impuestos")
                    for imp in impuestos:
                        impn= imp.getElementsByTagName("impuesto")
                        for tagi in impn:
                            codigo = tagi.getElementsByTagName("codigo")[0]
                            codigoPorcentaje= tagi.getElementsByTagName("codigoPorcentaje")[0]
                            tarifa= tagi.getElementsByTagName("tarifa")[0]
                            baseImponible= tagi.getElementsByTagName("baseImponible")[0]
                            valor= tagi.getElementsByTagName("valor")[0]
                    
                            print("cod:%s,codporc:%s,tarifa:%s,bi:%s,valor:%s" %
                              (codigo.firstChild.data,codigoPorcentaje.firstChild.data,tarifa.firstChild.data,
                               baseImponible.firstChild.data,valor.firstChild.data))"""
            
            
                
                    product=self.pool('product.product').search(cr, uid,[('name_template', '=',descripcion.firstChild.data)],context=context)
                                   
                    
                    if product:
                        aux1=product[0]
                        
                        inv_line_obj = self.pool.get('account.invoice.line')
                        ##tax=self.pool.get('product.template').browse(cr ,uid, aux1 ,context=context).supplier_taxes_id.id
                        
                            
                        valslines = dict(invoice_id= inv_id,
                                         partner_id= aux,
                                         product_id= aux1,
                                         price_unit= precioUnitario.firstChild.data,
                                         name=descripcion.firstChild.data,
                                         quantity= cantidad.firstChild.data,
                                         #invoice_line_tax_id=res['invoice_line_tax_id']                            
                                         )
        
                        print"valslines=%s"%valslines                        
                        lineas = inv_line_obj.create(cr, uid, valslines,context=None)
                    else:
                        valsproduct= dict(name=descripcion.firstChild.data,
                                          purchase_ok=True,
                                          sale_ok= False                           
                                         )
        
                        product_obj = self.pool.get('product.template')
                        producto = product_obj.create(cr, uid, valsproduct,context=None)
                        prod_id = product_obj.browse(cr ,uid, producto,context=None).id
                        cr.commit()
                        
                        inv_line_obj = self.pool.get('account.invoice.line')
                        ##tax=self.pool.get('product.template').browse(cr ,uid, prod_id ,context=context).supplier_taxes_id.id
                        
                        
                        valslines = dict(invoice_id= inv_id,
                                         partner_id= aux,
                                         product_id= prod_id,
                                         price_unit= precioUnitario.firstChild.data,
                                         name=descripcion.firstChild.data,
                                         quantity= cantidad.firstChild.data,
                                         #invoice_line_tax_id=res['invoice_line_tax_id']                        
                                         )
                        lineas = inv_line_obj.create(cr, uid, valslines,context=None)
                                    
            
            
        else:
            
            raise ValidationError('No existe Proveedor,Por favor registre los datos del proveedor')
    


      
    