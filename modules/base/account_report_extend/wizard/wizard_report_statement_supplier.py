# -*- encoding: utf-8 -*-
##############################################################################
#
#    Billboard work
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
#creador  *EG


from openerp.osv import fields, osv
import time
import xlwt as pycel
import cStringIO
import base64
import datetime
import openerp.tools
import re

class wizard_supplier_statement(osv.osv_memory):
    _name = "wizard.supplier.statement"
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        
        result = {'type':'ir.actions.report.xml',
                  'report_name': 'supplier_estado_cuenta',
                  'datas': data}
        return result
     
    def generate_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        return self._print_report(cr, uid, ids, data, context=context)
    
    def onchange_dates(self, cr, uid, ids, date_from, date_to):
        res ={}
        if date_from and date_to:
            if date_from > date_to:
                res['date_start'] = date_to 
                raise osv.except_osv("Aviso",'La fecha Desde debe ser menor a la fecha Hasta')
#             else:
                #print "bien"
        return {'value':res}
    
    def is_date(self, name):
        if name:
            campos = name.split('-')
            if len(campos)==3:
                return True
            
    def _format_date(self, date):
        if date:
            campos = date.split('-')
            date = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date
    
    def saldo (self, cr, uid, supplier, form ):
        res = {}
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        
        date_start = form.get('date_start', False) #Inicio del registro de informacion
        
        invoice_obj = self.pool.get('account.invoice')
        account_move_obj = self.pool.get('account.move')
        account_move_line = self.pool.get('account.move.line')
        
        date_now = time.strftime('%Y-%m-%d')
        
        saldo = 0.0
        if supplier:
            #Saldo de Facturas - Retenciones y Notas de Credito y Cruces de Facturas
            sql = """SELECT id AS id, date_invoice AS emision, amount_total AS total, ret_voucher_id as retencion
                         FROM account_invoice WHERE type = 'in_invoice'
                         AND partner_id = '%s'
                         AND state in ('open', 'paid')
                         AND date_invoice BETWEEN '%s' AND '%s' 
                         """%(supplier, date_start, date_now)
            ##print 'Facturas sql', sql
            cr.execute(sql)
            res = cr.dictfetchall()
            if res:
                for r in res:
                    amount_invoice = 0
                    amount_advance = 0.00
                    amount_inicial = 0.00
                    
                    info_invoice = invoice_obj.read(cr, uid ,r['id'], ['payment_ids','residual'])
                    
                    if self._format_date(r['emision']) >= self._format_date(date_start) \
                       and self._format_date(r['emision']) < self._format_date(date_from):
                        saldo += r['total']
                    
                    if info_invoice['payment_ids']: #Todos los pagos
                        for payment in info_invoice['payment_ids']:
                            
                            payments_info = account_move_line.read(cr, uid, payment,['date','debit','credit'])
                            
                            #Veo los pagos menores a la  fecha desde
                            if self._format_date(payments_info['date']) < self._format_date(date_from):
                                
                                saldo += payments_info['debit'] - payments_info['credit']
                            
            
                                
            #Muestro todas las lineas del saldo inicial para que se muestre                 
            #===============================================================
            #Lineas de Saldo inicial de Proveedores
            sql3 ="""SELECT am.id as id, am.debit as debit, am.credit as credit, am.date as date, am.ref as ref, am.name as name
                     FROM account_move_line am
                     WHERE am.partner_id = %s
                     AND am.account_id in (SELECT id FROM account_account WHERE parent_id = 1332)
                     AND am.journal_id =19
                     AND am.date between '%s' and '%s' """%(supplier,date_start,date_now)
             
            ##print 'sql3 saldo inicial', sql3
             
            cr.execute(sql3)
            res2 = cr.dictfetchall()
            
            if res2:
                for ml in res2:
                    move_obj = account_move_line.browse(cr, uid, ml['id'])
                    #Sumo el saldo inicial
                    
                    if not self.is_date(move_obj.name):
                        continue
                    
                    if self._format_date(move_obj.name) < self._format_date(date_from):
                        saldo += ml['debit'] - ml['credit']
                          
                    if move_obj.reconcile_id:
                        for rel in move_obj.reconcile_id.line_id:
                            if self._format_date(rel.date) < self._format_date(date_from):
                                saldo -= round(rel.debit or 0.00, 2)
                    elif move_obj.reconcile_partial_id:
                        for rel in move_obj.reconcile_partial_id.line_partial_ids:
                            if self._format_date(rel.date) < self._format_date(date_from):
                                saldo -= round(rel.debit or 0.00, 2)
   
        return saldo
    
    def get_supplier(self, cr, uid, form):
        supplier = form.get('partner_id', False)
        date_start = form.get('date_start', False)
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        address_obj = self.pool.get('res.partner.address')
        if supplier:
            sql="SELECT id, name as supplier FROM res_partner WHERE supplier is True AND id ="+str(supplier)+ "AND active is True"
            cr.execute(sql)
            res = cr.dictfetchall()
        else:
            sql="""SELECT id, name as supplier FROM res_partner WHERE supplier is True AND active is True 
                   AND id in (SELECT partner_id FROM account_move_line WHERE date  BETWEEN '%s' AND '%s'AND statement_id > 1
                              AND reconcile_id > 1 AND account_id in (SELECT id FROM account_account WHERE parent_id = 1332))"""%(date_from,date_to)
            cr.execute(sql)
            pagos = [aux[0] for aux in cr.fetchall()]
            sql="""SELECT id, name as supplier FROM res_partner WHERE supplier is True AND active is True
                    AND id in (SELECT partner_id FROM account_invoice WHERE date_invoice BETWEEN '%s' AND '%s' AND state in ('open', 'paid')
                    AND type in ('in_invoice', 'in_refund'))
                    """%(date_from,date_to)
            cr.execute(sql)
            facturas = [aux[0] for aux in cr.fetchall()]
            sql="""SELECT id, name as supplier FROM res_partner WHERE supplier is True AND active is True 
                   AND id in (SELECT partner_id FROM account_move_line WHERE date  BETWEEN '%s' AND '%s'AND reconcile_partial_id > 1 
                   AND account_id in (SELECT id FROM account_account WHERE parent_id = 1332))"""%(date_from,date_to)
            cr.execute(sql)
            abonos = [aux[0] for aux in cr.fetchall()]
            sql="""SELECT id, name as supplier FROM res_partner WHERE supplier is True AND active is True 
                   AND id in (SELECT partner_id FROM account_move_line WHERE date  BETWEEN '%s' AND '%s' AND journal_id =19 
                              AND account_id in (SELECT id FROM account_account WHERE parent_id = 1332))"""%(date_start,date_to)
            cr.execute(sql)
            iniciales = [aux[0] for aux in cr.fetchall()]
            partners = pagos + facturas + abonos + iniciales
            ##print "1", partners
            partner = list(set(partners))
            ##print "2", partner
            if partner:
                sql = "select id, name as supplier from res_partner where id in ("+','.join([str(x) for x in partner])+") order by name"
                cr.execute(sql)
                res = cr.dictfetchall()
            else:
                res =[] 
        if res:
            for r in res:
                city = ''
                street = ''
                phone = ''
                representante = ''
                zona = ''
                info_partner = self.pool.get('res.partner').read(cr, uid, r['id'],['property_account_payable',
                                                                                   'comment','ident_num','ref','address'])
                if info_partner['property_account_payable']:
                    r['codcontable']= info_partner['property_account_payable'][1]
                else:
                    r['codcontable']= ''
                r['ruc'] = info_partner.get('ident_num','')
                r['cod'] = info_partner.get('ref','')
                if info_partner['address']:
                    addres_info = address_obj.read(cr, uid,info_partner['address'][0],['state_id','city','street','phone'])
                    ##print 'addres_info', addres_info
                    zona = addres_info['state_id']
                    city = addres_info['city']
                    street = tools.ustr(addres_info['street']).strip()
                    phone = addres_info['phone']
                
                ##print 'zona', zona
                if zona:
                    r['zona'] = zona[1]
                else:
                    r['zona'] = ''
                r['city'] = city or ''
                r['street'] = street or ''
                r['phone']= phone or ''
        return res
        
        return res
    
    def moves_supplier(self, cr, uid,supplier, form):
        
        result = []
        
        move_obj = self.pool.get('account.move')
        
        line_obj = self.pool.get('account.move.line')
        
        invoice_obj = self.pool.get('account.invoice')
        
        retention_obj = self.pool.get('account.invoice.retention')
        
        statement_obj = self.pool.get('account.bank.statement')
        
        statement_line_obj = self.pool.get('account.bank.statement.line')
        
        tax_line_obj= self.pool.get('account.invoice.tax')
        
        
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        
        date_start = form.get('date_start', False) #Inicio del Periodo en Induvallas
        
        date_now = time.strftime('%Y-%m-%d')
        
        if supplier:
            saldo = 0.00
            saldo = self.saldo(cr,uid, supplier,form)
            #Saldos Iniciales
            sql3 ="SELECT am.id as id, am.name as emision, am.ref AS nro, am.date_maturity as vencimiento, "\
                       "am.debit as debit, am.credit as credit "\
                       "FROM account_move_line as am "\
                       "WHERE am.partner_id = %s "\
                       "AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1332) "\
                       "AND am.journal_id =19 "\
                       "AND am.date between '%s'AND '%s' order by nro"%(supplier,date_start,date_now)
            ##print 'sql3', sql3
            cr.execute(sql3)
            inicial = cr.dictfetchall()
            if inicial:
                for item in inicial:
                    dic_inicial = {}
                    if not self.is_date(item.get('emision')):
                        continue
                    ##print 'item.get', item.get('emision')
                    if self._format_date(item.get('emision')) >= self._format_date(date_from) and \
                        self._format_date(item.get('emision')) <= self._format_date(date_to):
                        dic_inicial['emision'] = item.get('emision','')
                        dic_inicial['vence'] = item.get('vencimiento','')
                        dic_inicial['cod'] = 'INI'
                        
                        move_line = line_obj.browse(cr, uid, item.get('id'))
                        
                        dic_inicial['doc'] = move_line.move_id.no_comp or ''
                        if item.get('nro',''):
                            dic_inicial['nro'] = str(item.get('nro','')).zfill(9)
                        else:
                            dic_inicial['nro'] = ''
                        
                        dic_inicial['det'] = 'Saldo Inicial Cliente'
                        
                        dic_inicial['debit'] = item.get('debit', 0.00)
                        dic_inicial['credit'] = item.get('credit', 0.00)
                        
                        saldo += dic_inicial['debit'] - dic_inicial['credit'] 
                        
                        dic_inicial['saldo'] = saldo
                         
                        result.append(dic_inicial)
                    
                    move_line = line_obj.browse(cr, uid, item.get('id'))
                    
                    if move_line.reconcile_id:
                        for rel in move_line.reconcile_id.line_id:
                            dic_inicial = {}
                            if self._format_date(rel.date) >= self._format_date(date_from) \
                                and self._format_date(rel.date) <= self._format_date(date_to):
                                if rel.debit:
                                    dic_inicial['emision'] = rel.date
                                    dic_inicial['vence'] = rel.date_maturity
                                    dic_inicial['cod'] = 'CAN INI'
                                    dic_inicial['doc'] = rel.move_id.no_comp
                                    if rel.ref:
                                        dic_inicial['nro'] = str(rel.ref).zfill(9)
                                    else:
                                         dic_inicial['nro'] = ''
                                    
                                    dic_inicial['det'] = rel.statement_id and rel.statement_id.name or rel.name or ''
                                    
                                    dic_inicial['debit'] = rel.debit
                                    dic_inicial['credit'] = rel.credit
                                    saldo += rel.debit - rel.credit
                                    dic_inicial['saldo'] = saldo
                                    result.append(dic_inicial)
                            
                    elif move_line.reconcile_partial_id:
                         
                        for rel in move_line.reconcile_partial_id.line_partial_ids:
                            dic_inicial = {}
                            if self._format_date(rel.date) >= self._format_date(date_from) \
                                and self._format_date(rel.date) <= self._format_date(date_to):
                                if rel.debit:
                                    dic_inicial['emision'] = rel.date
                                    dic_inicial['vence'] = rel.date_maturity
                                    dic_inicial['cod'] = 'ABO INI'
                                    dic_inicial['doc'] = rel.move_id.no_comp
                                    if rel.ref:
                                        dic_inicial['nro'] = str(rel.ref).zfill(9)
                                    else:
                                         dic_inicial['nro'] = ''
                                    
                                    dic_inicial['det'] = rel.statement_id and rel.statement_id.name or rel.name or ''
                                    
                                    dic_inicial['debit'] = rel.debit
                                    dic_inicial['credit'] = rel.credit
                                    
                                    saldo += rel.debit - rel.credit
                                    dic_inicial['saldo'] = saldo
                                    
                                    result.append(dic_inicial)
                            
            #Facturas y pagos
            sql = """SELECT id AS invoice, date_invoice as date
                     FROM account_invoice WHERE type = 'in_invoice'
                     AND state in ('open', 'paid','cancel')
                     AND partner_id = '%s'
                     AND date_invoice BETWEEN '%s' and '%s' """%(supplier, date_start, date_now)
            order = " ORDER BY factura"
            sql = sql + order
            ##print "sql\n", sql
            cr.execute(sql)
            res = cr.dictfetchall()
            
            if res:
                for r in res:
                    
                    invoice_info = invoice_obj.read(cr, uid, r['invoice'], ['date_invoice','number_inv_supplier','amount_total',
                                                                            'date_due','move_id','payment_ids', 'ret_id',
                                                                            'state','number','origin', 'factura'])
                    if self._format_date(r['date']) >= self._format_date(date_from) \
                        and self._format_date(r['date']) <= self._format_date(date_to): 
                        r['emision'] = invoice_info.get('date_invoice',False)
                        r['vence'] = invoice_info.get('date_due',False)
                        ##print 'vence', type(r['vence'])
                        if invoice_info.get('state') in ('open','paid'):
                            move_info = move_obj.read(cr, uid, invoice_info['move_id'][0], ['no_comp'])
                            r['doc'] = move_info.get('no_comp','')
                            r['nro'] = invoice_info['factura']
                            r['debit'] = 0.00
                            r['credit'] = invoice_info['amount_total']
                        else:
                            r['doc'] = invoice_info['number']
                            r['nro'] = invoice_info['factura'] or 's/n'
                            r['debit'] = 0.00
                            r['credit'] = 0.00
                            
                        r['cod'] = 'FAC'
                        r['det'] = invoice_info['origin'] or ''
                        
                        saldo += r['debit'] - r['credit'] 
                        r['saldo'] =  saldo
                        
                        result.append(r)
                        
                        if invoice_info['ret_id']:
                            dic_retention = {}
                            retencion_info = retention_obj.read(cr, uid, invoice_info['ret_id'][0],['fecha','num_comprobante', 
                                                                                                    'move_ret_id','tax_line',
                                                                                                    'state'])
                            if retencion_info['state'] not in ('draft','cancel'):
                                if retencion_info['move_ret_id']:
                                    move_info = move_obj.read(cr, uid, retencion_info['move_ret_id'][0], ['no_comp'])
                                    dic_retention['doc'] = move_info.get('no_comp','')
                                for x in retencion_info['tax_line']:
                                    tax_info = tax_line_obj.read(cr, uid, x, ['tax_amount'])
                                    dic_retention['debit'] = abs(tax_info['tax_amount'])
                                    dic_retention['credit'] = 0.00
                                dic_retention['emision'] = retencion_info.get('fecha',False)
                                dic_retention['vence'] = invoice_info.get('date_due',False)
                                
                                dic_retention['nro'] = invoice_info['factura']
                                
                                dic_retention['cod'] = 'RET'
                                if invoice_info['number_inv_supplier']:
                                    dic_retention['det'] = 'Retenciones Factura:'+str(invoice_info['number_inv_supplier'] or '')
                                else:
                                    dic_retention['det'] = 'Retenciones Factura:'+str(invoice_info['origin'] or '')
                                    
                                saldo += dic_retention['debit'] - dic_retention['credit']
                                
                                dic_retention['saldo'] =  saldo
                                result.append(dic_retention)
                      
                    if invoice_info['payment_ids']:
                        #Ordeno las pagos segun  fecha de ingreso
                        payment_order = line_obj.search(cr,uid, [('id','in',invoice_info['payment_ids'])],order='date asc')
                        
                        for payment in payment_order:
                            dic_payment = {}
                            payments_info = line_obj.read(cr, uid, payment,['date','debit','credit','move_id',
                                                                            'date_maturity','ref','name','statement_id',
                                                                            'journal_id'])
                            ##print 'payments_info', payments_info
                            if self._format_date(payments_info['date']) >= self._format_date(date_from)\
                               and self._format_date(payments_info['date']) <= self._format_date(date_to):
                                dic_payment['emision'] = payments_info['date']
                                dic_payment['vence'] = payments_info.get('date_maturity') or payments_info['date'] 
                                dic_payment['doc'] = payments_info['move_id'][1]
                                dic_payment['nro'] = payments_info['ref']
                                
                                if payments_info['journal_id'][1]=='Diario Cruce Facturas Canje':
                                    dic_payment['cod'] = 'NDC'
                                else:
                                    dic_payment['cod'] = 'CAN'
                                
                                detalle = payments_info['statement_id']
                                if detalle:
                                    detalle = tools.ustr(detalle[1])
                                else:
                                    detalle = payments_info['name']
                                dic_payment['det'] = detalle
                                dic_payment['debit'] = payments_info['debit']
                                dic_payment['credit'] = payments_info['credit']
                                saldo += payments_info['debit'] - payments_info['credit']
                                dic_payment['saldo'] = saldo
                                
                                result.append(dic_payment)
                            
        return result

    
    def action_excel(self, cr, uid, ids, context=None):
        wb = pycel.Workbook(encoding='utf-8')
        if context is None:
            context = {}
        data = {}
        data['form'] = self.read(cr, uid, ids)[0]
        form = data['form']
        date_start = form.get('date_start', False)
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        partner_id = form.get('partner_id', False)
        
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
        
        linea = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center;'
                                    'borders:bottom 1;')
        
        linea_center = pycel.easyxf('font: colour black;'
                                   'align: vertical center, horizontal center;'
                                   )
        
        linea_izq = pycel.easyxf('font: colour black;'
                                   'align: vertical center, horizontal left;'
                                   )
        linea_der = pycel.easyxf('font: colour black;'
                                 'align: vertical center, horizontal right;'
                                  )
        
        
            
        ws = wb.add_sheet("Estado Proveedor")
        ws.show_grid = False
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        ##print 'compania', compania
        x0=40
        #sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)
        ws.write_merge(1,1,1,x0,compania.name, style_cabecera)
        ws.write_merge(2,2,1,x0,'Direccion: '+compania.partner_id.street, style_cabecera)
        ws.write_merge(3,3,1,x0,'Ruc: '+compania.partner_id.ident_num, style_cabecera)
        ws.write_merge(4,4,1,x0,'Estado de Cuenta de Proveedor', style_cabecera)
        
        x1=6 #Fechas
        ws.write_merge(x1,x1,1,4, time.strftime('%Y-%m-%d'), style_cabeceraizq)
        ws.write(x1,5, 'Hora:', style_cabecerader)
        ws.write_merge(x1,x1, 6,8, time.strftime('%H:%M:%S'), style_cabeceraizq)
        ws.write_merge(x1,x1,12,13, 'Desde:', style_cabecerader)
        ws.write_merge(x1,x1,15,17, date_from, style_cabeceraizq)
        ws.write(x1, 21, 'Hasta:', style_cabecerader)
        ws.write_merge(x1,x1, 23,26, date_to, style_cabeceraizq)
        
        ws.fit_num_pages = 1
        ws.fit_height_to_pages = 0
        ws.fit_width_to_pages = 1
        ws.paper_size_code = 1
        ws.portrait = 0
        
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
            
        'Busco los proveedores'
        suppliers = self.get_supplier(cr, uid, form)
        
        tot_debit = 0.00
        tot_credit = 0.00
        tot_saldo = 0.00
        
        xi = 8 # Cabecera de Cliente
        x = 14 # Cabecera Tabla Movimientos
        xc = 15  #Saldo inicial 
        xm = 16 #Movimientos
        for item in suppliers:
            saldo_final = 0.00
            
            saldo = self.saldo(cr, uid, item['id'], form)
            
            moves = self.moves_supplier(cr, uid, item['id'], form)
            
            if saldo or moves:
                
                sum_debit = 0.00
                sum_credit = 0.00
                sum_saldo = 0.00
                
                ws.write_merge(xc,xc,30,33,'Saldo:', style1)
                ws.write_merge(xc,xc,34,40,saldo, style1)
                
                ws.write_merge(xi,xi,1,3,'Codigo Contable:', linea_izq)
                ws.write_merge(xi,xi,4,9,item['codcontable'], linea_izq)
                
                ws.write_merge(xi,xi,20,23,'Zona:', linea_izq)
                ws.write_merge(xi,xi,25,35,item['zona'], linea_izq)
                
                ws.write_merge(xi+2,xi+2,1,3,'Cuenta Proveedor:', linea_izq)
                ws.write_merge(xi+2,xi+2,4,17,item['cod'], linea_izq)
                
                ws.write_merge(xi+2,xi+2,20,23,'Ciudad:', linea_izq)
                ws.write_merge(xi+2,xi+2,25,35,item['city'], linea_izq)
                
                ws.write_merge(xi+4,xi+4,1,3,'Nombre Proveedor:', linea_izq)
                ws.write_merge(xi+4,xi+4,4,9,item['supplier'], linea_izq)
                
                ws.write_merge(xi+4,xi+4,20,23,'Dirección: ', linea_izq)
                ws.write_merge(xi+4,xi+4,25,35,item['street'], linea_izq)
                
                ws.write_merge(x,x,0,2,'Emision', style_header)
                ws.write(x,3,'Cod.M', style_header)
                ws.write_merge(x,x,4,8,'No.Fact', style_header)
                ws.write_merge(x,x,9,12,'Vence', style_header)
                ws.write_merge(x,x,13,25,'Detalle', style_header)
                ws.write_merge(x,x,26,29,'Debito', style_header)
                ws.write_merge(x,x,30,33,'Credito', style_header)
                ws.write_merge(x,x,34,40,'Saldo', style_header)
            
                for mov in moves:
                    ws.write_merge(xm,xm,0,2,mov['emision'], linea_center)
                    ws.write(xm,3,mov['cod'], linea_center)
                    ws.write_merge(xm,xm,4,8,mov['nro'], linea_center)
                    
                    date_due = str(mov.get('vence',False)).strip()
                    
                    if date_due!='False':
                         date_due = mov.get('vence',False)
                    else:
                        date_due = ''
                    ws.write_merge(xm,xm,9,12,date_due, linea_center)
                    ws.write_merge(xm,xm,13,25,mov['det'], linea_izq)
                    ws.write_merge(xm,xm,26, 29,mov['debit'], style)
                    sum_debit += mov['debit']
                    ws.write_merge(xm,xm,30, 33,mov['credit'], style)
                    sum_credit += mov['credit']
                    ws.write_merge(xm,xm,34,40,mov['saldo'], style)
                    sum_saldo += mov['saldo']
                    saldo_final = mov['saldo']
                    xm += 1
            
                ##print 'xm', xm
                tot_debit += sum_debit
                tot_credit += sum_credit
                tot_saldo += saldo_final
                
                xm += 1    
                ws.write_merge(xm,xm,24,25,'Total',style2)
                ws.write_merge(xm,xm,26,29,sum_debit,style2)
                ws.write_merge(xm,xm,30,33,sum_credit,style2)
                ws.write_merge(xm,xm,34,40,saldo_final,style1)
            
                ##print 'cm2', xm
                xi = xm + 2
                x = xi + 6
                xc = x + 1
                xm = xc + 1
                
        if len(suppliers) > 1:
            xi+=1
            ws.write_merge(xi,xi,24,25,'Total General',style2)
            ws.write_merge(xi,xi,26,29,tot_debit,style2)
            ws.write_merge(xi,xi,30,33,tot_credit,style2)
            ws.write_merge(xi,xi,34,40,tot_saldo,style2)
        
        w = 500
        w0 = 2000
        w1 = 3000
        w2 = 1500
        ws.col(0).width = w
        ws.col(1).width = 1000
        ws.col(2).width = 1000
        ws.col(3).width = w0
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
        return self.write(cr, uid, ids, {'data':out, 'name':'estado_proveedor.xls'})

    _columns = {
                'change_date':fields.boolean('Saldo Anterior', help="Active el campo para cambiar la fecha para el calculo del saldo anterior"), 
                'partner_id':fields.many2one('res.partner', 'Proveedor', required=False, domain=[('supplier','=', True)]),
                'date_from':fields.date('Fecha Desde'),
                'date_to':fields.date('Fecha Hasta'),
                'date_start':fields.date('Fecha de Inicio del Año Fiscal', help='Esta fecha sirve para calcular el saldo anterior a la Fecha Desde'),
                'data': fields.binary(string='Archivo'),
                'name':fields.char('Nombre', size=60),
        }                            
                                                                              
    _defaults = {
        'change_date': lambda * a: False,
        'date_from': lambda * a: time.strftime('%Y-%m-01'),
        'date_to': lambda * a: time.strftime('%Y-%m-%d'),
        'date_start': lambda * a: time.strftime('2011-07-01'), #A partir de esta fecha se sumara todos los saldos iniciales hasta la fecha inicial
#        'partner_id':lambda * a:663,
        }
        
wizard_supplier_statement()