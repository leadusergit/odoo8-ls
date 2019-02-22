# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Report Extend work
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

class wizard_report_customer(osv.osv_memory):
    _name='wizard.report.customer'
    _description='Analisis de Cartera de Cliente/Vendedor'
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def report_customer(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        return self._print_report_customer(cr, uid, ids, data, context=context) 
    
    def _print_report_customer(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {'type':'ir.actions.report.xml',
                  'report_name':'customer_portfolio',
                  'datas': data}
        return result
    
    def report_seller(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        return self._print_report_seller(cr, uid, ids, data, context=context) 
    
    def _print_report_seller(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {'type':'ir.actions.report.xml',
                  'report_name':'seller_portfolio',
                  'datas': data}
        return result
    
    def on_change_tipo(self, cr, uid, ids, tipo):
        ##print "on_change_tipo", tipo
        res = {}
        if tipo=='group':
            res['partner_id'] = False
            res['seller_id'] = False
        if tipo=='customer':
            res['seller_id'] = False
        if tipo=='seller':
            res['partner_id'] = False
        res['name'] =  False
        return {'value':res}
    
    def _format_date(self, date):
        if date:
            campos = date.split('-')
            date = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date
    
    def query(self, cr, uid,form):
        type = form.get('type', False)
        date_start = form.get('date_start', False)
        date_now = time.strftime('%Y-%m-%d')
        date_to = form.get('date', False)
        seller = form.get('seller_id', False)
        customer = form.get('partner_id', False)
        grupo = form.get('group_id', False)
        sql = ''
        where = ''
        group_by = ''
        res = []
        customers = []
        
        #Lineas del Saldo inicial
        if type in ('customer','group'):
            if customer:
                where = ' and partner_id='+str(customer)
            else:
                where = ' and partner_id is not null'
            
            if grupo:
                where = "and partner_id in (SELECT partner_id "\
                                                  "FROM res_partner_category_rel "\
                                                  "WHERE category_id ="+str(grupo)+") "
                
            sql_inicial = "select distinct partner_id "\
                          "from account_move_line "\
                          "where journal_id =19 and date between '%s' and '%s' "%(date_start,date_now)
            ##print 'sql_inicial', sql_inicial
            cr.execute(sql_inicial + where)
            res0 = [aux[0] for aux in cr.fetchall()]
        elif type in ('seller'):
            if seller:
                where = 'and seller_id = '+str(seller)
            else:
                where = 'and seller_id is not null'
                
            sql_inicial = "select partner_id, seller_id "\
                          "from account_move_line "\
                          "where journal_id =19 and date between '%s' and '%s' " %(date_start,date_now)
            group_by  = ' group by partner_id, seller_id'
            
                
            cr.execute(sql_inicial + where + group_by)
            res0 = cr.fetchall()
        
        query = "SELECT partner_id "\
                   "FROM account_invoice "\
                   "WHERE date_invoice BETWEEN '"+str(date_start)+"' and '"+str(date_now)+"' "\
                   "AND type in ('out_invoice','out_refund') AND state in ('open','paid') "
                   
        if type =='customer':
            if customer:
                where = "AND partner_id="+str(customer)+" "
            cr.execute(query + where)
            res1 = [aux[0] for aux in cr.fetchall()] 
                
            customers = res0 + res1    
            customers = list(set(customers))
            
        if type =='group':
            if grupo:
                where = "and partner_id in (SELECT partner_id "\
                                              "FROM res_partner_category_rel "\
                                              "WHERE category_id ="+str(grupo)+") "
            cr.execute(query + where)
            res1 = [aux[0] for aux in cr.fetchall()] 
                
            customers = res0 + res1    
            customers = list(set(customers))
        
        if type =='seller':
            if seller:
                where = " AND saleer_id="+str(seller)+" "
                
            else:
                where = " AND saleer_id is not null "
            
            query = "SELECT partner_id, saleer_id "\
                   "FROM account_invoice "\
                   "WHERE date_invoice BETWEEN '"+str(date_start)+"' and '"+str(date_now)+"' "\
                   "AND type in ('out_invoice','out_refund') AND state in ('open','paid') "
            group_by = 'group by partner_id, saleer_id'
           
                
            cr.execute(query + where + group_by)
            res1 = cr.fetchall()
            for i in res0:
                if i not in res1:
                   res1.append(i)
            
            sql = 'select rp.id as customer, ru.id as seller, rp.name, ru.name as vendedor '\
                  "from res_partner rp , res_users ru "\
                  "where rp.id in ("+','.join([str(x[0]) for x in res1])+") "\
                  "and ru.id in ("+','.join([str(x[1]) for x in res1])+") "\
                  "group by rp.id, ru.id, rp.name, ru.name order by rp.name, ru.name"
            
            ##print 'sql', sql
            cr.execute(sql)
            res = cr.dictfetchall()
            
        if type in ('customer','group') and customers:
            sql = "select id as customer, name "\
                      "from res_partner where id in ("+','.join([str(x) for x in customers])+") "\
                      "GROUP BY id,name ORDER BY name"
            ##print 'sql', sql
            cr.execute(sql)
            res = cr.dictfetchall()
        
        if res:
            for r in res:
                calle = ''
                nombre = ''
                if r['customer']:
                    partner = self.pool.get('res.partner').read(cr, uid ,[r['customer']],['ref','address'])[0]
                    ##print 'partner', partner
                    r['code'] = partner.get('ref',False)
                    if partner.get('address',[]):
                        for a in partner.get('address'):
                            address = self.pool.get('res.partner.address').read(cr, uid ,[a],['phone','street','name','city'])[0]
                            r['fono'] = address.get('phone', '')
                            if address.get('street', ''):
                                calle = tools.ustr(address.get('street'))
                            r['direccion'] = calle
                            r['contacto'] = address.get('name','')
                            r['city'] = address.get('city','')
                            break
        return res
    
    
    def detalles(self, cr, uid, customer, seller, form):
        retention_obj = self.pool.get('account.invoice.retention.voucher')
        date_start = form.get('date_start', False)
        date_to = form.get('date', False) #Fecha de corte
        date_now = time.strftime('%Y-%m-%d') #Buscar todas las facturas a la fecha del vendedor
        tipo = form.get('type', False)
        invoice_obj = self.pool.get('account.invoice')
        account_move_obj = self.pool.get('account.move')
        account_move_line = self.pool.get('account.move.line')
        
        sql = """SELECT id AS id, factura AS nro, date_invoice AS emision, date_due AS vencimiento, amount_total AS total
                     FROM account_invoice WHERE type = 'out_invoice'
                     AND state in ('open', 'paid')
                     AND date_invoice BETWEEN '%s' and '%s' """%(date_start,date_to)
        if tipo in ('customer','group'):
            if customer:
                where = 'AND partner_id = '+str(customer)+ ' '
        else:
            where = 'AND partner_id = '+str(customer) +' AND saleer_id='+str(seller) +' '
        order = 'order by factura'
        
        ##print 'sql + where + order', sql + where + order
        cr.execute(sql + where + order)
        res = cr.dictfetchall()
        vencidas = []
        por_vencer = []
        
        if res:
            for r in res:
                retencion = 0.00
                abono = 0.00
                saldo = 0.00
                debit = 0.00
                pagos = 0.00
                pagos_total =0.00
                valor_factura = 0.00
                diferencia = 0
                
                amount_note = 0.00
                note_diferencia = 0
                amount_note1 = 0.00
                
                advance_diferencia = 0
                amount_advance = 0.00
                amount_advance1 = 0.00
                
                opc = ''
                cr.execute("""SELECT order_id FROM sale_order_invoice_rel WHERE invoice_id = %s""",(r['id'],))
                order = cr.fetchone()
                if order != None:
                    sale_obj = self.pool.get('sale.order').browse(cr, uid, order[0])
                    for ol in sale_obj.order_line:
                        opc = ol.number_opc
                        break
                i = self.pool.get('account.invoice').browse(cr, uid ,r['id'])
                
                valor_factura = round(i.amount_total or 0.00,2)
                fecha = str(i.date_due).strip()
                if fecha != 'False':
                    diferencia = (self._format_date(i.date_due) - self._format_date(date_to)).days
                else:
                    continue
                ##print 'factura', i.factura
                ##print 'diferencia', diferencia
                #===============================================================
                # Diferencia de mayores dias de plazo
                #===============================================================
                if diferencia <= 0:
                   
                    for lines in i.payment_ids:#linea de todos los pagos
                        if self._format_date(lines.date) <= self._format_date(date_to): #Tomo solo los pagos menores a la fecha de corte y veo si esta pagada o no pagada a esa fecha
                            if lines.journal_id.name == 'Diario de Retenciones':
                                retencion += round(lines.credit or 0.00,2)
                            else:
                                pagos += round(lines.credit or 0.00, 2) - round(lines.debit or 0.00, 2)
                                
                            pagos_total += round(lines.credit or 0.00, 2) - round(lines.debit or 0.00, 2)

                    band = valor_factura - round(pagos_total or 0.00,2)
                    
                    if abs(round(band,2)) > 0.05: 
                        saldo = valor_factura - pagos - retencion
                        vencidas.append({'nro': r['nro'],
                                     'emision': r['emision'],
                                     'vencimiento' : r['vencimiento'],
                                     'dias': diferencia,
                                     'factura': r['total'],
                                     'retencion':retencion,
                                     'abono':pagos,
                                     'saldo':saldo,
                                     'opc':opc})
                elif diferencia > 0: #and diferencia <= 30:
                    for lines in i.payment_ids:#linea de todos los pagos
                        if self._format_date(lines.date) <= self._format_date(date_to): #Tomo solo los pagos menores a la fecha de corte y veo si esta pagada o no pagada a esa fecha
                            if lines.journal_id.name == 'Diario de Retenciones':
                                retencion += round(lines.credit or 0.00,2)
                            else:
                                pagos += round(lines.credit or 0.00, 2) - round(lines.debit or 0.00, 2)
                                
                            pagos_total += round(lines.credit or 0.00, 2) - round(lines.debit or 0.00, 2)
                    
                    band = valor_factura - round(pagos_total or 0.00,2)
                    #pagos += amount_note1
                    if abs(round(band,2)) > 0.05: 
                        saldo = valor_factura - pagos - retencion
                        por_vencer.append({'nro': r['nro'],
                                     'emision': r['emision'],
                                     'vencimiento' : r['vencimiento'],
                                     'dias': diferencia,
                                     'factura': r['total'],
                                     'retencion':retencion,
                                     'abono':pagos,
                                     'saldo': saldo,
                                     'opc':opc})
        #Anticipos de Clientes
        if seller:
            where = ' and stl.seller_id = '+str(seller)
                        
        sql2 = "select smr.statement_id as move, stl.date as emision, stl.amount as total, stl.date_maturity as vencimiento, stl.ref as nro "\
               "from account_bank_statement_line as stl "\
               "join account_bank_statement_line_move_rel  as smr on (stl.id = smr.move_id) "\
               "where stl.statement_type = 'ant' "\
               "and stl.partner_id="+str(customer)+" "\
               "and stl.date between '%s' and '%s'"%(date_start,date_to)+' '
               
               
        ##print 'sql2 anticipo', sql2
        
        cr.execute(sql2 + where)
        
        #Saco el extracto bancario sirve para ver la linea de la cuenta de clientes para cerrar
        movimiento = cr.dictfetchall()
        if movimiento:
            #Puedo saber los movimientos que realizo el extracto
            for mo in movimiento:
                
                reconcile_amount = 0.00
                partial_amount = 0.00
                
                amount_total = 0.00
                advance_diferencia = 0
                amount_advance = 0.00
                date_advance = str(mo['emision']).strip()
                line_id = None
                move_obj = account_move_obj.browse(cr, uid,mo['move'])
                
                for item in move_obj.line_id:
                    if item.credit > 0.0:
                        line_id = item.id
                 
                if line_id:
                    move_line = account_move_line.browse(cr, uid, line_id)
                if not line_id :
                    continue 
                
                if date_advance != 'False':
                    advance_diferencia = (self._format_date(mo['emision']) - self._format_date(date_to)).days
                    amount_total = round(mo['total'],2)
                    if advance_diferencia <= 0:
                        #Pagos y Cruces de los anticipos
                        if move_line.reconcile_id:
                            for rel in move_line.reconcile_id.line_id:
                                if self._format_date(rel.date) <= self._format_date(date_to):
                                    reconcile_amount += round(rel.credit or 0.00, 2)
                        elif move_line.reconcile_partial_id:
                            for rel in move_line.reconcile_partial_id.line_partial_ids:
                                if self._format_date(rel.date) <= self._format_date(date_to):
                                    partial_amount += round(rel.credit or 0.00,2)
                        #Saldo a favor o en contra    
                        amount_advance = amount_total - round(reconcile_amount or 0.00,2) - round(partial_amount or 0.00,2)
                        
                        if abs(round(amount_advance,2)) > 0.05:
                            vencidas.append({'nro': mo['nro'],
                                         'emision': mo['emision'],
                                         'vencimiento' : mo['vencimiento'],
                                         'dias': advance_diferencia,
                                         'factura': 0.00,
                                         'retencion':0.00,
                                         'abono': amount_total,
                                         'saldo': 0.00 - amount_advance,
                                         'opc':'ANTV'})
                    elif advance_diferencia > 0:
                        if move_line.reconcile_id:
                            for rel in move_line.reconcile_id.line_id:
                                if self._format_date(rel.date) <= self._format_date(date_to):
                                    reconcile_amount += round(rel.credit or 0.00, 2)
                        elif move_line.reconcile_partial_id:
                            for rel in move_line.reconcile_partial_id.line_partial_ids:
                                if self._format_date(rel.date) <= self._format_date(date_to):
                                    partial_amount += round(rel.credit or 0.00,2)
                            
                        amount_advance = amount_total - round(reconcile_amount or 0.00,2) - round(partial_amount or 0.00,2)
                        
                        if abs(round(amount_advance,2)) > 0.05:
                            por_vencer.append({'nro': mo['nro'],
                                     'emision': mo['emision'],
                                     'vencimiento' : mo['vencimiento'],
                                     'dias': advance_diferencia,
                                     'factura': 0.00,
                                     'retencion':0.00,
                                     'abono':amount_total,
                                     'saldo': 0.00 - amount_advance,
                                     'opc':'ANTPV'})
        #Lineas de Saldo inicial
        
        if seller:
            where = ' and seller_id = '+str(seller)
            
        else:
            where = ''
            
        sql3 ="""SELECT am.id as id, cast(am.name as date) as emision, am.ref AS nro, am.date_maturity as vencimiento, am.debit as total, am.credit as credit
                       FROM account_move_line am
                       WHERE am.partner_id = %s
                       AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226)
                       AND am.journal_id =19
                       AND am.date between '%s'AND '%s'
                       """%(customer,date_start,date_now)
        ##print 'sql3 saldo inicial', sql3
        order = ' order by am.ref desc'
        cr.execute(sql3 + where + order)
        res2 = cr.dictfetchall()
        ##print 'res2', res2
        if res2:
            for ml in res2:
                
                reconcile_amount = 0.00
                partial_amount = 0.00
                amount_total = 0.00
                diff = 0
                initial = 0.00
                
                move_obj = account_move_line.browse(cr, uid, ml['id'])
                date_vencimiento = str(ml['vencimiento']).strip()
                amount_total = round(ml['total'] or -ml['credit'],2)
                 
                if date_vencimiento != 'False':
                    diff = (self._format_date(date_vencimiento) - self._format_date(date_to)).days
                if diff  <= 0:
                    if move_obj.reconcile_id:
                        for rel in move_obj.reconcile_id.line_id:
                            
                            if self._format_date(rel.date) <= self._format_date(date_to):
                                reconcile_amount += round(rel.credit or 0.00, 2)
                    elif move_obj.reconcile_partial_id:
                        for rel in move_obj.reconcile_partial_id.line_partial_ids:
                            if self._format_date(rel.date) <= self._format_date(date_to):
                                partial_amount += round(rel.credit or 0.00,2)
                            
                    initial = amount_total - round(reconcile_amount or 0.00,2) - round(partial_amount or 0.00,2)
                    
                    if abs(round(initial,2)) > 0.05:
                        vencidas.insert(0,{'nro': str(ml['nro']).zfill(9),
                                     'emision': ml['emision'],
                                     'vencimiento' : ml['vencimiento'],
                                     'dias': diff,
                                     'factura': ml['total'] or -ml['credit'],
                                     'retencion':0.00,
                                     'abono':reconcile_amount or partial_amount or 0.00,
                                     'saldo': initial,
                                     'opc':'INI'})
                elif diff > 0:# and diff <= 30:
                    if move_obj.reconcile_id:
                        for rel in move_obj.reconcile_id.line_id:
                            if self._format_date(rel.date) <= self._format_date(date_to):
                                reconcile_amount += round(rel.credit or 0.00,2)
                    elif move_obj.reconcile_partial_id:
                        for rel in move_obj.reconcile_partial_id.line_partial_ids:
                            if self._format_date(rel.date) <= self._format_date(date_to):
                                partial_amount += round(rel.credit or 0.00,2)
                            
                    initial = amount_total - round(reconcile_amount or 0.00,2) - round(partial_amount or 0.00,2)
                    if abs(round(initial,2)) > 0.05:
                        por_vencer.insert(0,{'nro': str(ml['nro']).zfill(9),
                                     'emision': ml['emision'],
                                     'vencimiento' : ml['vencimiento'],
                                     'dias': diff,
                                     'factura': ml['total'] or -ml['credit'],
                                     'retencion':0.00,
                                     'abono':reconcile_amount or partial_amount or 0.00,
                                     'saldo': initial,
                                     'opc':'INI'})
                
        return {'vencidas':vencidas,'por_vencer':por_vencer}
    
    
    def action_excel(self, cr, uid, ids, context=None):
        wb = pycel.Workbook(encoding='utf-8')
        if context is None:
            context = {}
        data = {}
        data['form'] = self.read(cr, uid, ids)[0]
        form = data['form']
        date_to = form.get('date')
        
        #Formato de la Hoja de Excel
        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                        'align: vertical center, horizontal center;'
                                        )
            
        style_cabecerader = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal right;'
                                    )
        
        style_cabeceraizq = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal left;'
                                    )
        
        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center;'
                                    'borders: left 1, right 1, top 1, bottom 1;')
        
        linea = pycel.easyxf('borders:bottom 1;')
        
        linea_center = pycel.easyxf('font: colour black;'
                                   'align: vertical center, horizontal center;'
                                   )
        
        linea_izq = pycel.easyxf('font: colour black;'
                                   'align: vertical center, horizontal left;'
                                   )
        linea_der = pycel.easyxf('font: colour black;'
                                 'align: vertical center, horizontal right;'
                                  )
        
        ws = wb.add_sheet("Cartera Cliente")
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u"" 
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        ##print 'compania', compania
        x0=32
        #sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)
        ws.write_merge(1,1,1,x0,compania.name, style_cabecera)
        ws.write_merge(2,2,1,x0,'Direccion: '+compania.partner_id.street, style_cabecera)
        ws.write_merge(3,3,1,x0,'Ruc: '+compania.partner_id.ident_num, style_cabecera)
        if form.get('type',False)=='customer':
            ws.write_merge(4,4,1,x0,'Analisis de Cartera por Cliente', style_cabecera)
        elif form.get('type',False)=='group':
            ws.write_merge(4,4,1,x0,'Analisis de Cartera por Grupo', style_cabecera)
        elif form.get('type',False)=='seller':
            ws.write_merge(4,4,1,x0,'Analisis de Cartera por Vendedor', style_cabecera)
        
        x1=6 #Fechas
        ws.write_merge(x1,x1,1,10, 'Fecha de Corte: '+date_to, style_cabeceraizq)
        ws.write_merge(x1,x1,11,15, 'Hora:', style_cabecerader)
        ws.write_merge(x1,x1, 16,19, time.strftime('%H:%M:%S'), style_cabeceraizq)

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
        
        #Formato de Numero
        style = pycel.XFStyle()
        style.num_format_str = '#,##0.00'
        style.alignment = align
        style.font = font1
        
        #Formato de Numero Saldo
        font = pycel.Font()
        font.bold = True
        font.colour_index = 0x27
        
        style1 = pycel.XFStyle()
        style1.num_format_str = '#,##0.00'
        style1.alignment = align
        style1.font = font
        
        
        font2 = pycel.Font()
        font2.bold = True
        font2.colour_index = 0x0
        
        style2 = pycel.XFStyle()
        style2.num_format_str = '#,##0.00'
        style2.alignment = align
        style2.font = font2
        
        style3 = pycel.XFStyle()
        style3.num_format_str = '0'
        style3.alignment = align
        style3.font = font1
        
        
            
        'Busco los clientes'
        customers = self.query(cr, uid, form)
        
        amount_factura = 0.00
        amount_abono = 0.00
        amount_saldo = 0.00
        amount_retencion = 0.00
        
        xi = 8 # Cabecera de Cliente
        x = 12 # Cabecera Tabla Movimientos
        xm = 13 #Movimientos
        for item in customers:
            tot_factura = 0.00
            tot_abono = 0.00
            tot_saldo = 0.00
            tot_retencion = 0.00
            
            sum_factura = 0.00
            sum_abono = 0.00
            sum_saldo = 0.00
            sum_retencion = 0.00
            
            moves = self.detalles(cr, uid, item['customer'],item.get('seller',False),form)
            ##print 'detalles', moves
            if moves['vencidas'] or moves['por_vencer']:
                if form.get('type',False)=='seller':
                    ws.write_merge(xi-1,xi-1,20,23,'Vendedor:', linea_izq)
                    ws.write_merge(xi-1,xi-1,25,31,item.get('vendedor',''), linea_izq)
                ws.write_merge(xi,xi,1,3,'Codigo:', linea_izq)
                ws.write_merge(xi,xi,4,9,item['code'] or '', linea_izq)
                
                ws.write_merge(xi,xi,20,23,'Contacto:', linea_izq)
                ws.write_merge(xi,xi,25,31,item['contacto'] or '', linea_izq)
                
                ws.write_merge(xi+1,xi+1,1,3,'Nombre:', linea_izq)
                ws.write_merge(xi+1,xi+1,4,17,item['name'] or '', linea_izq)
                
                ws.write_merge(xi+1,xi+1,20,23,'Telefono:', linea_izq)
                ws.write_merge(xi+1,xi+1,25,31,item['fono'] or '', linea_izq)
                
                ws.write_merge(xi+2,xi+2,1,3,'Ciudad: ', linea_izq)
                ws.write_merge(xi+2,xi+2,4,9,item['city'] or '', linea_izq)
                
                ws.write_merge(xi+2,xi+2,20,23,'Direccion:', linea_izq)
                ws.write_merge(xi+2,xi+2,25,31,item['direccion'] or '', linea_izq)
                
                ws.write_merge(x,x,0,2,'Nro.Factura', style_header)
                ws.write(x,3,'Nro.OPC', style_header)
                ws.write_merge(x,x,4,8,'Fecha Emision', style_header)
                ws.write_merge(x,x,9,12,'Fecha Vence', style_header)
                ws.write_merge(x,x,13,16,'Valor Factura', style_header)
                ws.write_merge(x,x,17,20,'Abono', style_header)
                ws.write_merge(x,x,21,24,'Ret.', style_header)
                ws.write_merge(x,x,25,28,'Saldo', style_header)
                ws.write_merge(x,x,29,31,'Dias', style_header)
            
            if moves['vencidas']:
                ws.write_merge(xm,xm,1,9,'Vencidas', style_cabeceraizq)
                xm = xm + 1
                for mov in moves['vencidas']:
                    ws.write_merge(xm,xm,0,2,mov['nro'], linea_center)
                    ws.write(xm,3,mov['opc'], linea_center)
                    ws.write_merge(xm,xm,4,8,mov['emision'], linea_center)
                    ws.write_merge(xm,xm,9,12,mov['vencimiento'], linea_center)
                    
                    ws.write_merge(xm,xm,13,16,mov['factura'], style)
                    sum_factura += mov['factura']
                    
                    ws.write_merge(xm,xm,17, 20,mov['abono'], style)
                    sum_abono += mov['abono']
                    
                    ws.write_merge(xm,xm,21, 24,mov['retencion'], style)
                    sum_retencion += mov['retencion']
                    
                    
                    ws.write_merge(xm,xm,25,28,mov['saldo'], style)
                    sum_saldo += mov['saldo']
                    
                    ws.write_merge(xm,xm,29,31,mov['dias'], style3)
                    xm += 1
                    
                tot_factura += sum_factura
                tot_abono += sum_abono
                tot_retencion += sum_retencion
                tot_saldo += sum_saldo
                
                ws.write_merge(xm,xm,9,12,'Total Vencidas',style2)
                ws.write_merge(xm,xm,13,16,sum_factura,style2)
                ws.write_merge(xm,xm,17,20,sum_abono,style2)
                ws.write_merge(xm,xm,21,24,sum_retencion,style2)
                ws.write_merge(xm,xm,25,28,sum_saldo,style2)
                xm += 1
                
            sum_factura = 0.00
            sum_abono = 0.00
            sum_saldo = 0.00
            sum_retencion = 0.00
            
            if moves['por_vencer']:
                xm += 1
                ws.write_merge(xm,xm,1,9,'Por Vencer', style_cabeceraizq)
                xm = xm + 1
                for mov in moves['por_vencer']:
                    ws.write_merge(xm,xm,0,2,mov['nro'], linea_center)
                    ws.write(xm,3,mov['opc'], linea_center)
                    ws.write_merge(xm,xm,4,8,mov['emision'], linea_center)
                    ws.write_merge(xm,xm,9,12,mov['vencimiento'], linea_center)
                    
                    ws.write_merge(xm,xm,13,16,mov['factura'], style)
                    sum_factura += mov['factura']
                    
                    ws.write_merge(xm,xm,17, 20,mov['abono'], style)
                    sum_abono += mov['abono']
                    
                    ws.write_merge(xm,xm,21, 24,mov['retencion'], style)
                    sum_retencion += mov['retencion']
                    
                    
                    ws.write_merge(xm,xm,25,28,mov['saldo'], style)
                    sum_saldo += mov['saldo']
                    
                    ws.write_merge(xm,xm,29,31,mov['dias'], style3)
                    xm += 1
                    
                tot_factura += sum_factura
                tot_abono += sum_abono
                tot_saldo += sum_saldo
                tot_retencion += sum_retencion
                
                    
                ws.write_merge(xm,xm,9,12,'Total Por Vencer',style2)
                ws.write_merge(xm,xm,13,16,sum_factura,style2)
                ws.write_merge(xm,xm,17,20,sum_abono,style2)
                ws.write_merge(xm,xm,21,24,sum_retencion,style2)
                ws.write_merge(xm,xm,25,28,sum_saldo,style2)
                xm += 1
            
            if moves['vencidas'] or moves['por_vencer']:
                
                ws.write_merge(xm,xm,9,12,'Total',style2)
                ws.write_merge(xm,xm,13,16,tot_factura,style2)
                ws.write_merge(xm,xm,17,20,tot_abono,style2)
                ws.write_merge(xm,xm,21,24,tot_retencion,style2)
                ws.write_merge(xm,xm,25,28,tot_saldo,style2)
                xm += 1
                ws.write_merge(xm,xm,0,31,'',linea)
                xi = xm + 2
                x = xi + 4
                xm = x + 1
                
                amount_factura += tot_factura
                amount_abono += tot_abono
                amount_retencion += tot_retencion
                amount_saldo += tot_saldo
        
        if len(customers) > 1:
            xi+=1
            ws.write_merge(xi,xi,9,12,'Total General',style2)
            ws.write_merge(xi,xi,13,16,amount_factura,style2)
            ws.write_merge(xi,xi,17,20,amount_abono,style2)
            ws.write_merge(xi,xi,21,24,amount_retencion,style2)
            ws.write_merge(xi,xi,25,28,amount_saldo,style2)
        
        w = 500
        y = 1000
        w0 = 2000
        w1 = 3000
        w2 = 1500
        
        ws.col(0).width = y
        ws.col(1).width = y
        ws.col(2).width = y
        ws.col(3).width = w1
        ws.col(4).width = 100
        ws.col(5).width = w2
        ws.col(6).width = w
        ws.col(7).width = 1000
        ws.col(8).width = 1000
        ws.col(9).width = 1500
        ws.col(10).width = w
        ws.col(11).width = w
        ws.col(12).width = 1500
        ws.col(13).width = 1500
        ws.col(14).width = w
        ws.col(15).width = w
        ws.col(16).width = 1000
        ws.col(17).width = 1000
        ws.col(18).width = w
        ws.col(19).width = w
        ws.col(20).width = 1000
        ws.col(21).width = 1000
        ws.col(22).width = 1000
        ws.col(23).width = 1000
        ws.col(24).width = 1000
        ws.col(25).width = 1000
        ws.col(26).width = 1000
        ws.col(27).width = 1000
        ws.col(28).width = 1000
        ws.col(29).width = 1000
        ws.col(30).width = 1000
        ws.col(31).width = 1000
        ws.col(32).width = 1000
        ws.col(33).width = 1000
        ws.col(34).width = 1000
        ws.col(35).width = 1000
        ws.col(36).width = 1000
        ws.col(37).width = w
        ws.col(38).width = w
        ws.col(39).width = w
        ws.col(40).width = w                
        buf= cStringIO.StringIO()
        
        wb.save(buf)
        out=base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'data':out, 'name':'cartera_cliente.xls'})

        
    _columns={
              'type':fields.selection([('seller','Vendedor'),
                                       ('customer','Cliente'),
                                       ('group','Grupo'),
                                       ], 'Agrupadas por', help="Vendedor: Reporte Agrupado por Vendedor\n"\
                                                                "Cliente: Reporte Agrupado por Cliente\n"\
                                                                "Grupo: Reporte Agrupado por Grupo de Cliente\n"),
              'partner_id':fields.many2one('res.partner', 'Clientes', domain=[('customer','=',True),('active','=',True) ]),
              'seller_id':fields.many2one('res.users', 'Vendedor(a)', domain=[('groups_id','in',[21,20])]),
              'group_id':fields.many2one('res.partner.category', 'Grupo', domain=[('parent_id','=',4)]),
              'date':fields.date("Fecha de Corte"),
              'date_start':fields.date("Fecha Inicio A.Fiscal", help="Inicio del Periodo Fiscal para Induvallas"),
              'data': fields.binary(string='Archivo'),
              'name':fields.char('Nombre', size=60),
    }
    _defaults = {
        'date': lambda * a: time.strftime('%Y-%m-%d'),
        'date_start': lambda * a: time.strftime('2011-07-01'),#Informacion Valida de FActuras al OpenErp
        'type': lambda *a: 'seller',
    }

wizard_report_customer()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: