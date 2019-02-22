# -*- encoding: utf-8 -*-
##############################################################################
#
#    Billboard Module
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


import base64
import StringIO
import time
from openerp.osv import osv, fields
from xml.dom.minidom import Document
from openerp.tools import flatten
from datetime import datetime
from openerp.exceptions import ValidationError


class wizard_generate_file_ats(osv.osv_memory):
    _name = "wizard.generate.file.ats"
    
    def generate_file_ats(self, cr, uid, ids, context=None):
        document_ats_obj = self.pool.get('account.document.ats')
        document_ats_resumen_obj = self.pool.get('account.document.ats.resumen')
        document_ats_resumen_purchase_obj = self.pool.get('account.document.ats.detail.purchase')
        document_ats_sale_obj = self.pool.get('account.document.ats.detail.sale')
        document_ats_import_obj = self.pool.get('account.document.ats.resumen.import')
        document_ats_export_obj = self.pool.get('account.document.ats.resumen.export')
        document_ats_concept_retent_obj = self.pool.get('account.document.ats.resumen.concept_retent')
        document_ats_resu_retent_obj = self.pool.get('account.document.ats.resumen.resu.retent')
        document_ats_detail_purchase_reten_obj = self.pool.get('account.document.ats.detail.purchase.retention')
        account_invoice_tax = self.pool.get('account.invoice.tax')
        
        
        data = self.read(cr, uid, ids)[0]
        
        id_header = context['active_ids'][0]
        id_formulario = data['formulario']
        
        
        doc = Document()
        
        # Obtener Informacion de la compania
        compania = data['company'][0]
        #print 'compania', data
        lineas = self.pool.get('res.company').browse(cr, uid, [compania])[0]
        empresa = lineas.partner_id.name
        ruc_empresa = lineas.partner_id.ident_num
        tipoIdEmpresa = lineas.partner_id.ident_type
        
        mainform = doc.createElement("iva")
        doc.appendChild(mainform)
        
        ruc = doc.createElement("TipoIDInformante")
        mainform.appendChild(ruc)
        pruc = doc.createTextNode(tipoIdEmpresa.upper())
        ruc.appendChild(pruc)
        
        ruc = doc.createElement("IdInformante")
        mainform.appendChild(ruc)
        pruc = doc.createTextNode(ruc_empresa.rstrip())
        ruc.appendChild(pruc)
        
        social = doc.createElement("razonSocial")
        mainform.appendChild(social)
        empresa = empresa.rstrip().replace('.', '')
        empresa = empresa.replace('&','')
        psocial = doc.createTextNode(empresa)
        social.appendChild(psocial)
        
        # Obtener fechas
        #print 'header', id_header
        doc_ats = document_ats_obj.browse(cr, uid, id_header)
         
        anio_data, mes, dia, = str(doc_ats.date_start).split("-")
        
        fec_anio = doc.createElement("Anio")
        mainform.appendChild(fec_anio)
        pfec_anio = doc.createTextNode(anio_data.rstrip())
        fec_anio.appendChild(pfec_anio)
        
        fec_mes = doc.createElement("Mes")
        mainform.appendChild(fec_mes)
        pfec_mes = doc.createTextNode(mes.rstrip())
        fec_mes.appendChild(pfec_mes)
        
        aux = doc.createElement("numEstabRuc")
        mainform.appendChild(aux)
        pfec_mes = doc.createTextNode(str(lineas.num_sucursal).zfill(3))
        aux.appendChild(pfec_mes)
        
        nTotalVentas = doc.createElement("totalVentas")
        mainform.appendChild(nTotalVentas)
    
        
        aux = doc.createElement("codigoOperativo")
        mainform.appendChild(aux)
        pfec_mes = doc.createTextNode("IVA")
        aux.appendChild(pfec_mes)
        
        #resumencomp = self.pool.get('account.document.ats.resumen').search(cr, uid, [('document_ats_resumen_id','=',fechas.id)])
        resumen_doc_compras_ventas = doc_ats.document_ats_resumen_ids #account.document.ats.resumen
        for aux_data in [aux.document_ats_purchase_ids for aux in resumen_doc_compras_ventas]:
            if aux_data:
                compras_form = doc.createElement("compras")
                mainform.appendChild(compras_form)
                break
        for aux_data in [aux.document_ats_sale_ids for aux in resumen_doc_compras_ventas]:
            if aux_data:
                ventas_form = doc.createElement("ventas")
                mainform.appendChild(ventas_form)
                break#Puse esto por que se creaba varias veces esta cabecera
        total_ventas = 0.0
        facturas_ventas = []
        new_total_ventas = 0.00
        #Calcular Total de Ventas
        for resumen_compra_venta in resumen_doc_compras_ventas:
            
            resumen_compra_venta_id = resumen_compra_venta.id
            facturas_ventas += [aux.invoice_id.id for aux in resumen_compra_venta.document_ats_sale_ids if aux.invoice_id]
            
            sql = "select \
                tipo_id_prov as tip,ruc_prov as ruc, codigo_sustento as tipo,count(1) as numreg,autorizacion,sum(base_no_gravada) as bng, sum(base_imponible) as bi, \
                sum(base_imponible_0_iva) as bi0i, sum(base_imponible_grava) as big, sum(monto_iva) as mi,sum(monto_ice) as mice, sum(valor_ret_iva) as vri, sum(valor_ret_renta) as vrr \
                from account_document_ats_detail_sale \
                where document_ats_resumen_sale_id = %s \
                group by ruc_prov, codigo_sustento, tipo_id_prov,autorizacion \
                order by codigo_sustento" % (resumen_compra_venta_id)
            
            
            cr.execute(sql)
            #tabla account_document_ats_detail_sale
            detalles_ventas = cr.dictfetchall()
                           
            new_total_fact = sum([detalle_ventas['bng'] +  detalle_ventas['bi0i'] + detalle_ventas['big'] for detalle_ventas in detalles_ventas if detalle_ventas['tipo'] == '18' and len(detalle_ventas['autorizacion'])==10])
            new_total_credit = sum([detalle_ventas['bng'] + detalle_ventas['bi0i'] + detalle_ventas['big'] for detalle_ventas in detalles_ventas if detalle_ventas['tipo'] == '04' and len(detalle_ventas['autorizacion'])==10])
            print"new_total_fact::",new_total_fact
            print"new_total_credit::",new_total_credit
            new_total_ventas += new_total_fact - new_total_credit
              
        band = True
        for resumen_compra_venta in resumen_doc_compras_ventas:
            detalles_compras = resumen_compra_venta.document_ats_purchase_ids
            for detalle_compras in detalles_compras:
                if not detalle_compras.cod_tipo_comp:
                    continue
                
                detalle_compras_form = doc.createElement("detalleCompras")
                compras_form.appendChild(detalle_compras_form)
                
                cod_sustento = doc.createElement("codSustento")
                detalle_compras_form.appendChild(cod_sustento)
                pcod_sustento = doc.createTextNode(detalle_compras.codigo_sustento)
                cod_sustento.appendChild(pcod_sustento)
                
                
                cod_tipo_prov = doc.createElement("tpIdProv")
                detalle_compras_form.appendChild(cod_tipo_prov)
                pcod_tipo_prov = doc.createTextNode(detalle_compras.tipo_id_prov)
                cod_tipo_prov.appendChild(pcod_tipo_prov)
                
                cod_id_prov = doc.createElement("idProv")
                detalle_compras_form.appendChild(cod_id_prov)
                ruc = '' 
                ruc = detalle_compras.ruc_prov
                ruc = ruc.replace('+','')
                #pcod_id_prov = doc.createTextNode(detalle_compras.ruc_prov)
                pcod_id_prov = doc.createTextNode(ruc)
                cod_id_prov.appendChild(pcod_id_prov)
                
                
                tipoComprobante_c = doc.createElement("tipoComprobante")
                detalle_compras_form.appendChild(tipoComprobante_c)
                ptipoComprobante_c = doc.createTextNode(detalle_compras.cod_tipo_comp)
                tipoComprobante_c.appendChild(ptipoComprobante_c)

            
                if detalle_compras.tipo_id_prov =='03':#Entra solo cuando el codigo de tipo de id del partner es pasaporte(Eso dice la ficha Tecnica)
                    tipoProv = doc.createElement("tipoProv")
                    detalle_compras_form.appendChild(tipoProv)
                    tipoprov_ext = detalle_compras.invoice_id and detalle_compras.invoice_id.partner_id and detalle_compras.invoice_id.partner_id.tipoprov_ext or False
                    if not tipoprov_ext:
                        raise osv.except_osv((u'Información'), ('En la ficha de proveedor: '+str(detalle_compras.invoice_id.partner_id.name)+' falta llenar información del campo Tipo Identificacion Proveedor en la pestaña Ventas & Compras de la ficha'))
                    ptipoComprobante_c = doc.createTextNode(tipoprov_ext)
                    tipoProv.appendChild(ptipoComprobante_c)
                    
                    
                    denoProv = doc.createElement("denoProv")
                    detalle_compras_form.appendChild(denoProv)
                    pdenoProv = doc.createTextNode(detalle_compras.invoice_id.partner_id.name or 'xxxxx')
                    denoProv.appendChild(pdenoProv)
                    print"detalle_compras.invoice_id.partner_id=%s"%detalle_compras.invoice_id.partner_id.id
                    
                    """tipoProv = doc.createElement("parteRel")
                    detalle_compras_form.appendChild(tipoProv)
                    
                    parterel = detalle_compras.invoice_id and detalle_compras.invoice_id.partner_id and detalle_compras.invoice_id.partner_id.parterel or False
                    if not parterel:
                        raise osv.except_osv((u'Información'), ('En la ficha de proveedor: '+str(detalle_compras.invoice_id.partner_id.name)+' falta llenar información del campo \'Parte Relacionada\' en la pestaña Ventas & Compras de la ficha'))
                    ptipoComprobante_c = doc.createTextNode(parterel)
                    tipoProv.appendChild(ptipoComprobante_c)"""
                    
                print"detalle_compras.invoice_id.partner_id=%s"%detalle_compras.invoice_id.partner_id.id
                parterel = detalle_compras.invoice_id and detalle_compras.invoice_id.partner_id and detalle_compras.invoice_id.partner_id.parterel or 'NO'               
                print"parterel=%s"%parterel
                parteRel = doc.createElement("parteRel")
                detalle_compras_form.appendChild(parteRel)
                pparteRel = doc.createTextNode(parterel)
                parteRel.appendChild(pparteRel)
                
                
                fecha_reg = doc.createElement("fechaRegistro")
                detalle_compras_form.appendChild(fecha_reg)
                if detalle_compras.fecha_registro:
                    pfecha_reg = doc.createTextNode(time.strftime('%d/%m/%Y', time.strptime(detalle_compras.fecha_registro, '%Y-%m-%d')))
                else:
                    pfecha_reg = doc.createTextNode(time.strftime('%d/%m/%Y', time.strptime(detalle_compras.fecha_emision, '%Y-%m-%d')))

                fecha_reg.appendChild(pfecha_reg)
                
                
                establec = doc.createElement("establecimiento")
                detalle_compras_form.appendChild(establec)
                pestablec = doc.createTextNode(detalle_compras.autorizacion_establecimiento)
                establec.appendChild(pestablec)
                
                emision = doc.createElement("puntoEmision")
                detalle_compras_form.appendChild(emision)
                pemision = doc.createTextNode(detalle_compras.autorizacion_punto_emision)
                emision.appendChild(pemision)
                
                secuencial = doc.createElement("secuencial")
                detalle_compras_form.appendChild(secuencial)
                psecuencial = doc.createTextNode(str(detalle_compras.secuencial_factura))
                secuencial.appendChild(psecuencial)
                
                fecha_emi = doc.createElement("fechaEmision")
                detalle_compras_form.appendChild(fecha_emi)
                pfecha_emi = doc.createTextNode(time.strftime('%d/%m/%Y', time.strptime(detalle_compras.fecha_emision, '%Y-%m-%d')))
                fecha_emi.appendChild(pfecha_emi)
                
                autorizacion = doc.createElement("autorizacion")
                detalle_compras_form.appendChild(autorizacion)
                pautorizacion = doc.createTextNode(detalle_compras.autorizacion)
                autorizacion.appendChild(pautorizacion)
                
                baseNoGraIva = doc.createElement("baseNoGraIva")
                detalle_compras_form.appendChild(baseNoGraIva)
                pbaseNoGraIva = doc.createTextNode('{0:.2f}'.format(detalle_compras.base_imponible_no_iva))
                baseNoGraIva.appendChild(pbaseNoGraIva)
                
                baseImponible = doc.createElement("baseImponible")
                detalle_compras_form.appendChild(baseImponible)
                pbaseImponible = doc.createTextNode('{0:.2f}'.format(detalle_compras.base_imponible_0_iva))
                baseImponible.appendChild(pbaseImponible)
                
                baseImpGrav = doc.createElement("baseImpGrav")
                detalle_compras_form.appendChild(baseImpGrav)
                pbaseImpGrav = doc.createTextNode('{0:.2f}'.format(detalle_compras.base_imponible_grava))
                baseImpGrav.appendChild(pbaseImpGrav)
                #print"pbaseImpGrav-wdfalin253=%s"%pbaseImpGrav
                
                """baseImpExe compras añadida"""
                baseImpExe = doc.createElement("baseImpExe")
                detalle_compras_form.appendChild(baseImpExe)
                pbaseImpExe = doc.createTextNode('0.00')
                baseImpExe.appendChild(pbaseImpExe)
                #print"pbaseImpExe-wdfalin260=%s"%pbaseImpExe 
                
                montoIce = doc.createElement("montoIce")
                detalle_compras_form.appendChild(montoIce)
                pmontoIce = doc.createTextNode('0.00')
                montoIce.appendChild(pmontoIce)
               
                montoIva = doc.createElement("montoIva")
                detalle_compras_form.appendChild(montoIva)
                pmontoIva = doc.createTextNode('{0:.2f}'.format(detalle_compras.monto_iva))
                montoIva.appendChild(pmontoIva)
                
                """añadidos tags"""
                valRetBien10 = doc.createElement("valRetBien10") #721 10%
                detalle_compras_form.appendChild(valRetBien10)
                pvalRetBien10 = doc.createTextNode('{0:.2f}'.format(detalle_compras.valor_retencion_bien10))
                valRetBien10.appendChild(pvalRetBien10)
                
                valRetServ20 = doc.createElement("valRetServ20") #723  20%
                detalle_compras_form.appendChild(valRetServ20)
                pvalRetServ20 = doc.createTextNode('{0:.2f}'.format(detalle_compras.valor_retencion_serv20))
                valRetServ20.appendChild(pvalRetServ20)
                """"""
                
                valorRetBienes = doc.createElement("valorRetBienes")#725 30%
                detalle_compras_form.appendChild(valorRetBienes)
                #print 'valor_retencion_bienes', detalle_compras.valor_retencion_bienes
                pvalorRetBienes = doc.createTextNode('{0:.2f}'.format(detalle_compras.valor_retencion_bienes))
                valorRetBienes.appendChild(pvalorRetBienes)
                
                """añadidos tag"""
                valRetServ50 = doc.createElement("valRetServ50") # 50%
                detalle_compras_form.appendChild(valRetServ50)
                pvalRetServ50 = doc.createTextNode('{0:.2f}'.format(detalle_compras.valor_retencion_serv50))
                valRetServ50.appendChild(pvalRetServ50)
                """"""
                
                valorRetServicios = doc.createElement("valorRetServicios")#727 70%
                detalle_compras_form.appendChild(valorRetServicios)
                #print 'valor_retencion_servicios', detalle_compras.valor_retencion_servicios
                pvalorRetServicios = doc.createTextNode('{0:.2f}'.format(detalle_compras.valor_retencion_servicios))
                valorRetServicios.appendChild(pvalorRetServicios)
                
                valRetServ100 = doc.createElement("valRetServ100") #729 100%
                detalle_compras_form.appendChild(valRetServ100)
                pvalRetServ100 = doc.createTextNode('{0:.2f}'.format(detalle_compras.valor_retencion_servicios_100))
                valRetServ100.appendChild(pvalRetServ100)
                
                """Añadido tag suma reembolso"""
                if detalle_compras.invoice_id.detalle_reembolso_ids:
                    suma=0.00
                    for suma_reembolso in detalle_compras.invoice_id.detalle_reembolso_ids:
                        suma += suma_reembolso.base_imponible + suma_reembolso.base_gravada + suma_reembolso.base_no_gravada            
                        print"////sumaREEMBOLSO///=%s"%suma
                        
                    totbasesImpReemb = doc.createElement("totbasesImpReemb")
                    detalle_compras_form.appendChild(totbasesImpReemb)
                    ptotbasesImpReemb = doc.createTextNode('{0:.2f}'.format(suma))
                    totbasesImpReemb.appendChild(ptotbasesImpReemb)
                else:
                    totbasesImpReemb = doc.createElement("totbasesImpReemb")
                    detalle_compras_form.appendChild(totbasesImpReemb)
                    ptotbasesImpReemb = doc.createTextNode('0.00')
                    totbasesImpReemb.appendChild(ptotbasesImpReemb)
                """"""
                
                pagoExterior = doc.createElement('pagoExterior')
                detalle_compras_form.appendChild(pagoExterior)
                pagoLocExt = doc.createElement('pagoLocExt')
                pagoExterior.appendChild(pagoLocExt)
                vpagoLocExt = doc.createTextNode('01' if detalle_compras.invoice_id.payment_mode == 'local' else '02')
                pagoLocExt.appendChild(vpagoLocExt)
                
                if detalle_compras.invoice_id.payment_mode == 'ext':
                    tipoRegi = doc.createElement('tipoRegi')
                    pagoExterior.appendChild(tipoRegi)
                    vtipoRegi = doc.createTextNode('01')
                    tipoRegi.appendChild(vtipoRegi)
                    
                    paisEfecPagoGen = doc.createElement('paisEfecPagoGen')
                    pagoExterior.appendChild(paisEfecPagoGen)
                    vpaisEfecPagoGen = doc.createTextNode(detalle_compras.invoice_id.payment_country_id.ats_code)
                    paisEfecPagoGen.appendChild(vpaisEfecPagoGen)
                
                
                paisEfecPago = doc.createElement('paisEfecPago')
                pagoExterior.appendChild(paisEfecPago)
                vpaisEfecPago = doc.createTextNode(detalle_compras.invoice_id.payment_country_id and detalle_compras.invoice_id.payment_country_id.ats_code or 'NA')
                paisEfecPago.appendChild(vpaisEfecPago)
                auxLoc = detalle_compras.invoice_id.payment_mode == 'local' and 'NA' or None
                aplicConvDobTrib = doc.createElement('aplicConvDobTrib')
                pagoExterior.appendChild(aplicConvDobTrib)
                vaplicConvDobTrib = doc.createTextNode(auxLoc or detalle_compras.invoice_id.double_taxation and 'SI' or 'NO')
                aplicConvDobTrib.appendChild(vaplicConvDobTrib)
                pagExtSujRetNorLeg = doc.createElement('pagExtSujRetNorLeg')
                pagoExterior.appendChild(pagExtSujRetNorLeg)
                vpagExtSujRetNorLeg = doc.createTextNode(auxLoc or detalle_compras.invoice_id.double_taxation and 'SI' or 'NO')
                pagExtSujRetNorLeg.appendChild(vpagExtSujRetNorLeg)
                
                if detalle_compras.invoice_id.payment_method_ids:
                    print"co=%s"%detalle_compras.invoice_id.payment_method_ids
                    formasDePago = doc.createElement('formasDePago')
                    detalle_compras_form.appendChild(formasDePago)
                    for forma_pago in detalle_compras.invoice_id.payment_method_ids:
                        formaPago = doc.createElement('formaPago')
                        formasDePago.appendChild(formaPago)
                        vformaPago = doc.createTextNode(forma_pago.code)
                        formaPago.appendChild(vformaPago)
                        
                """elif detalle_compras.invoice_id.payment_type:
                    print"co-payment_type=%s"%detalle_compras.invoice_id.payment_type
                    formasDePago = doc.createElement('formasDePago')
                    detalle_compras_form.appendChild(formasDePago)
                    formaPago = doc.createElement('formaPago')
                    formasDePago.appendChild(formaPago)
                    vformaPago = doc.createTextNode(detalle_compras.invoice_id.payment_type.code)
                    formaPago.appendChild(vformaPago)"""
                        

                
                if detalle_compras.invoice_id.tipo_factura == 'reembolso':
                    
                    if detalle_compras.invoice_id.detalle_reembolso_ids:
                        reembolsos = doc.createElement('reembolsos')
                        detalle_compras_form.appendChild(reembolsos)
                    
                    for reembolso_id in detalle_compras.invoice_id.detalle_reembolso_ids:
                        #print 'reembolso_id',reembolso_id
                        reembolso = doc.createElement('reembolso')
                        reembolsos.appendChild(reembolso)
                        tipoComprobanteReemb = doc.createElement('tipoComprobanteReemb')
                        reembolso.appendChild(tipoComprobanteReemb)
                        aux = doc.createTextNode(reembolso_id.tipo_comprobante)
                        tipoComprobanteReemb.appendChild(aux)
                        #TIPO_DOC = {'r': '01', 'p': '03', 'c': '02'}
                        TIPO_DOC = {'r': '01', 'p': '03', 'c': '02'}
                        tpIdProvReemb = doc.createElement('tpIdProvReemb')
                        reembolso.appendChild(tpIdProvReemb)
                        if not reembolso_id.partner_id.ident_type:
                            numero = reembolso_id.invoice_id.number_inv_supplier or '/'
                            raise osv.except_osv((u'Infomación'), ('En el reembolso Nro:'+ str(numero)+', en el detalle de reembolso el proveedor '+ str(reembolso_id.partner_id.name)+' no tiene definido el tipo de documento en la ficha de proveedor. Llenelo para continuar '))
                        aux = doc.createTextNode(TIPO_DOC[reembolso_id.partner_id.ident_type])
                        tpIdProvReemb.appendChild(aux)
                        idProvReemb = doc.createElement('idProvReemb')
                        reembolso.appendChild(idProvReemb)
                        ruc = ''
                        ruc = reembolso_id.partner_id.ident_num
                        ruc = ruc.replace('+','')
                        #aux = doc.createTextNode(reembolso_id.partner_id.ident_num)
                        aux = doc.createTextNode(ruc)
                        idProvReemb.appendChild(aux)
                        establecimientoReemb = doc.createElement('establecimientoReemb')
                        reembolso.appendChild(establecimientoReemb)
                        aux = doc.createTextNode(reembolso_id.establecimiento or '')
                        establecimientoReemb.appendChild(aux)
                        puntoEmisionReemb = doc.createElement('puntoEmisionReemb')
                        reembolso.appendChild(puntoEmisionReemb)
                        aux = doc.createTextNode(reembolso_id.pto_emision or '')
                        puntoEmisionReemb.appendChild(aux)
                        secuencialReemb = doc.createElement('secuencialReemb')
                        reembolso.appendChild(secuencialReemb)
                        secuencial = reembolso_id.number
                        #print '############',len(secuencial)
                        if len(secuencial) > 9:
                            numero = reembolso_id.invoice_id.number_inv_supplier or '/'
                            raise osv.except_osv((u'Información'), ('En el detalle de reembolo Nro:'+str(numero)+' del proveedor '+str(reembolso_id.partner_id.name)+' la secuencia de Documento debe tener solo 9 digitos!'))
                        aux = doc.createTextNode(reembolso_id.number or '0')
                        secuencialReemb.appendChild(aux)
                        fechaEmisionReemb = doc.createElement('fechaEmisionReemb')
                        reembolso.appendChild(fechaEmisionReemb)
                        if not reembolso_id.date:
                            numero = reembolso_id.invoice_id.number_inv_supplier or '/'
                            raise osv.except_osv((u'Información'), ('En el detalle de reembolo Nro:'+str(numero)+' del proveedor '+str(reembolso_id.partner_id.name)+' no tiene fecha!'))
                        fecha_reembolso = reembolso_id.date and datetime.strptime(reembolso_id.date, '%Y-%m-%d')
                        aux = doc.createTextNode(fecha_reembolso and datetime.strftime(fecha_reembolso, '%d/%m/%Y') or '')
                        fechaEmisionReemb.appendChild(aux)
                        
                        autorizacionReemb = doc.createElement('autorizacionReemb')
                        reembolso.appendChild(autorizacionReemb)
                        aux = doc.createTextNode(reembolso_id.nro_autorizacion or '')
                        autorizacionReemb.appendChild(aux)
                        
                        baseImponibleReemb = doc.createElement('baseImponibleReemb')
                        reembolso.appendChild(baseImponibleReemb)
                        aux = doc.createTextNode('%.2f'%reembolso_id.base_imponible)
                        baseImponibleReemb.appendChild(aux)
                        
                        baseImpGravReemb = doc.createElement('baseImpGravReemb')
                        reembolso.appendChild(baseImpGravReemb)
                        aux = doc.createTextNode('%.2f'%reembolso_id.base_gravada)
                        baseImpGravReemb.appendChild(aux)
                        
                        baseNoGraIvaReemb = doc.createElement('baseNoGraIvaReemb')
                        reembolso.appendChild(baseNoGraIvaReemb)
                        aux = doc.createTextNode('%.2f'%reembolso_id.base_no_gravada)
                        baseNoGraIvaReemb.appendChild(aux)
                        
                        """tag anadido dc ats 2017"""
                        baseImpExeReemb = doc.createElement('baseImpExeReemb')
                        reembolso.appendChild(baseImpExeReemb)                        
                        aux = doc.createTextNode('0.00')
                        baseImpExeReemb.appendChild(aux)
                        """"""
                        
                        montoIceRemb = doc.createElement('montoIceRemb')
                        reembolso.appendChild(montoIceRemb)                        
                        aux = doc.createTextNode('%.2f'%reembolso_id.monto_ice)
                        montoIceRemb.appendChild(aux)
                        
                        montoIvaRemb = doc.createElement('montoIvaRemb')
                        reembolso.appendChild(montoIvaRemb)
                        aux = doc.createTextNode('%.2f'%reembolso_id.monto_iva)
                        montoIvaRemb.appendChild(aux)
                    
                
                if detalle_compras.invoice_id.tipo_factura != 'reembolso':
                    air_form = doc.createElement("air")
                    detalle_compras_form.appendChild(air_form)
                    
                    detalle_retenciones = detalle_compras.document_ats_detail_purchase_retention_ids
                    
                    auxiliar = {}
                    for aux in detalle_retenciones:
                        val = auxiliar.get(aux.codigo_retencion_air, [])
                        auxiliar[aux.codigo_retencion_air] = val + [aux]
                            
    #                 for detalle_retencion in detalle_retenciones:
                    for code, detalle_retencion in auxiliar.iteritems():
                        detalleAir_form = doc.createElement("detalleAir")
                        air_form.appendChild(detalleAir_form)
            
                        codigoRet = doc.createElement("codRetAir")
                        detalleAir_form.appendChild(codigoRet)
                        pcodigoRet = doc.createTextNode(code)
                        codigoRet.appendChild(pcodigoRet)
                        print"pcodigoRet=%s"%pcodigoRet
                        
                        vBaseImpAir = sum([aux.base_imponible_air for aux in detalle_retencion])
                        vValRetAir = sum([aux.valor_retencion for aux in detalle_retencion])
                        vporcentajeAir = round(vValRetAir / (vBaseImpAir or 1), 2) * 100
                        
                        baseImp = doc.createElement("baseImpAir")
                        detalleAir_form.appendChild(baseImp)
                        pbaseImp = doc.createTextNode('{0:.2f}'.format(vBaseImpAir))
                        baseImp.appendChild(pbaseImp)
                        
                        porcentajeRet = doc.createElement("porcentajeAir")
                        detalleAir_form.appendChild(porcentajeRet)
                        pporcentajeRet = doc.createTextNode('{0:.2f}'.format(vporcentajeAir))#detalle_retencion[0].porcentaje_air))
                        porcentajeRet.appendChild(pporcentajeRet)
                        
                        valorRet = doc.createElement("valRetAir")
                        detalleAir_form.appendChild(valorRet)
                        pvalorRet = doc.createTextNode('{0:.2f}'.format(vValRetAir))
                        valorRet.appendChild(pvalorRet)
                        codigo=code
                        """no se generan estoss tags si el codigo de retencion contiene 332 retencion 0%"""        
                        if detalle_compras.establecimiento_retencion !='000' and '332' not in code:
                            estabRetencion1 = doc.createElement("estabRetencion1")
                            detalle_compras_form.appendChild(estabRetencion1)
                            pestabRetencion1 = doc.createTextNode(str(detalle_compras.establecimiento_retencion))
                            estabRetencion1.appendChild(pestabRetencion1)
                    
                            ptoEmiRetencion1 = doc.createElement("ptoEmiRetencion1")
                            detalle_compras_form.appendChild(ptoEmiRetencion1)
                            pptoEmiRetencion1 = doc.createTextNode(str(detalle_compras.emision_retencion))
                            ptoEmiRetencion1.appendChild(pptoEmiRetencion1)
                    
                            secRetencion1 = doc.createElement("secRetencion1")
                            detalle_compras_form.appendChild(secRetencion1)
                            psecRetencion1 = doc.createTextNode(str(detalle_compras.secuencial_retencion))
                            secRetencion1.appendChild(psecRetencion1)
                    
                            autRetencion1 = doc.createElement("autRetencion1")
                            detalle_compras_form.appendChild(autRetencion1)
                            #pautRetencion1 = doc.createTextNode(str(detalle_compras.autorizacion_retencion))
                            pautRetencion1 = doc.createTextNode(str(detalle_compras.invoice_id.ret_id.authorization_number_offline or detalle_compras.invoice_id.ret_id.authorization_number or detalle_compras.autorizacion_retencion))
                            autRetencion1.appendChild(pautRetencion1)
                
                            """no se generan estoss tags si el codigo de retencion contiene 332 retencion 0%"""        
                        if '332' not in code and detalle_compras.fecha_emision_retencion != '00/00/0000' and detalle_compras.invoice_id.tipo_factura != 'reembolso':
                            fechaEmiRet1 = doc.createElement("fechaEmiRet1")
                            detalle_compras_form.appendChild(fechaEmiRet1)
                            pfechaEmiRet1 = doc.createTextNode(str(detalle_compras.fecha_emision_retencion))    
                            fechaEmiRet1.appendChild(pfechaEmiRet1)
                
                if detalle_compras.invoice_id.type == 'in_refund' and detalle_compras.invoice_id.origin:
                    invoice_id = detalle_compras.invoice_id.origin.split('(')[1][:-1]
                    invoice_id = self.pool.get('account.invoice').browse(cr, uid, int(invoice_id))
                    
                    docModificado = doc.createElement("docModificado")
                    detalle_compras_form.appendChild(docModificado)
                    pdocModificadoo = doc.createTextNode('01')
                    docModificado.appendChild(pdocModificadoo)
                    
                    estabModificado = doc.createElement("estabModificado")
                    detalle_compras_form.appendChild(estabModificado)
                    pestabModificado = doc.createTextNode(invoice_id.auth_inv_id.serie_entidad)
                    estabModificado.appendChild(pestabModificado)
                    
                    ptoEmiModificado = doc.createElement("ptoEmiModificado")
                    detalle_compras_form.appendChild(ptoEmiModificado)
                    pptoEmiModificado = doc.createTextNode(invoice_id.auth_inv_id.serie_emision)
                    ptoEmiModificado.appendChild(pptoEmiModificado)
                   
                    secModificado = doc.createElement("secModificado")
                    detalle_compras_form.appendChild(secModificado)
                    psecModificado = doc.createTextNode(str(invoice_id.number_inv_supplier).zfill(9))
                    secModificado.appendChild(psecModificado)
                
                    autModificado = doc.createElement("autModificado")
                    detalle_compras_form.appendChild(autModificado)
                    pautModificadoo = doc.createTextNode(invoice_id.auth_inv_id.name)
                    autModificado.appendChild(pautModificadoo)
                
                
            resumen_compra_venta_id = resumen_compra_venta.id
            print"resumen_compra_venta_id=%s"%resumen_compra_venta_id
            facturas_ventas += [aux.invoice_id.id for aux in resumen_compra_venta.document_ats_sale_ids if aux.invoice_id]
            
            sql = "select \
                tipo_id_prov as tip,ruc_prov as ruc, codigo_sustento as tipo,count(1) as numreg,autorizacion,sum(base_no_gravada) as bng, sum(base_imponible) as bi, \
                sum(base_imponible_0_iva) as bi0i, sum(base_imponible_grava) as big, sum(monto_iva) as mi, sum(monto_ice) as mice ,sum(valor_ret_iva) as vri, sum(valor_ret_renta) as vrr \
                from account_document_ats_detail_sale \
                where document_ats_resumen_sale_id = %s \
                group by ruc_prov, codigo_sustento,tipo_id_prov ,autorizacion \
                order by codigo_sustento" % (resumen_compra_venta_id)
            
            
            cr.execute(sql)
            detalles_ventas = cr.dictfetchall()
            """Total Ventas se suman los valores de las facturas Fisicas(Tipo Emision F)"""
            total_fact = sum([detalle_ventas['bng'] + detalle_ventas['bi0i'] + detalle_ventas['big'] for detalle_ventas in detalles_ventas if detalle_ventas['tipo'] == '18' and len(detalle_ventas['autorizacion'])==10])
            total_credit = sum([detalle_ventas['bng'] + detalle_ventas['bi0i'] + detalle_ventas['big'] for detalle_ventas in detalles_ventas if detalle_ventas['tipo'] == '04' and len(detalle_ventas['autorizacion'])==10])
            print"total_fact::",total_fact
            print"total_credit::",total_credit
            total_ventas += total_fact - total_credit
                
            #===============================================================
            # ventas_form = doc.createElement("ventas")
            # mainform.appendChild(ventas_form)
            #===============================================================
            for detalle_ventas in detalles_ventas:
                    
                if len(detalle_ventas['autorizacion'])==10:
                    detalle_ventas_form = doc.createElement("detalleVentas")
                    ventas_form.appendChild(detalle_ventas_form)
                    
                    tipo_ident = detalle_ventas['tip']                    
                    print"tipo_ident=%s"%tipo_ident
                
                    if detalle_ventas['ruc'] in ('9999999999999'):
                        tpIdCliente = doc.createElement("tpIdCliente")
                        detalle_ventas_form.appendChild(tpIdCliente)
                        ptpIdCliente = doc.createTextNode('07')
                        tpIdCliente.appendChild(ptpIdCliente)
                    
                    elif len(detalle_ventas['ruc'])==10 and not tipo_ident:
                        tpIdCliente = doc.createElement("tpIdCliente")
                        detalle_ventas_form.appendChild(tpIdCliente)
                        ptpIdCliente = doc.createTextNode('05')
                        tpIdCliente.appendChild(ptpIdCliente)
                        
                    elif len(detalle_ventas['ruc'])==13 and not tipo_ident:
                        tpIdCliente = doc.createElement("tpIdCliente")
                        detalle_ventas_form.appendChild(tpIdCliente)
                        ptpIdCliente = doc.createTextNode('04')
                        tpIdCliente.appendChild(ptpIdCliente)
                                                                  
                    else:
                        tpIdCliente = doc.createElement("tpIdCliente")
                        detalle_ventas_form.appendChild(tpIdCliente)
                        ptpIdCliente = doc.createTextNode(tipo_ident)
                        tpIdCliente.appendChild(ptpIdCliente)
                        
                    
                    
                    
                    if detalle_ventas['ruc']:
                        ruc = ''
                        ruc = detalle_ventas['ruc']
                        ruc = ruc.replace('+','')
                    else:
                        print""
                        raise ValidationError(u'Verificar configuración,datos de ficha cliente incompletos (ruc,tipo_contribuyente etc)')

                    
                    idCliente = doc.createElement("idCliente")
                    detalle_ventas_form.appendChild(idCliente)
                    #pidCliente = doc.createTextNode(ruc)
                    pidCliente = doc.createTextNode(ruc)
                    idCliente.appendChild(pidCliente)
                    
                    """"""
                    if detalle_ventas['ruc'] not in ('9999999999999'):
                        parteRelVtas = doc.createElement("parteRelVtas")
                        detalle_ventas_form.appendChild(parteRelVtas)
                        pparteRelVtas = doc.createTextNode('NO')
                        parteRelVtas.appendChild(pparteRelVtas)
                    """"""
                    """"""
                    if tipo_ident=='06':
                        tipoCliente = doc.createElement("tipoCliente")
                        detalle_ventas_form.appendChild(tipoCliente)
                        ptipoCliente = doc.createTextNode('01')
                        tipoCliente.appendChild(ptipoCliente)
                        
                        
                        partner_id = self.pool.get('res.partner').search(cr, uid, [('ident_num', '=', ruc)])
                        denominacion = self.pool.get('res.partner').browse(cr, uid, partner_id).name
                        print"/////denominacion///// =%s"%denominacion
                    
                        denoCli = doc.createElement("denoCli")
                        detalle_ventas_form.appendChild(denoCli)
                        pdenoCli = doc.createTextNode(str(denominacion))
                        denoCli.appendChild(pdenoCli)
                        
                    """"""    
                    
                    tipo = detalle_ventas['tipo']
                    print"tipo%s"%tipo                             
                    tipoComprobante = doc.createElement("tipoComprobante")
                    detalle_ventas_form.appendChild(tipoComprobante)
                    ptipoComprobante = doc.createTextNode(tipo)
                    tipoComprobante.appendChild(ptipoComprobante)
                    
                    """añadido tag tipoEmision Electronico o Fisico"""
                    num_auto = detalle_ventas['autorizacion']
                    print"num_auto=%s"%num_auto
                    
                    if len(num_auto) > 10:
                        tipoEmision = doc.createElement("tipoEmision")
                        detalle_ventas_form.appendChild(tipoEmision)
                        ptipoEmision = doc.createTextNode('E')
                        tipoEmision.appendChild(ptipoEmision)
                    else:
                        tipoEmision = doc.createElement("tipoEmision")
                        detalle_ventas_form.appendChild(tipoEmision)
                        ptipoEmision = doc.createTextNode('F')
                        tipoEmision.appendChild(ptipoEmision)
                                
                    
                    
                    num_reg = detalle_ventas['numreg']
                    
                    numeroComprobantes = doc.createElement("numeroComprobantes")
                    detalle_ventas_form.appendChild(numeroComprobantes)
                    pnumeroComprobantes = doc.createTextNode(str(num_reg))
                    numeroComprobantes.appendChild(pnumeroComprobantes)
                    
                    base_no_gravada = detalle_ventas['bng']
                    
                    baseNoGraIva = doc.createElement("baseNoGraIva") #Base imponible no objeto de iva
                    detalle_ventas_form.appendChild(baseNoGraIva)
                    pbaseNoGraIva = doc.createTextNode('{0:.2f}'.format(base_no_gravada or 0.0))
                    baseNoGraIva.appendChild(pbaseNoGraIva)
                    
                    base_imponible = detalle_ventas['bi0i']
                    
                    baseImponible = doc.createElement("baseImponible") #Base imponible tarifa 0% iva
                    detalle_ventas_form.appendChild(baseImponible)
                    pbaseImponible = doc.createTextNode('{0:.2f}'.format(base_imponible or 0.0))
                    baseImponible.appendChild(pbaseImponible)
                    
                    base_imponible_gravada = detalle_ventas['big']
                    
                    baseImpGrav = doc.createElement("baseImpGrav") #Base imponible tarifa diferente de 0% iva
                    detalle_ventas_form.appendChild(baseImpGrav)
                    pbaseImpGrav = doc.createTextNode('{0:.2f}'.format(base_imponible_gravada or 0.0))
                    baseImpGrav.appendChild(pbaseImpGrav)
                    print"pbaseImpGravlin572=%s"%pbaseImpGrav
                                     
                    monto_iva = detalle_ventas['mi']
                    
                    montoIva = doc.createElement("montoIva")
                    detalle_ventas_form.appendChild(montoIva)
                    pmontoIva = doc.createTextNode('{0:.2f}'.format(monto_iva))
                    montoIva.appendChild(pmontoIva)
                    
                    monto_ice = detalle_ventas['mice']
                    print" monto_ice =%s"% monto_ice 
                    
                    #if monto_ice == None:
                    montoIce = doc.createElement("montoIce")
                    detalle_ventas_form.appendChild(montoIce)
                    pmontoIce = doc.createTextNode('0.00')
                    montoIce.appendChild(pmontoIce)
                    """else:
                        montoIce = doc.createElement("montoIce")
                        detalle_ventas_form.appendChild(montoIce)
                        pmontoIce = doc.createTextNode('{0:.2f}'.format(monto_ice))
                        montoIce.appendChild(pmontoIce)"""                                 
                    
                    valor_ret_iva = detalle_ventas['vri']
                    
                    valorRetIva = doc.createElement("valorRetIva")
                    detalle_ventas_form.appendChild(valorRetIva)
                    pvalorRetIva = doc.createTextNode('{0:.2f}'.format(valor_ret_iva))
                    valorRetIva.appendChild(pvalorRetIva)
                    
                    valor_ret_renta = detalle_ventas['vrr']
                    
                    valorRetRenta = doc.createElement("valorRetRenta")
                    detalle_ventas_form.appendChild(valorRetRenta)
                    pvalorRetRenta = doc.createTextNode('{0:.2f}'.format(valor_ret_renta))
                    valorRetRenta.appendChild(pvalorRetRenta)
                    
                    partner_id = self.pool.get('res.partner').search(cr, uid, [('ident_num', '=', ruc)])
                    print" partner_id =%s"% partner_id 
                    pago = self.pool.get('res.partner').browse(cr, uid, partner_id)
                    print"pago=%s"%pago.payment_type_customer.code     
                                
                    if pago.payment_type_customer.code ==False and tipo !='04':
                        formasDePago = doc.createElement('formasDePago')
                        detalle_ventas_form.appendChild(formasDePago)
                        formaPago = doc.createElement('formaPago')
                        formasDePago.appendChild(formaPago)
                        pformaPago = doc.createTextNode('20')
                        formaPago.appendChild(pformaPago)
                        
                    if pago.payment_type_customer.code and tipo !='04':
                        formasDePago = doc.createElement('formasDePago')
                        detalle_ventas_form.appendChild(formasDePago)
                        formaPago = doc.createElement('formaPago')
                        formasDePago.appendChild(formaPago)
                        pformaPago = doc.createTextNode(str(pago.payment_type_customer.code))
                        formaPago.appendChild(pformaPago)
                
                
                #===============================================================
                # ventasEstablecimiento = doc.createElement("ventasEstablecimiento")
                # mainform.appendChild(ventasEstablecimiento)    
                #===============================================================
                
            if facturas_ventas and band:
                band = False
                ##genera lista de ventas por compañia
#                 cr.execute('select c.num_establecimiento, sum(i.amount_untaxed) '
#                             'from account_invoice i join res_company c on c.id=i.company_id '
#                             "where i.type='out_invoice' and i.state in ('open', 'paid') and i.id=ANY(%s) "
#                             'group by c.num_establecimiento', (facturas_ventas,))
                            
                
                ##genera lista de ventas por numero de autorizacion (solo se suman las ventas con numero de aut tradicional)
                cr.execute('select a.serie_entidad,sum(i.amount_subtotal) '
                           'from account_journal j,account_invoice i join account_authorisation a on a.id=i.auth_ret_id and i.id=ANY(%s) '
                           "where i.type = 'out_invoice' and i.state in ('open','paid') and j.id=i.journal_id and a.doc_type='custom' "
                           'group by a.serie_entidad', (facturas_ventas,))
                
                result = cr.fetchall()
                print 'result', result
                """if result:
                    for item in result: 
                        ventasEstablecimiento = doc.createElement("ventasEstablecimiento")
                        mainform.appendChild(ventasEstablecimiento)"""
                        
                if result:
                    ventasEstablecimiento = doc.createElement("ventasEstablecimiento")
                    mainform.appendChild(ventasEstablecimiento)
                    for num_estab, total_estab in result:
                        #print 'num_estab',num_estab
                        print 'total_estab',total_estab    
                        ventaEst = doc.createElement("ventaEst")
                        ventasEstablecimiento.appendChild(ventaEst)
                        #print 'total_ventas', total_ventas
                        codEstab = doc.createElement('codEstab')
                        ventaEst.appendChild(codEstab)
                        valventaEst = doc.createTextNode(str(num_estab).zfill(3))
                        codEstab.appendChild(valventaEst)
                    
                        ventasEstab = doc.createElement('ventasEstab')
                        ventaEst.appendChild(ventasEstab)
                        valventaEst = doc.createTextNode('{0:.2f}'.format(total_estab))
                        #valventaEst = doc.createTextNode('{0:.2f}'.format(new_total_ventas))
                        ventasEstab.appendChild(valventaEst)
                else:
                    ventasEstablecimiento = doc.createElement("ventasEstablecimiento")
                    mainform.appendChild(ventasEstablecimiento)
                    ventaEst = doc.createElement("ventaEst")
                    ventasEstablecimiento.appendChild(ventaEst)
                    codEstab = doc.createElement('codEstab')
                    ventaEst.appendChild(codEstab)
                    valventaEst = doc.createTextNode('001')
                    codEstab.appendChild(valventaEst)
                    
                    ventasEstab = doc.createElement('ventasEstab')
                    ventaEst.appendChild(ventasEstab)
                    valventaEst = doc.createTextNode('0.00')
                    ventasEstab.appendChild(valventaEst)
            
            detalles_canceladas = resumen_compra_venta.document_ats_cancel_ids
            if detalles_canceladas:
                anulados_form = doc.createElement("anulados")
                mainform.appendChild(anulados_form)
            for detalle_cancelada in detalles_canceladas:
                #print 'detalle_cancelada',detalle_cancelada      
                #print 'detalle_cancelada.tipo', detalle_cancelada.tipo
                detalle_anuladas_form = doc.createElement("detalleAnulados")
                anulados_form.appendChild(detalle_anuladas_form)
                
                tipoComprobante = doc.createElement("tipoComprobante")
                detalle_anuladas_form.appendChild(tipoComprobante)
                ptipoComprobante = doc.createTextNode(detalle_cancelada.tipo)
                tipoComprobante.appendChild(ptipoComprobante)
                
                establecimiento = doc.createElement("establecimiento")
                detalle_anuladas_form.appendChild(establecimiento)
                pestablecimiento = doc.createTextNode(detalle_cancelada.establecimiento)
                establecimiento.appendChild(pestablecimiento)
                
                puntoEmision = doc.createElement("puntoEmision")
                detalle_anuladas_form.appendChild(puntoEmision)
                ppuntoEmision = doc.createTextNode(detalle_cancelada.punto_emision)
                puntoEmision.appendChild(ppuntoEmision)
                
                secuencialInicio = doc.createElement("secuencialInicio")
                detalle_anuladas_form.appendChild(secuencialInicio)
                psecuencialInicio = doc.createTextNode(detalle_cancelada.secuencial_inicio)
                secuencialInicio.appendChild(psecuencialInicio)
                
                
                secuencialFin = doc.createElement("secuencialFin")
                detalle_anuladas_form.appendChild(secuencialFin)
                psecuencialFin = doc.createTextNode(detalle_cancelada.secuencial_fin)
                secuencialFin.appendChild(psecuencialFin)
                
                autorizacion = doc.createElement("autorizacion")
                detalle_anuladas_form.appendChild(autorizacion)
                pautorizacion = doc.createTextNode(detalle_cancelada.autorizacion)
                autorizacion.appendChild(pautorizacion)
                 
        pfec_mes = doc.createTextNode('{0:.2f}'.format(total_ventas))
        nTotalVentas.appendChild(pfec_mes)
        #cr.fetchall() [(u'001', 324579.15)]
        #print"doc.toxml()=%s"%doc.toxml()
       
        out = base64.encodestring(doc.toxml())
        #print"out=%s"%out
        return self.pool['base.file.report'].show(cr, uid, out, 'ats.xml')
#         return self.write(cr, uid, ids, {'data':out, 'name':'ats.xml', 'state':'generate'})
    

    _columns = {
        'formulario':fields.char('Formulario', size=5),
        'company':fields.many2one('res.company', 'Compania', required=True),
        'version':fields.char('Version Formulario', size=20),
        'data':fields.binary('Archivo', readonly=True),
        'name':fields.char('Nombre', size=20,readonly=True),
        'state' : fields.selection((('init', 'Datos'),
                            ('generate', 'Resultado')), 'Estado', readonly=True),
           
    }
    _defaults = {
        'state': lambda * a: 'init',
        'company': lambda self, cr, uid, ctx: self.pool.get('res.company')._company_default_get(cr, uid)
    }         
   
wizard_generate_file_ats()