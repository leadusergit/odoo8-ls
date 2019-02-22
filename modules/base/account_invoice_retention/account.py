# -*- coding: utf-8 -*-
###################################################
#
#    Account Invoice Retention MODULE
#    Copyright (C) 2012 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
#    $autor: Dairon Medina Caro <dairon.medina@gmail.com>
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
###################################################
import calendar
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

import openerp
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.osv import fields, osv, expression
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools.safe_eval import safe_eval as eval
from openerp.exceptions import ValidationError
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class account_bank_statement(osv.osv):
    _name = "account.bank.statement"
    _inherit = "account.bank.statement"
    
    def _get_sequence(self, cr, uid, ids, field_name, args, context):
        res = {}
        for item in self.browse(cr, uid, ids):
            if item.sequence:
                sql = "update account_bank_statement set sequence='" + str(item.sequence).zfill(7) + "' where id = " + str(item.id)
                cr.execute(sql)
            else:
                sql = "update account_bank_statement set sequence='" + str(item.id).zfill(7) + "' where id = " + str(item.id)
                cr.execute(sql)
            res[item.id] = item.sequence and str(item.sequence).zfill(7) or str(item.id).zfill(7)
        return res
    
    _columns = {
                'has_deposit': fields.boolean('Registrar Depósito(Ventas)', help='Habilite para registrar los datos del deposito siempre que el extracto bancario sea de facturas de cliente.'),
                'num_deposit':fields.integer('No. de Comprobante'),
                'date_deposit':fields.date('Fecha de Depósito'),
                'amount_deposit':fields.float('Monto', digists=(12, 2)),
                'acc_deposit_id':fields.many2one('res.partner.bank', 'Cta. Bancaria', domain=[('partner_id.id', '=', 1)]),
                'payments':fields.selection([('trans', 'Transferencia'), ('depo', 'Depósito')], 'Forma de Pago', size=5,),
                'move_id': fields.many2one('account.move', 'Asiento', readonly=True, select=1, ondelete='restrict', help="Link to the automatically generated Journal Items."),
                'no_comp_rel':fields.related('move_id', 'no_comp', type='char', string='Nro.Comprobante', store=False, size=50),
                'tipo_comprobante':fields.selection([('ComproDiario', 'ComprobanteDiario'),
                                         ('IngresoCaja', 'Ingreso de Caja'), ('Egreso', 'Egresos'), ('OPago', 'OrdenPago')], 'Tipo'),
                'no_comp_bank':fields.char('Nro.Comp', size=50),
                'create_date': fields.datetime('Date Created', readonly=True, select=True),
                'journal_type':fields.char('Descripcion Tipo Diario', size=8),
                'concepto': fields.text('Concepto', required=True),
             }
    
    _defaults = {
        'tipo_comprobante': lambda * a : 'Egreso',
    }
    
    
    def onchange_journal_id(self, cr, uid, statement_id, journal_id, context=None):
        res = super(account_bank_statement, self).onchange_journal_id(cr, uid, statement_id, journal_id, context=context)
        #print ' res ', res
        data = res['value']
        journal_type = self.pool.get('account.journal').read(cr, uid, journal_id, ['type'], context=context)['type']
        data['journal_type'] = journal_type
        #print ' account_invoice_retencion ', res
        return res 
    
    
account_bank_statement()

class account_bank_statement_line(osv.osv):
    _name = "account.bank.statement.line"
    _inherit = "account.bank.statement.line"
    _columns = {
                'payment_form': fields.selection([('s/t', ''),
                                                  ('DINERS', 'DINERS CLUB'),
                                                  ('VISA', 'VISA'),
                                                  ('MASTER', 'MASTER CARD'),
                                                  ('AMERICAN', 'AMERICAN EXPRESS')], 'Credit Card'),
                'tipo_factura': fields.char('Tipo', size=20),
                'numero_orden': fields.char('Numero Orden', size=8),
                'no_comp': fields.related('statement_id', 'no_comp_rel', type='char', size=50, string='Nro.Comprobante', store=False),
    }
account_bank_statement_line()


class res_partner_bank(osv.osv):
    _name = 'res.partner.bank'
    _inherit = 'res.partner.bank'
    
    _columns = {
              'acc_deposit_ids':fields.one2many('account.bank.statement', 'acc_deposit_id', 'Extractos de la Cuenta'),
              'acc_type':fields.selection([('AHO', 'Ahorros'), ('COR', 'Corriente')], 'Tipo de Cuenta'),
              } 
res_partner_bank()

class account_tax(osv.osv):
    _name = 'account.tax'
    _inherit = 'account.tax'
    _order = 'tax_group desc'
    
    # Funcion de la misma clase, pero se quito el round en la linea else: r['amount']=... ese round que tenia, estaba por demas
    def _compute(self, cr, uid, taxes, price_unit, quantity, product=None, partner=None, precision=None):
#     def _compute(self, cr, uid, taxes, price_unit, quantity, address_id=None, product=None, partner=None):
        """
        Compute tax values for given PRICE_UNIT, QUANTITY and a buyer/seller ADDRESS_ID.

        RETURN:
            [ tax ]
            tax = {'name':'', 'amount':0.0, 'account_collected_id':1, 'account_paid_id':2}
            one tax for each tax id in IDS and their children
        """       
        #res = self._unit_compute(cr, uid, taxes, price_unit, product, partner, quantity)
        res = self._unit_compute(cr, uid, taxes, price_unit, product, partner, quantity)
        #print"///_compute air128=%s"%res
#         res = self._unit_compute(cr, uid, taxes, price_unit, address_id, product, partner, quantity)
        total = 0.0
        precision_pool = self.pool.get('decimal.precision')
        for r in res:
            if r.get('balance', False):
                r['amount'] = round(r.get('balance', 0.0) * quantity, precision_pool.precision_get(cr, uid, 'Account')) - total
            else:
                r['amount'] = r.get('amount', 0.0) * quantity
                total += r['amount']
        return res
        
    _columns = {
        'name': fields.char('Nombre', size=128),
        'tax_group' : fields.selection([('vat', 'IVA Diferente de 0%'),
                                        ('vat0', 'IVA 0%'),
                                        ('novat', 'No objeto de IVA'),
                                        ('ret_vat', 'Retención de IVA'),
                                        ('ret_ir', 'Ret. Imp. Renta'),
                                        ('no_ret_ir', 'No sujetos a Ret. de Imp. Renta'),
                                        ('imp_ad', 'Imps. Aduanas'),
                                        ('other', 'Other')], 'Grupo'),
        'percent_comp':fields.char('Porcentaje', size=20, help='Como desea que se imprima el porcentaje del impuesto en el comprobande de retención.(Si es el caso)'),
        'desc_corta':fields.char('Descripción Corta', size=10, help='Descripción que se imprima el porcentaje del impuesto en el comprobande de retención.(Si es el caso)'),
        }
account_tax()

class account_tax_template(osv.osv):
    _name = 'account.tax.template'
    _inherit = 'account.tax.template'
    
    _columns = {
        'tax_group' : fields.selection([('iva0', 'IVA 0% x'), ('noiva', 'No objeto de IVA x'), ('ret', 'Retención x'),
                                        ('vat', 'IVA Diferente de 0%'),
                                        ('vat0', 'IVA 0%'),
                                        ('novat', 'No objeto de IVA'),
                                        ('ret_vat', 'Retenciónde IVA'),
                                        ('ret_ir', 'Ret. Imp. Renta'),
                                        ('no_ret_ir', 'No sujetos a Ret. de Imp. Renta'),
                                        ('imp_ad', 'Imps. Aduanas'),
                                        ('other', 'Other')], 'Grupo'),
        }
account_tax_template()


class account_authorisation(osv.osv):
    """
    Documentos de Autorizacion del SRI
    para Facturas.
    """
    _name = 'account.authorisation'
    _description = __doc__
    
    def _format_date(self, date_from):
        date_from = date_from or time.strftime('%Y-%m-%d')
        if date_from:
            campos = date_from.split('-')
            date_to = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date_to
        
    def _check_active(self, cr, uid, ids, name, args, context):
        """
        Check the due_date to give the value active field
        """
        res = {}
        objs = self.browse(cr, uid, ids)
        now = self._format_date(time.strftime("%Y-%m-%d"))
        for item in objs:
            due_date = self._format_date(item.expiration_date)
            res[item.id] = now <= due_date
            if now <= due_date:
                sql = "update account_authorisation set show = True where id=" + str(item.id)
                _logger.info('Activa %s' % (sql,))
                cr.execute(sql)
            else:
                sql = "update account_authorisation set show = False where id=" + str(item.id)
                _logger.info('Caducada %s' % (sql,))
                cr.execute(sql)
        return res

    # Validar que el numero de autorizacion del SRI tenga 10 digitos y sea solo numeros
    # def onchange_authorisation(self, cr, uid, ids, authori, autoimpresor):
    #    num = authori
    #    result = {}
    #    
    #    if not autoimpresor:
    #        lon = 10
    #    else:
    #        lon = 37
        
    #    if authori:
    #        if len(authori) == lon and authori.isdigit(): 
    #            return {'value':{'name':authori}}
    #        else:
    #            result['value'] = {'name':authori}
    #            result['warning'] = {'title':"Error de Digitacion", "message":"El numero de autorizacion debe de tener 10 digitos o no puede contener letras"}
    #            return result
    
    def long_number_validation(self, doc_type, number):

        lon = 37,49  if doc_type == 'electronic' else 10
        if len(number) not in lon:
            return lon, False
        return lon, True
    
    def create(self, cr, uid, vals, context=None):
        lon, valuation = self.long_number_validation(vals['doc_type'], vals['name'])
        if not valuation:
            raise osv.except_osv(('Aviso'), ('El numero de autorizacion no es el válido, debe ser igual a ' + str(lon) + ' caracteres.'))
        return super(account_authorisation, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        doc_type = vals.get('doc_type', False)
        number = vals.get('name', False)
        for obj in self.read(cr, uid, ids, ['doc_type', 'name']):
            lon, valuation = self.long_number_validation(doc_type or obj['doc_type'], number or obj['name'])
            if not valuation:
                raise osv.except_osv(('Aviso'), ('El numero de autorizacion no es el válido, debe ser igual a ' + str(lon) + ' caracteres.'))
        return super(account_authorisation, self).write(cr, uid, ids, vals, context=context)
        
    
    def write_cod(self):
        
        if (self.type =='in_invoice') or (self.type =='out_invoice'):
            return '01'
        if (type =='ret_customer') or (self.type =='retention'):
            return '07'
        elif (self.type =='in_refund') or (self.type =='out_refund'):
            return '04'
        elif(self.type =='guia_remision') :
            return '06'
              
          
               
                
    _columns = {
        'name' : fields.char('Num. de Autorizacion', size=49, required=True),
        'serie_entidad' : fields.char('Serie Entidad', size=3),
        'serie_emision' : fields.char('Serie Emision', size=3),
        'num_start' : fields.integer('Nro.Desde'),
        'num_end' : fields.integer('Nro.Hasta'),
        'expiration_date' : fields.date('Vence'),
        'resolucion_num': fields.integer('Num Resolucion'),
        'resolucion_date': fields.date('Fecha de Resolucion'),
#         'active' : fields.function(_check_active, string='Activo', method=True, type='boolean'),
        'active' : fields.boolean('Activo'),
        
        'type' : fields.selection((('in_invoice', 'FACTURA PROVEEDOR: Aut. Facturas, Liq de Comp. o Nota de Venta de Proveedor (externa).'),
                                ('in_refund', 'N/C PROVEEDOR: Aut. Notas de Crédito de Proveedor (externa)'),
                                ('ret_customer', 'RET. FUEN. CLIENTE: Aut. Ret. Fue. de Cliente (externa)'),
                                ('retention', 'RET. FUEN. COMPAÑIA: Aut. Ret. Fue. de la Compañía (interna)'),
                                ('out_invoice', 'FACTURA CLIENTE: Aut. Factura de Venta de la Compañía (interna)'),
                                ('out_refund', 'N/C COMPAÑIA: Aut. Notas de Crédito de la Compañía (interna)'),
                                ('guia_remision', 'GUIA REMISION: Aut. Guía de Remisión (interna/externa)')), 'Tipo'),
        'code_doc':fields.char('Tipo de Comprobante',default= write_cod),
        'partner_id' : fields.many2one('res.partner', 'Empresa'),
        'sequence_id' : fields.many2one('ir.sequence', 'Secuencia',),
        'show': fields.boolean('Mostrar',),
        'doc_type': fields.selection([('auto', 'Autoimpreso'), ('electronic', 'Documento electrónico'),
                                      ('custom', 'Tradicional')], 'Tipo de documento', required=True)
        }

    _defaults = {
        'active': lambda * a : True,
        'type' : lambda * a : 'in_invoice',
        'show': lambda * a : False,
        'doc_type': lambda *a: 'custom'
            }
       

    _sql_constraints = [
        ('number_unique',
         'unique(name,partner_id,serie_entidad,serie_emision,type)',
         'La relacion de autorizacion + serie entidad + serie emisor + tipo, debe ser unica.'),
        ]

account_authorisation()

class account_invoice_retention(osv.osv):
    _name = 'account.invoice.retention'
    _description = 'Retention Document for Invoices'
    
    def act_create_ret(self, cr, uid, ids, context):
        #print "act_create_ret", ids
        obj = self.browse(cr, uid, ids)[0]
        if not obj.journal_id:
            raise osv.except_osv('Aviso', 'Debe seleccionar un Diario')
        invs = {}
        move_data = {'date': time.strftime('%Y-%m-%d'), 'journal_id': obj.journal_id.id,
                     'partner_id':obj.partner_id.id, 'ref':"Aut: " + obj.autorization.name + " Num. Comp: " + obj.num_comprobante}
        move_id = self.pool.get('account.move').create(cr, uid, move_data)    
        for tax in obj.tax_line:
            inv_id = tax.invoice_id.id
            #print "inv", inv_id
            if not inv_id:
                raise osv.except_osv('Aviso', 'No se puede ejecutar la retención, porque existen lineas de impuesto que no están relacionadas a una factura. \n En este caso usted sólo podrá anticipar la retención')
            if inv_id not in invs:
                invs[inv_id] = {}
            # invs[inv_id][tax.id]=tax.real_amount_ret
            invs[inv_id][tax.id] = tax.amount
        #print "invs", invs
        lines_to_concil = {}
        for inv_id, taxes in invs.items():
            inv = self.pool.get('account.invoice').browse(cr, uid, inv_id, context)
            if inv.state != 'open':
                raise osv.except_osv('Aviso', 'No se puede ejecutar la retención, porque una de las facturas relacionadas no está en estado (Abierto) id: %s' % inv.id)
            total_fact = 0
            for tax_id, val in taxes.items():
                #print "move1", inv.move_id
                #print "move2", inv.move_id.id
                
                movimiento = self.pool.get('account.move').browse(cr, uid, inv.move_id.id, context)
                tax = self.pool.get('account.invoice.tax').browse(cr, uid, tax_id, context)
                #print "movimiento", movimiento
                if movimiento.line_id:
                    for line in movimiento.line_id:
                        if line.reconcile_id and line.reconcile_id.line_id:
                            for rec_line in line.reconcile_id.line_id:
                                for rec_line2 in rec_line.move_id.line_id:			    
                                    if rec_line2.tax_code_id and rec_line2.tax_code_id == tax.tax_code_id:
                                        raise osv.except_osv('Aviso', 'No se puede realiza el registro de la retención, porque ya existen una retención conciliada a una factura %s' % inv.name)
                        elif line.reconcile_partial_id and line.reconcile_partial_id.line_partial_ids:
                            for rec_line in line.reconcile_partial_id.line_partial_ids:
                                for rec_line2 in rec_line.move_id.line_id:
                                    if rec_line2.tax_code_id and rec_line2.tax_code_id == tax.tax_code_id:
                                        raise osv.except_osv('Aviso', 'No se puede realiza el registro de la retención, porque ya existen una retención conciliada a esta factura %s' % inv.name)
                if obj.type == 'out_invoice':    
                    deb = 0.0
                    cred = 0.0
                                       
                    if val < 0:
                        cred = abs(val)
                    else:
                        deb = val
                    line_data = {'name': inv.name or 'Ret. Cliente', 'journal_id': obj.journal_id.id,
                                 'account_id': tax.account_id.id, 'period_id': inv.period_id.id,
                                 'date': time.strftime('%Y-%m-%d'), 'debit': deb, 'credit':cred , 'move_id': move_id, 'ref':'Aut: ' + obj.autorization.name + ' Num. Comp: ' + obj.num_comprobante,
                                 'tax_code_id':tax.tax_code_id.id, 'tax_amount':val, 'partner_id':obj.partner_id.id}
                elif obj.type == 'retention':
                    deb = 0.0
                    cred = 0.0
                   
                    if val < 0:
                        cred = abs(val)
                    else:
                        deb = val
                    line_data = {'name': inv.name or 'Ret. Proveedor', 'journal_id': obj.journal_id.id,
                                 'account_id': tax.account_id.id, 'period_id': inv.period_id.id,
                                 'date': time.strftime('%Y-%m-%d'), 'debit':deb, 'credit': cred, 'move_id': move_id, 'ref':'Aut: ' + obj.autorization.name + ' Num. Comp: ' + obj.num_comprobante,
                                 'tax_code_id':tax.tax_code_id.id, 'tax_amount':val, 'partner_id':obj.partner_id.id}    
                self.pool.get('account.move.line').create(cr, uid, line_data)
                if tax.base_code_id:
                    line_data_base = {'name': inv.name or 'Ret. Proveedor', 'journal_id': obj.journal_id.id,
                                 'account_id': tax.account_id.id, 'period_id': inv.period_id.id,
                                 'date': time.strftime('%Y-%m-%d'), 'debit':'0.0', 'credit': '0.0', 'move_id': move_id, 'ref':'Aut: ' + obj.autorization.name + ' Num. Comp: ' + obj.num_comprobante,
                                 'tax_code_id':tax.base_code_id.id, 'tax_amount':tax.base_amount, 'partner_id':obj.partner_id.id}    
                    self.pool.get('account.move.line').create(cr, uid, line_data_base)
                total_fact += val
            if obj.type == 'out_invoice':           
                deb = 0.0
                cred = 0.0
               
                
                if total_fact < 0:
                    deb = abs(total_fact)
                else:
                    cred = total_fact
                line_data = {'name': inv.name or 'Ret. Cliente', 'journal_id': obj.journal_id.id,
                             'account_id': inv.account_id.id, 'period_id':inv.period_id.id, 'ref':'Aut: ' + obj.autorization.name + ' Num. Comp: ' + obj.num_comprobante,
                             'date': time.strftime('%Y-%m-%d'), 'debit':deb, 'credit': cred, 'move_id': move_id, 'partner_id':obj.partner_id.id}
            elif obj.type == 'retention':
                deb = 0.0
                cred = 0.0
                if total_fact < 0:
                    deb = abs(total_fact)
                else:
                    cred = total_fact
                line_data = {'name': inv.name or 'Ret. Proveedor', 'journal_id': obj.journal_id.id, 'ref':'Aut: ' + obj.autorization.name + ' Num. Comp: ' + obj.num_comprobante,
                             'account_id': inv.account_id.id, 'period_id':inv.period_id.id,
                             'date': time.strftime('%Y-%m-%d'), 'debit':deb, 'credit': cred, 'move_id': move_id, 'partner_id':obj.partner_id.id}

            line_id = self.pool.get('account.move.line').create(cr, uid, line_data)
            lines_to_concil[inv.id] = [line_id]
            for lin in inv.move_id.line_id:
                if obj.type == 'out_invoice':
                    if lin.account_id == inv.account_id and lin.debit > 0:
                        lines_to_concil[inv.id].append(lin.id)
                        break
                else:
                    if lin.account_id == inv.account_id and lin.credit > 0:
                        lines_to_concil[inv.id].append(lin.id)
                        break
        if obj.name == '/':
            numero = self.pool.get('ir.sequence').get_id(cr, uid, obj.journal_id.sequence_id.id)
        else:
            numero = obj.name
        self.pool.get('account.move').post(cr, uid, [move_id], {'has_name': numero})
        for inv, lconcil in lines_to_concil.items():
            self.pool.get('account.move.line').reconcile_partial(cr, uid, lconcil, 'manual', context=context)
            self.pool.get('account.invoice').write(cr, uid, [inv], {'ret_id':obj.id})
        self.write(cr, uid, [obj.id], {'move_ret_id':move_id, 'state':'paid', 'name':numero})
        return True
        

    def act_cancel(self, cr, uid, ids, context):
        # TODO fixme its cancel -> state must be cancel

        for obj in self.browse(cr, uid, ids):
            if obj.move_ret_id:
                
                self.pool.get('account.move').button_cancel(cr, uid, [obj.move_ret_id.id])
                self.pool.get('account.move').unlink(cr, uid, [obj.move_ret_id.id])
                                        
                if context['tipo_fact'] == 'out_invoice' or context['tipo_fact'] == 'in_invoice':                    
                    self.write(cr, uid, [obj.id], {'state':'cancel', 'move_ret_id':False})
                else:
                    self.write(cr, uid, [obj.id], {'state':'draft', 'move_ret_id':False})
                                
                
        return True

    def act_cancel2(self, cr, uid, ids, context):
        # TODO fixme its cancel -> state must be cancel

        for obj in self.browse(cr, uid, ids):
            # if obj.move_ret_id:
                
                # self.pool.get('account.move').button_cancel(cr, uid, [obj.move_ret_id.id])
                # self.pool.get('account.move').unlink(cr, uid, [obj.move_ret_id.id])
                
            cr.execute("select a.factura,a.ret_id,r.name from account_invoice as a left join res_partner as r on r.id=a.partner_id where a.move_id=%i" % (obj.move_ret_id,))
            resultado = cr.fetchall()
            if resultado: 
                factura = resultado[0][0]
                    # retencion=resultado[0][1]
                proveedor = resultado[0][2]
                raise osv.except_osv(_('Error de Anulacion'), _('No se puede anular la retencion, ya que tiene asociada la factura ') + factura + ('del proveedor ') + proveedor)                                 
                    
            else:    
                self.write(cr, uid, [obj.id], {'state':'cancel', 'move_ret_id':False})            
                
        return True
    
    def act_reabrir(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids)[0]
        if obj.move_ret_id:
            self.pool.get('account.move').button_cancel(cr, uid, [obj.move_ret_id.id])
            self.pool.get('account.move').unlink(cr, uid, [obj.move_ret_id.id])
        self.write(cr, uid, [obj.id], {'state':'draft', 'move_ret_id':False})
        return False

    def act_anticipar_ret(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids)[0]
        if obj.type == 'retention':
            self.write(cr, uid, [obj.id], {'state':'early'})
            return True
        else:
            osv.except_osv('Aviso', 'No se puede registrar una retención anticipada de este tipo')
            return False
    
    def check_inv_auth(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids)[0]
        if obj.autorization.doc_type != 'electronic':
            if obj.autorization.num_start <= int(obj.num_comprobante) <= obj.autorization.num_end:
                return True    
            else:
                return False
        return True
#    def write(self, cr, uid, ids, vals, context=None):
#        #print "vals", vals
#        if vals.has_key('num_comprobante'):
#            if vals['num_comprobante']:
#                vals['name']= str(vals['num_comprobante']).zfill(7)
#                air = super(account_invoice_retention, self).write(cr, uid, ids, vals, context=context)
#        else:
#            air = super(account_invoice_retention, self).write(cr, uid, ids, vals, context=context)
#        return air
        
    def _get_name(self, cr, uid, ids, field, args, context=None):
        res = {}
        retentions = self.browse(cr, uid, ids, context=context)
        for retention in retentions:
            res[retention.id] = retention.num_comprobante and ('%s'%retention.num_comprobante).zfill(9) or ''
        return res
    
    _columns = {
        'name' : fields.function(_get_name, method=True, string='Retención', type='char', size=30,
                                 store={'account.invoice.retention': (lambda self, cr, uid, ids, ctx=None: ids, ['num_comprobante'], 10)}),
        'invoice_id': fields.many2one('account.invoice', 'Factura', required=True),
        'autorization' : fields.many2one('account.authorisation', 'Aut. de Retención',
                                         help='a)Retención a proveedor: Autorizacion del SRI para los  \
                                         comprabantes de retención de la empresa \
                                         \n b)Retención de clientes: Autorizacion del SRI los comprobantes de retención de Cliente',
                                         readonly=True, states={'draft':[('readonly', False)]}),
        'num_comprobante': fields.char('Número de Comprobante', size=30, required=True, readonly=True, states={'draft':[('readonly', False)]}, select=True),
        'type' : fields.selection((('retention', 'Retención a proveedor.'),
                                ('out_invoice', 'Retención de cliente.')), 'Tipo', readonly=True, select=True),
        'partner_id' : fields.many2one('res.partner', 'Empresa', select=True, readonly=True, states={'draft':[('readonly', False)]}),
        'journal_id': fields.many2one('account.journal', 'Diario', readonly=True, states={'draft':[('readonly', False)]}),
        'move_ret_id' : fields.many2one('account.move', 'Asiento de Ret.', readonly=True, help="Enlace al asiento de Retención generado."),
        'fecha':fields.date('Fecha', select=True, readonly=True, required=True, states={'draft':[('readonly', False)]}),
        'tax_line': fields.one2many('account.invoice.tax', 'ret_id', 'Líneas de Impuestos', readonly=True, states={'draft':[('readonly', False)]}),
        'state': fields.selection([
            ('draft', 'Borrador'),
            ('early', 'Anticipada'),
            ('paid', 'Realizada'),
            ('cancel', 'Anulada'),
        ], 'Estado', select=True, readonly=True),
        'company_id': fields.related('invoice_id', 'company_id', type='many2one', relation='res.company', store=True)
    }
    _defaults = {
        'type' : lambda * a : 'retention',
        'state': lambda * a: 'draft',
        'fecha':lambda * a: time.strftime('%Y-%m-%d'),
    }
    _constraints = [
        (check_inv_auth, 'El numero generado de la retencion no concuerda con los valores la autorización de retencion.', ["num_comprobante"]),
    ]
account_invoice_retention()


class account_invoice_tax(osv.osv):
    _name = 'account.invoice.tax'
    _inherit = 'account.invoice.tax'

    def _compute_percentage(self, cr, uid, ids, field, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj['id']] = obj['amount'] / obj['base']
        return res
    
    _columns = {
        'fiscal_ex' : fields.char('Ejercicio Fiscal', size=4),
        'tax_group' : fields.char('Grupo', size=25),
#         'percent' : fields.char('Porcentaje', size=20),
        'percent': fields.function(_compute_percentage, method=True, string='Porcentaje', type='float', digits=(16,8),
                                   store={_inherit: (lambda self, cr, uid, ids, *a: ids, [None], 10)}),
        'ret_id': fields.many2one('account.invoice.retention', 'Retención', select=True),
        # 'real_amount_ret' : fields.float('Importe Real', digits = (16,2)),
        'desc_corta':fields.char('Descripción', size=10),
        }

    @api.v7
    def compute(self, cr, uid, invoice_id, context):
        return super(account_invoice_tax, self).compute(cr, uid, invoice_id, context)
    
    @api.v8
    def compute(self, inv):
        tax_grouped = {}
        cur = inv.currency_id.with_context(date=inv.date_invoice or time.strftime("%Y-%m-%d"))
        company_currency = inv.company_id.currency_id
        for line in inv.invoice_line:
            tax_aux = line.invoice_line_tax_id.compute_all(
            (line.price_unit * (1 - (line.discount or 0.0) / 100.0)), 
            line.quantity, line.product_id, inv.partner_id,line.invoice_id.date_invoice,inv.porcentaje_iva_aplicado)
            #,line.invoice_id.date_invoice
            print"compute air574"
            #print"tax_aux['taxes']=%s"%tax_aux['taxes']
            for tax in tax_aux['taxes']:
                val = {}
                #print"val=%s"%val
#                tax_group = self.pool.get('account.tax').read(cr, uid, tax['id'], ['tax_group', 'amount', 'percent_comp', 'desc_corta'])
                tax_group = self.env['account.tax'].browse(tax['id'])
                #print"tax_group=%s"%tax_group 
                #print" tax_group['amount']=%s"% tax_group['amount']
                #print" tax_group.type=%s"% tax_group.type                
                val['invoice_id'] = inv.id
                val['tax_group'] = tax_group['tax_group']
                val['percent'] = tax_group['percent_comp']
                val['desc_corta'] = tax_group['desc_corta']
                val['name'] = tax['name'].encode('UTF-8')
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                if tax_group['tax_group'] == 'ret_vat':
                    print"tax['amount'] =%s"%tax['amount'] 
                    print"tax['price_unit'] =%s"%tax['price_unit']
                    print"tax_group['amount'] =%s"%tax_group['amount']
                    
                    if tax['price_unit']==0.00:
                       raise ValidationError(u'No existe division para cero(precio unitario NO debe ser igual a 0.00)')
                    
                    """se obtiene el porcentaje aplicado si cantidad es entera o fraccion"""                    
                    if line['quantity'].is_integer():
                        aux1=val['amount']/tax['price_unit']
                        print"aux1=%s"%aux1               
                    else:
                        aux1= tax['amount']/(tax['price_unit'] * line['quantity'])
                    
                    """porcentaje aplicado en números enteros"""
                    aux2=round((-aux1*1000),2) #se toman 2 decimales
                    print"aux2=%s"%aux2
                    
                    """se obtiene el módulo 0 del porcentaje aplicado esta variable sera usada si el porcentaje del impuesto proviene
                        de copdigo python"""
                    aux3=aux2%12
                    print"aux3=%s"%aux3
                    
                                                     
                    """si el porcentaje del impuesto tax_group['amount'] esta configurado en el impuesto se obtendra el monto de la variable ax_group['amount']"""             
                    if tax_group['amount'] !=0:                        
                        """si el mod es 0 aplica 12% caso contrario aplica 14%"""  
                        porimp=round((-tax_group['amount']*1000),2)%12
                        
                        if porimp==0 :
                            base = val['base'] = float(tax['amount'] / (tax_group['amount'] or 1.0))*0.12
                            ##base = val['base'] = float(tax['amount'] / (aux1 or 1.0))*0.12              
                            val['base'] = base
                            print"val['base']12IMPP=%s"%val['base']  
                        else:
                            base = val['base'] = float(tax['amount'] / (tax_group['amount'] or 1.0))*0.14
                            ##base = val['base'] = float(tax['amount'] / (aux1 or 1.0))*0.14              
                            val['base'] = base
                            print"val['base']14IMPP=%s"%val['base']
                    
                    else: #"""Si el porcentaje del impuesto tax_group['amount'] se da desde codigo python """
                        if aux3==0:
                            base = val['base'] = float(tax['amount'] / (aux1 or 1.0))*0.12              
                            val['base'] = base
                            print"12IMPPYTH=%s"%val['base']  
                        else:
                            base = val['base'] = float(tax['amount'] / (aux1 or 1.0))*0.14              
                            val['base'] = base
                            print"14IMPPYTH=%s"%val['base'] 
                    
                else:
                    val['base'] = tax['price_unit'] * line['quantity']
                    print"val['base']-else air=%s"%val['base'] 
                
                if inv.type in ('out_invoice', 'in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
#                     val['base_amount'] = cur.compute(cr, uid, from_currency_id, to_currency_id, from_amount, round=True, context=None)
                    val['base_amount'] = cur.compute(val['base'] * tax['base_sign'], company_currency, round=False)
                    val['tax_amount'] = cur.compute(val['amount'] * tax['tax_sign'], company_currency, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur.compute(val['base'] * tax['ref_base_sign'], company_currency, round=False)
                    val['tax_amount'] = cur.compute(val['amount'] * tax['ref_tax_sign'], company_currency, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = cur.round(t['base'])
            t['amount'] = cur.round(t['amount'])
            t['base_amount'] = cur.round(t['base_amount'])
            t['tax_amount'] = cur.round(t['tax_amount'])
        return tax_grouped

    def move_line_get(self, cr, uid, invoice_id):
        res = []
        cr.execute('SELECT * FROM account_invoice_tax WHERE invoice_id=%s', (invoice_id,))
        for t in cr.dictfetchall():
            if not t['amount'] \
                    and not t['tax_code_id'] \
                    and not t['tax_amount']:
                continue
            res.append({
                'type':'tax',
                'name':t['name'],
                'price_unit': t['amount'],
                'quantity': 1,
                'price': t['amount'] or 0.0,
                'account_id': t['account_id'],
                'tax_code_id': t['tax_code_id'],
                'tax_amount': t['tax_amount'],
                'tax_group': t['tax_group'],
            })
        return res
account_invoice_tax()

class account_move(osv.osv):
    _name = 'account.move'
    _inherit = 'account.move'
    _rec_name = 'no_comp'
    
    def onchange_date(self, cr, uid, ids, date):
        period_id = self.pool.get('account.period').find(cr, uid, date)
        return {'value': {'period_id': period_id}}
    
    def name_get(self, cr, uid, ids, context=None):
        res = self.read(cr, uid, ids, [self._rec_name], context, load='_classic_write')
        return [(aux['id'], aux[self._rec_name]) for aux in res]
    
    def _format_date(self, date_from):
        if date_from:
            campos = date_from.split('-')
            date_to = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date_to
    
    def _get_start(self, primera_fecha):
        current_date = self._format_date(primera_fecha)
        carry, new_month = divmod(current_date.month - 1 + 1, 12)
        new_month += 1
        dp = calendar.monthrange(current_date.year, new_month)
        current_date = current_date.replace(year=current_date.year + carry, month=new_month, day=dp[1])
        return current_date.strftime('%Y-%m-%d')

    
    def button_validate(self, cursor, user, ids, context=None):
        #print 'Move line heredado'
        
        moves = self.browse(cursor, user, ids, context=context)
        for move in moves:
            if move.journal_id.allow_date:
                if not time.strptime(move.date[:10], '%Y-%m-%d') >= time.strptime(move.period_id.date_start, '%Y-%m-%d') or not time.strptime(move.date[:10], '%Y-%m-%d') <= time.strptime(move.period_id.date_stop, '%Y-%m-%d'):
                        raise osv.except_osv(_('Error !'), _('The date of your Journal Entry is not in the defined period!'))
            for line in move.line_id:
                if line.period_id.id != move.period_id.id:
                    raise osv.except_osv(_('Error !'), _('You cannot create entries on different periods/journals in the same move'))
                if line.journal_id.id != move.journal_id.id:
                    raise osv.except_osv(_('Error !'), _('You cannot create entries on different periods/journals in the same move'))
                
        super(account_move, self).button_validate(cursor, user, ids, context)
    
    def _check_date(self, cursor, user, ids, context=None):
        return True
    
    def _check_period_journal(self, cursor, user, ids, context=None):
        return True
        
    
    _columns = {
        'number_entries':fields.integer('Numero Comprobante Diario', help='Numero secuencial segun diario contable que aparece en el reporte de comprobantes de ingreso, egreso y diario'),
        # 'no_comp':fields.function(_funtion_journal_voucher, string='Nro.Comp', type='char', method=True, size=50, select=True, store=True),
        'no_comp':fields.char('Nro.Comp', size=50),
#         'tipo_comprobante':fields.selection([('ComproDiario', 'ComprobanteDiario'),
#                                          ('IngresoCaja', 'Ingreso de Caja'), ('N.A.', 'N.A.'), ('Egreso', 'Egreso'), ('OPago', 'OrdenPago'), ('CajaChica', 'CajaChica')], 'Tipo Comprobante', required=True),
        'tipo_comprobante':fields.selection([('ComproDiario', 'Comprobante de diario'),
                                             ('IngresoCaja', 'Ingreso de Caja'),
                                             ('Egreso', 'Egreso de Caja')], 'Tipo Comprobante', required=True),
        'other_info': fields.text('Detalle', required=True, readonly=True, states={'draft':[('readonly', False)]}),
                # 'date_from':fields.date('Inicio', help="Fecha inicio del diferido"),#FEcha Inicio del diferido
        # 'date_to':fields.date('Fin', help="Fecha fin del diferido"),#FEcha fin del diferido
        # 'is_deferred':fields.boolean('Gasto Diferido', help="Marque este campo cuando desee crear un Gasto Diferido a partir del asiento por apunte"),#Asiento genera Diferido
    }
    _defaults = {
        'tipo_comprobante': lambda *a: 'ComproDiario'  
    #    'date_from': lambda *a: time.strftime('%Y-%m-%d'),
    #    'date_to': lambda obj, cr, uid, context: obj.pool.get('account.move')._get_start(time.strftime('%Y-%m-%d')),
    }
    
    def __get_no_comp(self, cr, uid, tipo_comprobante='ComproDiario', no_comp=False):
        if tipo_comprobante != 'ComproDiario':
            company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
            cr.execute('SELECT MAX(no_comp) FROM account_move WHERE tipo_comprobante=%s and company_id=%s', (tipo_comprobante, company_id))
            res = int(cr.fetchone()[0] or 0)
            no_comp = str(res + 1).zfill(9)
        return no_comp
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.has_key('tipo_comprobante'):
            no_comp = self.__get_no_comp(cr, uid, vals['tipo_comprobante'], vals.get('no_comp'))
            if no_comp:
                vals['no_comp'] = no_comp
        res = super(account_move, self).write(cr, uid, ids, vals, context)
        return res
    
    def create(self, cr, uid, vals, context={}):
        vals['no_comp'] = self.__get_no_comp(cr, uid, vals.get('tipo_comprobante', 'ComproDiario'), vals.get('no_comp'))
        journal_id = self.pool.get('account.journal').browse(cr, uid, vals['journal_id'])
        ctx = context.copy()
        ctx['date'] = vals.get('date')
        vals['name'] = self.pool.get('ir.sequence').get_id(cr, uid, journal_id.sequence_id.id)
#         vals['tipo_comprobante'] = vals.get('tipo_comprobante') or 'Egreso'
        if vals.has_key('tipo'):
            if vals['bandera'] == 0:
                if not vals.has_key('journal_id') or not vals['journal_id']:
                    raise osv.except_osv(_('Error de Configuracion !'), _('El asiento no tiene un diario contable definido !'))
            
                if not vals.has_key('period_id'):        
                    period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', time.strftime('%Y-%m-%d')),
                                                                          ('date_stop', '>=', time.strftime('%Y-%m-%d'))])
                    if period_ids:
                        period_id = period_ids[0]
                else:
                    period_id = vals['period_id']     
        
                period = self.pool.get('account.period').browse(cr, uid, period_id)
                if period.state == 'close':
                    raise osv.except_osv(_('Error'), _('No se puede realizar movimientos en periodos cerrados ', period.name))
        
#                 if not vals.get('no_comp'):
#                     if vals['tipo_comprobante'] == 'ComproDiario':
#                         sequence = self.pool.get('ir.sequence').get(cr, uid, 'comprobante_diario_seq')
#                     elif vals['tipo_comprobante'] == 'IngresoCaja':
#                         sequence = self.pool.get('ir.sequence').get(cr, uid, 'ingreso_caja_seq')
#                     # TODO AUMENTAR EL DOCUMENTO DE EGRESO
#                     elif vals['tipo_comprobante'] == 'Egreso':
#                         sequence = self.pool.get('ir.sequence').get(cr, uid, 'comprobante_egreso_seq')
#                     elif vals['tipo_comprobante'] == 'OPago':
#                         sequence = self.pool.get('ir.sequence').get(cr, uid, 'orden_pago_seq')
#                         #print ' sequence ', sequence
#                     elif vals['tipo_comprobante'] == 'CajaChica':
#                         sequence = 0
#                     
#                     vals['no_comp'] = sequence
        else:
            if not vals.has_key('journal_id') or not vals['journal_id']:
                raise osv.except_osv(_('Error de Configuracion !'), _('El asiento no tiene un diario contable definido !'))
            
            if not vals.has_key('period_id'):        
                period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', time.strftime('%Y-%m-%d')),
                                                                      ('date_stop', '>=', time.strftime('%Y-%m-%d'))])
                if period_ids:
                    period_id = period_ids[0]
            else:
                period_id = vals['period_id']
            
            period = self.pool.get('account.period').browse(cr, uid, period_id)
            if period.state == 'close':
                raise osv.except_osv(_('Error'), _('No se puede realizar movimientos en periodos cerrados ', period.name))
    
#             if not vals.get('no_comp'):
#                 if vals['tipo_comprobante'] == 'ComproDiario':
#                     sequence = self.pool.get('ir.sequence').get(cr, uid, 'comprobante_diario_seq')
#                 elif vals['tipo_comprobante'] == 'IngresoCaja':
#                     sequence = self.pool.get('ir.sequence').get(cr, uid, 'ingreso_caja_seq')
#                 # TODO AUMENTAR EL DOCUMENTO DE EGRESO
#                 elif vals['tipo_comprobante'] == 'Egreso':
#                     sequence = self.pool.get('ir.sequence').get(cr, uid, 'comprobante_egreso_seq')
#                 elif vals['tipo_comprobante'] == 'OPago':
#                     sequence = self.pool.get('ir.sequence').get(cr, uid, 'orden_pago_seq')
#                 elif vals['tipo_comprobante'] == 'CajaChica':
#                     sequence = 0
#                 else:
#                     journal_id = self.pool.get('account.journal').browse(cr, uid, vals['journal_id'])
#                     sequence = self.pool.get('ir.sequence').get_id(cr, uid, journal_id.sequence_id.id)
#                 vals['no_comp'] = sequence 
            
        if not vals.has_key('other_info'):
            vals['other_info'] = context.get('other_info', ' ')
        return super(account_move, self).create(cr, uid, vals, context)
    
    _constraints = [
        (_check_period_journal,
            'You cannot create entries on different periods/journals in the same move',
            ['line_id']),
        (_check_date,
            'The date of your Journal Entry is not in the defined period!',
            ['journal_id'])
    ]    

   
account_move()

# Para adicionar el numero de formulario de declaracion SRI
class account_tax_code(osv.osv):
    _name = 'account.tax.code'
    _inherit = 'account.tax.code'
    _columns = {
                'formulario':fields.selection([('103', '103'), ('104', '104') ], "Formulario", help="Formulario de Declaracion"),
        }
account_tax_code()


# Clase heredada de class account_analytic_account para validar que no se repita el codigo de la cuenta analitica
class account_analytic_account(osv.osv):
    _name = "account.analytic.account"
    _inherit = "account.analytic.account"

    def onchange_code(self, cr, uid, ids, num_code):
        
        res = {}
        if num_code:
            cr.execute("SELECT code from account_analytic_account where code='%s'" % (num_code,))
            code = cr.fetchall()
            if code:
                res['value'] = {'code':""}
                res['warning'] = {'title':"Error de Usuario", "message":"Ya existe el Numero de Codigo de la Cuenta Analitica, debe de ingresar uno diferente!"}
                return res
            else:
                return {'value':{'code':num_code}}  
                
        return res
    
account_analytic_account()

class account_account(osv.osv):
    _inherit = "account.account"
    _columns = {
        'casillero':fields.char('Formulario 101', size=16),
        'cuenta_resultado':fields.boolean('Cuenta Resultado?', help="Marque este casillero si al saldo de la cuenta debe sumarse la utilidad o perdida del ejercicio"),
    }
account_account()

class  account_journal(osv.osv):
    _inherit = 'account.journal'
    _columns = {
        'type': fields.selection([('sale', 'Sale'), ('sale_refund', 'Sale Refund'), ('purchase', 'Purchase'), ('purchase_refund', 'Purchase Refund'), ('cash', 'Cash'), ('bank', 'Bank and Cheques'), ('general', 'General'), ('situation', 'Opening/Closing Situation'), ('pagos_varios', 'Pagos Varios')], 'Type', size=32, required=True,
                                 help="Select 'Sale' for Sale journal to be used at the time of making invoice."\
                                 " Select 'Purchase' for Purchase Journal to be used at the time of approving purchase order."\
                                 " Select 'Cash' to be used at the time of making payment."\
                                 " Select 'General' for miscellaneous operations."\
                                 " Select 'Opening/Closing Situation' to be used at the time of new fiscal year creation or end of year entries generation."),
    } 
account_journal()

class account_move_line(osv.osv):
    _name = 'account.move.line'
    _inherit = 'account.move.line'
    _columns = {
        'no_comp': fields.related('move_id', 'no_comp', type='char', size=50, string='Nro.Comprobante', store=False),
        'numero_orden': fields.char('Numero Orden', size=8),
        'debit': fields.float('Debit', digits=(16, 2)),
        'credit': fields.float('Credit', digits=(16, 2)),
    }
    
    def unlink(self, cr, uid, ids, context=None):
        lines = self.browse(cr, uid, ids, context=context)
        for line in lines:
            args = [('aml_id', '=', line.id), ('conciliation_id.state', '=', 'confirm')]
            con_line = self.pool['account.conciliation.line'].search(cr, uid, args)
            if con_line or line.x_conciliado:
                raise osv.except_osv('ValidationError', u'No puede eliminar líneas de asiento que se encuentren en una conciliación bancaria.')
        return super(account_move_line, self).unlink(cr, uid, ids, context)
    
account_move_line()


