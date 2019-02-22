# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
import csv
import time
from openerp.osv import fields, osv
import mx.DateTime
from mx.DateTime import RelativeDateTime
from openerp.tools import config
import datetime


class wizard_report_invoices_customer(osv.osv_memory):
    _name='wizard.report.invoices.customer'
    _description='Reporte de Facturas de Clientes'
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def report_invoices(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        return self._print_report_invoices(cr, uid, ids, data, context=context) 
    
    def _print_report_invoices(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {'type':'ir.actions.report.xml',
                  'report_name':'account_invoices_customer',
                  'datas': data}
        return result
    
    def report_refunds(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        return self._print_report_refunds(cr, uid, ids, data, context=context) 
    
    def _print_report_refunds(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {'type':'ir.actions.report.xml',
                  'report_name':'account_refunds_customer',
                  'datas': data}
        return result
    
    def report_all(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        return self._print_report_all(cr, uid, ids, data, context=context) 
    
    def _print_report_all(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {'type':'ir.actions.report.xml',
                  'report_name':'account_invoices_all',
                  'datas': data}
        return result
    
    def report_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        return self._print_report_cancel(cr, uid, ids, data, context=context) 
    
    def _print_report_cancel(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {'type':'ir.actions.report.xml',
                  'report_name':'account_invoices_cancel',
                  'datas': data}
        return result
    
    def export_excel(self, cr, uid, ids, context=None):
        form = self.read(cr, uid, ids)[0]
        ##print "form"
        buf = StringIO.StringIO()
        writer = csv.writer(buf, delimiter=',')
        fila = []
        cabecera = self.cabecera(cr, uid, form)
        if cabecera[0]['case']=='1':
            fila = ['','','','','REPORTE POR CLIENTE']
        elif cabecera[0]['case']=='2':
            fila = ['','','','','REPORTE POR VENDEDOR']
        else:
            fila = ['','','','','REPORTE DE FACTURAS']
        
        writer.writerow(fila)
        fila = []
        filtro = form.get('filter', False)
        fila = ['fecha: '+str(time.strftime('%d/%m/%Y').upper())]
        writer.writerow(fila)
        if filtro =='date':
            date_from = form.get('date_from', False)
            date_to = form.get('date_to', False)
            fila = ['Desde: ' +str(date_from),' Hasta: '+str(date_to)]
            writer.writerow(fila)
        elif filtro =='period':
            period_id = form.get('period_id', False)
            obj_period = self.pool.get('account.period').browse(cr,uid, period_id)
            fila = ['Mes de: '+str(self._format_date(obj_period.date_start).strftime('%B %Y')).upper()]
            writer.writerow(fila)
        
        fila = []
        salto = []
        totales = []
        fila = ['Fecha Fac. ','Fecha Ven.', 'TIP','Factura','Cliente-Proveedor', 'Suman','Descuento', 'Iva','TOTAL','Estado']
        writer.writerow(fila)
        if cabecera:
            totalsuman = 0.0
            totaldescuento = 0.0
            totaliva = 0.0
            total = 0.0
            out_invoice = 0
            out_refund = 0
            invoice_cancel = 0
            refund_cancel = 0
            for line in cabecera:
                ##print "line", line
                if line['case']=='1':
                    partner = ''
                    partner = line['customer']
                    if partner:
                        partner = partner.encode('utf-8')
                    fila = ['','','','Cliente:', partner]
                    writer.writerow(fila)
                elif line['case']=='2':
                    partner = ''
                    partner = line['seller']
                    if partner:
                        partner = partner.encode('utf-8')
                    fila = ['','','','Vendedor:',partner]
                    writer.writerow(fila)
                
                lines = self.get_lines(cr, uid, line['parameter'], form)
                if lines:
                    sbtsuman = 0.0
                    sbtdescuento = 0.0
                    sbtiva = 0.0
                    sbttotal = 0.0 
                    for item in lines:
                        if item['tipo']=='FAC':
                            out_invoice+=1
                            if item['estado']=='AN':
                                invoice_cancel +=1 
                                
                        elif item['tipo']=='NC':
                            out_refund+=1
                            if item['estado']=='AN':
                                refund_cancel+=1
                        partner = ''
                        partner = item['partner']
                        partner = partner.encode('utf-8')
                        ##print "partner", partner
                        sbtsuman += item['suman']
                        sbtdescuento += item['descuento']
                        sbtiva += item['iva']
                        sbttotal += item['total']
                        fila = [item['emision'],item['vencimiento'],item['tipo'],item['nro'],partner,
                                item['suman'],item['descuento'],item['iva'],item['total'], item['estado']]
                        writer.writerow(fila)
                    
                    
                    totalsuman += sbtsuman
                    totaldescuento += sbtdescuento
                    totaliva += sbtiva
                    total += sbttotal

                    subtotal = []
                    if cabecera[0]['case'] in ('1','2'):
                        subtotal = ['','','','','SUBTOTAL',sbtsuman, sbtdescuento, sbtiva,sbttotal]
                        writer.writerow(subtotal)
                        
            
            salto = ['\n']
            writer.writerow(salto)
            amount = ['','','','','TOTAL',totalsuman, totaldescuento, totaliva,total]
            writer.writerow(amount)
            
            totales = []
            totales = ['TOTAL FACTURAS',out_invoice,'','','TOTAL NOTAS DE CREDITO',out_refund]
            writer.writerow(totales)
            totales = []
            totales = ['ANULADAS',invoice_cancel,'','','ANULADAS',refund_cancel]
            writer.writerow(totales)
                    
        out = base64.encodestring(buf.getvalue())
        buf.close() 
        return self.write(cr, uid, ids, {'data':out, 'name':'reporte_facturas.csv'}, context=context)
    
    def cabecera(self, cr, uid, form):
        #print "form", form
        ##print "form", form
        res = []
        result = []
        l = []
        customer = form.get('partner_id', False)
        seller = form.get('seller_id', False)
        date_start = form.get('date_start', False)
        date_to = form.get('date_to', False)
        filtro = form.get('filter', False)
        state = form.get('tipo', False)
        group = form.get('type_report', False)
        
        if filtro =='date':
            date_from = form.get('date_from', False)
            date_to = form.get('date_to', False)
            filter  = "AND ai.date_invoice BETWEEN '"+date_from+"' AND '"+date_to+ "' "
        elif filtro =='period':
            period_id = form.get('period_id', False)
            filter = "AND ai.period_id="+str(period_id)+" "
        
        if state=='out_invoice':#Abiertas , pagadas , caneladas
            states = "AND ai.state in ('open','cancel','paid') AND ai.type = 'out_invoice' "
        elif state =='out_refund':
            states = "AND ai.state in ('open','cancel','paid') AND ai.type = 'out_refund' "
        elif state =='all':
            states = "AND ai.state in ('open','cancel','paid') AND ai.type in ('out_invoice','out_refund') "
        elif state =='cancel':
            states = "AND ai.state in ('cancel') AND ai.type in ('out_invoice') "
        case = 0
        if group =='seller':
            sql = "SELECT ai.saleer_id as parameter, ru.name as seller , '2' as case FROM account_invoice as ai "\
                      "LEFT JOIN res_users as ru ON (ru.id = ai.saleer_id) "
            if seller:
                where = "WHERE ai.saleer_id = "+str(seller)+" "
            else:
                case = 1
                
            groups = "GROUP by ai.saleer_id,ru.name ORDER by ru.name"
        elif group =='customer':
            sql = "SELECT ai.partner_id as parameter, rp.name as customer, '1' as case FROM account_invoice as ai "\
                   "LEFT JOIN res_partner as rp ON (rp.id = ai.partner_id) "
            
            if customer:
                where = "WHERE ai.partner_id = "+str(customer)+" "
            else:
                case = 1
                
            groups = "GROUP by ai.partner_id, rp.name ORDER by rp.name"
        elif group == 'all':
            case = 1
            sql = "SELECT ai.id as parameter, 'customer' as customer, 'seller' as seller, '3' as case FROM account_invoice as ai "
            groups = "ORDER by ai.date_invoice,ai.factura "
        
        if case==1:
            where = states + filter
            where = "WHERE " + where[3:]
        
        sql = sql + where +  states + filter + groups
        
        ##print "#Wizard sql", sql
        cr.execute(sql)
        res = cr.dictfetchall()
#        if res:
#            #print "res", res
        return res
    
    
    #Facturas Pagadas y Abiertas
    def get_lines(self,cr, uid,parameter,form):
        result = []
        res = []
        invoices = []
        filtro = form.get('filter', False)
        tipo = form.get('tipo', False)
        customer = form.get('partner_id', False)
        
        date_start = form.get('date_start', False)
        date_to = form.get('date_to', False)
        filtro = form.get('filter', False)
        state = form.get('tipo', False)
        group = form.get('type_report', False)
        
        if filtro =='date':
            date_from = form.get('date_from', False)
            date_to = form.get('date_to', False)
            filter  = "AND ai.date_invoice BETWEEN '"+date_from+"' AND '"+date_to+ "' "
        elif filtro =='period':
            period_id = form.get('period_id', False)
            filter = "AND ai.period_id="+str(period_id)+" "
        
        if state=='out_invoice':#Abiertas , pagadas , caneladas
            states = "AND ai.state in ('open','cancel','paid') AND ai.type = 'out_invoice' "
        elif state =='out_refund':
            states = "AND ai.state in ('open','cancel','paid') AND ai.type = 'out_refund' "
        elif state =='all':
            states = "AND ai.state in ('open','cancel','paid') AND ai.type in ('out_invoice','out_refund') "
        elif state =='cancel':
            states = "AND ai.state in ('cancel') AND ai.type in ('out_invoice') "
        case = 0
        where = ""
        sql = "SELECT ai.id,ai.date_invoice, ai.date_due,ai.type,ai.num_retention as factura,rp.name as partner,ai.amount_subtotal as suman, "\
              "ai.amount_discount as descuento, ai.t_iva as iva, ai.amount_pay as total, ai.state FROM account_invoice as ai "\
              "JOIN res_partner as rp ON (rp.id = ai.partner_id) "\
              "LEFT JOIN res_users as ru ON (ru.id = ai.saleer_id) "
                  
        if group =='seller':
            
            if parameter:
                where = "WHERE ai.saleer_id = "+str(parameter)+" "
            else:
                 where = "WHERE ai.saleer_id is null "
                
                
        elif group =='customer':
            
            if parameter:
                where = "WHERE ai.partner_id = "+str(parameter)+" "
            else:
                where = "WHERE ai.partner_id is null "
            
        elif group == 'all':
            where = "WHERE ai.id="+str(parameter)
        
        order = 'ORDER BY ai.date_invoice, ai.factura'
        sql = sql + where +  states + filter + order
        
        ##print "#Wizard sql*******************************\n", sql
        cr.execute(sql)
        res = cr.dictfetchall()
        if res:
            for inv in res:
                tipo = ''
                estado = ''
                suman = round(inv['suman'],2)
                descuento = round(inv['descuento'],2)
                iva = round(inv['iva'],2)
                total = round(inv['total'],2)
                
                if inv['type']=='out_refund':
                    tipo = 'NC'
                    suman = -suman
                    descuento = -descuento
                    iva = -iva
                    total = -total
                else:
                    tipo = 'FAC'
                if inv['state']=='open':
                    estado = 'MY'
                elif inv['state']=='paid':
                    estado = 'MY'
                elif inv['state']=='cancel':
                    estado = 'AN'
                    suman = 0.0
                    descuento = 0.0
                    iva = 0.0
                    total = 0.0
                    
                val = {
                       'nro': inv['factura'],
                       'tipo': tipo,
                       'partner': inv['partner'],
                       'emision': inv['date_invoice'],
                       'vencimiento' : inv['date_due'],
                       'suman': suman,
                       'descuento': descuento,
                       'iva': iva,
                       'total': total,
                       'estado' : estado,
                       }
                result.append(val)
        return result
    
    def on_change_tipo(self, cr, uid, ids, tipo):
        #print "on_change_tipo", tipo
        res = {}
        if tipo=='all':
            res['partner_id'] = False
            res['seller_id'] = False
        if tipo=='customer':
            res['seller_id'] = False
        if tipo=='seller':
            res['partner_id'] = False
        
        res['name'] =  False
        
        return {'value':res}
    
    def _get_period(self, cr, uid, context={}):
        periods = self.pool.get('account.period').find(cr, uid)
        if periods:
            return periods[0]
        else:
            return False
        
    def _format_date(self, date):
        if date:
            campos = date.split('-')
            date = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date
        
    _columns={
              'type_report':fields.selection([('seller','Vendedor'),
                                              ('customer','Cliente'),
                                              ('all','Sin Agrupar')], 'Reporte de Facturas Agrupadas por', help="Vendedor: Facturas Agrupadas por Vendedor\n"\
                                                                                                 "Cliente: Facturas Agrupadas por Cliente\n"\
                                                                                                 "Sin Agrupar: Reporte sin Agrupar Vendedor o Cliente"),
              'partner_id':fields.many2one('res.partner', 'Clientes', domain=[('customer','=',True),('active','=',True) ]),
              'seller_id':fields.many2one('res.users', 'Vendedor(a)', domain=[('groups_id','in',[21,20])]),
              'filter':fields.selection([('date', 'Fecha'),
                                         ('period', 'Periodo')
                                         ], 'Filtrar', help="Filtrar por Fecha /Periodo de Factura."),
              'date_stop':fields.date("Fecha de Corte"),
              'date_to':fields.date("Hasta"),
              'date_from':fields.date("Desde"),
              'date_start':fields.date("Fecha Inicio A.Fiscal", help="Inicio del Periodo Fiscal para Induvallas"),
              'period_id':fields.many2one('account.period', 'Periodo', help="Seleccione el Periodo"),
              'tipo':fields.selection([('out_invoice', 'Facturas'),
                                       ('out_refund', 'Notas de Credito'),
                                       ('cancel', 'Facturas Anuladas'),
                                       ('all', 'General'),
                                       ], 'Tipo', help="Facturas: Toma todas las facturas en estado Abierto, pagadas y canceladas.\n"\
                                                  "Notas de Credito: Toma todas las Notas de Credito estado abierto, pagadas y canceladas.\n"\
                                                  "General: Toma todas las Facturas y Notas de Credito de Estado Abierto, pagadas y canceladas.\n"\
                                                  "Facturas Anuladas: Toma solo facturas anuladas. "),
              'data': fields.binary(string='Archivo'),
              'name':fields.char('Nombre', size=60),
    }
    _defaults = {
        'date_from': lambda * a: time.strftime('%Y-%m-01'),
        'date_to': lambda * a: time.strftime('%Y-%m-%d'),
        'date_start': lambda * a: time.strftime('2011-07-01'),#Informacion Valida de FActuras al OpenErp
        'date_stop':lambda * a: time.strftime('%Y-%m-%d'),
        'filter': lambda *a: 'date',
        'tipo': lambda *a: 'out_invoice',
        'period_id':_get_period,
        'type_report':lambda *a: 'customer',
    }

wizard_report_invoices_customer()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: