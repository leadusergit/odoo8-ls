# -*- coding: utf-8 -*-
##############################################################################
#
#    Gnuthink Software Labs
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

__author__ = 'mario.chogllo@gnuthink.com (Mario Chogllo)'

import time
import datetime
#from datetime import *
from openerp.osv import osv
from openerp.osv import fields
from mx import DateTime
import netsvc
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

class account_tax_fechas(osv.osv_memory):
    _name = "account.tax.fechas"
        
    _columns = {
        'inicio':fields.date('Inicio', required=True),
        'fin':fields.date('Fin', required=True),
        }    
    
    _defaults = {
        'inicio': lambda *a: time.strftime('%Y-%m-%d'),
        'fin': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def _llamar_reporte(self, cr, uid, ids, context={}):
        
        #print ' llamar reporte ***********'    
        
        for actual in self.browse(cr, uid, ids, context):
            ds = mx.DateTime.strptime(actual.inicio, '%Y-%m-%d')	
            
        facturas_ids = self.pool.get('account.invoice').search(cr, uid,[('date_invoice', '<=', actual.fin),('date_invoice','>=',actual.inicio),('state','in',['open','paid'])])
        header_id=self.pool.get('account.tax.header').create(cr, uid, {
                'inicio':actual.inicio,
                'fin':actual.fin,
                })
        tipos = {}
        for factura in facturas_ids:
            fact = self.pool.get('account.invoice').browse(cr, uid, factura)
            #print ' estado *********** ', fact.state
            if fact.state not in ('open','paid'):
                break
            
            invoice_tax_ids=self.pool.get('account.invoice.tax').search(cr, uid,
                                                                         [('invoice_id','=',factura),
                                                                          ('tax_group','in',['ret_vat','ret_ir','no_ret_ir'])],
                                                                        order='name')
            for linea in self.pool.get('account.invoice.tax').browse(cr, uid, invoice_tax_ids):
                if not (linea.name in tipos.keys()):
                    tipo_id = self.pool.get('account.tax.type').create(cr, uid, {
                            'header_id': header_id,
                            'name': linea.name,
                            })
                    tipos[linea.name]=linea.name
                else:
                    tipo_id = self.pool.get('account.tax.type').search(cr, uid, [('name','=',linea.name),('header_id','=',header_id)])[0]
                line_id=self.pool.get('account.tax.report.linea').create(cr, uid, {
                        'type_id':tipo_id,
                        'impuesto':linea.name,
                        'fecha':fact.date_invoice,
                        'documento':fact.number_inv_supplier,
                        'nombre':fact.partner_id.name,
                        'ruc':fact.partner_id.ident_num,
                        'b_imponible':linea.base,
                        'porcentaje':linea.percent,
                        'valor':linea.amount,
                        })
                tipo=self.pool.get('account.tax.type').browse(cr, uid, tipo_id)
                self.pool.get('account.tax.type').write(cr, uid, tipo_id, {
                        'b_total':tipo.b_total+linea.base,
                        'v_total':tipo.v_total+linea.amount,
                        })
        return {
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'account.tax.header',
            'type': 'ir.actions.act_window',
            'res_id' : header_id,
        } 

account_tax_fechas()

class account_tax_header(osv.osv):
    _name = "account.tax.header"
    _columns = {
        'inicio':fields.date('Inicio', required=True, readonly=True),
        'fin':fields.date('Fin', required=True, readonly=True),
	'tax_ids':fields.one2many('account.tax.type', 'header_id', 'Tipos de impuestos', required=True, readonly=True),
        }

    _defaults = {
    }

account_tax_header()

class account_tax_type(osv.osv):
    _name = "account.tax.type"
    _columns = {
        'header_id': fields.many2one('account.tax.header','Reporte impuestos', readonly=True),
        'name':fields.char("Tipo", size=100),
        'lineas_ids':fields.one2many('account.tax.report.linea', 'type_id', 'Movimiento', required=False, readonly=True),
        'b_total':fields.float('Total B. Imp'),
        'v_total':fields.float('Total Valor'),
        }
account_tax_type()

class account_tax_report_linea(osv.osv):
    _name = "account.tax.report.linea"
    
    _order = 'impuesto'
    _columns = {
        'impuesto':fields.char('RETENCION', size=32),
        'fecha': fields.date('Fecha'),
        'documento':fields.char('Documento',size=16),
        'nombre':fields.char('Nombre',size=32),
        'ruc':fields.char('RUC',size=14),
        'b_imponible':fields.float('B. Imponible'),
        'porcentaje':fields.char('Porcentaje', size=10),
        'valor':fields.float('Valor'),
        'type_id': fields.many2one('account.tax.type','Tipo', readonly=True),
        }
    
account_tax_report_linea()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
