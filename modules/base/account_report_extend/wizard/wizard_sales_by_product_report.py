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

__author__ = 'edison.guachamin@atikasoft.com.ec (Edison G.)'

import cStringIO
import base64
import StringIO
import csv
import time
from openerp.osv import fields, osv
import mx.DateTime
from mx.DateTime import RelativeDateTime
import openerp.tools
import datetime
import xlwt as pycel #Libreria que Exporta a Excel
from openerp.tools import config
bancos = []

class wizard_report_sales(osv.osv_memory):
    _name = "wizard.report.sales"
    _description = 'Reporte de Ventas por Producto y Vendedor'
    
    def _get_period(self, cr, uid, ids, context=None):
        return self.pool.get('account.period').find(cr, uid)[0]
    
    def _format_date(self, date):
        if date:
            campos = date.split('-')
            date = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date
    
    def _get_seller(self, cr, uid,form):
        
        if form.get('seller_ids', False):
            sql = 'select id, name as vendedor from res_users where active is True and id in ('+','.join([str(x)for x in form.get('seller_ids', False)])+") order by name"
        else:
            sql = "select id, name as vendedor from res_users where active is True and id in (select distinct uid from res_groups_users_rel where gid in(20,21)) order by name"
        ##print 'sqlk', sql
        cr.execute(sql)
        #res = [aux[0] for aux in cr.fetchall()]
        res = cr.dictfetchall()
        return res
    
    def _get_product (self, cr, uid, form):
        
        if form.get('product_ids', False):
            sql = "select pp.id, pp.default_code as code, pt.name as producto, pu.name as unidad from product_product as pp "\
                  "join product_template as pt on (pp.product_tmpl_id=pt.id) "\
                  "join product_uom as pu on (pt.uom_id=pu.id) "\
                  "where pp.id in ("+','.join([str(x)for x in form.get('product_ids', False)])+")"\
                  "order by pt.name"
        else:
            sql = "select pp.id, pp.default_code as code, pt.name as producto, pu.name as unidad from product_product as pp "\
                  "join product_template as pt on (pp.product_tmpl_id=pt.id) "\
                  "join product_uom as pu on (pt.uom_id=pu.id) "\
                 " where pp.product_tmpl_id in (select id from product_template where sale_ok is True) "\
                  "order by pt.name"
        ##print "sql", sql
        cr.execute(sql)
        res = cr.dictfetchall()
        return res
    
    def _get_invoices(self, cr,uid, seller_id, form):
        productos = self._get_product(cr, uid, form)
        sql = "select ai.id from account_invoice as ai "\
              "join account_invoice_line as ail on (ail.invoice_id = ai.id) "\
              "where ai.saleer_id="+str(seller_id)+" and ail.product_id in("+','.join([str(x['id']) for x in productos])+") "\
              "and ai.type in ('out_invoice','out_refund') "\
              "and ai.state in ('open','paid') "
        if form.get('filter')=='by_date':
            where = (" and ai.date_invoice between '%s' and '%s' ") % (form.get('date_from'), form.get('date_to'))
        else:
            where = (" and ai.period_id =%s") % (form.get('period_id'))
        cr.execute(sql + where)
        res = cr.dictfetchall()
        return res
    
    
    
    def _get_lines(self, cr, uid,form,seller_id, product_id):
        #result = []
        
        account_invoice_obj = self.pool.get('account.invoice')
        account_period_obj = self.pool.get('account.period')
        
        date_now = time.strftime('%Y-%m-%d')
        
        filter = form.get('filter')
        type = form.get('type')
        if form.get('group_by')=='by_none':
            sql_header = "select  ai.type as tipo, ai.factura, ail.quantity as cantidad, ail.price_unit as precio_unitario, ail.price_subtotal as precio_total, ail.discount as descuento"
            
        else:
            sql_header = "select  ai.type as tipo, ai.factura as factura, sum(ail.quantity) as cantidad, ail.price_unit as precio_unitario, sum(ail.price_subtotal) as precio_total, sum(ail.discount) as descuento"
            group = " group by tipo, factura, precio_unitario"
        
        sql=" from account_invoice as ai "\
              "join account_invoice_line as ail on (ail.invoice_id=ai.id) "\
              "where ai.state in ('open','paid') "\
              "and ai.type in ('out_invoice','out_refund') "
        if filter =='by_date':
            where = (" and ai.date_invoice between '%s' and '%s' ") % (form.get('date_from'), form.get('date_to'))
        else:
            where = (" and ai.period_id =%s") % (form.get('period_id'))
        if type=='by_seller':
            tipo = "and ail.product_id="+str(product_id) + " and ai.saleer_id ="+str(seller_id)+" "
        else:
             tipo = "and ail.product_id="+str(product_id)
        ##print 'lineas', sql+where
        if form.get('group_by')=='by_none':
            cr.execute(sql_header+ sql + where + tipo)
        else:
            cr.execute(sql_header + sql + where + tipo + group)
        
        result = cr.dictfetchall()
        #invoices = [x[0] for x in cr.fetchall()]
        ##print 'invoices', invoices
        return result 
    
    def action_excel(self, cr, uid, ids, context=None):
        ##print 'context', context
        account_move_line_obj = self.pool.get('account.move.line')
        
        wb = pycel.Workbook(encoding='utf-8')
        if context is None:
            context = {}
        data = {}
        data['form'] = self.read(cr, uid, ids)[0]
        form = data['form']
        ##print'form', form
        
        #Formato de la Hoja de Excel
        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                        'align: vertical center, horizontal center;'
                                        )
            
        style_cabecerader = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal right;',
                                    num_format_str='#,##0.00'
                                    )
        
        style_cabeceraizq = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal left;'
                                    )
        
        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center;'
                                    'borders: left 1, right 1, top 1, bottom 1;')
        
        linea = pycel.easyxf('borders:bottom 1;')
        
        linea_center = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal center;')
        
        linea_izq = pycel.easyxf('font: colour black, bold True;'
                                   'align: vertical top, horizontal left, wrap True;')
        #Numero
        linea_der = pycel.easyxf('font: colour black, height 140;'
                                 'align: vertical center, horizontal right;',
                                 num_format_str='#,##0.00'
                                )
        linea_der1 = pycel.easyxf('font: colour black, bold True;'
                                 'align: vertical center, horizontal right;'
                                )
        
        ws = wb.add_sheet("Reporte de Ventas")
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u"" 
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        ##print 'compania', compania
        x0=7
        #sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)
        ws.write_merge(1,1,1,x0,compania.name, style_cabecera)
        ws.write_merge(2,2,1,x0,tools.ustr('Dirección: ')+compania.partner_id.street, style_cabecera)
        ws.write_merge(3,3,1,x0,'Ruc: '+compania.partner_id.ident_num, style_cabecera)
        if form.get('type')=='by_seller':
            ws.write_merge(4,4,1,x0,'REPORTE VENTAS DE PRODUCTOS POR VENDEDOR', style_cabecera)
        else:
            ws.write_merge(4,4,1,x0,'REPORTE VENTAS DE PRODUCTOS', style_cabecera)
        
        x1=6 #Fechas
        if form.get('filter') == 'by_date':
            date_from = form.get('date_from')
            date_to = form.get('date_to')
        else:
            period_obj = self.pool.get('account.period').browse(cr, uid, form.get('period_id'))
            date_from = period_obj.date_start
            date_to = period_obj.date_stop
            
        ws.write_merge(x1,x1,1,3, 'Fecha Desde: '+date_from, style_cabeceraizq)
        ws.write_merge(x1,x1,4,5, 'Fecha Hasta: '+date_to, style_cabeceraizq)
        ws.write(x1,6,'Hora:', style_cabecerader)
        ws.write_merge(x1,x1, 7,8, time.strftime('%H:%M:%S'), style_cabeceraizq)

        ws.fit_num_pages = 1
        ws.fit_height_to_pages = 0
        ws.fit_width_to_pages = 1
        #ws.paper_size_code = 1
        ws.portrait = 1
        
        align = pycel.Alignment()
        align.horz = pycel.Alignment.HORZ_RIGHT  
        align.vert = pycel.Alignment.VERT_CENTER
        
        font1 = pycel.Font()
        font1.colour_index = 0x0
        font1.height = 140
        
        #Formato de Numero
        style = pycel.XFStyle()
        style.num_format_str = '#,##0.00'
        style.alignment = align
        style.font = font1
        
        #Formato de Numero Saldo
        font = pycel.Font()
        font.bold = True
        
        style1 = pycel.XFStyle()
        style1.num_format_str = '#,##0.00'
        style1.alignment = align
        style1.font = font
        
        
        font2 = pycel.Font()
        font2.bold = True
        
        style2 = pycel.XFStyle()
        style2.alignment = align
        style2.font = font2
        
        
        x = 7
        
        ws.write(x,1,'Producto', style_header)
        ws.write(x,2,'Tipo', style_header)
        ws.write(x,3,'Factura', style_header)
        ws.write(x,4,'Unidad', style_header)
        ws.write(x,5,'Cantidad', style_header)
        ws.write(x,6,'Precio Unit.', style_header)
        ws.write(x,7,'Desc. %', style_header)
        ws.write(x,8,'Precio Tot.', style_header)
        
        xm = 8#Movimientos
        
        'Busco los Vendedores Primer Caso' 
        if form.get('type')=='by_seller':
            get_seller = self._get_seller(cr, uid, form)
            if get_seller:
                s1amount0 = s1amount1 = s1amount2 = s1amount3 =0
                for s in get_seller:
                    
                    samount0 = samount1 = samount2 = samount3=0
                    
                    productos = self._get_product(cr, uid, form)
                    band = self._get_invoices(cr, uid, s['id'], form)
                    if not band:
                        continue
                    
                    ws.write_merge(xm,xm,0,7,'Vendedor:'+' '+s['vendedor'], linea_izq)
                    
                    for p in productos:
                        amount0 = amount1 = amount2 = amount3=0
                        
                        code = p.get('code','') 
                        name = p['producto']
                        if code:
                            name = name +' - '+code 
                        detalle = self._get_lines(cr, uid, form, s['id'], p['id'])
                        
                        if detalle:
                            sum0=sum1=sum2=sum3=0
                            xm += 1
                            ws.write_merge(xm,xm,1,7,name, linea_izq)
                            xm += 1
                            for moves in detalle:
                                ##print moves
                                if moves['tipo'] =='out_invoice':
                                    tipo = 'FAC'
                                    signo = 1
                                else:
                                    tipo = 'N.C'
                                    signo = -1
                                ws.write(xm,2,tipo, linea_center)
                                ws.write(xm,3,moves['factura'], linea_center)
                                ws.write(xm,4,p['unidad'], linea_center)
                                ws.write(xm,5,moves['cantidad'], linea_center)
                                sum0+=moves['cantidad']
                                ws.write(xm,6,moves['precio_unitario'], linea_der)
                                #sum1+=moves['precio_unitario']
                                
                                ws.write(xm,7,moves['descuento'], linea_der)
                                sum2+=moves['descuento']
                                
                                ws.write(xm,8,signo*moves['precio_total'], linea_der)
                                sum3+= signo*moves['precio_total']
                                xm += 1
                            amount0+=sum0
                            #amount1+=sum1
                            amount2+=sum2
                            amount3+=sum3
                            
                            #xm += 1    
                            ws.write_merge(xm,xm,1,4,'TOTAL PRODUCTO', style_cabecerader)
                            ws.write(xm,5,amount0, linea_center)
                            #ws.write(xm,6,amount1, linea_der)
                            ws.write(xm,7,amount2, linea_der)
                            ws.write(xm,8,amount3, linea_der)
                            xm += 1
                        
                        samount0+=amount0
                       # samount1+=amount1
                        samount2+=amount2
                        samount3+=amount3
                        
                    
                    s1amount0+=samount0
                    #s1amount1+=samount1
                    s1amount2+=samount2
                    s1amount3+=samount3
                    #xm+=1
                    ws.write_merge(xm,xm,1,4,'TOTAL VENDEDOR', style_cabecerader)
                    ws.write(xm,5,samount0, linea_center)
                    #ws.write(xm,6,samount1, linea_der)
                    ws.write(xm,7,samount2, linea_der)
                    ws.write(xm,8,samount3, linea_der)
                    xm+=1
                #xm+=1
                ws.write_merge(xm,xm,1,4,'TOTAL GENERAL', style_cabecerader)
                ws.write(xm,5,s1amount0, linea_center)
                #ws.write(xm,6,s1amount1, linea_der)
                ws.write(xm,7,s1amount2, linea_der)
                ws.write(xm,8,s1amount3, linea_der)
        else:
            samount0 = samount1 = samount2 = samount3=0
            productos = self._get_product(cr, uid, form)
            for p in productos:
                amount0 = amount1 = amount2 = amount3=0
                code = p.get('code','') 
                name = p['producto']
                if code:
                    name = name +' - '+code 
                detalle = self._get_lines(cr, uid, form, False, p['id'])
                if detalle:
                    sum0 = sum1 = sum2 = sum3 =0
                    xm += 1
                    ws.write_merge(xm,xm,1,7,name, linea_izq)
                    xm += 1
                    for moves in detalle:
                        if moves['tipo'] =='out_invoice':
                            tipo = 'FAC'
                            signo = 1
                        else:
                            tipo = 'N.C'
                            signo = -1
                        ws.write(xm,2,tipo, linea_center)
                        ws.write(xm,3,moves['factura'], linea_center)
                        ws.write(xm,4,p['unidad'], linea_center)
                        ws.write(xm,5,moves['cantidad'], linea_center)
                        sum0 += moves['cantidad']
                        
                        ws.write(xm,6,moves['precio_unitario'], linea_der)
                        #sum1 += moves['precio_unitario']
                        
                        ws.write(xm,7,moves['descuento'], linea_der)
                        sum2 += moves['descuento']
                        
                        ws.write(xm,8,signo*moves['precio_total'], linea_der)
                        sum3 += signo*moves['precio_total']
                        
                        xm += 1
                        
                    amount0+=sum0
                    #amount1+=sum1
                    amount2+=sum2
                    amount3+=sum3
                    
                    ws.write_merge(xm,xm,1,4,'TOTAL PRODUCTO', linea_der1)
                    ws.write(xm,5,amount0, linea_center)
                    #ws.write(xm,6,amount1, linea_der)
                    ws.write(xm,7,amount2, linea_der)
                    ws.write(xm,8,amount3, linea_der)
                    xm+=1
                
                samount0+=amount0
                #samount1+=amount1
                samount2+=amount2
                samount3+=amount3    
                
            ws.write_merge(xm,xm,1,4,'TOTAL GENERAL', linea_der1)
            ws.write(xm,5,samount0, linea_center)           
            #ws.write(xm,6,samount1, linea_der)
            ws.write(xm,7,samount2, linea_der)
            ws.write(xm,8,samount3, linea_der)
        y = 3000
        
        ws.col(0).width = 500
        ws.col(1).width = 8000
        ws.col(2).width = y 
        ws.col(3).width = y
        ws.col(4).width = y
        ws.col(5).width = y
        ws.col(6).width = y
        ws.col(7).width = y

        
        buf= cStringIO.StringIO()
        
        wb.save(buf)
        out=base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'data':out, 'name':'Ingresos.xls'})
     

    _columns = {
            'product_ids':fields.many2many('product.product','product_line_rel', 'wizard_id', 'product_id','Producto', domain=[('sale_ok','=',True)]),
            'date_start':fields.date('Fecha Inicio'),
            'date_from':fields.date('Fecha Desde'),
            'date_to':fields.date('Fecha Hasta'),
            'period_id':fields.many2one('account.period', 'Periodo'),
            'seller_ids':fields.many2many('res.users','users_line_rel', 'wizard_id', 'seller_id','Vendedor(a)', domain=[('groups_id','in',[21,20]),
                                                                                                                        ('active','=',True)]),
            'filter':fields.selection([('by_date','Fecha'),
                                       ('by_period','Periodo'),
                                      ], 'Filtrar por', required=True),
            'type':fields.selection([('by_product','Por Producto'),
                                       ('by_seller','De Producto por Vendedor'),
                                      ], 'Reporte de Ventas', required=True),
            'group_by':fields.selection([('by_product','Por Producto'),
                                       ('by_none','Sin Agrupar'),
                                      ], 'Agrupar', required=True),
            'data': fields.binary(string='Archivo'),
            'name':fields.char('Nombre', size=60),
        }                            
                                                                              
    _defaults = {
        'date_from': lambda * a: time.strftime('%Y-%m-01'),
        'date_to': lambda * a: time.strftime('%Y-%m-%d'),
        'date_start': lambda * a: time.strftime('2011-07-01'),
        'period_id':_get_period,
        'group_by':lambda * a: 'by_none',
        'filter':lambda * a: 'by_date',
        'type':lambda * a: 'by_seller',
        }
        
wizard_report_sales()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
