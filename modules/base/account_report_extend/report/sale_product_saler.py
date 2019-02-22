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

import xml
import copy
from operator import itemgetter
import time
import datetime
from openerp.report import report_sxw
import openerp.tools

class sale_product_saler(report_sxw.rml_parse):
    _name = 'report.sale.product.saler'
        
    def set_context(self, objects, data, ids, report_type=None):
        #print ' set context ', data
        #print ' set context ids ', ids
        #print ' report type ', report_type
        #print ' objects ', objects
        return super(sale_product_saler, self).set_context(objects, data, ids, report_type=report_type)
        
    def __init__(self, cr, uid, name, context):
        self.tot_neta = 0
        self.total_porcentaje=0
        self.cantidad_total=0
        #print ' init method ', context
        super(sale_product_saler, self).__init__(cr, uid, name, context)
        self._datos_wizard = {}
        #print ' init method 2'
        self.localcontext.update({
            'time': time,
            'obtener_informacion':self._get_data,
            'total':self._get_total_prec,
            'acumulado': self._get_porcentaje,
            'cantidadt':self._get_cantidad,
            'seller':self.get_seller
        })
        self.context = context
    def get_seller(self, seller_id):
        if seller_id:
            info_user = self.pool.get('res.users').read(self.cr, self.uid, seller_id, ['name','id'])
            return tools.ustr(info_user['name'])
        else:
            return ''

    def _get_data(self, param):
        total=0
        res ={}
        line = ""
        query = "select count(*), il.product_id, ai.saleer_id, pt.name, sum(il.price_subtotal) as precio, sum(il.quantity) as cantidad \
            from account_invoice_line il,account_invoice ai, product_template pt  \
            where il.invoice_id = ai.id  \
            and il.product_id = pt.id and ai.type ='out_invoice' "
        
        datos = param['form']
        #print ' datos ', datos
        if datos.has_key('date_start') and datos['date_start']:
            line = " and ai.date_invoice >= '" + datos['date_start'] + "'"
            query += line
        if datos.has_key('date_finish') and datos['date_finish']:
            line = " and ai.date_invoice <= '" + datos['date_finish'] + "'"
            query += line
        if datos.has_key('product_id') and datos['product_id']:
            line = " and il.product_id = " + str(datos['product_id'])
            query += line
        if datos.has_key('user_id') and datos['user_id']:
            user = self.pool.get('res.users').read(self.cr, self.uid, datos['user_id'], ['name','id'])
            line = " and ai.saleer_id=" + user['id']
            query += line
        
        query += ' group by product_id,ai.saleer_id, pt.name ,il.quantity'
        self.cr.execute(query)
        res = self.cr.dictfetchall()
        
        query ="""select sum(il.quantity) as cantidad             
                    from account_invoice_line il,account_invoice ai, product_template pt              
                    where il.invoice_id = ai.id              
                    and il.product_id = pt.id and ai.type ='out_invoice' """
        datos = param['form']
        
        if datos.has_key('date_start') and datos['date_start']:
            line = " and ai.date_invoice >= '" + datos['date_start'] + "'"
            query += line
        if datos.has_key('date_finish') and datos['date_finish']:
            line = " and ai.date_invoice <= '" + datos['date_finish'] + "'"
            query += line
        if datos.has_key('product_id') and datos['product_id']:
            line = " and il.product_id = " + str(datos['product_id'])
            query += line
        if datos.has_key('user_id') and datos['user_id']:
            user = self.pool.get('res.users').read(self.cr, self.uid, datos['user_id'], ['name','id'])
            line = " and ai.saleer_id=" + user['id']
            query += line
        self.cr.execute(query)
        resc = self.cr.dictfetchall()
        cant = resc[0]['cantidad']
        self.cantidad_total = cant 
        
        query = """select sum(il.price_subtotal) as precio 
                   from account_invoice_line il,account_invoice ai, product_template pt  
                   where il.invoice_id = ai.id  
                   and il.product_id = pt.id and ai.type ='out_invoice' """
        datos = param['form']
        if datos.has_key('date_start') and datos['date_start']:
            line = " and ai.date_invoice >= '" + datos['date_start'] + "'"
            query += line
        if datos.has_key('date_finish') and datos['date_finish']:
            line = " and ai.date_invoice <= '" + datos['date_finish'] + "'"
            query += line
        if datos.has_key('product_id') and datos['product_id']:
            line = " and il.product_id = " + str(datos['product_id'])
            query += line
        if datos.has_key('user_id') and datos['user_id']:
            user = self.pool.get('res.users').read(self.cr, self.uid, datos['user_id'], ['name','id'])
            line = " and ai.saleer_id=" + user['id']
            query += line
        self.cr.execute(query)
        rest = self.cr.dictfetchall()
        valort = rest[0]['precio']
        self.tot_neta = valort           
        
        if res:
            for valor1 in res:
                #print "valor1: ",valor1['precio']
                porcentaje = valor1['precio'] / valort * 100
                #print "porcentaje : ",porcentaje
                valor1['porcentaje'] = porcentaje
                self.total_porcentaje+=porcentaje
        #print res
        return res
    
    def _get_porcentaje(self):
        return self.total_porcentaje
    
    def _get_total_prec(self):
        return self.tot_neta
    
    def _get_cantidad(self):
        return self.cantidad_total
    

report_sxw.report_sxw('report.sale.product.saler', 
                      'account.invoice', 
                      'addons/account_report_extend/report/sale_product_saler.rml', 
                      parser=sale_product_saler, 
                      header=False)
