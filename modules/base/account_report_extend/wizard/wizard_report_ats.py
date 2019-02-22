# -*- encoding: utf-8 -*-
##############################################################################
#
#    Tax reporte
#    Copyright (C) 2010-2010 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
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
#creador  *Vll

from openerp.osv import fields, osv
import time, datetime,cStringIO, openerp.addons, base64,re
import xlwt as pycel

class wizard_report_ats(osv.osv_memory):
    
    _name = "wizard.report.ats"
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    
    def generate_report(self, cr, uid, ids, context=None):
        
        
        #print ' ids ', ids
        
        
        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                        'align: vertical center, horizontal center;'
                                        )
        
        linea_center = pycel.easyxf('font: colour black;'
                                   'align: vertical center, horizontal center;'
                                   )
        
        linea_left = pycel.easyxf('font: colour black;'
                                   'align: vertical center, horizontal left;'
                                   )
        
        wb = pycel.Workbook(encoding='utf-8')
        ws = wb.add_sheet("Detalle de Compras")
        ws.show_grid = False
        company_id = self.pool.get('res.company')._company_default_get(cr, uid)
        company_id = self.pool.get('res.company').browse(cr, uid, company_id)
#         path_image = addons.get_module_resource('account_report_extend', 'images', 'coviprov_logo.bmp')
#         ws.insert_bitmap(company_id.logo, 0, 0, scale_x=0.3 , scale_y=0.4)
        
        #print ' context active_ids ', context['active_ids']
        
        x = 1
        y = 2
        for active_id in context['active_ids']:
            obj_header = self.pool.get('account.document.ats').browse(cr, uid, active_id)
            
            ws.write_merge(0, 0,1,6, company_id.name, style_cabecera)
            ws.write(1, 1, "DOCUMENTO", style_cabecera)
            ws.write(1, 2, "TIPO", style_cabecera)
            ws.write(1, 3, "NUMERO", style_cabecera)
            ws.write(1, 4, "BASE IMPONIBLE TAR 0%", style_cabecera)
            ws.write(1, 5, "BASE IMPONIBLE TAR 12%", style_cabecera)
            ws.write(1, 6, "VALOR IVA", style_cabecera)
            
            for resumen_compras_ventas in obj_header.document_ats_resumen_ids:
                ##print " y:%s x:%s" % (y, x)
                documento = ''
                if resumen_compras_ventas.documento == 'purchase_liq':
                    documento = 'Liquidacion de Compra'
                elif resumen_compras_ventas.documento == 'invoice':
                    documento = 'Factura'
                elif resumen_compras_ventas.documento == 'sales_note':
                    documento = 'Nota de Venta'
                elif resumen_compras_ventas.documento == 'anticipo':
                    documento = 'Anticipo'    
                elif resumen_compras_ventas.documento == 'gas_no_dedu':
                    documento = 'Gastos No Deduci'
                elif resumen_compras_ventas.documento == 'doc_inst_est':
                    documento = 'Doc Inst Est'
                elif resumen_compras_ventas.documento == 'Anulado':
                    documento = 'Doc Anulado'
                elif resumen_compras_ventas.documento == 'gasto_financiero':
                    documento = 'Gastos Financieros'
                else:
                    documento = 'Otro Doc'
                
                
                tipo = ''
                if resumen_compras_ventas.type == 'in_invoice':
                    tipo = 'Factura Compra'
                elif resumen_compras_ventas.type == 'out_invoice':
                    tipo = 'Factura Venta'
                elif resumen_compras_ventas.type == 'in_refund':
                    tipo = 'Nota Credito Compra'
                elif resumen_compras_ventas.type == 'out_refund':
                    tipo = 'Nota Credito Venta'    
                elif resumen_compras_ventas.type == 'Anulado':
                    tipo = 'Doc. Anulado'
                else:
                    tipo = 'Otro Tipo'
               
                y+=1
                x = 1 
                ws.write(y, x, documento, style_cabecera)
                x+=1
                ##print " y:%s x:%s" % (y, x)
                ws.write(y, x, tipo, style_cabecera)
                x+=1
                ##print " y:%s x:%s" % (y, x)
                ws.write(y, x, resumen_compras_ventas.numero_documento, style_cabecera)
                x+=1
                ##print " y:%s x:%s" % (y, x)
                ws.write(y, x, resumen_compras_ventas.base_imponible_tarifa_cero, style_cabecera)
                x+=1
                ws.write(y, x, resumen_compras_ventas.base_imponible_tarifa_doce, style_cabecera)
                x+=1
                ws.write(y, x, resumen_compras_ventas.valor_iva, style_cabecera)
                y+=1
                cont = 0
                
                for detalle_compras in resumen_compras_ventas.document_ats_purchase_ids:
                    
                    
                    documento = ''
                    if detalle_compras.tipo == 'purchase_liq':
                        documento = 'Liquidacion de Compra'
                    elif detalle_compras.tipo == 'invoice':
                        documento = 'Factura'
                    elif detalle_compras.tipo == 'sales_note':
                        documento = 'Nota de Venta'
                    elif detalle_compras.tipo == 'anticipo':
                        documento = 'Anticipo'    
                    elif detalle_compras.tipo == 'gas_no_dedu':
                        documento = 'Gastos No Deduci'
                    elif detalle_compras.tipo == 'doc_inst_est':
                        documento = 'Doc Anulado'
                    elif detalle_compras.tipo == 'gasto_financiero':
                        documento = 'Gastos Financieros'
                    else:
                        documento = 'Otro Doc'
                    
                    
                    
                    if cont == 0:
                        x = 2
                        ws.write(y, x, "Cod.Sustento", style_cabecera)
                        x+=1
                        ws.write(y, x, "Tipo ID PROV", style_cabecera)                    
                        x+=1
                        ws.write(y, x, "RUC", style_cabecera)                    
                        x+=1
                        ws.write(y, x, "EMPRESA", style_cabecera)                    
                        x+=1
                        ws.write(y, x, "TIPO DOC", style_cabecera)
                        x+=1
                        ws.write(y, x, "Fecha Registro", style_cabecera)
                        x+=1
                        ws.write(y, x, "Establecimiento", style_cabecera)
                        x+=1
                        ws.write(y, x, "Emision", style_cabecera)
                        x+=1
                        ws.write(y, x, "Secuencial", style_cabecera)
                        x+=1
                        ws.write(y, x, "Fecha Emision", style_cabecera)
                        x+=1
                        ws.write(y, x, "Autorizacion", style_cabecera)
                        x+=1
                        ws.write(y, x, "Base no Gravada", style_cabecera)
                        x+=1
                        ws.write(y, x, "Base Imponible", style_cabecera)
                        x+=1
                        ws.write(y, x, "Base Imponible Gravada", style_cabecera)                    
                        x+=1
                        ws.write(y, x, "Monto IVA", style_cabecera)                    
                        x+=1
                        ws.write(y, x, "Retencion Bienes", style_cabecera)
                        x+=1
                        ws.write(y, x, "Retencion Servicios", style_cabecera)
                        x+=1
                        ws.write(y, x, "Retencion Servicios al 100", style_cabecera)
                        y+=1
                        cont+=1
                        
                        
                        x = 2
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_compras.codigo_sustento, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_compras.tipo_id_prov, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_compras.ruc_prov, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.invoice_id.partner_id.name, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, documento, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_compras.fecha_registro, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.autorizacion_establecimiento, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.autorizacion_punto_emision, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.secuencial_factura, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.fecha_emision, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.autorizacion, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.base_no_gravada, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.base_imponible, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.base_imponible_grava, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.monto_iva, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.valor_retencion_bienes, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.valor_retencion_servicios, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.valor_retencion_servicios_100, linea_center)
                        y+=1   
                    else:
                        
                        x = 2
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_compras.codigo_sustento, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_compras.tipo_id_prov, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_compras.ruc_prov, linea_center)
                        x+=1
                        print 'detalle_compras.invoice_id',detalle_compras.invoice_id
                        ws.write(y, x, detalle_compras.invoice_id.partner_id.name, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, documento, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_compras.fecha_registro, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.autorizacion_establecimiento, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.autorizacion_punto_emision, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.secuencial_factura, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.fecha_emision, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.autorizacion, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.base_no_gravada, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.base_imponible, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.base_imponible_grava, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.monto_iva, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.valor_retencion_bienes, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.valor_retencion_servicios, linea_center)
                        x+=1
                        ws.write(y, x, detalle_compras.valor_retencion_servicios_100, linea_center)
                        y+=1
                  
                  
                for detalle_ventas in resumen_compras_ventas.document_ats_sale_ids:
                    
                    if cont == 0:
                        x = 2
                        ws.write(y, x, "Cod.Sustento", style_cabecera)
                        x+=1
                        ws.write(y, x, "Tipo ID PROV", style_cabecera)                    
                        x+=1
                        ws.write(y, x, "RUC", style_cabecera)                    
                        x+=1
                        ws.write(y, x, "EMPRESA", style_cabecera)                    
                        x+=1
                        ws.write(y, x, "TIPO DOC", style_cabecera)
                        x+=1
                        ws.write(y, x, "Fecha Registro", style_cabecera)
                        x+=1
                        ws.write(y, x, "Establecimiento", style_cabecera)
                        x+=1
                        ws.write(y, x, "Emision", style_cabecera)
                        x+=1
                        ws.write(y, x, "Secuencial", style_cabecera)
                        x+=1
                        ws.write(y, x, "Fecha Emision", style_cabecera)
                        x+=1
                        ws.write(y, x, "Autorizacion", style_cabecera)
                        x+=1
                        ws.write(y, x, "Base no Gravada", style_cabecera)
                        x+=1
                        ws.write(y, x, "Base Imponible", style_cabecera)
                        x+=1
                        ws.write(y, x, "Base Imponible Gravada", style_cabecera)                    
                        x+=1
                        ws.write(y, x, "Monto IVA", style_cabecera)                    
                        x+=1
                        ws.write(y, x, "Retencion IVA", style_cabecera)
                        x+=1
                        ws.write(y, x, "Retencion Renta", style_cabecera)
                        y+=1
                        cont+=1
                        
                        
                        x = 2
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_ventas.codigo_sustento, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_ventas.tipo_id_prov, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_ventas.ruc_prov, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.invoice_id.partner_id.name, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, documento, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_ventas.fecha_registro, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.autorizacion_establecimiento, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.autorizacion_punto_emision, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.secuencial_factura, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.fecha_emision, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.autorizacion, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.base_no_gravada, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.base_imponible, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.base_imponible_grava, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.monto_iva, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.valor_ret_iva, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.valor_ret_renta, linea_center)
                        y+=1
                        
                    else:                        
                        x = 2
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_ventas.codigo_sustento, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_ventas.tipo_id_prov, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_ventas.ruc_prov, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.invoice_id.partner_id.name, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, documento, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_ventas.fecha_registro, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.autorizacion_establecimiento, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.autorizacion_punto_emision, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.secuencial_factura, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.fecha_emision, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.autorizacion, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.base_no_gravada, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.base_imponible, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.base_imponible_grava, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.monto_iva, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.valor_ret_iva, linea_center)
                        x+=1
                        ws.write(y, x, detalle_ventas.valor_ret_renta, linea_center)
                        y+=1 
                  
                for detalle_anulado in resumen_compras_ventas.document_ats_cancel_ids:
                   
                    if cont == 0:
                        x = 2
                        ws.write(y, x, "Tipo Comprobante", style_cabecera)
                        x+=1
                        ws.write(y, x, "Establecimiento", style_cabecera)                    
                        x+=1
                        ws.write(y, x, "Punto Emision", style_cabecera)                    
                        x+=1
                        ws.write(y, x, "Secuencial Inicio", style_cabecera)
                        x+=1
                        ws.write(y, x, "Secuencial Fin", style_cabecera)
                        x+=1
                        ws.write(y, x, "Autorizacion", style_cabecera)
                        x+=1
                        ws.write(y, x, "B.I. Tarifa Cero", style_cabecera)
                        x+=1
                        ws.write(y, x, "B.I. Gravada", style_cabecera)
                        x+=1
                        ws.write(y, x, "IVA", style_cabecera)
                        y+=1
                        cont+=1
                       
                        x = 2
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_anulado.tipo, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_anulado.establecimiento, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_anulado.punto_emision, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_anulado.secuencial_inicio, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_anulado.secuencial_fin, linea_center)
                        x+=1
                        ws.write(y, x, detalle_anulado.autorizacion, linea_center)
                        x+=1
                        ws.write(y, x, detalle_anulado.base_imponible_tarifa_cero, linea_center)
                        x+=1
                        ws.write(y, x, detalle_anulado.base_imponible_tarifa_doce, linea_center)
                        x+=1
                        ws.write(y, x, detalle_anulado.valor_iva, linea_center)
                        y+=1
                        
                    else:                        
                        x = 2
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_anulado.tipo, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_anulado.establecimiento, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_anulado.punto_emision, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_anulado.secuencial_inicio, linea_center)
                        x+=1
                        ##print " y:%s x:%s" % (y, x)
                        ws.write(y, x, detalle_anulado.secuencial_fin, linea_center)
                        x+=1
                        ws.write(y, x, detalle_anulado.autorizacion, linea_center)
                        x+=1
                        ws.write(y, x, detalle_anulado.base_imponible_tarifa_cero, linea_center)
                        x+=1
                        ws.write(y, x, detalle_anulado.base_imponible_tarifa_doce, linea_center)
                        x+=1
                        ws.write(y, x, detalle_anulado.valor_iva, linea_center)
                        y+=1    
                    
                        
        wsResCom = wb.add_sheet("Resumen de Compras")
        wsResCom.show_grid = False
#         path_image = addons.get_module_resource('account_report_extend', 'images', 'coviprov_logo.bmp')
#         wsResCom.insert_bitmap(path_image, 0, 0, scale_x=0.3 , scale_y=0.3)
        
        
        wsResCom.write_merge(1, 1,1,6, company_id.name, style_cabecera)
        wsResCom.write(2, 1, "RESUMEN DE COMPRAS, VENTAS Y RETENCIONES", style_cabecera)
        wsResCom.write_merge(7, 7,1,3, "RESUMEN DE COMPRAS - VENTAS", style_cabecera)
        
        
        x = 1
        y = 8
        for active_id in context['active_ids']:
            
            obj_header = self.pool.get('account.document.ats').browse(cr, uid, active_id)
                
            wsResCom.write(y, 1, "DOCUMENTO", style_cabecera)
            wsResCom.write(y, 2, "TIPO", style_cabecera)
            wsResCom.write(y, 3, "NUMERO", style_cabecera)
            wsResCom.write(y, 4, "BASE IMPONIBLE TAR 0%", style_cabecera)
            wsResCom.write(y, 5, "BASE IMPONIBLE TAR 12%", style_cabecera)
            wsResCom.write(y, 6, "VALOR IVA", style_cabecera)
            
            
            for resumen_compras_ventas in obj_header.document_ats_resumen_ids:
                ##print " y:%s x:%s" % (y, x)
                documento = ''
                if resumen_compras_ventas.documento == 'purchase_liq':
                    documento = 'Liquidacion de Compra'
                elif resumen_compras_ventas.documento == 'invoice':
                    documento = 'Factura'
                elif resumen_compras_ventas.documento == 'sales_note':
                    documento = 'Nota de Venta'
                elif resumen_compras_ventas.documento == 'anticipo':
                    documento = 'Anticipo'    
                elif resumen_compras_ventas.documento == 'gas_no_dedu':
                    documento = 'Gastos No Deduci'
                elif resumen_compras_ventas.documento == 'doc_inst_est':
                    documento = 'Doc Inst Est'
                elif resumen_compras_ventas.documento == 'Anulado':
                    documento = 'Doc Anulado'
                elif resumen_compras_ventas.documento == 'gasto_financiero':
                    documento = 'Gastos Financieros'
                else:
                    documento = 'Otro Doc'
                
                
                tipo = ''
                if resumen_compras_ventas.type == 'in_invoice':
                    tipo = 'Factura Compra'
                elif resumen_compras_ventas.type == 'out_invoice':
                    tipo = 'Factura Venta'
                elif resumen_compras_ventas.type == 'in_refund':
                    tipo = 'Nota Credito Compra'
                elif resumen_compras_ventas.type == 'out_refund':
                    tipo = 'Nota Credito Venta'    
                elif resumen_compras_ventas.type == 'Anulado':
                    tipo = 'Doc. Anulado'
                else:
                    tipo = 'Otro Tipo'
               
                y+=1
                x = 1 
                wsResCom.write(y, x, documento, linea_left)
                x+=1
                ##print " y:%s x:%s" % (y, x)
                wsResCom.write(y, x, tipo, linea_left)
                x+=1
                ##print " y:%s x:%s" % (y, x)
                wsResCom.write(y, x, resumen_compras_ventas.numero_documento, linea_center)
                x+=1
                ##print " y:%s x:%s" % (y, x)
                wsResCom.write(y, x, resumen_compras_ventas.base_imponible_tarifa_cero, linea_center)
                x+=1
                wsResCom.write(y, x, resumen_compras_ventas.base_imponible_tarifa_doce, linea_center)
                x+=1
                wsResCom.write(y, x, resumen_compras_ventas.valor_iva, linea_center)
                y+=1
                cont = 0

            y+=2
            x = 1
            wsResCom.write(y, x, "RESUMEN CONCEPTO DE RETENCION", style_cabecera)
            y+=1
            x = 1
            wsResCom.write(y, x, "CODIGO", style_cabecera)
            x = 2
            wsResCom.write(y, x, "CONCEPTO DE RETENCION", style_cabecera)
            x = 3
            wsResCom.write(y, x, "NUMERO REGISTROS", style_cabecera)
            x = 4
            wsResCom.write(y, x, "BASE IMPONIBLE", style_cabecera)
            x = 5
            wsResCom.write(y, x, "VALOR RETENCION", style_cabecera)
            
            for resumen_retenciones in obj_header.document_ats_resumen_concept_retent_ids:
                y+=1
                x = 1
                wsResCom.write(y, x, resumen_retenciones.codigo, linea_center)
                x+=1
                wsResCom.write(y, x, resumen_retenciones.documento, linea_left)
                x+=1
                wsResCom.write(y, x, resumen_retenciones.numero_documento, linea_center)
                x+=1
                wsResCom.write(y, x, resumen_retenciones.base_imponible_ir, linea_center)
                x+=1
                wsResCom.write(y, x, resumen_retenciones.retencion_ir, linea_center)
                
            
            
            y+=2
            x = 1
            wsResCom.write(y, x, "RETENCION EN LA FUENTE DEL IVA", style_cabecera)
            y+=1
            x = 2
            wsResCom.write(y, x, "CONCEPTO DE RETENCION", style_cabecera)
            x = 3
            wsResCom.write(y, x, "NUMERO REGISTROS", style_cabecera)
            x = 4
            wsResCom.write(y, x, "BASE IMPONIBLE", style_cabecera)
            x = 5
            wsResCom.write(y, x, "VALOR RETENCION", style_cabecera)             
                    
            for resumen_ret_fuente in obj_header.document_ats_resumen_retent_fuente_ids:
                y+=1
                x = 2
                wsResCom.write(y, x, resumen_ret_fuente.documento, linea_left)
                x+=1
                wsResCom.write(y, x, resumen_ret_fuente.numero_documento, linea_center)
                x+=1
                wsResCom.write(y, x, resumen_ret_fuente.base_imponible_ir, linea_center)
                x+=1
                wsResCom.write(y, x, resumen_retenciones.retencion_ir, linea_center)    
            
        
        
        ws.col(1).width = 3200
        ws.col(4).width = 7000
        ws.col(5).width = 7000
                
        buf = cStringIO.StringIO()
        
        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'data':out, 'name':'reporte_impuestos.xls'})

    _columns = {
                
            'data': fields.binary(string='Archivo'),
            'name':fields.char('Nombre', size=60),
            'company_id':fields.many2one('res.company','Compania')
    }
    _defaults = {  
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid,context=context).company_id.id,
        }                 
                                                                            

wizard_report_ats()
