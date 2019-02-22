# -*- coding: utf-8 -*-
##############################################################################
#
#    Atikasoft Cia. Ltda
#    Copyright (C) 2004-2009 
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

__author__ = 'vllumiquinga@atikasoft.com.ec (Vinicio Ll.)'

import time
import datetime
from openerp.osv import osv, fields
from mx import DateTime
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime
from itertools import izip
#from openerp import tools, api
#from openerp import models, fields, api

class wizard_generate_ats(osv.osv_memory):
    _name = "wizard.generate.ats"
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def _generate_info_header(self, cr, uid, data):
        date_ini = data['form']['date_start']
        date_fin = data['form']['date_finish']
        
        res = {
                'numero_compras':0,
                'monto_compras':0,
                'numero_ventas':0,
                'monto_ventas':0,
                'base_no_gravada':0,
                'base_imponible':0,
                'date_start':date_ini,
                'date_finish':date_fin
        }
        return res
        

    def _numero_compras(self, cr, uid, data):
        company_id = str(data['form']['company_id'][0])
        query = "select count(*) \
                from account_invoice \
                where type in ('in_invoice') \
                and tipo_factura not in ('anticipos') and company_id="+company_id

        cr.execute(query)
        res = cr.dictfetchall()
        return res[0]['count']
    
    def _numero_ventas(self, cr, uid, data):
        company_id = str(data['form']['company_id'][0])
        query = "select count(*) \
                from account_invoice \
                where type in ('in_invoice') \
                and tipo_factura not in ('anticipos') and company_id="+company_id

        cr.execute(query)
        res = cr.dictfetchall()
        return res[0]['count']    
        
    def _monto_compras(self, cr, uid, data):
        company_id = str(data['form']['company_id'][0])
        query = "select count(*) \
                from account_invoice \
                where type in ('in_invoice') \
                and tipo_factura not in ('anticipos') and company_id="+company_id
        cr.execute(query)
        res = cr.dictfetchall()
        return res[0]['count']
    
    def _monto_ventas(self, cr, uid, data):
        company_id = str(data['form']['company_id'][0])
        query = "select count(*) \
                from account_invoice \
                where type in ('in_invoice') \
                and tipo_factura not in ('anticipos') and company_id="+company_id
        cr.execute(query)
        res = cr.dictfetchall()
        return res[0]['count']
    
    def _base_no_gravada(self, cr, uid, ids, data, context):
        
        date_ini = data['form']['date_start']
        date_fin = data['form']['date_finish']
        company_id = str(data['form']['company_id'][0])
        
        res = 0
        
        query = "select sum(ait.base) as base_no_gravada \
        from account_invoice ai \
        JOIN account_invoice_tax ait ON (ai.id = ait.invoice_id) \
        where \
        ai.type = 'in_invoice' \
        and ai.tipo_factura not in ('anticipo') \
        and ai.state in ('open','paid') \
        and ai.date_invoice <= '" + date_fin + "' \
        and ai.date_invoice >= '" + date_ini + "' and ai.company_id="+company_id +" \
        and ai.tipo_factura = 'invoice' \
        and ait.tax_group = 'vat0'"
        
        cr.execute(query)
        base_no_gravada = cr.dictfetchall()[0]['base_no_gravada']
        if not base_no_gravada:
            return res
        else:
            return base_no_gravada[0]['base_no_gravada']    

    def _base_imponible(self, cr, uid, ids, data, context):
        
        date_ini = data['form']['date_start']
        date_fin = data['form']['date_finish']
        company_id = str(data['form']['company_id'][0])
        
        query = "select sum(ait.base) as base_imponible\
        from account_invoice ai \
        JOIN account_invoice_tax ait ON (ai.id = ait.invoice_id) \
        where \
        ai.type = 'in_invoice' \
        and ai.tipo_factura not in ('anticipo') \
        and ai.state in ('open','paid') \
        and ai.date_invoice <= '" + date_fin + "' \
        and ai.date_invoice >= '" + date_ini + "' and ai.company_id="+company_id +" \
        and ai.tipo_factura = 'invoice' \
        and ait.tax_group = 'vat'"

        cr.execute(query)
        base_imponible = cr.dictfetchall()[0]['base_imponible']
        if not base_imponible:
            return res
        else:
            return base_imponible


    def get_impuesto_code_base(self,cr,uid,ids,code,company):
        
        print"code156=%s"%code
        base_code = ''
        sql = "select code \
        from account_tax_code \
        where company_id = %s and id in  (select base_code_id \
                     from account_tax at \
                     where description = '%s')" % (company,code)
        
        cr.execute(sql)
        res_taxes = cr.dictfetchall()  
        for res_tax in res_taxes:
            base_code = res_tax['code'] 
        print"base_code167=%s"%base_code       
        
        return base_code

#ejecuta resumen
    def _generate_info(self, cr, uid, ids, data, context):
        
        val_resumen = {}
        val_detalle = {}
        date_ini = data['form']['date_start']
        date_fin = data['form']['date_finish']
        #multicompania
        company_id = str(data['form']['company_id'][0])
        #print 'company_id',company_id
        
        
        invoice_obj = self.pool.get('account.invoice')
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
        
        val_anulado_cr = {}
        
        
        #Validar en la cabecera del document ats
        document_ats_ids = document_ats_obj.search(cr, uid, [('date_finish', '=', date_fin), ('date_start', '=', date_ini)])
        if document_ats_ids:
            document_ats_purchase_ids = document_ats_resumen_obj.search(cr, uid, [('document_ats_resumen_id', 'in', document_ats_ids)])
            document_ats_resumen_obj.unlink(cr, uid, document_ats_purchase_ids)
            document_ats_sale_ids = document_ats_resumen_obj.search(cr, uid, [('document_ats_resumen_id', 'in', document_ats_ids)])
            document_ats_resumen_obj.unlink(cr, uid, document_ats_sale_ids)
            document_ats_obj.unlink(cr, uid, document_ats_ids)

        #obtener cabecera compras
        vals_cab = self._generate_info_header(cr, uid, data)
        
        #=======================================================================
        # Compras
        #=======================================================================
        query = "select count(1) as numero, tipo_factura, sum(t_b_excenta_iva) as tarifa_cero, type, \
                    sum(t_bi_iva) as tarifa_doce,sum(t_iva) as iva \
                    from account_invoice \
                    where type in ('in_invoice','in_refund') \
                    and auth_inv_id is not NULL \
                    and tipo_factura not in ('anticipo') \
                    and tipo_factura is not null \
                    and state in ('open','paid') \
                    and date_invoice <= '" + date_fin + "' and date_invoice >= '" + date_ini +"' and company_id ="+company_id+" \
                    group by tipo_factura, type "
                    
        #print "compras", query
        cr.execute(query)
        res_compras = cr.dictfetchall()

        resumen_line = []
                 
        for compra in res_compras:
            #print '###########compra#########', compra  
            val_resumen = {
                'codigo':'01',
                'documento':compra['tipo_factura'],
                'type':compra['type'],
                'numero_documento':compra['numero'],
                'base_imponible_tarifa_cero':compra['tarifa_cero'],
                'base_imponible_tarifa_doce':compra['tarifa_doce'],
                'valor_iva':compra['iva'],
            }
            fila = (0, 0, val_resumen)
            resumen_line.append(fila)
            #===========================================================================
            # #detalle compras
            #===========================================================================
            
            if compra['tipo_factura'] != 'gas_no_dedu':
                
                query = "select ai.emission_date as fecha_fac, ai.tipo_factura, aa.serie_entidad as entidad, aa.serie_emision as emision,\
                        ai.number_inv_supplier as num_fac,ai.date_invoice as fec_emi, aa.name as aut, ai.id as fac_id, ai.t_iva as fac_iva,\
                        ai.id as invoice_id, ai.origin as ori, ai.ret_id as ret_id, rp.ident_num as ruc, ai.t_b_0_iva as bi0i, ai.t_b_no_iva as bini,ai.t_b_excenta_iva as bng,ai.t_bi_iva as big,ai.t_iva as mi, ai.t_ret_iva as ri, ai.amount_subtotal as sub, \
                        ai.cod_sustento as cod_sustento \
                        from account_invoice ai,\
                             account_authorisation aa,\
                             res_partner rp \
                     where ai.type = '" + compra['type'] + "'\
                        and rp.id = ai.partner_id \
                        and ai.auth_inv_id = aa.id \
                        and ai.tipo_factura not in ('anticipo') \
                        and ai.tipo_factura is not null \
                        and ai.state in ('open','paid') \
                        and ai.date_invoice <= '" + date_fin + "' \
                        and ai.date_invoice >= '" + date_ini + "' and ai.company_id ="+company_id+" \
                        and ai.tipo_factura = '" + compra['tipo_factura'] + "' ORDER BY ai.id"
            else:
                
                query = "select ai.emission_date as fecha_fac, ai.tipo_factura,\
                        '' as entidad, '' as emision,ai.number_inv_supplier as num_fac,ai.date_invoice as fec_emi, '' as aut,ai.id as fac_id, \
                        ai.id as invoice_id, ai.t_iva as fac_iva,ai.origin as ori, ai.ret_id as ret_id, rp.ident_num as ruc, ai.t_b_0_iva as bi0i, ai.t_b_no_iva as bini, ai.t_b_excenta_iva as bng,ai.t_bi_iva as big,ai.t_iva as mi, ai.t_ret_iva as ri, ai.amount_subtotal as sub, \
                        ai.cod_sustento as cod_sustento \
                        from account_invoice ai, res_partner rp \
                        where ai.type = '" + compra['type'] + "'\
                        and ai.state in ('open','paid') \
                        and rp.id = ai.partner_id \
                        and ai.date_invoice <= '" + date_fin + "' \
                        and ai.date_invoice >= '" + date_ini + "' and ai.company_id ="+company_id+" \
                        and ai.tipo_factura = '" + compra['tipo_factura'] + "' \
                        and ai.tipo_factura is not null \
                        and ai.tipo_factura not in ('anticipo') order by ai.id"
            
            cr.execute(query)
            #print 'Por tipo de factura',query
            res_compras_detalle = cr.dictfetchall()
            compras_line = []
            for detalle_compra in res_compras_detalle:
                identificacion_prov = detalle_compra['ruc']
                #print 'identificacion_prov', identificacion_prov
                if not identificacion_prov:
                    raise osv.except_osv((u'Información'), ('El proveedor de la factura Nro: '+str(detalle_compra['num_fac']))+' no tiene registrado un ruc! Llenelo para continuar')
                sql = "select ident_type from res_partner where ident_num = '%s'" % (identificacion_prov)
                cr.execute(sql)
                proveedor = cr.dictfetchall()
                codigo_tipo = proveedor[0]['ident_type']
                tipo = ''
                if codigo_tipo == 'r':
                    tipo = '01'
                elif codigo_tipo == 'p':
                    tipo = '03'
                elif codigo_tipo == 'c':
                    tipo = '02'
                cod_tip_comp = ''
                if compra['tipo_factura'] == 'purchase_liq' and compra['type'] == 'in_invoice':
                    cod_tip_comp = '03'
                elif compra['tipo_factura'] == 'invoice' and compra['type'] == 'in_invoice':
                    cod_tip_comp = '01'
                elif compra['tipo_factura'] == 'invoice' and compra['type'] == 'in_refund':
                    cod_tip_comp = '04'
                elif compra['tipo_factura'] == 'sales_note' and compra['type'] == 'in_invoice':
                    cod_tip_comp = '02'
                elif compra['tipo_factura'] == 'alicuota' and compra['type'] == 'in_invoice':
                    cod_tip_comp = '19'
                elif compra['tipo_factura'] == 'ticket_aereo' and compra['type'] == 'in_invoice':
                    cod_tip_comp = '11'
                elif compra['tipo_factura'] == 'comp_venta_ext' and compra['type'] == 'in_invoice':
                    cod_tip_comp = '15' 
                elif compra['tipo_factura'] == 'reembolso' and compra['type'] == 'in_invoice':
                    cod_tip_comp = '41'
                elif compra['tipo_factura'] == 'reembolso' and compra['type'] == 'out_refund':
                    cod_tip_comp = '04'
                elif compra['tipo_factura'] == 'gasto_viaje' and compra['type'] == 'in_invoice':
                    cod_tip_comp = '41'
                #dc#ats tag <tipoComprobante>cod_tip_comp </tipoComprobante>
                elif compra['tipo_factura'] == 'gasto_financiero' and compra['type'] == 'in_invoice':
                    cod_tip_comp = '12' 
                elif compra['tipo_factura'] == 'gasto_financiero' and compra['type'] == 'in_refund':
                    cod_tip_comp = '12'                      
                elif compra['tipo_factura'] == 'doc_inst_est' and compra['type'] == 'in_invoice':
                    cod_tip_comp = '20' 
                elif compra['tipo_factura'] == 'doc_inst_est' and compra['type'] == 'in_refund':
                    cod_tip_comp = '20'             
                
                codigo_sustento = detalle_compra['cod_sustento']
                
                print"detalle_compra['mi']=%s"%detalle_compra['mi']
                
                if detalle_compra['mi']>0 and detalle_compra['big']>0:
                    #valor=detalle_compra['bini']
                    valor1=detalle_compra['bng']
                else:
                    #valor=detalle_compra['sub']
                    valor1=detalle_compra['sub']
                                   
                val_detalle = {                   
                    'codigo_sustento':codigo_sustento,
                    'tipo_id_prov':tipo,
                    'cod_tipo_comp':cod_tip_comp,
                    'invoice_id':detalle_compra['invoice_id'],
                    'ruc_prov':detalle_compra['ruc'],
                    'tipo':detalle_compra['tipo_factura'],
                    'fecha_registro':detalle_compra['fecha_fac'],
                    'autorizacion_establecimiento':detalle_compra['entidad'],
                    'autorizacion_punto_emision':detalle_compra['emision'],
                    'secuencial_factura':detalle_compra['num_fac'],
                    'fecha_emision':detalle_compra['fec_emi'],
                    'autorizacion':detalle_compra['aut'],
                    'documento_modificado':'0',
                    'establecimiento_modificado':'000',
                    'emision_modificado':'000',
                    'secuencial_modificado':'0000000',
                    'autorizacion_modificado':'0000000000',
                    #'base_no_gravada':detalle_compra['bng'],
                    'base_no_gravada':valor1,
                    'base_imponible':detalle_compra['sub'],
                    'base_imponible_grava':detalle_compra['big'],
                    'base_imponible_0_iva':detalle_compra['bi0i'],
                    'base_imponible_no_iva':detalle_compra['bini'],
                    #'base_imponible_no_iva':valor,
                    'monto_iva':detalle_compra['mi']

                }
                
                
                #Retenciones==========================
                factura_id = detalle_compra['fac_id']
                
                cr.execute('SELECT ait.name AS name, ait.tax_group AS tax_group, atc.code AS tax_code, '
                           '    ait.tax_amount AS tax_amount, ait.base_amount AS ba '
                           'FROM account_invoice_tax ait LEFT JOIN account_tax_code atc ON atc.id=ait.tax_code_id '
                           'WHERE ait.invoice_id=%s and ait.company_id=%s', (factura_id, company_id))
                
                codigo_impuesto_721 = 0.00
                codigo_impuesto_723 = 0.00
                codigo_impuesto_725 = 0.00
                codigo_impuesto_50 = 0.00
                codigo_impuesto_727 = 0.00
                codigo_impuesto_729 = 0.00
                
                if detalle_compra['ri'] == 0:
                    #se inicializan las variables
                    val_detalle['valor_retencion_bien10'] = 0
                    val_detalle['valor_retencion_serv20'] = 0
                    val_detalle['valor_retencion_bienes'] = 0
                    val_detalle['valor_retencion_serv50'] = 0
                    val_detalle['valor_retencion_servicios'] = 0
                    val_detalle['valor_retencion_servicios_100'] = 0
                   
                    
                    
                    account_invoice_taxes = cr.dictfetchall()
                    retent_line = []
                    for account_invoice_taxe in account_invoice_taxes:
                        grupo = account_invoice_taxe['tax_group']
                        codigo_impuesto = account_invoice_taxe['tax_code']or account_invoice_taxe['name'][:5] 
                        print "codigo_impuesto377=%s"%codigo_impuesto
                        if grupo in ('ret_ir', 'no_ret_ir'):
                            
                            base_amount = account_invoice_taxe['ba']
                            tax_amount = 0.0 
                            if account_invoice_taxe['tax_amount'] < 0: 
                                tax_amount = (-1) * account_invoice_taxe['tax_amount'] 
                            else: 
                                tax_amount = account_invoice_taxe['tax_amount'] 
                            
                            porcentaje = (float)(round(((round((tax_amount / base_amount), 2)) * 100), 2))
                             
                            if codigo_impuesto == '322':
                                base_res = base_amount * (0.10)
                            else:
                                base_res = base_amount
                            
                            #if factura_id == 13599:
                            base_code = self.get_impuesto_code_base(cr, uid, ids, codigo_impuesto,company_id)
                            print "base_code395=%s"%self.get_impuesto_code_base(cr, uid, ids, codigo_impuesto,company_id)
                            if base_code:
                                codigo_impuesto = base_code
                               
                                
                            val_retent = {
                                    'codigo_retencion_air':codigo_impuesto.strip(),
                                    'base_imponible_air':base_res,
                                    'porcentaje_air':porcentaje,
                                    'valor_retencion':tax_amount,
                            }
                                                           
                            fila_ret = (0, 0, val_retent)
                            retent_line.append(fila_ret)            
                            val_detalle['document_ats_detail_purchase_retention_ids'] = retent_line
                            
                    
                else:
                    
                    account_invoice_taxes = cr.dictfetchall()
                    retent_line = []
                    for account_invoice_tax in account_invoice_taxes:
                        grupo = account_invoice_tax['tax_group']
                        codigo_impuesto = account_invoice_tax['tax_code'] or account_invoice_tax['name'][:5]
                        print"codigo_impuesto419=%s"%codigo_impuesto     
                        
                        if codigo_impuesto == '721':#corresponde al 10%
                            codigo_impuesto_721 = (account_invoice_tax['tax_amount'] * (-1))
                            print"codigo_impuesto_721=%s"%codigo_impuesto_721
                            #val_detalle['valor_retencion_bienes'] = (account_invoice_tax['tax_amount'] * (-1))
                            #val_detalle['valor_retencion_servicios'] = 0
                            #val_detalle['valor_retencion_servicios_100'] = 0
                            
                        elif codigo_impuesto == '723':#corresponde al 20%
                            codigo_impuesto_723 = (account_invoice_tax['tax_amount'] * (-1))
                            print"codigo_impuesto_723=%s"%codigo_impuesto_723
                            #val_detalle['valor_retencion_servicios'] = (account_invoice_tax['tax_amount'] * (-1))
                            #val_detalle['valor_retencion_bienes'] = 0
                            #val_detalle['valor_retencion_servicios_100'] = 0                            
                        elif codigo_impuesto == '725':#corresponde al 30%
                            codigo_impuesto_725 = (account_invoice_tax['tax_amount'] * (-1))
                            print"codigo_impuesto_725=%s"%codigo_impuesto_725
                            #val_detalle['valor_retencion_servicios_100'] = (account_invoice_tax['tax_amount'] * (-1))
                        elif codigo_impuesto == '726':#corresponde al 30%
                            codigo_impuesto_50 = (account_invoice_tax['tax_amount'] * (-1))
                            print"codigo_impuesto_50=%s"%codigo_impuesto_50
                               
                        elif codigo_impuesto == '729':#corresponde al 70%
                            codigo_impuesto_727 = (account_invoice_tax['tax_amount'] * (-1))
                            print"codigo_impuesto_727=%s"%codigo_impuesto_727
                        
                        elif codigo_impuesto == '731':#corresponde al 100%
                            codigo_impuesto_729 = (account_invoice_tax['tax_amount'] * (-1))
                            print"codigo_impuesto_729=%s"%codigo_impuesto_729
                            
                          
                        if grupo in ('ret_ir', 'no_ret_ir'):
                            
                            
                            base_amount = account_invoice_tax['ba']
                            tax_amount = 0.0 
                            if account_invoice_tax['tax_amount'] < 0: 
                                tax_amount = (-1) * account_invoice_tax['tax_amount'] 
                            else: 
                                tax_amount = account_invoice_tax['tax_amount'] 
                            
                            porcentaje = (float)(round(((round((tax_amount / base_amount), 2)) * 100), 2))
                                 
                            if codigo_impuesto == '322':
                                base_res = base_amount * (0.10)
                            else:
                                base_res = base_amount
                            
                            base_code = self.get_impuesto_code_base(cr, uid, ids, codigo_impuesto,company_id)
                            print "base_code458=%s"%base_code
                            if base_code:
                                codigo_impuesto = base_code
                            
                            val_retent = {
                                    #strip() elimina espacios en blanco a la izq y derecha de la cadena
                                    'codigo_retencion_air':codigo_impuesto.strip(),
                                    'base_imponible_air':base_res,
                                    'porcentaje_air':porcentaje,
                                    'valor_retencion':tax_amount,
                            }
                                
                            fila_ret = (0, 0, val_retent)
                            retent_line.append(fila_ret)
            
                            val_detalle['document_ats_detail_purchase_retention_ids'] = retent_line                       
                    
                    #si alguna de las variables contiene un valor mayor a 0 este se guarda en el campo correspondiente    
                    val_detalle['valor_retencion_servicios_100'] = codigo_impuesto_729 or 0.00
                    val_detalle['valor_retencion_servicios'] = codigo_impuesto_727 or 0.00
                    val_detalle['valor_retencion_serv50'] = codigo_impuesto_50 or 0.00
                    val_detalle['valor_retencion_bienes'] = codigo_impuesto_725 or 0.00 
                    val_detalle['valor_retencion_serv20'] = codigo_impuesto_723 or 0.00 
                    val_detalle['valor_retencion_bien10'] = codigo_impuesto_721 or 0.00 
                       
                       
                
                sql_retention = "select aa.serie_entidad as sen, aa.serie_emision as sem,aa.name as aut, air.fecha as fec, ai.ret_id as ret_id \
                from account_invoice ai,account_authorisation aa, account_invoice_retention air \
                where \
                ai.company_id=%s \
                and ai.auth_ret_id = aa.id \
                and ai.ret_id = air.id \
                and ai.id = %s" % (company_id, factura_id)
                #,air.fe_auth_key as aut_fe, air.fe_id as sec_fe
                cr.execute(sql_retention)
                #RET/2015/0081
                #RTEP&/2015/0599 
                #RTORA/2015/0020
                account_invoice_retentions = cr.dictfetchall()
                rentencion_obj = self.pool.get('account.invoice.retention')
                if account_invoice_retentions:
                
                    for account_invoice_retention in account_invoice_retentions:    
                        val_detalle['establecimiento_retencion'] = account_invoice_retention['sen'] 
                        val_detalle['emision_retencion'] = account_invoice_retention['sem']
                        
                        ret_info = rentencion_obj.browse(cr, uid,account_invoice_retention['ret_id'])
                        secuencia = ret_info.name
                        if secuencia and secuencia[:3]=='RET':
                            secuencia = secuencia[9:]
                        
                        if secuencia and secuencia[:2]=='RT':
                            secuencia = secuencia[11:]
                        #print 'secuencia', secuencia
                        #print 'account_invoice_retention', 
                        if hasattr(ret_info, 'fe_id') and ret_info.fe_nro_comprobante:
                            secuencia = ret_info.fe_nro_comprobante
                            
                        val_detalle['secuencial_retencion'] = secuencia
                        
                        auth = account_invoice_retention['aut']
                        if hasattr(ret_info, 'fe_auth_key') and ret_info.fe_auth_key:
                            auth = ret_info.fe_auth_key
                        
                        val_detalle['autorizacion_retencion'] = auth
                        val_detalle['fecha_emision_retencion'] = str(time.strftime('%d/%m/%Y', time.strptime(account_invoice_retention['fec'], '%Y-%m-%d'))) 
                        
                else:
                    val_detalle['establecimiento_retencion'] = '000' 
                    val_detalle['emision_retencion'] = '000'
                    val_detalle['secuencial_retencion'] = '0'
                    val_detalle['autorizacion_retencion'] = '000'
                    val_detalle['fecha_emision_retencion'] = '00/00/0000'
                                
                #print 'val_detalle', val_detalle
                fila_compras = (0, 0, val_detalle)
                compras_line.append(fila_compras)
            val_resumen['document_ats_purchase_ids'] = compras_line
        
        
        #=======================================================================
        # #Ventas
        #=======================================================================
        query = "select count(1) as numero, tipo_factura, sum(t_b_excenta_iva) as tarifa_cero,type, \
                    sum(t_bi_iva) as tarifa_doce,sum(t_iva) as iva ,type\
                    from account_invoice \
                    where type = 'out_invoice' \
                    and state in ('open','paid') \
                    and date_invoice <= '" + date_fin + "' and date_invoice >= '" + date_ini +"' and company_id ="+company_id+" \
                    group by tipo_factura, type "
        cr.execute(query)
        res_ventas = cr.dictfetchall()
        for venta in res_ventas:
            val_resumen = {
                'codigo':'01',
                'documento':venta['tipo_factura'],
                'type':venta['type'],
                'numero_documento':venta['numero'],
                'base_imponible_tarifa_cero':venta['tarifa_cero'],
                'base_imponible_tarifa_doce':venta['tarifa_doce'],
                'valor_iva':venta['iva'],
            }
            fila = (0, 0, val_resumen)
            resumen_line.append(fila)
        vals_cab['document_ats_resumen_ids'] = resumen_line
        
        #======================================================================
        # Valores facturas ventas
        #======================================================================t_bi_iva
        query = "select  ai.tipo_factura,"\
                "ai.t_b_no_iva as tarifa_cero,"\
                "ai.id as invoice_id,"\
                "ai.t_b_0_iva as bi0i,"\
                "ai.date_invoice as date,"\
                "ai.num_retention as factura,"\
                "ai.t_bi_iva as tarifa_doce,"\
                "ai.t_iva as iva,"\
                "ret.ret_ir as ret_renta,"\
                "ai.type,"\
                "rp.ident_num as ruc,"\
                "aa.name as autorizacion,"\
                "aa.serie_emision as emision,"\
                "ret.ath_sri as emision_retencion,"\
                "ret.nro_retencion as retencion,"\
                "ret.broadcast_date as date_retencion,rp.ident_type as it, ret.ret_vat as ri "\
                "from account_invoice as ai "\
                "LEFT JOIN res_partner rp on (ai.partner_id=rp.id) "\
                "LEFT JOIN account_authorisation aa on (ai.auth_ret_id=aa.id) "\
                "LEFT JOIN account_invoice_retention_voucher ret on (ai.ret_voucher_id=ret.id) "\
                "where ai.type = 'out_invoice' "\
                "and ai.state in ('open','paid') "\
                "and ai.date_invoice <= '" + date_fin + "' and ai.date_invoice >= '" + date_ini + "' "\
                "and ai.company_id ="+company_id +" "\
                "--and ret.state ='valid' "
        
        cr.execute(query)
        res_venta_detalle = cr.dictfetchall()
        ventas_line = []
        for detalle_ventas in res_venta_detalle:
            
            
            codigo_tipo = detalle_ventas['it']
            tipo = ''
            if codigo_tipo == 'r':
                tipo = '04'
            elif codigo_tipo == 'p':
                tipo = '06'
            elif codigo_tipo == 'c':
                tipo = '05'
                
            CODIGO_SUSTENTOS = {
                'reembolso': '04',
                'invoice': '18',
            }
            secuencia = detalle_ventas['retencion']
            if secuencia and secuencia[:3]=='RET':
                secuencia = secuencia[9:]
            if secuencia and secuencia[:2]=='RT':
                secuencia = secuencia[11:]
            
            #dc#
            if detalle_ventas['iva']>0 and detalle_ventas['tarifa_doce']>0:
                valor2=detalle_ventas['tarifa_cero']
            else:
                valor2=detalle_ventas['tarifa_doce']
                    
            val_detallev = {                                   
                    'tipo_id_prov':tipo,
                    'ruc_prov':detalle_ventas['ruc'],
                    'invoice_id':detalle_ventas['invoice_id'],
                    'codigo_sustento':CODIGO_SUSTENTOS[detalle_ventas['tipo_factura']],
                    #'codigo_sustento':'18',
                    'base_no_gravada':detalle_ventas['tarifa_cero'],
                    ##'base_no_gravada':valor2,
                    'base_imponible':detalle_ventas['tarifa_doce'],
                    'base_imponible_grava': detalle_ventas['tarifa_doce'],
                    'monto_iva':detalle_ventas['iva'],
                    'valor_ret_iva':detalle_ventas['ri'],
                    'valor_ret_renta':detalle_ventas['ret_renta'],
                    'base_imponible_0_iva':detalle_ventas['bi0i'],                  
                    'tipo':detalle_ventas['tipo_factura'],
                    'fecha_registro':detalle_ventas['date'],
                    'fecha_emision':detalle_ventas['date'],
                    'autorizacion_punto_emision':detalle_ventas['emision'],
                    'autorizacion':detalle_ventas['autorizacion'],
                    'documento_modificado':'0',
                    'establecimiento_modificado':'000',
                    'emision_modificado':'000',
                    'secuencial_modificado':'0000000',
                    'autorizacion_modificado':'0000000000',
                    'secuencial_factura':detalle_ventas['factura'],
                    'emision_retencion':detalle_ventas['emision_retencion'],
                    #'secuencial_retencion':detalle_ventas['retencion'],
                    'secuencial_retencion':secuencia,
                    'fecha_emision_retencion':detalle_ventas['date_retencion'],
                    'documento_modificado':'0',
                    'establecimiento_modificado':'000',
                    'emision_modificado':'000',
                    'secuencial_modificado':'0000000',
                    'autorizacion_modificado':'0000000000',
            }

            fila_detv = (0, 0, val_detallev)
            ventas_line.append(fila_detv)
        val_resumen['document_ats_sale_ids'] = ventas_line
        
        
        
        #=======================================================================
        # #Notas de Credito de Cliente
        #=======================================================================
        query = "select count(1) as numero, tipo_factura, sum(t_b_excenta_iva) as tarifa_cero,type, \
                    sum(t_bi_iva) as tarifa_doce,sum(t_iva) as iva ,type\
                    from account_invoice \
                    where type = 'out_refund' \
                    and state in ('open','paid') \
                    and date_invoice <= '" + date_fin + "' and date_invoice >= '" + date_ini + "' and company_id ="+company_id+" \
                    group by tipo_factura, type "
                    
        cr.execute(query)
        res_notas = cr.dictfetchall()
        resumen_notas_line = []
        val_nota_cr = {}
        for nota_credito in res_notas:
            val_nota_cr = {
                'codigo':'01',
                'documento':nota_credito['tipo_factura'],
                'type':nota_credito['type'],
                'numero_documento':nota_credito['numero'],
                'base_imponible_tarifa_cero':nota_credito['tarifa_cero'],
                'base_imponible_tarifa_doce':nota_credito['tarifa_doce'],
                'valor_iva':nota_credito['iva'],
            }
            fila = (0, 0, val_nota_cr)
            resumen_line.append(fila)
        vals_cab['document_ats_resumen_ids'] = resumen_line
        
        
        #======================================================================
        # Detalle Notas de Credito de cliente
        #======================================================================
        query = "select ai.id as invoice_id, ai.tipo_factura, \
        ai.t_b_0_iva as bi0i, \
        ai.t_b_no_iva as bini, \
        ai.t_b_excenta_iva as tarifa_cero, \
        ai.t_bi_iva as tarifa_doce, \
        ai.date_invoice as date,\
        ai.num_retention as factura,\
        ai.t_iva as iva,\
        ai.amount_ret_ir as ret_bienes,\
        ai.type,\
        rp.ident_num as ruc,\
        aa.name as autorizacion,\
        aa.serie_emision as emision,\
        ret.ath_sri as emision_retencion,\
        ret.nro_retencion as retencion,\
        ret.broadcast_date as date_retencion, ai.t_ret_iva as ri, rp.ident_type as it \
        from account_invoice as ai LEFT JOIN res_partner rp on (ai.partner_id=rp.id)\
        LEFT JOIN account_authorisation aa on (ai.auth_ret_id=aa.id) \
        LEFT JOIN account_invoice_retention_voucher ret on (ai.ret_voucher_id=ret.id)\
        where ai.type = 'out_refund'\
        and ai.state in ('open','paid')\
        and ai.date_invoice <= '" + date_fin + "' and ai.date_invoice >= '" + date_ini + "' and ai.company_id ="+company_id
        #--and ret.state ='valid'"
        
        cr.execute(query)
        res_detalle_notas = cr.dictfetchall()
        notas_line = []
        for detalle_nota in res_detalle_notas:
            
            
            codigo_tipo = detalle_nota['it']
            tipo = ''
            if codigo_tipo == 'r':
                tipo = '04'
            elif codigo_tipo == 'p':
                tipo = '06'
            elif codigo_tipo == 'c':
                tipo = '05'
            secuencia = detalle_nota['retencion']
            if secuencia and secuencia[:3]=='RET':
                secuencia = secuencia[9:]
            if secuencia and secuencia[:2]=='RT':
                secuencia = secuencia[11:]               
                
             #dc#
            if detalle_nota['iva']>0 and detalle_nota['tarifa_doce']>0:
                valor3=detalle_nota['bini']
            else:
                valor3=detalle_nota['bi0i']
                
            val_detallev = { 
                    'tipo_id_prov':tipo,
                    'invoice_id':detalle_nota['invoice_id'],
                    'ruc_prov':detalle_nota['ruc'],
                    'codigo_sustento':'04',
                    'base_no_gravada':detalle_nota['bini'],
                     # #'base_no_gravada':valor3,
                    'base_imponible_no_iva':detalle_nota['bini'],
                    'base_imponible':detalle_nota['bi0i'],
                    'base_imponible_grava': detalle_nota['tarifa_doce'],
                    'base_imponible_0_iva': detalle_nota['bi0i'],
                    'monto_iva':detalle_nota['iva'],
                    'valor_ret_iva':detalle_nota['ri'],
                    'valor_ret_renta':float(0.00),
                    
                    'tipo':detalle_nota['tipo_factura'],
                    'fecha_registro':detalle_nota['date'],
                    'fecha_emision':detalle_nota['date'],
                    'autorizacion_punto_emision':detalle_nota['emision'],
                    'autorizacion':detalle_nota['autorizacion'],
                    'documento_modificado':'0',
                    'establecimiento_modificado':'000',
                    'emision_modificado':'000',
                    'secuencial_modificado':'0000000',
                    'autorizacion_modificado':'0000000000',
                    'secuencial_factura':detalle_nota['factura'],
                    
                    'emision_retencion':detalle_nota['emision_retencion'],
                    #'secuencial_retencion':detalle_nota['retencion'],
                    'secuencial_retencion':secuencia,
                    'fecha_emision_retencion':detalle_nota['date_retencion'],
                    'documento_modificado':'0',
                    'establecimiento_modificado':'000',
                    'emision_modificado':'000',
                    'secuencial_modificado':'0000000',
                    'autorizacion_modificado':'0000000000',
            }

            fila_detv = (0, 0, val_detallev)
            notas_line.append(fila_detv)
        val_nota_cr['document_ats_sale_ids'] = notas_line
        
        
        
        #=======================================================================
        # #DOCUMENTOS ANULADOS
        #=======================================================================
        query = "select count(1) as numero, sum(t_b_excenta_iva) as tarifa_cero,\
                    sum(t_bi_iva) as tarifa_doce,sum(t_iva) as iva, state\
                    from account_invoice \
                    where state in ('cancel') \
                    and factura is not null\
                    and date_invoice <= '" + date_fin + "' and date_invoice >= '" + date_ini + "' and company_id ="+company_id+" \
                    group by state "
                   
        cr.execute(query)
        res_anulados = cr.dictfetchall()
        for doc_anulado in res_anulados:
            val_anulado_cr = {
                'codigo':'01',
                'documento':'Anulado',
                'type':'Anulado',
                'numero_documento':doc_anulado['numero'],
                'base_imponible_tarifa_cero':doc_anulado['tarifa_cero'],
                'base_imponible_tarifa_doce':doc_anulado['tarifa_doce'],
                'valor_iva':doc_anulado['iva'],
            }
            fila = (0, 0, val_anulado_cr)
            resumen_line.append(fila)
        vals_cab['document_ats_resumen_ids'] = resumen_line
        
        
        ##=========================
        ##DETALLE DOCUMENTOS ANULADOS
        ##==============================
        query_anu = "select ai.t_b_excenta_iva as tarifa_cero,ai.t_bi_iva as tarifa_doce,ai.t_iva as iva, ai.type as type, \
                ai.tipo_factura as tipo_factura, aa.name as autorizacion, aa.serie_emision as emision, aa.serie_entidad as entidad, \
                aa.num_start as si, aa.num_end as sf, ai.number as factura \
                from account_invoice ai \
                LEFT JOIN account_authorisation aa on (ai.auth_ret_id=aa.id) \
                where state in ('cancel') \
                and date_invoice <= '%s' and date_invoice >= '%s' and ai.company_id= %s\
                order by type" % (date_fin, date_ini,company_id)
        #print 'sql anulados', query_anu
        cr.execute(query_anu)
        res_det_anulados = cr.dictfetchall()
        resumen_anulados_det = []
        for det_anulado in res_det_anulados:
            #print 'det_anulado', det_anulado
            codigo_sustento = ''
            if det_anulado['tipo_factura'] == 'purchase_liq' and det_anulado['type'] == 'in_invoice':
                codigo_sustento = '03'
            elif det_anulado['tipo_factura'] == 'invoice' and det_anulado['type'] == 'in_invoice':
                codigo_sustento = '01'
            elif det_anulado['tipo_factura'] == 'invoice' and det_anulado['type'] == 'in_refund':
                codigo_sustento = '04'
            elif det_anulado['tipo_factura'] == 'sales_note' and det_anulado['type'] == 'in_invoice':
                codigo_sustento = '02'
            elif det_anulado['tipo_factura'] == 'invoice' and det_anulado['type'] == 'out_invoice':
                codigo_sustento = '18'
            elif det_anulado['tipo_factura'] == 'invoice' and det_anulado['type'] == 'out_refund':
                codigo_sustento = '04'    
            elif det_anulado['tipo_factura'] == 'reembolso' and det_anulado['type'] == 'in_invoice':
                codigo_sustento = '41'
            
            if not det_anulado['factura']:
                continue
            
            
            val_anulado = {
                'tipo':codigo_sustento,
                'establecimiento':det_anulado['entidad'],
                'punto_emision':det_anulado['emision'],
                'secuencial_inicio':str(int(det_anulado['factura'][8:])),
                'secuencial_fin':str(int(det_anulado['factura'][8:])),
                'autorizacion':det_anulado['autorizacion'],
                'base_imponible_tarifa_cero':det_anulado['tarifa_cero'],
                'base_imponible_tarifa_doce':det_anulado['tarifa_doce'],
                'valor_iva':det_anulado['iva'],
            }
            print '#####################################################',val_anulado
            fila = (0, 0, val_anulado)
            resumen_anulados_det.append(fila)
            
        val_anulado_cr['document_ats_cancel_ids'] = resumen_anulados_det     
        
        

        #Importaciones 
        sql_imp = "select count(1) as numero, tipo_factura, sum(t_b_excenta_iva) as tarifa_cero, \
                    sum(t_bi_iva) as tarifa_doce,sum(t_iva) as iva \
                    from account_invoice \
                    where type = 'in_invoice' \
                    and tipo_factura in ('importacion')\
                    and tipo_factura not in ('anticipo') \
                    and state in ('open','paid') \
                    and date_invoice <= '" + date_fin + "' and date_invoice >= '" + date_ini +"' and company_id ="+company_id+" \
                    group by tipo_factura"
        cr.execute(sql_imp)
        res_imp = cr.dictfetchall()
        import_line = []
        
        for importaciones in res_imp:
            val_impor = {
                'codigo':'01',
                'documento':importaciones['tipo_factura'],
                'numero_documento':importaciones['numero'],
                'v_cif_fob':importaciones['tarifa_cero'],
                'valor_iva':importaciones['tarifa_doce'],
            }
            fila_imp = (0, 0, val_impor)
            import_line.append(fila_imp)
        vals_cab['document_ats_resumen_import_ids'] = import_line

        # Exportaciones    

        sql_exp = "select count(1) as numero, tipo_factura, sum(t_b_excenta_iva) as tarifa_cero, \
                    sum(t_bi_iva) as tarifa_doce,sum(t_iva) as iva \
                    from account_invoice \
                    where type = 'out_invoice' \
                    and tipo_factura in ('exportacion')\
                    and tipo_factura not in ('anticipo') \
                    and state in ('open','paid') \
                    and date_invoice <= '" + date_fin + "' and date_invoice >= '" + date_ini +"' and company_id ="+company_id+" \
                    group by tipo_factura"
        cr.execute(sql_exp)
        res_exp = cr.dictfetchall()
        exp_line = []
        
        for exportaciones in res_exp:
            val_exp = {
                'codigo':'01',
                'documento':exportaciones['tipo_factura'],
                'numero_documento':exportaciones['numero'],
                'v_cif_fob':exportaciones['tarifa_cero'],
                'valor_iva':exportaciones['tarifa_doce'],
            }
            fila_exp = (0, 0, val_exp)
            exp_line.append(fila_exp)
        vals_cab['document_ats_resumen_export_ids'] = exp_line
            
        #concepto de retencion compras        
        sql = "select ait.name as nombre, sum(ait.base_amount) as base, sum(ait.tax_amount) as retenido, count(1) as reg, atc.code as code \
        from account_invoice ai, account_invoice_tax ait, account_tax_code atc\
        where ai.id = ait.invoice_id\
        and ait.base_code_id = atc.id\
        and ai.type = 'in_invoice'\
        and ai.state in ('open','paid')\
        and ai.date_invoice <= '" + date_fin + "' and ai.date_invoice >= '" + date_ini + "' and ai.company_id ="+company_id+" \
        and tax_group in ('ret_ir','no_ret_ir')\
        group by ait.name, atc.code\
        order by code" 
                      
                      
        cr.execute(sql)
        res_ret_compras = cr.dictfetchall()
        retencion_line = []
        for ret in res_ret_compras:
            cr.execute('SELECT invoice.id as invoice_id, tax.id as tax_id FROM account_invoice invoice'
                       '  JOIN account_invoice_tax tax on tax.invoice_id=invoice.id '
                       '  JOIN account_tax_code code on code.id=tax.base_code_id '
                       "WHERE invoice.type='in_invoice' AND invoice.state in ('open', 'paid') "
                       "AND invoice.date_invoice between %s AND %s AND tax_group in ('ret_ir','no_ret_ir') "
                       'AND tax.name=%s AND code.code=%s and invoice.company_id=%s '
                       'ORDER BY invoice.date_invoice', (date_ini, date_fin, ret['nombre'], ret['code'],company_id))
            details_ids = [(0, 0, aux) for aux in cr.dictfetchall()]
            val_retencion = {
                'codigo':ret['code'],
                'documento':ret['nombre'],
                'numero_documento':ret['reg'],
                'base_imponible_ir':ret['base'],
                'retencion_ir':(-1) * (ret['retenido']),
                'details_ids': details_ids
            }
            fila_retencion = (0, 0, val_retencion)
            retencion_line.append(fila_retencion)
        vals_cab['document_ats_resumen_concept_retent_ids'] = retencion_line    
        
        
        
        #resumen de retenciones - retencion en la fuente de IVA
        ###########################################
                      
        sql_q = "select ait.name as nombre, sum(ait.base_amount) as base, sum(ait.tax_amount) as retenido, count(1) as reg \
                from account_invoice ai, account_invoice_tax ait \
                where ai.id = ait.invoice_id\
                and ai.type = 'in_invoice'\
                and ai.state in ('open','paid')\
                and ai.date_invoice <= '" + date_fin + "' and ai.date_invoice >= '" + date_ini + "' and ai.company_id ="+company_id+" \
                and tax_group not in ('ret_ir','no_ret_ir')\
                group by ait.name\
                order by reg desc"
                      
                     
        cr.execute(sql_q)
        res_iva_compras = cr.dictfetchall()
        ret_iva_line = []
        for ret_iva in res_iva_compras:
            cr.execute('SELECT invoice.id as invoice_id, tax.id as tax_id '
                       'FROM account_invoice invoice join account_invoice_tax tax on tax.invoice_id=invoice.id '
                       "WHERE invoice.type='in_invoice' AND invoice.state in ('open', 'paid') "
                       "AND invoice.date_invoice between %s AND %s AND tax_group not in ('ret_ir','no_ret_ir') "
                       'AND tax.name=%s and invoice.company_id = %s ORDER BY invoice.date_invoice', (date_ini, date_fin, ret_iva['nombre'],company_id))
            details_ids = [(0, 0, aux) for aux in cr.dictfetchall()]
            val_ret_iva = {
                'documento':ret_iva['nombre'],
                'numero_documento':ret_iva['reg'],
                'base_imponible_ir':ret_iva['base'],
                'porcentaje_ret':ret_iva['retenido'],
                'retencion_ir':ret_iva['retenido'],
                'details_ids': details_ids
            }
            fila_ret_iva = (0, 0, val_ret_iva)
            ret_iva_line.append(fila_ret_iva)
        vals_cab['document_ats_resumen_retent_fuente_ids'] = ret_iva_line    
        
        header_id = document_ats_obj.create(cr, uid, vals_cab)
        
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'account.document.ats',
                'type': 'ir.actions.act_window',
                'res_id' : header_id,
                #'target':'new',
                }
#ejecuta wizard
    def fill_data(self, cr, uid, ids, context=None):
        
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        return self._generate_info(cr, uid, ids, data, context=context)
    
    #@api.model
    #def _default_company(self):
    #    return self.env['res.company']._company_default_get('res.partner')
    
    _columns = {
            'date_start':fields.date('Fecha Desde'),
            'date_finish':fields.date('Fecha Hasta'),
            'company_id':fields.many2one('res.company','Compania')
    }                            
                                                                              
    _defaults = {
        'date_start': lambda * a: time.strftime('%Y-%m-01'),
        'date_finish': lambda * a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid,context=context).company_id.id,
        }
        
wizard_generate_ats()

class account_document_ats(osv.osv):
    _name = 'account.document.ats'
    _rec_name = 'date_start'
    #===========================================================================
    # def name_get(self, cr, uid, ids, context=None):
    #    if not len(ids):
    #        return []
    #    reads = self.read(cr, uid, ids, ['name'], context)
    #    res = []
    #    for record in reads:
    #        name = record['name']
    #        if not name:
    #            name = 'ATS'
    #        res.append((record['id'], name))
    #    return res
    # 
    #===========================================================================
    _columns = {
        #'name':fields.char('Sequencia', size=100),
        'date_start':fields.date('Fecha Desde'),
        'date_finish':fields.date('Fecha Hasta'),
        'numero_compras':fields.integer('No. Compras'),
        'numero_ventas':fields.integer('No. Ventas'),
        'monto_ventas':fields.float('Ventas Netas'),
        'monto_compras':fields.float('Compras Netas'),
        'document_ats_resumen_ids':fields.one2many('account.document.ats.resumen', 'document_ats_resumen_id', 'Facturas'),
        'document_ats_resumen_import_ids':fields.one2many('account.document.ats.resumen.import', 'document_ats_resumen_import_id', 'Facturas Import'),
        'document_ats_resumen_export_ids':fields.one2many('account.document.ats.resumen.export', 'document_ats_resumen_export_id' , 'Exportaciones ATS'),
        'document_ats_resumen_concept_retent_ids':fields.one2many('account.document.ats.resumen.concept_retent', 'document_ats_resumen_concept_retent_id', 'Concepto de Retencion ATS'),
        'document_ats_resumen_retent_fuente_ids':fields.one2many('account.document.ats.resumen.resu.retent', 'document_ats_resumen_retent_fuente_id' , 'Resumen de Retenciones ATS'),
    }
    
    def print_report(self, cr, uid, ids, context=None):
        report_pool = self.pool.get('wizard.report.ats')
        report_id = report_pool.create(cr, uid, {'name': 'Reporte ATS.xls'}, context=context)
        ctx = context.copy()
        ctx['active_ids'] = ids
        report_pool.generate_report(cr, uid, [report_id], context=ctx)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Archivo generado',
            'res_model': 'wizard.report.ats',
            'res_id': report_id,
            'view_mode': 'form',
            'target': 'new'
        }
        
account_document_ats()

class account_document_ats_resumen(osv.osv):
    _name = 'account.document.ats.resumen'
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['type', 'documento', 'numero_documento'], context)
        res = []
        for record in reads:
            numero = str(record['numero_documento'])
            documento = record['type']
            if documento in ('in_invoice', 'out_invoice'):
                documento = 'Facturas'
            elif documento in ('in_refund', 'out_refund'):
                documento = 'Notas de Credito'
            name = numero + '/' + documento
            if not name:
                name = 'Detalle'
            res.append((record['id'], name))
        return res
    
    _columns = {
        'codigo':fields.char('Codigo', size=4),
        'type':fields.selection([('in_invoice', 'Factura Compra'),
                                 ('out_invoice', 'Factura Venta'),
                                 ('in_refund', 'Nota de Credito Compra'),
                                 ('out_refund', 'Nota de Credito Venta'),
                                 ('Anulado', 'Anulado'),
                                 ], 'Tipo', readonly=False),
        'documento':fields.selection([('invoice', 'Factura'),
                                         ('purchase_liq', 'Liquidación de Compra'),
                                         ('sales_note', 'Nota de Venta'),
                                         ('anticipo', 'Anticipo'),
                                         ('alicuota', 'Alícuotas'),
                                         ('ticket_aereo', 'Ticket aereo'),
                                         ('gas_no_dedu', 'Gastos No Deduci'),
                                         ('reembolso', 'Reembolso de gasto'), 
                                         ('gasto_viaje', 'Gasto de Viaje'),
                                         ('gasto_deducble', 'Gasto deducible sin Factura'),
                                         ('doc_inst_est', 'Doc Emitido Estado'),
                                         ('comp_venta_ext', 'Comprobante de Venta Emitido Exterior'),
                                      ('Anulado', 'Anulado'),
                                      ('gasto_financiero', 'Gastos Financieros'),
                                      ], 'Documento', readonly=False),
        'numero_documento':fields.integer('No. Registros'),
        'base_imponible_tarifa_cero':fields.float('Base Imponible Tarifa 0%'),
        'base_imponible_tarifa_doce':fields.float('Base Imponible Tarifa 12%'),
        'valor_iva':fields.float('Valor IVA'),
        'document_ats_purchase_ids':fields.one2many('account.document.ats.detail.purchase', 'document_ats_resumen_purchase_id', 'Detalles Compras'),
        'document_ats_sale_ids':fields.one2many('account.document.ats.detail.sale', 'document_ats_resumen_sale_id', 'Detalles Ventas'),
        'document_ats_resumen_id':fields.many2one('account.document.ats', 'Documento ATS', ondelete='cascade'),
        'document_ats_cancel_ids':fields.one2many('account.document.ats.detail.cancel', 'document_ats_resumen_cancel_id', 'Detalle Anulados'),
    }
account_document_ats_resumen()

    
class account_document_ats_detail_purchase(osv.osv):
    _name = 'account.document.ats.detail.purchase'
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['secuencial_factura'], context)
        res = []
        for record in reads:
            name = record['secuencial_factura']
            if not name:
                name = 'Detalle'
            res.append((record['id'], name))
        return res
    
    _columns = {
        'codigo_sustento':fields.char('Cod.Sustento', size=4),
        'invoice_id': fields.many2one('account.invoice', 'Factura'),
        'tipo_id_prov':fields.char('Tipo', size=4),
        'ruc_prov':fields.char('Ruc', size=16),
        'cod_tipo_comp':fields.char('Cod Tipo Comprobante', size=2),
        'tipo':fields.selection([('invoice', 'Factura'),
                                         ('purchase_liq', 'Liquidación de Compra'),
                                         ('sales_note', 'Nota de Venta'),
                                         ('anticipo', 'Anticipo'),
                                         ('alicuota', 'Alícuotas'),
                                         ('ticket_aereo', 'Ticket aereo'),
                                         ('gas_no_dedu', 'Gastos No Deduci'),
                                         ('reembolso', 'Reembolso de gasto'),
                                         ('gasto_viaje', 'Gasto de Viaje'),
                                         ('gasto_deducble', 'Gasto deducible sin Factura'),
                                         ('doc_inst_est', 'Doc Emitido Estado'),
                                         ('gasto_financiero', 'Gastos Financieros'),
                                         ('comp_venta_ext', 'Comprobante de Venta Emitido Exterior')
                                 ], 'Documento', readonly=True),
        'fecha_registro':fields.date('Fecha Registro'),
        'autorizacion_establecimiento':fields.char('Establecimiento', size=4),
        'autorizacion_punto_emision':fields.char('Emision', size=4),
        'secuencial_factura':fields.char('Secuencial', size=16),
        'fecha_emision':fields.date('Fecha Emision'),
        'autorizacion':fields.char('Autorizacion', size=64),
        'base_no_gravada':fields.float('Base no Gravada', help='Impuestos del grupo IVA 0%'),
        'base_imponible':fields.float('Base Imponible', help='Impuestos del grupo IVA Diferente de 0'),
        'base_imponible_grava':fields.float('Base Imponible Gravada', help='Impuestos del grupo No objeto de IVA'),
        'base_imponible_0_iva':fields.float('Base Imponible 0% IVA', help='Impuestos del grupo 0% de IVA'),
        'base_imponible_no_iva':fields.float('Base Imponible no aplica IVA', help='Impuestos del grupo No objeto de IVA'),
        'monto_ice':fields.float('Monto ICE'),
        'monto_iva':fields.float('Monto IVA'),
        
        'valor_retencion_bien10':fields.float('Retencion Bienes 10%', help='Impuestos con codigo 721 Si el producto es bien'),
        'valor_retencion_serv20':fields.float('Retencion Servicios 20%', help='Impuestos con codigo 723 Si el producto es servicio'),
        'valor_retencion_bienes':fields.float('Retencion Bienes 30%', help='Impuestos con codigo 725 Si el producto es bien'),
        'valor_retencion_serv50':fields.float('Retencion Servicios 50%', help='Impuestos si el producto es servicio'),
        'valor_retencion_servicios':fields.float('Retencion Servicios 70%', help='Impuestos con codigo 727 Si el producto en servicio'),
        'valor_retencion_servicios_100':fields.float('Retencion Servicios al 100%', help='Impuesto con el 729 de cualquier producto si tiene posicion fiscal Persona Natural no obligada a llevar contabilidad'),
        'establecimiento_retencion':fields.char('Establecimiento Retencion', size=4),
        'emision_retencion':fields.char('Emision Retencion', size=4),
        'secuencial_retencion':fields.char('Secuencial Retencion', size=16),
        'autorizacion_retencion':fields.char('Autorizacion Retencion', size=37),
        'fecha_emision_retencion':fields.char('Fecha Emision retencion', size=13),
        'documento_modificado':fields.char('Documento Modificado', size=16),
        'establecimiento_modificado':fields.char('Establecimiento Modificado', size=16),
        'emision_modificado':fields.char('Pto. Emision Modificado', size=16),
        'secuencial_modificado':fields.char('Secuencial Modificado', size=16),
        'autorizacion_modificado':fields.char('Autorizacion Modificado', size=16),
        'document_ats_resumen_purchase_id':fields.many2one('account.document.ats.resumen', 'Resumen ATS', ondelete='cascade'),
        'document_ats_detail_purchase_retention_ids':fields.one2many('account.document.ats.detail.purchase.retention', 'document_ats_detail_purchase_id', 'Detalles Retencion'),
    }
account_document_ats_detail_purchase()

class account_document_ats_detail_purchase_retention(osv.osv):
    _name = 'account.document.ats.detail.purchase.retention'
    _columns = {
        'codigo_retencion_air':fields.char('Codigo Impuesto', size=5),
        #si se modifica el tamaño a 5 toma obligado 5 caracteres incluyendo espacios 
        # esto ocaciona error en el xml
        'base_imponible_air':fields.float('Base Imponible'),
        'porcentaje_air':fields.float('Porcentaje Impuesto'),
        'valor_retencion':fields.float('Valor Retencion'),
        'document_ats_detail_purchase_id':fields.many2one('account.document.ats.detail.purchase', 'Detail ATS', ondelete='cascade'),
    }
account_document_ats_detail_purchase_retention()


class account_document_ats_detail_sale(osv.osv):
    _name = 'account.document.ats.detail.sale'
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['secuencial_factura'], context)
        res = []
        for record in reads:
            name = record['secuencial_factura']
            if not name:
                name = 'Detalle'
            res.append((record['id'], name))
        return res
    
    _columns = {
        'codigo_sustento':fields.char('Cod.Sustento', size=4),
        'tipo_id_prov':fields.char('Tipo', size=4),
        'ruc_prov':fields.char('Ruc', size=16),
        'invoice_id':fields.many2one('account.invoice', 'Factura'),
        'tipo':fields.selection([('invoice', 'Factura'),
                                 ('purchase_liq', 'Liquidación de Compra'),
                                 ('sales_note', 'Nota de Venta'),
                                 ('anticipo', 'Anticipo'),
                                 ('alicuota', 'Alícuotas'),
                                 ('ticket_aereo', 'Ticket aereo'),
                                 ('gas_no_dedu', 'Gastos No Deduci'),
                                 ('reembolso', 'Reembolso de gasto'),
                                 ('gasto_viaje', 'Gasto de Viaje'),
                                 ('gasto_deducble', 'Gasto deducible sin Factura'),
                                 ('doc_inst_est', 'Doc Emitido Estado'),
                                 ('gasto_financiero', 'Gastos Financieros'),
                                 ('comp_venta_ext', 'Comprobante de Venta Emitido Exterior')
                                 ], 'Documento', readonly=True),
        'fecha_registro':fields.date('Fecha Registro'),
        'autorizacion_establecimiento':fields.char('Establecimiento', size=4),
        'autorizacion_punto_emision':fields.char('Emision', size=4),
        'secuencial_factura':fields.char('Secuencial', size=16),
        'fecha_emision':fields.date('Fecha Emision'),
        'autorizacion':fields.char('Autorizacion', size=64),
        'base_no_gravada':fields.float('Base no Gravada', help='Impuestos del grupo IVA 0%'),
        'base_imponible':fields.float('Base Imponible', help='Impuestos del grupo IVA Diferente de 0'),
        'base_imponible_grava':fields.float('Base Imponible Gravada', help='Impuestos del grupo No objeto de IVA'),
        'base_imponible_0_iva':fields.float('Base Imponible 0% IVA', help='Impuestos del grupo 0% de IVA'),
        'base_imponible_no_iva':fields.float('Base Imponible no aplica IVA', help='Impuestos del grupo No objeto de IVA'),
        'monto_ice':fields.float('Monto ICE'),
        'monto_iva':fields.float('Monto IVA'),
        'valor_ret_iva':fields.float('Retencion IVA'),
        'valor_ret_renta':fields.float('Retencion Renta'),
        'establecimiento_retencion':fields.char('Establecimiento Retencion', size=4),
        'emision_retencion':fields.char('Serie Emision Retencion', size=50),
        'secuencial_retencion':fields.char('Secuencial Retencion', size=16),
        'autorizacion_retencion':fields.char('Autorizacion Retencion', size=37),
        'fecha_emision_retencion':fields.date('Fecha Emision retencion'),
        'documento_modificado':fields.char('Documento Modificado', size=16),
        'establecimiento_modificado':fields.char('Establecimiento Modificado', size=16),
        'emision_modificado':fields.char('Pto. Emision Modificado', size=16),
        'secuencial_modificado':fields.char('Secuencial Modificado', size=16),
        'autorizacion_modificado':fields.char('Autorizacion Modificado', size=16),
        'document_ats_resumen_sale_id':fields.many2one('account.document.ats.resumen', 'Resumen ATS', ondelete='cascade'),
    }
account_document_ats_detail_sale()


class account_document_ats_resumen_import(osv.osv):
    _name = 'account.document.ats.resumen.import'
    _columns = {
                'codigo':fields.char('Codigo', size=4),
                'documento':fields.char('Transaccion', size=16),
                'numero_documento':fields.integer('Numero Registros'),
                'v_cif_fob':fields.float('Valor CIF o FOB'),
                'valor_iva':fields.float('Valor IVA'),
                'document_ats_resumen_import_id':fields.many2one('account.document.ats', 'Importaciones ATS', ondelete='cascade'),
                }
account_document_ats_resumen_import()
    
class account_document_ats_resumen_export(osv.osv):
    _name = 'account.document.ats.resumen.export'
    _columns = {
                'codigo':fields.char('Codigo', size=4),
                'documento':fields.char('Documento', size=16),
                'numero_documento':fields.integer('Numero Documento'),
                'v_cif_fob':fields.float('Valor CIF o FOB'),
                'valor_iva':fields.float('Valor IVA'),
                'document_ats_resumen_export_id':fields.many2one('account.document.ats', 'Exportaciones ATS', ondelete='cascade'),
                }
account_document_ats_resumen_export()
    
class account_document_ats_resumen_concept_retent(osv.osv):
    _name = 'account.document.ats.resumen.concept_retent'
    _columns = {
                'codigo':fields.char('Codigo', size=4),
                'porcentaje':fields.float('%'),
                'documento':fields.char('Concepto de Retencion', size=128),
                'numero_documento':fields.integer('No. Reg'),
                'base_imponible_ir':fields.float('Base Imponible'),
                'retencion_ir':fields.float('Valor Retencion'),
                'document_ats_resumen_concept_retent_id':fields.many2one('account.document.ats', 'Concepto de Retencion ATS', ondelete='cascade'),
                'details_ids': fields.one2many('account.document.ats.resumen.concept_retent.line', 'resum_id', 'Detalles')
                }
account_document_ats_resumen_concept_retent()

class account_document_ats_resumen_concept_retent_line(osv.osv):
    _name = 'account.document.ats.resumen.concept_retent.line'
    _columns = {
        'resum_id': fields.many2one('account.document.ats.resumen.concept_retent', 'Resumen', required=True, ondelete='cascade'),
        'invoice_id': fields.many2one('account.invoice', 'Factura', required=True, ondelete='cascade'),
        'tax_id': fields.many2one('account.invoice.tax', 'Impuesto', required=True, ondelete='cascade'),
        'factura': fields.related('invoice_id', 'factura', string='Factura', type='char', size=32),
        'base': fields.related('tax_id', 'base', string='Base imponible', type='float', digits=(16,2)),
        'amount': fields.related('tax_id', 'amount', string='Monto', type='float', digits=(16,2))
    }
account_document_ats_resumen_concept_retent_line()
    
class account_document_ats_resumen_resu_retent(osv.osv):
    _name = 'account.document.ats.resumen.resu.retent'
    _columns = {
                'operacion':fields.char('Operacion', size=4),
                'documento':fields.char('Concepto de Retencion', size=158),
                'numero_documento':fields.integer('No. Registros'),
                'base_imponible_ir':fields.float('B.I.'),
                'porcentaje_ret':fields.float('% Retencion'),
                'retencion_ir':fields.float('Valor Retenido'),
                'document_ats_resumen_retent_fuente_id':fields.many2one('account.document.ats', 'Resumen de Retenciones ATS', ondelete='cascade'),
                'details_ids': fields.one2many('account.document.ats.resumen.resu.retent.line', 'resum_id', 'Detalles')
                }    
account_document_ats_resumen_resu_retent()

class account_document_ats_resumen_resu_retent_line(osv.osv):
    _name = 'account.document.ats.resumen.resu.retent.line'
    _columns = {
        'resum_id': fields.many2one('account.document.ats.resumen.resu.retent', 'Resumen', required=True, ondelete='cascade'),
        'invoice_id': fields.many2one('account.invoice', 'Factura', required=True, ondelete='cascade'),
        'tax_id': fields.many2one('account.invoice.tax', 'Impuesto', required=True, ondelete='cascade'),
        'factura': fields.related('invoice_id', 'factura', string='Factura', type='char', size=32),
        'base': fields.related('tax_id', 'base', string='Base imponible', type='float', digits=(16,2)),
        'amount': fields.related('tax_id', 'amount', string='Monto', type='float', digits=(16,2))
    }
account_document_ats_resumen_resu_retent_line()

class account_document_ats_detail_cancel(osv.osv):
    _name = 'account.document.ats.detail.cancel'
    _columns = {
        #'invoice_id':    
        'tipo':fields.char('Tipo Comprobante', size=3),
        'establecimiento':fields.char('Establecimiento', size=3),
        'punto_emision':fields.char('Punto Emision', size=5),
        'secuencial_inicio':fields.char('Secuencial Inicio', size=10),
        'secuencial_fin':fields.char('Secuencial Fin', size=10),
        'autorizacion':fields.char('Autorizacion', size=35),
        'base_imponible_tarifa_cero':fields.float('B.I. Tarifa Cero'),
        'base_imponible_tarifa_doce':fields.float('B.I. Gravada'),
        'valor_iva':fields.float('IVA'),
        'document_ats_resumen_cancel_id':fields.many2one('account.document.ats.resumen', 'Resumen ATS', ondelete='cascade'),
    }
account_document_ats_detail_cancel()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: