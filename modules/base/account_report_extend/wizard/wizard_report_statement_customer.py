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
#creador  *EG

from openerp.osv import fields, osv
import time
import xlwt as pycel
import cStringIO
import base64
import datetime
import openerp.tools
import re


class wizard_statement_customer(osv.osv_memory):
    _name = "wizard.statement.customer"
    _description = "ESTADO DE CUENTA DE CLIENTE"
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {'type':'ir.actions.report.xml',
                  'report_name': 'estado_cuenta',
                  'datas': data}
        return result
     
    def action_report(self, cr, uid, ids, context=None):
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
        ##print 'name', name
        if name:
            campos = name.split('-')
            if len(campos)==3:
                return True
            
    def _format_date(self, date):
        if date:
            campos = date.split('-')
            date = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date
    
    def saldo (self, cr, uid, customer, form ):
        res = {}
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        
        date_start = form.get('date_start', False) #Inicio del registro de informacion
        
        invoice_obj = self.pool.get('account.invoice')
        account_move_obj = self.pool.get('account.move')
        account_move_line = self.pool.get('account.move.line')
        
        date_now = time.strftime('%Y-%m-%d')
        
        saldo = 0.0
        if customer:
            #Saldo de Facturas - Retenciones y Notas de Credito y Cruces de Facturas
            sql = """SELECT id AS id, date_invoice AS emision, amount_total AS total, ret_voucher_id as retencion
                         FROM account_invoice WHERE type = 'out_invoice'
                         AND partner_id = '%s'
                         AND state in ('open', 'paid')
                         AND date_invoice BETWEEN '%s' AND '%s' 
                         """%(customer, date_start, date_now)
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
                            
            #Sumo los anticipos y menos los pagos de los anticipos                
            sql2 = "select smr.statement_id as move, stl.amount as total, stl.date as date "\
                   "from account_bank_statement_line as stl "\
                   "join account_bank_statement_line_move_rel  as smr ON (stl.id = smr.move_id) "\
                   "where stl.statement_type = 'ant' "\
                   "and stl.partner_id="+str(customer)+" "\
                   "and stl.date between '%s' and '%s' "%(date_start,date_now)
                   
            ##print 'sql2 anticipo', sql2
            
            cr.execute(sql2)
            movimiento = cr.dictfetchall()
            if movimiento:
                for mo in movimiento:
                    if self._format_date(mo['date']) >= self._format_date(date_start) \
                        and self._format_date(mo['date']) < self._format_date(date_from):
                        saldo += -mo['total']
                        
                    move_obj = account_move_obj.browse(cr, uid, mo['move'])
                    
                    for item in move_obj.line_id:
                        if item.credit > 0.0:
                            line_id = item.id
                     
                    if line_id:
                        move_line = account_move_line.browse(cr, uid, line_id)
                    if not line_id :
                        continue 
                    
                    if move_line.reconcile_id:
                        for rel in move_line.reconcile_id.line_id:
                            if self._format_date(rel.date) < self._format_date(date_from):
                                saldo -= round(rel.credit or 0.00, 2)
                    elif move_line.reconcile_partial_id:
                        for rel in move_line.reconcile_partial_id.line_partial_ids:
                            if self._format_date(rel.date) < self._format_date(date_from):
                                saldo -= round(rel.credit or 0.00,2)
                                
            #Muestro todas las lineas del saldo inicial para que se muestre                 
            #===============================================================
            #Lineas de Saldo inicial
            sql3 ="""SELECT am.id as id, am.debit as debit, am.credit as credit, am.date as date, am.ref as ref, am.name as name
                     FROM account_move_line am
                     WHERE am.partner_id = %s
                     AND am.account_id in (SELECT id FROM account_account WHERE parent_id = 1226)
                     AND am.journal_id =19
                     AND am.date between '%s' and '%s' """%(customer,date_start,date_now)
             
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
                                saldo -= round(rel.credit or 0.00, 2)
                    elif move_obj.reconcile_partial_id:
                        for rel in move_obj.reconcile_partial_id.line_partial_ids:
                            if self._format_date(rel.date) < self._format_date(date_from):
                                saldo -= round(rel.credit or 0.00,2)
   
        return saldo
    
    def customer(self, cr, uid, form):
        customer = form.get('partner_id', False)
        address_obj = self.pool.get('res.partner.address')
        if customer:
            sql ="SELECT id, name as customer FROM res_partner WHERE customer is True AND id ="+str(customer) +" AND active is True"
        else:
            sql = "SELECT id, name as customer from res_partner  WHERE customer is True AND active is True ORDER BY name"
        cr.execute(sql)
        res = cr.dictfetchall()    
        if res:
            for r in res:
                city = ''
                street = ''
                phone = ''
                representante = ''
                zona = ''
                info_partner = self.pool.get('res.partner').read(cr, uid, r['id'],['property_account_receivable',
                                                                                   'comment','ident_num','ref','address'])
                if info_partner['property_account_receivable']:
                    r['codcontable']= info_partner['property_account_receivable'][1]
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
    
    def moves_customer(self, cr, uid,customer, form):
        
        result = []
        
        move_obj = self.pool.get('account.move')
        
        line_obj = self.pool.get('account.move.line')
        
        invoice_obj = self.pool.get('account.invoice')
        
        retention_obj = self.pool.get('account.invoice.retention.voucher')
        
        statement_obj = self.pool.get('account.bank.statement')
        
        statement_line_obj = self.pool.get('account.bank.statement.line')
        
        
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        
        date_start = form.get('date_start', False) #Inicio del Periodo en Induvallas
        
        date_now = time.strftime('%Y-%m-%d')
        
        if customer:
            saldo = 0.00
            saldo = self.saldo(cr,uid, customer,form)
            #Saldos Iniciales
            sql3 ="SELECT am.id as id, am.name as emision, am.ref AS nro, am.date_maturity as vencimiento, "\
                       "am.debit as debit, am.credit as credit "\
                       "FROM account_move_line as am "\
                       "WHERE am.partner_id = %s "\
                       "AND am.account_id in ( SELECT id FROM account_account WHERE parent_id = 1226) "\
                       "AND am.journal_id =19 "\
                       "AND am.date between '%s'AND '%s' order by nro"%(customer,date_start,date_now)
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
                        dic_inicial['nro'] = item.get('nro','')
                        
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
                                if rel.credit:
                                    dic_inicial['emision'] = rel.date
                                    dic_inicial['vence'] = rel.date_maturity
                                    dic_inicial['cod'] = 'CAN INI'
                                    dic_inicial['doc'] = rel.move_id.no_comp 
                                    dic_inicial['nro'] = rel.ref or '' 
                                    
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
                                ##print 'entra'
                                if rel.credit:
                                    dic_inicial['emision'] = rel.date
                                    dic_inicial['vence'] = rel.date_maturity
                                    dic_inicial['cod'] = 'ABO INI'
                                    dic_inicial['doc'] = rel.move_id.no_comp 
                                    dic_inicial['nro'] = rel.ref or '' 
                                    
                                    dic_inicial['det'] = rel.statement_id and rel.statement_id.name or rel.name or ''
                                    
                                    dic_inicial['debit'] = rel.debit
                                    dic_inicial['credit'] = rel.credit
                                    
                                    saldo += rel.debit - rel.credit
                                    dic_inicial['saldo'] = saldo
                                    
                                    result.append(dic_inicial)
                            
            #Facturas y pagos
            sql = """SELECT id AS invoice, date_invoice as date
                     FROM account_invoice WHERE type = 'out_invoice'
                     AND state in ('open', 'paid','cancel')
                     AND partner_id = '%s'
                     AND date_invoice BETWEEN '%s' and '%s' """%(customer, date_start, date_now)
            order = " ORDER BY num_retention"
            sql = sql + order
            ##print "sql\n", sql
            cr.execute(sql)
            res = cr.dictfetchall()
            
            if res:
                for r in res:
                    
                    invoice_info = invoice_obj.read(cr, uid, r['invoice'], ['date_invoice','num_retention','amount_total',
                                                                            'date_due','move_id','payment_ids', 'ret_voucher_id',
                                                                            'state','number'])
                    if self._format_date(r['date']) >= self._format_date(date_from) \
                        and self._format_date(r['date']) <= self._format_date(date_to): 
                        r['emision'] = invoice_info.get('date_invoice',False)
                        r['vence'] = invoice_info.get('date_due',False)
                        ##print 'vence', type(r['vence'])
                        if invoice_info.get('state') in ('open','paid'):
                            move_info = move_obj.read(cr, uid, invoice_info['move_id'][0], ['no_comp'])
                            r['doc'] = move_info.get('no_comp','')
                            r['nro'] = invoice_info['num_retention']
                            r['debit'] = invoice_info['amount_total']
                            r['credit'] = 0.00
                        else:
                            r['doc'] = invoice_info['number']
                            r['nro'] = invoice_info['num_retention'] or 's/n'
                            r['debit'] = 0.00
                            r['credit'] = 0.00
                            
                        r['cod'] = 'FAC'
                        r['det'] = 'Facturacion: Factura Cliente'
                        
                        saldo += r['debit'] - r['credit'] 
                        r['saldo'] =  saldo
                        
                        result.append(r)
                      
                    if invoice_info['payment_ids']:
                        #Ordeno las pagos segun  fecha de ingreso
                        payment_order = line_obj.search(cr,uid, [('id','in',invoice_info['payment_ids'])],order='date asc')
                        
                        for payment in payment_order:
                            dic_payment = {}
                            payments_info = line_obj.read(cr, uid, payment,['date','debit','credit','move_id',
                                                                            'date_maturity','ref','name','statement_id',
                                                                            'journal_id','type_move'])
                            ##print 'payments_info', payments_info
                            if self._format_date(payments_info['date']) >= self._format_date(date_from)\
                               and self._format_date(payments_info['date']) <= self._format_date(date_to):
                                dic_payment['emision'] = payments_info['date']
                                dic_payment['vence'] = payments_info.get('date_maturity') or payments_info['date'] 
                                dic_payment['doc'] = payments_info['move_id'][1]
                                dic_payment['nro'] = payments_info['ref']
                                
                                ##print 'diario', payments_info['journal_id'][1]
                                
                                if payments_info['journal_id'][1]=='Diario de Retenciones':
                                    dic_payment['cod'] = 'RET'
                                    retencion = invoice_info['ret_voucher_id']
                                    if retencion:
                                        retencion_info = retention_obj.read(cr, uid, retencion[0], ['broadcast_date','state'])
                                        if retencion_info['state']=='valid':
                                           date_retention = retencion_info.get('broadcast_date', '')
                                           dic_payment['emision'] = date_retention
                                           dic_payment['vence'] = date_retention
                                elif payments_info['journal_id'][1]=='Diario Cruce Facturas Canje':
                                    dic_payment['cod'] = 'NDC'
                                elif payments_info['type_move']:
                                    dic_payment['cod'] = payments_info['type_move']
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
            #Anticipos
            sql2 = "select smr.statement_id as move, stl.date as emision, "\
                   "stl.amount as total, stl.date_maturity as vencimiento, stl.ref as nro, stl.id as linea "\
                   "from account_bank_statement_line as stl "\
                   "join account_bank_statement_line_move_rel  as smr on (stl.id = smr.move_id) "\
                   "where stl.statement_type = 'ant' "\
                   "and stl.partner_id="+str(customer)+" "\
                   "and stl.date between '%s' and '%s'"%(date_start, date_now)+' order by stl.date'
            
            cr.execute(sql2)
        
            #Saco el extracto bancario sirve para ver la linea de la cuenta de clientes para cerrar
            movimiento = cr.dictfetchall()
            if movimiento:
                #Puedo saber los movimientos que realizo el extracto
                for mo in movimiento:
                    dic_advance = {}
                    line = None
                    move = move_obj.browse(cr, uid,mo['move'])
                    
                    for item in move.line_id:
                        if item.credit > 0.0:
                            line = item.id
                     
                    if line:
                        move_line = line_obj.browse(cr, uid, line)
                    if not line :
                        continue
                    
                    if self._format_date(mo['emision']) >= self._format_date(date_from)\
                        and self._format_date(payments_info['date']) <= self._format_date(date_to):
                        dic_advance['emision'] = mo.get('emision',False)
                        dic_advance['vence'] = mo.get('vencimiento',False)
                        dic_advance['cod'] = 'ANT'
                        dic_advance['doc'] = move_line.move_id.no_comp 
                        dic_advance['nro'] = mo.get('nro','')
                        statement_info = statement_line_obj.read(cr, uid,mo['linea'],['statement_id'] )
                        ##print 'statement_info', statement_info
                        dic_advance['det'] = statement_info['statement_id'][1]
                        dic_advance['debit'] = 0.00
                        dic_advance['credit'] = mo['total']
                        
                        saldo += dic_advance['debit'] - dic_advance['credit']
                        
                        dic_advance['saldo'] = saldo 
                        result.append(dic_advance)
                    #Pagos completos y parciales
                    if move_line.reconcile_id:
                        for rel in move_line.reconcile_id.line_id:
                            if self._format_date(rel.date) >= self._format_date(date_from) \
                               and self._format_date(rel.date) <= self._format_date(date_to):
                               if rel.debit:
                                    dic_advance = {}
                                    dic_advance['emision'] = rel.date
                                    dic_advance['vence'] = rel.date_maturity or ''
                                    dic_advance['cod'] = 'CIE ANT'
                                    dic_advance['doc'] = rel.move_id.no_comp 
                                    dic_advance['nro'] = rel.ref or '' 
                                    
                                    dic_advance['det'] = rel.statement_id and rel.statement_id.name or rel.name or ''
                                    
                                    dic_advance['debit'] = rel.debit
                                    dic_advance['credit'] = rel.credit
                                    saldo += rel.debit - rel.credit
                                    dic_advance['saldo'] = saldo
                                    result.append(dic_advance)
                            
                    elif move_line.reconcile_partial_id:
                        
                        for rel in move_line.reconcile_partial_id.line_partial_ids:
                             if self._format_date(rel.date) >= self._format_date(date_from) \
                                and self._format_date(rel.date) <= self._format_date(date_to):
                                if rel.debit:
                                    dic_advance = {}
                                    dic_advance['emision'] = rel.date
                                    dic_advance['vence'] = rel.date_maturity or ''
                                    dic_advance['cod'] = 'ABO ANT'
                                    dic_advance['doc'] = rel.move_id.no_comp 
                                    dic_advance['nro'] = rel.ref or '' 
                                    
                                    dic_advance['det'] = rel.statement_id and rel.statement_id.name or rel.name or ''
                                    
                                    dic_advance['debit'] = rel.debit
                                    dic_advance['credit'] = rel.credit
                                    
                                    saldo += rel.debit - rel.credit
                                    dic_advance['saldo'] = saldo
                                    
                                    result.append(dic_advance)
                            
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
        
        
            
        ws = wb.add_sheet("Estado Cliente")
        ws.show_grid = False
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        ##print 'compania', compania
        x0=40
        #sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)
        ws.write_merge(1,1,1,x0,compania.name, style_cabecera)
        ws.write_merge(2,2,1,x0,'Direccion: '+compania.partner_id.street, style_cabecera)
        ws.write_merge(3,3,1,x0,'Ruc: '+compania.partner_id.ident_num, style_cabecera)
        ws.write_merge(4,4,1,x0,'Estado de Cuenta de Cliente', style_cabecera)
        
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
            
        'Busco los clientes'
        customers = self.customer(cr, uid, form)
        
        tot_debit = 0.00
        tot_credit = 0.00
        tot_saldo = 0.00
        
        xi = 8 # Cabecera de Cliente
        x = 14 # Cabecera Tabla Movimientos
        xc = 15  #Saldo inicial 
        xm = 16 #Movimientos
        for item in customers:
            saldo_final = 0.00
            
            saldo = self.saldo(cr, uid, item['id'], form)
            
            moves = self.moves_customer(cr, uid, item['id'], form)
            
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
                
                ws.write_merge(xi+2,xi+2,1,3,'Cuenta Cliente:', linea_izq)
                ws.write_merge(xi+2,xi+2,4,17,item['cod'], linea_izq)
                
                ws.write_merge(xi+2,xi+2,20,23,'Ciudad:', linea_izq)
                ws.write_merge(xi+2,xi+2,25,35,item['city'], linea_izq)
                
                ws.write_merge(xi+4,xi+4,1,3,'Nombre Cliente:', linea_izq)
                ws.write_merge(xi+4,xi+4,4,9,item['customer'], linea_izq)
                
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
                
        if len(customers) > 1:
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
        return self.write(cr, uid, ids, {'data':out, 'name':'estado_cliente.xls'})

    _columns = {
                'change_date':fields.boolean('Saldo', help="Active el Campo para Cambiar la fecha del inicio del periodo"),
                'partner_id':fields.many2one('res.partner', 'Cliente', required=False, domain=[('customer','=', True)]),
                'date_from':fields.date('Fecha Desde'),
                'date_to':fields.date('Fecha Hasta'),
                'date_start':fields.date('Fecha de Inicio del Año Fiscal'),
                'data': fields.binary(string='Archivo'),
                'name':fields.char('Nombre', size=60),
    }
    _defaults = {
        'date_from': lambda * a: time.strftime('%Y-%m-01'),
        'date_to': lambda * a: time.strftime('%Y-%m-%d'),
        'date_start': lambda * a: time.strftime('2011-07-01'),#Fecha de partida del openerp en Induvallas
    }
        
wizard_statement_customer()