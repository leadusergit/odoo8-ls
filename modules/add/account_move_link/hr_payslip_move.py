# -*- coding: utf-8 -*-
import time
import openerp.addons.decimal_precision as dp
from datetime import date, datetime, timedelta

from openerp.osv import fields, osv
from openerp.tools import float_compare, float_is_zero
from openerp.tools.translate import _

class account_move(osv.osv):
    _inherit = 'account.move'        
         
    _columns = {
        'payslip_ref': fields.many2one('hr.payslip','Ref Nomina',readonly=True),
        'inv_ref': fields.many2one('account.invoice','Ref Factura',readonly=True),
        'ret_ref': fields.many2one('account.invoice.retention.voucher','Ref Retencion Cliente',readonly=True),
        'vchr_ref': fields.many2one('account.voucher','Ref Pago',readonly=True),

    }   
    
    _defaults = {
            'payslip_ref':0,
            'inv_ref':0,
            'ret_ref':0,
            'vchr_ref':0,
                 }
    
class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'

    
    def process_sheet(self, cr, uid, ids, context=None):
        move_pool = self.pool.get('account.move')
        period_pool = self.pool.get('account.period')
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Payroll')
        timenow = time.strftime('%Y-%m-%d')

        for slip in self.browse(cr, uid, ids, context=context):
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            if not slip.period_id:
                search_periods = period_pool.find(cr, uid, slip.date_to, context=context)
                period_id = search_periods[0]
            else:
                period_id = slip.period_id.id

            default_partner_id = slip.employee_id.address_home_id.id
            name = _('Payslip of %s') % (slip.employee_id.name)
            print"//module account_move_link//payslip"
            move = {
                'narration': name,
                'date': timenow,
                'ref': slip.number,
                'no_comp': slip.number,
                'journal_id': slip.journal_id.id,
                'period_id': period_id,
                'payslip_ref':slip.id  #dc link a payslip origen
            }
            for line in slip.details_by_salary_rule_category:
                amt = slip.credit_note and -line.total or line.total
                if float_is_zero(amt, precision_digits=precision):
                    continue
                partner_id = line.salary_rule_id.register_id.partner_id and line.salary_rule_id.register_id.partner_id.id or default_partner_id
                debit_account_id = line.salary_rule_id.account_debit.id
                credit_account_id = line.salary_rule_id.account_credit.id

                if debit_account_id:

                    debit_line = (0, 0, {
                    'name': line.name,
                    'date': timenow,
                    'partner_id': (line.salary_rule_id.register_id.partner_id or line.salary_rule_id.account_debit.type in ('receivable', 'payable')) and partner_id or False,
                    'account_id': debit_account_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': amt > 0.0 and amt or 0.0,
                    'credit': amt < 0.0 and -amt or 0.0,
                    'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
                    'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                    'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
                })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                if credit_account_id:

                    credit_line = (0, 0, {
                    'name': line.name,
                    'date': timenow,
                    'partner_id': (line.salary_rule_id.register_id.partner_id or line.salary_rule_id.account_credit.type in ('receivable', 'payable')) and partner_id or False,
                    'account_id': credit_account_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': amt < 0.0 and -amt or 0.0,
                    'credit': amt > 0.0 and amt or 0.0,
                    'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
                    'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                    'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
                })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Credit Account!')%(slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': timenow,
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Debit Account!')%(slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': timenow,
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)

            move.update({'line_id': line_ids})
            move_id = move_pool.create(cr, uid, move, context=context)
            print"move_id=%s"%move_id
            self.write(cr, uid, [slip.id], {'move_id': move_id, 'period_id' : period_id}, context=context)
            if slip.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context=context)
                
        return self.write(cr, uid, ids, {'paid': True, 'state': 'done'}, context=context)
    #super(hr_payslip, self).process_sheet(cr, uid, [slip.id], context=context)
  
 
    
class account_invoice_retention_voucher(osv.osv):
    _inherit = "account.invoice.retention.voucher"
    
    # Boton generar asientos del comprobante de retencion *EM, se modifico el funcionamiento anterior EG
    def action_move_lines_voucher(self, cr, uid, ids, context=None):
        """heredado desde modulo account_invoice_retention
            se añade campos al generar asiento contable"""
        obj_move = self.pool.get('account.move')
        obj_move_line = self.pool.get('account.move.line')
        obj_voucher_line = self.pool.get('account.invoice.retention.voucher.line')
        obj_journal = self.pool.get('account.journal')
        obj_account = self.pool.get('account.account')
        torec = []
        inv_open = []
        cad = ''
        out_invoice = 0
        move_id = 0
        period_id = 0
        partner_id = 0
        journal = 0
        des = ''
        ref = ''
        a = []
        n = 0
        for com in self.browse(cr, uid, ids):
            band = False#Retenciones que no tiene facturas
            a.append('R.RENTA#' + str(com.number))
            for inv in com.invoice_ids:
                band = True
            for inv in com.invoice_ids:
                if inv.state in ('open'):
                    inv_open.append(inv.num_retention)
                    cad = cad + str(inv.num_retention) + ' / '
                    move_id_invoice = inv.move_id.id
                    period_id = self._get_period(cr, uid, com.broadcast_date)
                    partner_id = inv.partner_id.id 
                    print"//module account_move_link//ret voucher"
                    print"***partner_id***=%s"%partner_id
                    journal = inv.journal_id.id
                    out_invoice = inv.id
                    #Descripcion de la Retencion R.RENTA#1236 FACT# 36963
                    ref = inv.num_retention
#                     n = int(inv.factura) or int(inv.num_retention)
                    n = inv.factura or inv.num_retention
                    a.append('FACT#' + str(n))
                    
            open = len(inv_open)

            if open == 1 and move_id_invoice and band and com.state in ('draft', 'new'):
                des = ' - '.join(a)
                id_v_lines = obj_voucher_line.search(cr, uid, [('ret_voucher_id', '=', com.id)])
                #identificar en cada plan de cuenta el numero de id de la cuenta de clientes
                account_ids = [com.partner_id.property_account_receivable.id, com.partner_id.property_account_payable.id]
#                 account_ids = obj_account.search(cr, uid, [('parent_id', 'in', (4544, 455120))])
                move_line_id = obj_move_line.search(cr, uid, [('move_id', '=', move_id_invoice),
                                                              ('account_id', 'in', account_ids),
                                                              ('credit', '=', 0.00)])                
                #print "Linea de Cuenta por cobrar de Cliente", move_line_id
                obj_cliente = self.pool.get('res.partner').browse(cr, uid, partner_id)                
                if move_line_id:
                    #obj_cliente = obj_move_line.browse(cr, uid, move_line_id)
                    journal_id = obj_journal.search(cr, uid, [('name', 'ilike', ('%retencion%'))])
                    
                    if not journal_id:
                        raise osv.except_osv(('Datos Incompletos'),
                                             ('No existe el diario de nombre RETENCIONES. Por favor crearlo'))
                    if id_v_lines:
                        move_id = obj_move.create(cr, uid, {'journal_id':journal_id[0],
                                                            'period_id':period_id,
                                                            'ref':com.num_voucher_purchase,
                                                            'no_comp':com.num_voucher_purchase,
                                                            'ret_ref':com.id,# referencia ret origen
                                                            'date':com.broadcast_date,
                                                            'tipo_comprobante':'ComproDiario'})

                        obj_v_lines = obj_voucher_line.browse(cr, uid, id_v_lines)
                        total = 0.0
                        account_id = False
                        
                        for line in obj_v_lines:
                            if line.tax_id.account_paid_id:
                                account_id = line.tax_id.account_paid_id.id
                            else:
                                raise osv.except_osv(('Error Uso'),
                                                     ('Configure la cuenta de impuestos de devoluciones de la cuenta de impuestos'))
                            total += line.ret_amount
                            """código añadido para obtener el partner configurado en la cuenta contable"""
                            account_obj = self.pool.get('account.account')
                            print"account_obj=%s"%account_obj
                            cuenta_id = account_obj.search(cr, uid, [('partner_id','!=',None)]) 
                            print"cuenta_id=%s"%cuenta_id
                            
                            if account_id in cuenta_id :
                                partner_account = self.pool.get('account.account').browse(cr, uid, account_id)
                                partner= partner_account.partner_id.id
                                print"partner_idif=%s"%partner
                            else:
                                partner=partner_id
                                                               
                            print"account_id=%s"%account_id                               
                            print"partner=%s"%partner
                            
                            val = {
                                 'date':com.broadcast_date,
                                 'account_id':account_id,
                                 'partner_id':partner,#DC#partner_id,partner de cuenta contable
                                 'period_id':period_id,
                                 'period_id':period_id,
                                 'journal_id':journal_id[0],
                                 'debit':line.ret_amount,
                                 'credit':0.0,
                                 'move_id':int(move_id) ,
                                 'name':line.tax_id.account_paid_id.name,
                                 'state':'valid',
                                 'ref': ref,
                                 'inv_type':'retencion'
                                 }
                            id_m_line = obj_move_line.create(cr, uid, val)
                            
                        if total > 0:
                            print"total=%s"%total
                            val2 = {
                                 'date':com.broadcast_date,
                                 'account_id':obj_cliente.property_account_receivable.id,
                                 'partner_id':partner_id,#partner de documento
                                 'period_id':period_id,
                                 'journal_id':journal_id[0],
                                 'debit':0.0,
#                                 'name':obj_cliente.property_account_receivable.name,
                                 'name':des,
                                 'credit':total,
                                 'state':'valid',
                                 'move_id':int(move_id) ,
                                 'ref': ref,
                                 'inv_type':'retencion'
                                 }
                            id_n_l = obj_move_line.create(cr, uid, val2)
                            print"int(move_id)=%s"%int(move_id)
                            #===================================================
                            # Generacion de Pago parcial para la Retencion
                            #===================================================
                            
                            
                            partial = obj_move_line.search(cr, uid, [('move_id', '=', move_id_invoice),
                                                                     ('credit', '=', 0.00),
                                                                     ('reconcile_partial_id', '<>', False)])
                            #print "Agrego Retencion al Pago Parcial", partial
                            print"partial=%s"%partial
                            if partial:
                                torec.append(partial[0])
                                torec.append(id_n_l)
                                ##print "l", torec
                                context['retencion'] = True
                                obj_move_line.reconcile_partial(cr, uid, torec, 'statement', context)
                            else:
                                torec.append(move_line_id[0])
                                torec.append(id_n_l)
                                #print "Creo el pago parcial", torec
                                context['retencion'] = True
                                obj_move_line.reconcile_partial(cr, uid, torec, 'statement', context)
                        
                        if move_id:
                            self.pool.get('account.move').post(cr, uid, [move_id])
                        self.write(cr, uid, [com.id], {'state':'valid', 'move_id':move_id, 'total':total, 'nro_retencion':str(com.number)})
                else:
                    raise osv.except_osv(('Error Uso'), ('Revise la cuenta de cliente de la factura'))
            elif open == 0:
                raise osv.except_osv(('Error Uso'), ('Esta retencion no tiene factura en estado abierto'))
            else:
                raise osv.except_osv(('Error Uso'), ('Estas facturas tienen las misma retencion en estado abierto: ' + cad))

        return True

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    
    def action_move_create(self, cr, uid, ids, *args):
        #print "2) action_move_create", ids
        # Actualiza Informacion de la Orden Venta en la Factura para el proceso de comisiones de vendedores
        # self.action_sale_cuota(cr, uid, ids)
        # Se Crea el Activo a partir de la Orden de Compra. Siempre y cuando se Escoja un Producto que este configurado como Activo
        self.action_asset_create(cr, uid, ids)
        #=======================================================================
        # Creacion de la tabla de Diferidos
        #=======================================================================
        self.action_generate_billing(cr, uid, ids)
        
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        rete_voucher_obj = self.pool.get('account.invoice.retention.voucher')
        context = {}
        
        for inv in self.browse(cr, uid, ids):
            or_amount = 0.0
            ir_amount = 0.0
            # Revision de Totales para la creacion de Notas de Credito de Facturas de Ventas
            if inv.type in ['out_refund']:
                # #print "o1", inv.origin
                if inv.origin:
                    # Buscar en el campo num_retention
                    foi = self.search(cr, uid, [('num_retention', 'ilike', inv.origin)])
                    # #print "foi", foi
                    if foi:
                        or_amount = self.browse(cr, uid, foi[0]).amount_total
                        # #print "or_amount", or_amount
                        if inv.amount_total > or_amount:
                            raise osv.except_osv('Total Incorrecto', 'Por favor Revise el total !\nEl Total a Pagar no debe ser mayor al de la factura de origen:' + inv.origin + '.')
            # Revision de Totales para la creacion de Notas de Credito de Facturas de Compras
            if inv.type in ['in_refund']:
                # #print "o2", inv.origin
                # Buscar en el campo number_inv_supplier
                if inv.origin:
                    a = True
                    for i in inv.origin:
                        if i not in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0'):
                            a = False
                             
                    if a and int(inv.origin):
                        ir = self.search(cr, uid, [('number_inv_supplier', '=', int(inv.origin))])
                        # #print "ir", ir
                        if ir:
                            # Valor sin retencion para facturas de proveedores
                            ir_amount = self.browse(cr, uid, ir[0]).amount_pay
                            # #print "ir_amount", ir_amount
                            if inv.amount_total > ir_amount:
                                raise osv.except_osv('Total Incorrecto', 'Por favor Revise el total !\nEl Total a Pagar no debe ser mayor al de la factura de origen:' + inv.origin + '.')
                    
            
            tipo_factura = inv.tipo_factura
            factura_tipo = inv.type
            number = False
            if inv.type == 'in_invoice' and inv.type in ['in_invoice', 'in_refund']:
                if inv.type == 'in_invoice' and inv.amount_untaxed >= 1000 and not len(inv.payment_method_ids):
                    raise osv.except_osv('ATS', u'El valor de la Base Imponible supera los $1000, por favor ingrese por lo menos un metodo de pago en la Pestaña de Información de Pago.')
                
            if inv.move_id:
                continue
            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice':time.strftime('%Y-%m-%d'),
                                               'date_from_deferred':time.strftime('%Y-%m-%d')})
            company_currency = inv.company_id.currency_id.id
                # create the analytical lines
            line_ids = self.read(cr, uid, [inv.id], ['invoice_line'])[0]['invoice_line']
            
            # one move line per invoice line
            # #print ' antes del envio '
            iml = self._get_analytic_lines(cr, uid, inv.id)
            #print ' iml account invoice ', iml

            if tipo_factura in ('purchase_liq', 'gas_no_dedu', 'doc_inst_est', 'invoice','gasto_financiero'):
                self.obtain_lines_advances(cr, uid, inv, iml)
                
            # check if taxes are all computed
            self.check_all_computed_taxes(cr, uid, inv, context)
            #print"inv.check_total=%s"%inv.check_total
            #print"inv.amount_pay=%s"%inv.amount_pay
            #print"inv.currency_id=%s"%(inv.currency_id.rounding / 2.0)
            """LINEA MODIFICADA PARA EVITAR ERROR AL VALIDAR FACTURA PROVEEDOR  SE VALIDA CON EL TOTAL RESTADO EL IMPUESTO"""
            #if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_pay) >= (inv.currency_id.rounding / 2.0):
            if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding / 2.0):
                raise osv.except_osv('Total incorrecto!', 'Por favor verificar el valor de la factura!\nEl valor real no es igual al calculado!')
            
                        
            # one move line per tax line
            iml += ait_obj.move_line_get(cr, uid, inv.id)
            #print ' iml ***** AAAA **** ', iml
                        
            # delete tax line when ret_ir or ret_vat
            if not inv.gen_ret_mode or inv.type == 'out_invoice':
#                #print "entra_out_invoice"
                iml = [item for item in iml if not item.has_key('tax_group') or (item.has_key('tax_group') and not item['tax_group'] in ['ret_ir', 'ret_vat'])]
#                #print "iml", iml
            
            # Asignacion del campo ref en el move_line del numero de Factura para una mejor busqueda desde los extractos o desde la linea de asientos
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
            else:
                ref = inv.number
            if inv.type in ('in_invoice', 'in_refund'):
                if tipo_factura in ['invoice', 'purchase_liq', 'sales_note']:
                    ref = inv.number_inv_supplier and str(inv.number_inv_supplier).zfill(9)
                elif tipo_factura in ['anticipo', 'gas_no_dedu','gasto_financiero']:
                    ref = inv.code_advance_liq
                else:
                    ref = inv.number
#                     ref = self._convert_ref(inv.number)
            elif inv.type in ('out_invoice', 'out_refund'):
                
                if inv.auth_ret_id:
                    if inv.auth_ret_id.sequence_id:
                        if not inv.num_retention:
                            # #print "Asigno el Numero de Factura/Nota de Credito de Venta"
                            if inv.type == 'out_invoice' and inv.auth_ret_id.type not in ('out_invoice'):
                                    raise osv.except_osv('Aviso de Contabilidad',
                                                         'Debe seleccionar una autorizacion de tipo Factura Cliente')
                            number = self.pool.get('ir.sequence').get_id(cr, uid, inv.auth_ret_id.sequence_id.id)
                            ref = number
                        else:
                            ref = inv.num_retention
                if not inv.date_to_deferred:
                    inv.date_to_deferred = inv.date_invoice
#             else:
#                 ref = self._convert_ref(inv.number)
            # #print "referencia", ref
            
            diff_currency_p = inv.currency_id.id <> company_currency
            descuentos = []

            total = total_currency = band = descuento = 0
            
            if inv.type == 'out_invoice' and inv.invoice_line:
                for det in inv.invoice_line:
                    if det.discount != 0:
                        band = 1
            
            # Metodo que divide a las diferentes cuentas las valores del Diario Analitico            
            self.obtain_line_analytics(cr, uid, inv, iml)
            
            for i in iml:
                if inv.currency_id.id != company_currency:
                    i['currency_id'] = inv.currency_id.id
                    i['amount_currency'] = i['price']
                    i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id,
                                                 company_currency, i['price'],
                                                 context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')})
                else:
                    i['amount_currency'] = False
                    i['currency_id'] = False
#                 i['ref'] = ref
                
                if inv.type in ('out_invoice', 'in_refund'):
                    total += i['price']
                    total_currency += i['amount_currency'] or i['price']
                    i['price'] = -i['price']
                else:
                    total -= i['price']
                    total_currency -= i['amount_currency'] or i['price']
            
            acc_id = inv.account_id.id
            name = inv['name'] or '/'
            totlines = False
            # #print "payment_term", inv.payment_term   
            """permite crear asiento contable de acuerdo a las reglas configuradas en el termino de pago
             30-60-90-120 días"""         
            if inv.payment_term:
              totlines = self.pool.get('account.payment.term').compute(cr, uid, inv.payment_term.id,
                                                                    total, inv.date_invoice or False)

            if totlines and band == 0:
                # #print "Normal band 0 y Totlines"
                res_amount_currency = total_currency
                i = 0
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1])
                    else:
                        amount_currency = False
                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                        and  amount_currency or False,
                        'currency_id': diff_currency_p \
                        and inv.currency_id.id or False,
                        'ref': ref,
                        'inv_type':factura_tipo
                    })
            if not totlines and band == 0:
                # #print "Normal band 0 y not Totlines"
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity' : inv.date_due or False,
                    'amount_currency': diff_currency_p \
                    and total_currency or False,
                    'currency_id': diff_currency_p \
                    and inv.currency_id.id or False,
#                     'ref': ref,
                    'inv_type':factura_tipo
                })
            
            if totlines and band == 1: 
                # #print "Entro totlines band ==1"
                aux1 = 0
                for i in iml:
#                    #print "i", i
                    if i.has_key('discount') and i['discount'] != 0:
                        aux1 += (i['price_unit'] * i['quantity']) * i['discount'] / 100
                res_amount_currency = total_currency
                
                i = 0
                for t in totlines:
                    r = round(aux1, int(dp.get_precision('Account')))
                    resta = t[1] - r
#                    #print "resta", resta
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid,
                                                          company_currency, inv.currency_id.id, t[1])
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency
                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': resta,
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                        and  amount_currency or False,
                        'currency_id': diff_currency_p \
                        and inv.currency_id.id or False,
                        'ref': ref,
                        'inv_type':factura_tipo
                    })
            if not totlines and band == 1:
                # #print "Entro not totlines and band ==1"
                aux1 = 0
                for i in iml:
                    if i.has_key('discount') and i['discount'] != 0:
                        aux1 += (i['price_unit'] * i['quantity']) * i['discount'] / 100
                presicion = dp.get_precision('Account')(cr)
                r = round(aux1, presicion[1])
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total - r,
                    'account_id': acc_id,
                    'date_maturity' : inv.date_due or False,
                    'amount_currency': diff_currency_p \
                    and total_currency or False,
                    'currency_id': diff_currency_p \
                    and inv.currency_id.id or False,
                    'ref': ref,
                    'inv_type':factura_tipo
                })
            if band == 1:
                # #print "entra band = 1"
                for i in iml:
                    if i.has_key('discount'):
                        descuento = i['discount']
                        aux = i['discount']
                        if aux != 0:
                            descuento = (i['price_unit'] * i['quantity']) * i['discount'] / 100
                            price = round(descuento, int(dp.get_precision('Account')))
                            # #print "////////////PRECIO////// %s \n\n" % (price)
                            cuenta = i['discount_id']
                            iml.append({
                                    'type': 'dest',
                                    'name': name,
                                    'price': price,
                                    'account_id':cuenta ,
                                    'date_maturity': inv.date_due or False,
                                    'amount_currency': diff_currency_p \
                                    and  amount_currency or False,
                                    'currency_id': diff_currency_p \
                                    and inv.currency_id.id or False,
                                    'ref': ref,
                                    'inv_type':factura_tipo
                                })
                        
            date = inv.date_invoice or time.strftime('%Y-%m-%d')
            part = inv.partner_id.id
            print"//module account_move_link//invoice"
            print"partner=%s"%part  
                
            #print "IML \n %s \n" % iml
            line = map(lambda x:(0, 0, self.line_get_convert(cr, uid, x, part, date, context={})) , iml)  
            #print"partner_account=%s"%partner_account                              
            #print "LINES ////:\n %s \n\n\n" % line   
            print"inv.journal_id.group_invoice_lines=%s"%inv.journal_id.group_invoice_lines              
                    
            if inv.journal_id.group_invoice_lines:
                line2 = {}
                for x, y, l in line:
                    tmp = str(l['account_id'])
                    tmp += '-' + str(l.get('tax_code_id', "False"))
                    tmp += '-' + str(l.get('product_id', "False"))
                    tmp += '-' + str(l.get('analytic_account_id', "False"))
                    tmp += '-' + str(l.get('date_maturity', "False"))
                    
                    if tmp in line2:
                        am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
                        line2[tmp]['debit'] = (am > 0) and am or 0.0
                        line2[tmp]['credit'] = (am < 0) and -am or 0.0
                        line2[tmp]['tax_amount'] += l['tax_amount']
                        line2[tmp]['analytic_lines'] += l['analytic_lines']
                    else:
                        line2[tmp] = l
                line = []
                for key, val in line2.items():
                    line.append((0, 0, val))
                    
            journal_id = inv.journal_id.id  # self._get_journal(cr, uid, {'type': inv['type']})
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id)
            if journal.centralisation:
                raise osv.except_osv(_('UserError'),
                                     _('Cannot create invoice move on centralised journal'))     
            
            #dc#datos de registro en account_move_line
            print"line_id :\n %s \n\n\n"%line
            move = { 'line_id': line, 'journal_id': journal_id, 'date': date, 'ref': 'FACT. ' + (inv.factura or ''),
                    'other_info': inv.comment, 'no_comp': inv.number_inv_supplier or inv.factura,'inv_ref':inv.id}
            period_id = inv.period_id and inv.period_id.id or False
            
            if not period_id:
                period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', inv.date_invoice or time.strftime('%Y-%m-%d')),
                                                                              ('date_stop', '>=', inv.date_invoice or time.strftime('%Y-%m-%d'))])
                if period_ids:
                    period_id = period_ids[0]
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id
            # #print "Account Move values: %s" % move
            
            journal_code = inv.journal_id.code
            # NO CAMBIAR ESTAS LINEAS PARA QUE NO SE DANE LA SECUENCIA
#             if journal_code == 'VE':
#             # if journal.type == 'sale':
#                 move['tipo_comprobante'] = 'ComproDiario'
#             elif journal_code == 'CO':
#             # elif journal.type == 'purchase':
#                 move['tipo_comprobante'] = 'OPago'
#             elif journal_code == 'DD':
#                 move['tipo_comprobante'] = 'CajaChica'                    
#             elif journal_code == 'RCCH':
#                 move['tipo_comprobante'] = 'CajaChica'           
           
            move_id = self.pool.get('account.move').create(cr, uid, move, context=context)
            new_move_name = self.pool.get('account.move').browse(cr, uid, move_id).name
            ##print "new_move_name", new_move_name                  
            band = False
            number_retention = 0
            inv_data = {'move_id': move_id, 'period_id':period_id, 'move_name':new_move_name}
            for tax in inv.tax_line:
                if tax.tax_group in ['ret_vat', 'ret_ir']:
                    band = True
                    break
            ret_id = False
            if inv.amount_total != 0 and inv.tax_line:
                if inv.type == 'in_invoice':
                    #print 'inv.type838INVOICE=%s '%inv.type 
                    if band and tipo_factura != 'anticipo':
                        if not inv.auth_ret_id:
                            raise osv.except_osv('Aviso de Contabilidad',
                                             'Debe seleccionar una autorizacion de retenciones')
                        if inv.has_early_ret:
                            self._check_ret_anticipada_valida(cr, uid, ids, inv.ret_id.id)
                        ret_id = self.automatic_retention_create(cr, uid, ids)
                elif inv.type == 'out_invoice':
                    ret_id = self.automatic_retention_create(cr, uid, ids)
                    if inv.auth_ret_id:
                        if inv.auth_ret_id.sequence_id:
                            if not inv.num_retention:
                                if inv.auth_ret_id.type not in ('out_invoice'):
                                    raise osv.except_osv('Aviso de Contabilidad',
                                                     'Debe seleccionar una autorizacion de tipo Factura Cliente')
                                inv_data['num_retention'] = number
                                inv_data['factura'] = number
                elif inv.type == 'out_refund':
                    if inv.auth_ret_id:
                        if inv.auth_ret_id.sequence_id:
                            if not inv.num_retention:
#                            number = self.pool.get('ir.sequence').get_id(cr, uid, inv.auth_ret_id.sequence_id.id)
                                inv_data['num_retention'] = number
                                inv_data['factura'] = number
            else:
            # #print 'entra1'
                if inv.type == 'out_invoice':
                    ret_id = self.automatic_retention_create(cr, uid, ids)
                    if inv.auth_ret_id:
                        if inv.auth_ret_id.type not in ('out_invoice'):
                            raise osv.except_osv('Aviso de Contabilidad',
                                             'Debe seleccionar una autorizacion de tipo Factura Cliente')
                        if inv.auth_ret_id.sequence_id:
                            if not inv.num_retention:
                                inv_data['num_retention'] = number
                                inv_data['factura'] = number
                elif inv.type == 'out_refund':
                    if inv.auth_ret_id:
                        if inv.auth_ret_id.sequence_id:
                            if not inv.num_retention:
                                inv_data['num_retention'] = number
                                inv_data['factura'] = number
            
            
            self.write(cr, uid, [inv.id], inv_data)
            
            
            self.pool.get('account.move').post(cr, uid, [move_id], context={'invoice':inv})
            print 'move_id=%s '%move_id 
            # self.pool.get('account.move').post(cr, uid, [move_id], {'has_name': inv.number})
            if inv.gen_ret_mode:
                if band and tipo_factura != 'anticipo':
                    aux_ret_id = ret_id
                    if not ret_id:
                        aux_ret_id = inv.ret_id.id
                    self.pool.get('account.invoice.retention').write(cr, uid, aux_ret_id, {'move_ret_id':move_id})
                    
            # Actualizar la retencion en caso que tenga cuando vuelve de borrador a abierto
            if inv.ret_voucher and inv.ret_voucher_id and inv.ret_voucher_id.id:
                dir_com = ''
                if inv.partner_id.street and inv.partner_id.street2:
                    dir_com = inv.partner_id.street + ' Y ' + inv.partner_id.street2
                elif inv.partner_id.street:
                    dir_com = inv.partner_id.street
                    
                rete_voucher_obj.write(cr, uid, [inv.ret_voucher_id.id], {'partner':inv.partner_id.name, 'ruc':inv.partner_id.ident_num,
                                                                          'social_reason':inv.company_id.name, 'ruc_ci':inv.company_id.partner_id.ident_num,
                                                                          'address':dir_com, 'state':'draft', 'type_voucher_purchase':str(inv.tipo_factura),
                                                                          'num_voucher_purchase':inv.num_retention,
                                                                          'partner_id':inv.partner_id.id , 'numero':str(number or inv.num_retention).zfill(9)})
                for item in inv.ret_voucher_id.ret_voucher_line_ids:
                    b_i_iva = inv.t_bi_iva * 0.12
                    b_i_ir = inv.amount_untaxed
                    if period_id:
                        obj_period = self.pool.get('account.period').browse(cr, uid, period_id)
                        anio_fis = obj_period.fiscalyear_id.id
                                            
                    self.pool.get('account.invoice.retention.voucher.line').write(cr, uid, item.id, {'tax_base':b_i_ir,
                                                                                                    'fiscal_year_id':anio_fis,
                                                                                                    'ret_voucher_id':inv.ret_voucher_id.id,
                                                                                             })
                
        self._log_event(cr, uid, ids)
        return True


class account_voucher(osv.osv):
    _inherit = "account.voucher"
    
    
    def account_move_get(self, cr, uid, voucher_id, context=None):
        '''
        This method prepare the creation of the account move related to the given voucher.

        :param voucher_id: Id of voucher for which we are creating account_move.
        :return: mapping between fieldname and value of account move to create
        :rtype: dict
        '''
        seq_obj = self.pool.get('ir.sequence')
        voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        if voucher.number:
            name = voucher.number
        elif voucher.journal_id.sequence_id:
            if not voucher.journal_id.sequence_id.active:
                raise osv.except_osv(_('Configuration Error !'),
                    _('Please activate the sequence of selected journal !'))
            c = dict(context)
            c.update({'fiscalyear_id': voucher.period_id.fiscalyear_id.id})
            name = seq_obj.next_by_id(cr, uid, voucher.journal_id.sequence_id.id, context=c)
        else:
            raise osv.except_osv(_('Error!'),
                        _('Please define a sequence on the journal.'))
        if not voucher.reference:
            ref = name.replace('/','')
        else:
            ref = voucher.reference
        print"//module account_move_link//voucher"
        move = {
            'name': name,
            'journal_id': voucher.journal_id.id,
            'narration': voucher.narration,
            'date': voucher.date,
            'ref': ref,
            'no_comp':ref,
            'vchr_ref': voucher.id,#dc #link voucher asiento contable
            'period_id': voucher.period_id.id,
        }
        return move
    
    
    

"""class account_bank_statement(osv.osv):
    _inherit = 'account.bank.statement'


    def unlink(self, cr, uid, ids, context=None):
        statement_line_obj = self.pool['account.bank.statement.line']
        for item in self.browse(cr, uid, ids, context=context):
            print"item.state=%s"%item.state
            if item.state not in('draft','open'):
                raise osv.except_osv(
                    _('Invalid Action!!'),
                    _('In order to delete a bank statement, you must first cancel it to delete related journal items.')
                )
            # Explicitly unlink bank statement lines
            # so it will check that the related journal entries have
            # been deleted first
            statement_line_obj.unlink(cr, uid, [line.id for line in item.line_ids], context=context)
#         return super(account_bank_statement, self).unlink(cr, uid, ids, context=context)"""