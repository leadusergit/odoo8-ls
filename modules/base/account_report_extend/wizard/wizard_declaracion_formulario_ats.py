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


import wizard
import base64
import pooler
import time
from openerp.osv import osv, fields
from xml.dom.minidom import Document


init_form = """<?xml version="1.0"?>
<form string="Asistente para generar el archivo ATS">
      <field name="company" required="1"  colspan="4"/>
      <field name="formulario" required="1"  colspan="4"/>
      <!--field name="version" required="1"  colspan="4"/-->
</form>
"""

form_finish = """<?xml version="1.0"?>
<form string="Generar Formulario ATS">
    <image name="gtk-dialog-info" colspan="2"/>
    <group colspan="2" col="4">
        <separator string="Archivo Generado" colspan="4"/>
        <field name="data" readonly="1" colspan="3"/>
    </group>
</form>"""


init_fields = {
    'formulario':{'string':"Formulario:",'type':'selection','selection':[('ats','ats')]},
    'company' : {'string':'Compania', 'type':'many2one', 'relation':'res.company'}, 
    'version': {'string':'Version Formulario', 'type':'char', 'size': 20,},   
}

finish_fields = {
    'data': {'string':'Archivo', 'type':'binary', 'readonly': True, },
    'name': {'string':'Nombre', 'type':'string', 'readonly': True, },
}

class wizard_declaracion_formulario_ats(wizard.interface):
 
    
     def _generate_file(self, cr, uid, data, context):
        ##print "DATA: ", data
        ##print "CONTEXT: ",context
        id_header = data['id']
        ##print "id_header:",id_header
        id_formulario = data['form']['formulario']
        ##print"id_formulario: ",id_formulario
        version = data['form']['version']
        
        doc = Document()
        
        # Obtener Informacion de la compania
        compania = data['form']['company']
        ##print "compania: ",compania
        lineas = pooler.get_pool(cr.dbname).get('res.company').browse(cr, uid, [compania])[0]
        ##print"lineas:",lineas
        empresa = lineas.partner_id.name
        ##print"empresa:",empresa
        ruc_empresa = lineas.partner_id.ident_num
        ##print "RUC: ", ruc_empresa
        
        mainform = doc.createElement("iva")
        doc.appendChild(mainform)
        
        ruc = doc.createElement("numeroRuc")
        mainform.appendChild(ruc)
        pruc = doc.createTextNode(ruc_empresa.rstrip())
        ruc.appendChild(pruc)
        
        social = doc.createElement("razonSocial")
        mainform.appendChild(social)
        psocial = doc.createTextNode(empresa.rstrip())
        social.appendChild(psocial)
        
        # Obtener fechas
        doc_ats = pooler.get_pool(cr.dbname).get('account.document.ats').browse(cr, uid, [id_header])[0]
        anio_data, mes, dia,  = str(doc_ats.date_start).split("-")
        ##print "dia: ", dia
        ##print "mes: ", mes
        ##print "anio: ", anio_data
        
        fec_anio = doc.createElement("anio")
        mainform.appendChild(fec_anio)
        pfec_anio = doc.createTextNode(anio_data.rstrip())
        fec_anio.appendChild(pfec_anio)
        
        fec_mes = doc.createElement("mes")
        mainform.appendChild(fec_mes)
        pfec_mes = doc.createTextNode(mes.rstrip())
        fec_mes.appendChild(pfec_mes)
        
        compras_form = doc.createElement("compras")
        mainform.appendChild(compras_form)
        
        ventas_form = doc.createElement("ventas")
        mainform.appendChild(ventas_form)
        
        anulados_form = doc.createElement("anulados")
        mainform.appendChild(anulados_form)
         
        #resumencomp = pooler.get_pool(cr.dbname).get('account.document.ats.resumen').search(cr, uid, [('document_ats_resumen_id','=',fechas.id)])
        resumen_doc_compras_ventas = doc_ats.document_ats_resumen_ids
        
        for resumen_compra_venta in resumen_doc_compras_ventas:
            
            detalles_compras = resumen_compra_venta.document_ats_purchase_ids
            for detalle_compras in detalles_compras:
                
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
                pcod_id_prov = doc.createTextNode(detalle_compras.ruc_prov)
                cod_id_prov.appendChild(pcod_id_prov)
                
                
                
                tipoComprobante_c = doc.createElement("tipoComprobante")
                detalle_compras_form.appendChild(tipoComprobante_c)
                ptipoComprobante_c = doc.createTextNode(detalle_compras.cod_tipo_comp)
                tipoComprobante_c.appendChild(ptipoComprobante_c)
                
                
                
                fecha_reg = doc.createElement("fechaRegistro")
                detalle_compras_form.appendChild(fecha_reg)
                pfecha_reg = doc.createTextNode(time.strftime('%d/%m/%Y', time.strptime(detalle_compras.fecha_registro, '%Y-%m-%d')))
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
                pfecha_emi = doc.createTextNode(time.strftime('%d/%m/%Y', time.strptime(detalle_compras.fecha_emision, '%Y-%m-%d')) )
                fecha_emi.appendChild(pfecha_emi)
                
                autorizacion = doc.createElement("autorizacion")
                detalle_compras_form.appendChild(autorizacion)
                pautorizacion = doc.createTextNode(detalle_compras.autorizacion)
                autorizacion.appendChild(pautorizacion)
                
                baseNoGraIva = doc.createElement("baseNoGraIva")
                detalle_compras_form.appendChild(baseNoGraIva)
                pbaseNoGraIva = doc.createTextNode(str('0.00'))
                baseNoGraIva.appendChild(pbaseNoGraIva)
                
                baseImponible = doc.createElement("baseImponible")
                detalle_compras_form.appendChild(baseImponible)
                pbaseImponible = doc.createTextNode(str(round(detalle_compras.base_no_gravada,2)))
                baseImponible.appendChild(pbaseImponible)
                
                baseImpGrav = doc.createElement("baseImpGrav")
                detalle_compras_form.appendChild(baseImpGrav)
                pbaseImpGrav = doc.createTextNode(str(round(detalle_compras.base_imponible_grava,2)))
                baseImpGrav.appendChild(pbaseImpGrav)
                
                montoIce = doc.createElement("montoIce")
                detalle_compras_form.appendChild(montoIce)
                pmontoIce = doc.createTextNode('0.00')
                montoIce.appendChild(pmontoIce)
               
                montoIva = doc.createElement("montoIva")
                detalle_compras_form.appendChild(montoIva)
                pmontoIva = doc.createTextNode(str(round(detalle_compras.monto_iva,2)))
                montoIva.appendChild(pmontoIva)
                
                valorRetBienes = doc.createElement("valorRetBienes")
                detalle_compras_form.appendChild(valorRetBienes)
                pvalorRetBienes = doc.createTextNode(str(round(detalle_compras.valor_retencion_bienes,2)))
                valorRetBienes.appendChild(pvalorRetBienes)
                
                valorRetServicios = doc.createElement("valorRetServicios")
                detalle_compras_form.appendChild(valorRetServicios)
                pvalorRetServicios = doc.createTextNode(str(round(detalle_compras.valor_retencion_servicios,2)))
                valorRetServicios.appendChild(pvalorRetServicios)
                
                valRetServ100 = doc.createElement("valRetServ100")
                detalle_compras_form.appendChild(valRetServ100)
                pvalRetServ100 = doc.createTextNode(str(round(detalle_compras.valor_retencion_servicios_100,2)))
                valRetServ100.appendChild(pvalRetServ100)
                
                air_form = doc.createElement("air")
                detalle_compras_form.appendChild(air_form)
                
                detalle_retenciones = detalle_compras.document_ats_detail_purchase_retention_ids
                
                for detalle_retencion in detalle_retenciones:
                    detalleAir_form = doc.createElement("detalleAir")
                    air_form.appendChild(detalleAir_form)
        
                    codigoRet = doc.createElement("codRetAir")
                    detalleAir_form.appendChild(codigoRet)
                    pcodigoRet = doc.createTextNode(detalle_retencion.codigo_retencion_air)
                    codigoRet.appendChild(pcodigoRet)
                    
                    baseImp = doc.createElement("baseImpAir")
                    detalleAir_form.appendChild(baseImp)
                    pbaseImp = doc.createTextNode(str(round(detalle_retencion.base_imponible_air,2)))
                    baseImp.appendChild(pbaseImp)
                    
                    porcentajeRet = doc.createElement("porcentajeAir")
                    detalleAir_form.appendChild(porcentajeRet)
                    pporcentajeRet = doc.createTextNode(str(detalle_retencion.porcentaje_air))
                    porcentajeRet.appendChild(pporcentajeRet)
                    
                    valorRet = doc.createElement("valRetAir")
                    detalleAir_form.appendChild(valorRet)
                    pvalorRet = doc.createTextNode(str(round(detalle_retencion.valor_retencion,2)))
                    valorRet.appendChild(pvalorRet)
                    
                
               
                
                
                
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
                pautRetencion1 = doc.createTextNode(str(detalle_compras.autorizacion_retencion))
                pautRetencion1 = doc.createTextNode(str(detalle_compras.invoice_id.ret_id.authorization_number_offline or detalle_compras.invoice_id.ret_id.authorization_number))
                #autRetencion1.appendChild(pautRetencion1)
                
                fechaEmiRet1 = doc.createElement("fechaEmiRet1")
                detalle_compras_form.appendChild(fechaEmiRet1)
                pfechaEmiRet1 = doc.createTextNode(str(detalle_compras.fecha_emision_retencion))    
                fechaEmiRet1.appendChild(pfechaEmiRet1)
                
                estabRetencion2 = doc.createElement("estabRetencion2")
                detalle_compras_form.appendChild(estabRetencion2)
                pestabRetencion2 = doc.createTextNode(str('000'))
                estabRetencion2.appendChild(pestabRetencion2)
                
                ptoEmiRetencion2 = doc.createElement("ptoEmiRetencion2")
                detalle_compras_form.appendChild(ptoEmiRetencion2)
                pptoEmiRetencion2 = doc.createTextNode(str('000'))
                ptoEmiRetencion2.appendChild(pptoEmiRetencion2)
                
                secRetencion2 = doc.createElement("secRetencion2")
                detalle_compras_form.appendChild(secRetencion2)
                psecRetencion2 = doc.createTextNode(str('0'))
                secRetencion2.appendChild(psecRetencion2)
                
                autRetencion2 = doc.createElement("autRetencion2")
                detalle_compras_form.appendChild(autRetencion2)
                pautRetencion2 = doc.createTextNode(str('000'))
                autRetencion2.appendChild(pautRetencion2)
                
                fechaEmiRet2 = doc.createElement("fechaEmiRet2")
                detalle_compras_form.appendChild(fechaEmiRet2)
                pfechaEmiRet2 = doc.createTextNode(str('00/00/0000'))
                fechaEmiRet2.appendChild(pfechaEmiRet2)
                
                
                docModificado = doc.createElement("docModificado")
                detalle_compras_form.appendChild(docModificado)
                pdocModificado = doc.createTextNode(str('0'))
                docModificado.appendChild(pdocModificado)
                
                estabModificado = doc.createElement("estabModificado")
                detalle_compras_form.appendChild(estabModificado)
                pestabModificado = doc.createTextNode(str('000'))
                estabModificado.appendChild(pestabModificado)
                
                ptoEmiModificado = doc.createElement("ptoEmiModificado")
                detalle_compras_form.appendChild(ptoEmiModificado)
                pptoEmiModificado = doc.createTextNode(str('000'))
                ptoEmiModificado.appendChild(pptoEmiModificado)
               
                secModificado = doc.createElement("secModificado")
                detalle_compras_form.appendChild(secModificado)
                psecModificado = doc.createTextNode(str('0'))
                secModificado.appendChild(psecModificado)
                
                
                autModificado = doc.createElement("autModificado")
                detalle_compras_form.appendChild(autModificado)
                pautModificadoo = doc.createTextNode(str('0000000000'))
                autModificado.appendChild(pautModificadoo)

                
            
            resumen_compra_venta_id = resumen_compra_venta.id
            
            sql = "select \
                tipo_id_prov as tip,ruc_prov as ruc, codigo_sustento as tipo,count(1) as numreg, sum(base_no_gravada) as bng, sum(base_imponible) as bi, \
                sum(base_imponible_grava) as big, sum(monto_iva) as mi, sum(valor_ret_iva) as vri, sum(valor_ret_renta) as vrr \
                from account_document_ats_detail_sale \
                where document_ats_resumen_sale_id = %s \
                group by ruc_prov, codigo_sustento,tipo_id_prov \
                order by codigo_sustento"%(resumen_compra_venta_id)
            
            
            cr.execute(sql)
            detalles_ventas = cr.dictfetchall()
            
            if detalles_ventas:

                for detalle_ventas in detalles_ventas:
                    
                    detalle_ventas_form = doc.createElement("detalleVentas")
                    ventas_form.appendChild(detalle_ventas_form)
                    
                    tipo_ident = detalle_ventas['tip']
                    
                    tpIdCliente = doc.createElement("tpIdCliente")
                    detalle_ventas_form.appendChild(tpIdCliente)
                    ptpIdCliente = doc.createTextNode(tipo_ident)
                    tpIdCliente.appendChild(ptpIdCliente)
                    
                    ruc = detalle_ventas['ruc']
                    
                    idCliente = doc.createElement("idCliente")
                    detalle_ventas_form.appendChild(idCliente)
                    pidCliente = doc.createTextNode(ruc)
                    idCliente.appendChild(pidCliente)
                    
                    tipo = detalle_ventas['tipo']
                    
                    tipoComprobante = doc.createElement("tipoComprobante")
                    detalle_ventas_form.appendChild(tipoComprobante)
                    ptipoComprobante = doc.createTextNode(tipo)
                    tipoComprobante.appendChild(ptipoComprobante)
                    
                    num_reg = detalle_ventas['numreg']
                    
                    numeroComprobantes = doc.createElement("numeroComprobantes")
                    detalle_ventas_form.appendChild(numeroComprobantes)
                    pnumeroComprobantes = doc.createTextNode(str(num_reg))
                    numeroComprobantes.appendChild(pnumeroComprobantes)
                    
                    base_no_gravada = detalle_ventas['bng']
                    
                    baseNoGraIva = doc.createElement("baseNoGraIva")
                    detalle_ventas_form.appendChild(baseNoGraIva)
                    pbaseNoGraIva = doc.createTextNode(str(round(base_no_gravada,2)))
                    baseNoGraIva.appendChild(pbaseNoGraIva)
                    
                    base_imponible = detalle_ventas['bi']
                    
                    baseImponible = doc.createElement("baseImponible")
                    detalle_ventas_form.appendChild(baseImponible)
                    pbaseImponible = doc.createTextNode(str(round(base_imponible,2)))
                    baseImponible.appendChild(pbaseImponible)
                    
                    base_imponible_gravada = detalle_ventas['big']
                    
                    baseImpGrav = doc.createElement("baseImpGrav")
                    detalle_ventas_form.appendChild(baseImpGrav)
                    pbaseImpGrav = doc.createTextNode(str(round(base_imponible_gravada,2)))
                    baseImpGrav.appendChild(pbaseImpGrav)
                    
                    monto_iva = detalle_ventas['mi']
                    
                    montoIva = doc.createElement("montoIva")
                    detalle_ventas_form.appendChild(montoIva)
                    pmontoIva = doc.createTextNode(str(round(monto_iva,2)))
                    montoIva.appendChild(pmontoIva)
                    
                    valor_ret_iva = detalle_ventas['vri']
                    
                    valorRetIva = doc.createElement("valorRetIva")
                    detalle_ventas_form.appendChild(valorRetIva)
                    pvalorRetIva = doc.createTextNode(str(valor_ret_iva))
                    valorRetIva.appendChild(pvalorRetIva)
                    
                    valor_ret_renta = detalle_ventas['vrr']
                    
                    valorRetRenta = doc.createElement("valorRetRenta")
                    detalle_ventas_form.appendChild(valorRetRenta)
                    pvalorRetRenta = doc.createTextNode(str(valor_ret_renta))
                    valorRetRenta.appendChild(pvalorRetRenta)
                    
        
            detalles_canceladas = resumen_compra_venta.document_ats_cancel_ids
            for detalle_cancelada in detalles_canceladas:
                                
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
                 
         
        out = base64.encodestring(doc.toxml())
        if (id_formulario=='ats'):
            return {'data' : out, 'name' : 'Formulario_A.T.S.xml'}

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
    
wizard_declaracion_formulario_ats('wizard.declaracion.formulario.ats')
