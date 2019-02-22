# -*- encoding: utf-8 -*-
##############################################################################
#
#    Balance General
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


from openerp.osv import fields, osv
import xlwt as pycel
import time, cStringIO, base64, datetime, openerp.tools, re
from report_general import report_general
from openerp.addons.account.report.account_general_ledger import general_ledger
from openerp.addons.base_ec.tools.xls_tools import *

def style(bold=False, font_name='Calibri', size=11, font_color='black',
          rotation=0, align='left', vertical='center', wrap=False,
          border=False, color=None, format=None):
    return get_style(bold, font_name, size, font_color, rotation, align, vertical, wrap, border, color, format)

STYLES = {
    'std': style(),
    'bold': style(True),
    'company': style(True, size=14, font_color='dark_red_ega'),
    'header': style(True, size=12),
    'title': style(True, size=12, font_color='dark_yellow', align='center'),
    'num': style(format='[$$-300A]#,##0.00;[$$-300A]-#,##0.00', align='right'),
    'numbold': style(True, format='[$$-300A]#,##0.00;[$$-300A]-#,##0.00', align='right')
}

class account_report_general_ledger(osv.osv_memory):
    _inherit = "account.report.general.ledger"
    _columns = {
        'date_start':fields.date("Fecha Inicio"),
        'data': fields.binary(string='Arch', readonly=True),
        'file_name':fields.char('Archivo', size=32),
        'partner_id': fields.many2one('res.partner', 'Empresa'),
        'invoice_id': fields.many2one('account.invoice', 'Factura'),
        'move_id': fields.many2one('account.move', 'Asiento'),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Cuenta analítica'),
        'state':fields.selection([('ini', 'Inicial'), ('res', 'Resultado')], 'Estado', required=True, readonly=True),
    }
    _defaults = {
        'state': 'ini'
    }
    
    def _print_report(self, cr, uid, ids, data, context=None):
        res = super(account_report_general_ledger, self)._print_report(cr, uid, ids, data, context)
        obj = self.read(cr, uid, ids[0], ['partner_id', 'invoice_id', 'move_id', 'analytic_account_id'])
        for key, value in obj.iteritems():
            if type(value) == tuple and len(value) == 2:
                obj[key] = value[0]
        res['data']['form'].update(obj)
        res['data']['form']['used_context'].update(obj)
        return res

    def print_report_xls(self, cr, uid, ids, context=None):
        obj = self.read(cr, uid, ids, ['chart_account_id', 'accounts_ids', 'partner_id', 'invoice_id', 'move_id', 'analytic_account_id'])[0]
        move_obj = self.pool.get('account.move')
        for key, value in obj.iteritems():
            if type(value) == tuple and len(value) == 2:
                obj[key] = value[0]
        context = context or {}
        check = self.check_report(cr, uid, ids, context)
        type_dummy, data, report_name = check['type'], check['data'], check['report_name']
        report_dummy = general_ledger(cr, uid, report_name, dict(context, **obj))
        book = pycel.Workbook(encoding='utf-8')
        sheet = book.add_sheet('Hoja 1')
        account_ids = self.pool.get('account.account').browse(cr, uid, context.get('active_ids'))
        report_dummy.set_context(account_ids, data, context.get('active_ids'), 'pdf')
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        row = 0
        sheet.write(row, 0, company.name, STYLES['company'])
        sheet.write(row+1, 0, company.rml_header1, STYLES['header'])
        sheet.write(row+2, 0, company.rml_footer, STYLES['header'])
        sheet.write(row+3, 0, company.rml_footer_readonly, STYLES['header'])
        sheet.write_merge(row+5, row+5, 0, 10, 'LIBRO MAYOR', STYLES['title'])
        row += 7
        for col, field in enumerate(['FECHA', 'DIARIO', 'EMPRESA', 'REFERENCIA', 'ASIENTO', 'NOMBRE', 'CONTRAPARTE', 'DEBE', 'HABER', 'SALDO'], 1):
            sheet.write(row, col, field, STYLES['bold'])
        row += 1
        for account_id in account_ids:
            for aux in report_dummy.get_children_accounts(account_id):
                sheet.write(row, 0, '  '*(aux.level-1) + aux.code + ' ' + aux.name, STYLES['bold'])
                sheet.write(row, 8, report_dummy._sum_debit_account(aux), STYLES['numbold'])
                sheet.write(row, 9, report_dummy._sum_credit_account(aux), STYLES['numbold'])
                sheet.write(row, 10, report_dummy._sum_balance_account(aux), STYLES['numbold'])
                row += 1
                for line in report_dummy.lines(aux):
                    ref = '*'
                    sheet.write(row, 1, line['ldate'], STYLES['std'])
                    sheet.write(row, 2, line['lcode'], STYLES['std'])
                    sheet.write(row, 3, line['partner_name'], STYLES['std'])
                    if not line['lref']:
                       move_info = move_obj.browse(cr, uid,line['mmove_id'])
                       ref =  move_info.ref
                    else:
                        ref =  line['lref']
                        
                    sheet.write(row, 4,ref, STYLES['std'])
                    sheet.write(row, 5, line['move'], STYLES['std'])
                    sheet.write(row, 6, line['lname'], STYLES['std'])
                    sheet.write(row, 7, line['line_corresp'], STYLES['std'])
                    sheet.write(row, 8, line['debit'], STYLES['num'])
                    sheet.write(row, 9, line['credit'], STYLES['num'])
                    sheet.write(row, 10, line['progress'], STYLES['num'])
                    row += 1
        #Guardando
        buf = cStringIO.StringIO()
        book.save(buf)
        outfile = base64.encodestring(buf.getvalue())
        buf.close()
#         self.write(cr, uid, ids, {'state': 'res', 'data': outfile, 'file_name': 'Libro mayor.xls'})
        return self.pool.get('base.file.report').show(cr, uid, outfile, 'Libro mayor.xls')

account_report_general_ledger()

class wizard_report_general_ledger_xsl(osv.osv_memory):
     
    _inherit = "account.common.account.report"
    _name = "account.report.general.ledger.xsl"
    _description = "General Ledger Report xsl"
     
     
     
    def _get_period_before(self, cr, uid, periodo_actual_data, fiscalyear):
         
        res = []
        period_obj = self.pool.get('account.period')
        date_start = periodo_actual_data.date_start
        if date_start:
            campos = date_start.split('-')
            #print "campos", campos
            if int(campos[1]) > 1:
                cont = 1
                var = int(campos[1]) - 1
                while cont <= var:
                    date_start = datetime.date(int(campos[0]), var, int(campos[2]))
                    period_ids = period_obj.search(cr, uid, [('date_start', '=', date_start)])
                    res.append(period_ids[0])
                    var -= 1
                return res
            else:
                return res
     
     
     
    def before_balance(self, cr, uid, account_id, fiscalyear, periodo_id, date_start, date_to, date_from, filtro):
         
         
        saldo = 0.0
        group = "GROUP BY l.account_id"
        where = ""
        sql = "SELECT COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, COALESCE(SUM(l.credit), 0) as credit, COALESCE(SUM(l.debit), 0) as debit "\
                "FROM account_move_line l WHERE l.account_id =" + str(account_id)
         
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')
         
        if not fiscalyear:
            fiscalyear_ids = fiscalyear_obj.search(cr, uid, [('state', '=', 'draft')])
            fiscalyear_clause = (','.join([str(x) for x in fiscalyear_ids])) or '0'
        else:
            fiscalyear_clause = fiscalyear
         
        if filtro == 'filter_period':
            period_actual_data = period_obj.browse(cr, uid, periodo_id)
            periodo = self._get_period_before(cr, uid, period_actual_data, fiscalyear)
            if periodo:
                ids = ','.join([str(x) for x in periodo])
                #print "ids", ids 
                where = " AND l.state<>'draft' AND l.period_id in (SELECT id from account_period WHERE fiscalyear_id in (%s) AND id in (%s)) " % (fiscalyear_clause, ids,)
            else:
                #print ' el caso contrario '
                return 0.0
             
        elif filtro == 'filter_date':
            #print "a", date_to
            #print "b", date_from
            if date_to == date_from:
                #print "entra 1"
                return 0.0
            else:
                where = " AND l.state<>'draft' AND l.move_id in ( select id from account_move  where date >= '" + str(date_from) + "' AND date < '" + str(date_to) + "')"
             
        elif filtro == 'none':
            return 0.0
            #where = " AND l.state<>'draft' AND l.period_id in (SELECT id from account_period WHERE fiscalyear_id in (%s))"%(fiscalyear_clause)
        #print "whre", where
        sql = sql + where + group
        #print "**************sql saldo anterior*********", sql
        cr.execute(sql)
        res = cr.dictfetchall()
        #print res
        for r in res:
            saldo = round (r['balance'], 2)
#        saldo = res[0]['balance']
#        saldo = abs(saldo)
        #print "saldo", saldo
        return saldo
     
     
     
     
     
    def get_children_accounts(self, cr, uid, account, form, context):
         
        account_obj = self.pool.get('account.account')
        account_move_line_obj = self.pool.get('account.move.line')
             
        res = []
        ctx = context.copy()
        ids_acc = account_obj.search(cr, uid, [('parent_id', 'child_of', [account['id']])], context=ctx, order="code, name")
        if ids_acc:
            for child_id in ids_acc:
                child_account = account_obj.browse(cr, uid, child_id, context=ctx)
                sold_account = child_account.balance
                if form['display_account'] == 'bal_mouvement':
                    if child_account.type != 'view' \
                    and len(account_move_line_obj.search(cr, uid,
                        [('account_id', '=', child_account.id)],
                        context=ctx)) <> 0 :
                        res.append(child_account)
                elif form['display_account'] == 'bal_solde':
                    if child_account.type != 'view' \
                    and len(account_move_line_obj.search(cr, uid,
                        [('account_id', '=', child_account.id)],
                        context=ctx)) <> 0 :
                        if (sold_account <> 0.0):
                            res.append(child_account)
                else:
                    if child_account.type != 'view' \
                    and len(account_move_line_obj.search(cr, uid,
                        [('account_id', '>=', child_account.id)],
                        context=ctx)) <> 0 :
                        res.append(child_account)
        ##print "get_children_accounts",res
        if not len(res):
            return [account]
         
        return res
     
    def new_filters(self, cr, uid, form):
        sql = ''
        if form.get('partner_id'): sql += 'l.partner_id=%s AND ' % form['partner_id']
        if form.get('invoice_id'): sql += 'l.invoice_id=%s AND ' % form['invoice_id']
        if form.get('move_id'): sql += 'l.move_id=%s AND ' % form['move_id']
        if form.get('analytic_account_id'): sql += 'l.analytic_account_id=%s AND ' % form['analytic_account_id']
        return sql
     
    def lines(self, cr, uid, account, form, context):
         
        account_move_line_obj = self.pool.get('account.move.line')
        account_invoice_obj = self.pool.get('account.invoice')
         
        tot_currency = 0.0
        ctx = context.copy()
        res = []
        if account and account['child_consol_ids']: # add ids of consolidated childs also of selected account
            ctx['consolidate_childs'] = True
            ctx['account_id'] = account['id'] 
         
        inv_types = {
                'out_invoice': 'Factura Ventas',
                'in_invoice': 'Factura Compras',
                'out_refund': 'Nota Credito Cliente',
                'in_refund': 'Nota Credito Proveedor',
        }
 
        if form['sortby'] == 'sort_date':
            sorttag = 'ORDER by l.date'
        else:
            sorttag = 'ORDER by j.code'
             
        #print "2 lines ctx", ctx
        query = account_move_line_obj._query_get(cr, uid, context=ctx)
        #print "query************", query
             
        sql = "SELECT l.id, l.date, l.ref, m.ref as ref2, l.name, m.no_comp as move, l.type_move, m.tipo_comprobante as tipo_comprobante, l.statement_id as sts,"\
                     "COALESCE(l.debit,0) as debit, COALESCE(l.credit,0) as credit, l.period_id"\
                " FROM account_move_line as l"\
                " JOIN account_move m on (l.move_id=m.id)"\
                 " WHERE l.account_id =" + str(account['id']) + " AND "\
                 " (l.debit <> 0 or l.credit <> 0) AND "
                       
        ##print "sql", sql
        sql = sql + self.new_filters(cr, uid, form) + str(query) + sorttag
        ##print "**************************************************Export Excel sql************************************************************"
        ##print sql
        cr.execute(sql)
        res = cr.dictfetchall()
         
        ##print ' RES  ', res
         
        sum = 0.0
         
        for l in res:
            ##print ' ele  ', l
            line = account_move_line_obj.browse(cr, uid, l['id'])
            l['code'] = line.journal_id.code
            cr.execute('Select id from account_invoice where move_id =%s' % (line.move_id.id))
            tmpres = cr.dictfetchall()
            if len(tmpres) > 0 :
                inv = account_invoice_obj.browse(cr, uid, tmpres[0]['id'])
                if inv.type in ('out_invoice', 'out_refund'):
                    l['ref'] = inv_types[inv.type] + ':' + str(inv.num_retention)
                elif inv.type in ('in_invoice', 'in_refund'):
                    if inv.tipo_factura in ['invoice', 'purchase_liq', 'sales_note']:
                        l['ref'] = inv_types[inv.type] + ':' + str(inv.number_inv_supplier)
                    elif inv.tipo_factura in ['anticipo', 'gas_no_dedu','gasto_financiero']:
                        l['ref'] = inv_types[inv.type] + ':' + str(inv.code_advance_liq)
                else:
                    l['ref'] = inv_types[inv.type] + ':' + str(inv.factura)
             
            if line.partner_id:
                l['partner'] = line.partner_id.name
            else:
                l['partner'] = ''
                 
            if hasattr(line, 'employee_id') and  line.employee_id:
                l['employee'] = line.employee_id.name
            else:
                l['employee'] = ''
 
            l['cedula'] = (line.partner_id and line.partner_id.ident_num) or (hasattr(line, 'employee_id') and line.employee_id and line.employee_id.identification_id)
             
            if hasattr(line, 'preproject_id') and  line.preproject_id:
                l['project'] = line.preproject_id.name
            else:
                l['project'] = ''
             
            if line.tax_code_id:
                tax = line.tax_code_id
                l['impuesto'] = tax.code + '-' + tax.name
                 
#             ref = l.get('ref') or ''
#             l['type_move'] = l['type_move'] or (len(ref.split(':')) == 2 and ref.split(':')[-1])
                      
            sum = l['debit'] - l['credit']
            l['progress'] = sum
        return res
     
 
    def _config_cabecera_report(self, cr, uid, wb):
        cabacera_libro_mayor = report_general()
        cabacera_libro_mayor.pool = self.pool
        return cabacera_libro_mayor.get_cabecera_libro_mayor(cr, uid, wb)
     
   
    def _print_report(self, cr, uid, ids, data, context=None):
        account_obj = self.pool.get('account.account')
        account_period_obj = self.pool.get('account.period')
        ctx = context.copy()
        fiscalyear = 0
         
        if context is None:
            context = {}
         
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids)[0])
#         data['form'].update(self.read(cr, uid, ids, ['landscape', 'initial_balance', 'amount_currency', 'sortby', 'date_start', 'state',
#                                                      'parnter_id', 'invoice_id', 'move_id', 'analytic_account_id'])[0])
        if not data['form']['fiscalyear_id']:# GTK client problem onchange does not consider in save record
            data['form'].update({'initial_balance': False})
         
        wb = pycel.Workbook(encoding='utf-8')
        ws = wb.add_sheet("LIBRO MAYOR")
        ws.show_grid = False
         
         
        cabacera_libro_mayor = report_general()
        cabacera_libro_mayor.pool = self.pool
        cabacera_libro_mayor.get_cabecera_libro_mayor(cr, uid, wb, data['form'], ws)
         
        #========================================================
        #=======================================================
        if data['form'].has_key('fiscalyear_id'):
            ctx['fiscalyear'] = data['form']['fiscalyear_id']
            fiscalyear = data['form']['fiscalyear_id']
         
        filtro = data['form']['filter']
         
        if filtro == 'filter_period':
             
            period_from_id = data['form']['used_context']['period_from']
            period_to_id = data['form']['used_context']['period_to']
            periods = account_period_obj.build_ctx_periods(cr, uid, period_from_id, period_to_id)
            ctx['periods'] = periods
             
            if periods:
                saldo = self.before_balance(cr, uid,
                                                    account_id=data['form']['chart_account_id'],
                                                    fiscalyear=fiscalyear,
                                                    periodo_id=periods[0],
                                                    date_start=None,
                                                    date_to=None,
                                                    date_from=None,
                                                    filtro=filtro)
            #print ' saldo de la cuenta ', saldo
            #print ' data[form][chart_account_id] ', data['form']['chart_account_id']
            #print ' context ctx ', ctx
             
            account_ids = ctx['active_ids']
             
            accounts_data = account_obj.read(cr, uid, account_ids, context=ctx)
             
            #print ' accounts_data  **** ', accounts_data
             
            debito = 0
            credito = 0
             
            x = 10
            for account in accounts_data: 
                for line in self.get_children_accounts(cr, uid, account=account, form=data['form'], context=ctx):
                    i = 0
                    for periodo in periods:                            
                        if i == 0:
                            saldo = self.before_balance(cr, uid,
                                                    account_id=account['id'],
                                                    fiscalyear=fiscalyear,
                                                    periodo_id=periodo,
                                                    date_start=None,
                                                    date_to=None,
                                                    date_from=None,
                                                    filtro=filtro)
                            i += 1
                    
                        ws.write(x, 1, line['code'], cabacera_libro_mayor.style_cuarto_nivel)
                        ws.write(x, 2, line['name'].encode('utf-8'), cabacera_libro_mayor.style_cuarto_nivel)
                         
                        x = x + 1
                        ws.write(x, 1, "SALDO ANTERIOR", cabacera_libro_mayor.style_cuarto_nivel)
                        ws.write(x, 13, saldo, cabacera_libro_mayor.style_cuarto_nivel)
                         
                        period_data = account_period_obj.read(cr, uid, periodo, ['name'])
                        ctx['periods'] = [periodo]
                        x = x + 1
                        ws.write(x, 1, "PERIODO", cabacera_libro_mayor.style_cuarto_nivel)
                        ws.write(x, 2, period_data['name'], cabacera_libro_mayor.style_cuarto_nivel)
                        x = x + 1
                                             
                        for aal in self.lines(cr, uid, account=line, form=data['form'], context=ctx):
                            saldo += aal.get('debit') - aal.get('credit')
                            debito += aal.get('debit')
                            credito += aal.get('credit')
                            row_line = []
                            partner = ''
                            name = ''
                            ref = None
                            move = ''
                             
                            partner = aal.get('partner')
                            partner = partner.split()
                            sin_espacios = ' '.join(partner)
                            partner = sin_espacios.encode('utf-8')
                             
                            employee = aal.get('employee')
                            employee = employee.split()
                            sin_espacios = ' '.join(employee)
                            employee = sin_espacios.encode('utf-8')
                             
                            cedula = aal.get('cedula') or ''
                            cedula = cedula.split()
                            sin_espacios = ' '.join(cedula)
                            cedula = sin_espacios.encode('utf-8')
                             
                            project = aal.get('project')
                            project = project.split()
                            sin_espacios = ' '.join(project)
                            project = sin_espacios.encode('utf-8')
                             
                             
                            move = str(aal.get('move'))
                            ref = aal.get('ref')
                            if not aal.get('ref'):
                                ref = '' 
                            ref = ref.split()
                            sin_espacios = ' '.join(ref)
                            ref = sin_espacios.encode('utf-8')
                             
                            impuesto = aal.get('impuesto') or ''
                             
                            ws.write(x, 1, aal.get('date'), cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 2, aal.get('code'), cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 3, move, cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 4, aal.get('tipo_comprobante'), cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 5, aal.get('ref2'), cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 6, aal.get('type_move') or '', cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 7, cedula, cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 8, partner, cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 9, employee, cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 10, project, cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 11, impuesto, cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 12, ref, cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 13, round(aal.get('debit'), 2), cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 14, round(aal.get('credit'), 2), cabacera_libro_mayor.style_cuenta)
                            ws.write(x, 15, round(saldo, 2), cabacera_libro_mayor.style_cuenta)
                             
                            x = x + 1
                                 
                    x = x + 1
                     
                ws.write(x, 11, round(debito, 2), cabacera_libro_mayor.style_cuarto_nivel)
                ws.write(x, 12, round(credito, 2), cabacera_libro_mayor.style_cuarto_nivel)
                ws.write(x, 13, round(saldo, 2), cabacera_libro_mayor.style_cuarto_nivel)
                 
                 
        if filtro == 'filter_date':
             
            #print ' form ', data['form']
             
            ctx['date_from'] = data['form']['date_from']
            ctx['date_to'] = data['form']['date_to']
             
            saldo = self.before_balance(cr, uid,
                                                account_id=data['form']['chart_account_id'],
                                                fiscalyear=fiscalyear,
                                                periodo_id=None,
                                                date_start=data['form']['date_start'],
                                                date_to=data['form']['date_to'],
                                                date_from=data['form']['date_from'],
                                                filtro=filtro)
            #print ' saldo de la cuenta ', saldo
            #print ' data[form][chart_account_id] ', data['form']['chart_account_id']
            #print ' context ctx ', ctx
             
            account_ids = ctx['active_ids']
             
            accounts_data = account_obj.read(cr, uid, account_ids, context=ctx)
             
            #print ' accounts_data  **** ', accounts_data
             
            debito = 0
            credito = 0
             
            x = 12    
            for account in accounts_data: 
                for line in self.get_children_accounts(cr, uid, account=account, form=data['form'], context=ctx):
                    i = 0
                    #for periodo in periods:                            
                    if i == 0:
                        saldo = self.before_balance(cr, uid,
                                                account_id=account['id'],
                                                fiscalyear=fiscalyear,
                                                periodo_id=None,
                                                date_start=data['form']['date_start'],
                                                date_to=data['form']['date_to'],
                                                date_from=data['form']['date_from'],
                                                filtro=filtro)
                        i += 1
                
                    ws.write(x, 1, line['code'], cabacera_libro_mayor.style_cuarto_nivel)
                    ws.write(x, 2, line['name'].encode('utf-8'), cabacera_libro_mayor.style_cuarto_nivel)
                     
                    x = x + 1
                    ws.write(x, 1, "SALDO ANTERIOR", cabacera_libro_mayor.style_cuarto_nivel)
                    ws.write(x, 13, saldo, cabacera_libro_mayor.style_cuarto_nivel)
                     
                    x = x + 1
                                         
                    for aal in self.lines(cr, uid, account=line, form=data['form'], context=ctx):
                        saldo += aal.get('debit') - aal.get('credit')
                        debito += aal.get('debit')
                        credito += aal.get('credit')
                        row_line = []
                        partner = ''
                        name = ''
                        ref = None
                        move = ''
                         
                         
                        partner = aal.get('partner')
                        partner = partner.split()
                        sin_espacios = ' '.join(partner)
                        partner = sin_espacios.encode('utf-8')
                         
                        employee = aal.get('employee')
                        employee = employee.split()
                        sin_espacios = ' '.join(employee)
                        employee = sin_espacios.encode('utf-8')
                         
                        cedula = aal.get('cedula') or ''
                        cedula = cedula.split()
                        sin_espacios = ' '.join(cedula)
                        cedula = sin_espacios.encode('utf-8')
                         
                        project = aal.get('project')
                        project = project.split()
                        sin_espacios = ' '.join(project)
                        project = sin_espacios.encode('utf-8')
                         
                        move = str(aal.get('move'))
                        ref = aal.get('ref')
                        if not aal.get('ref'):
                            ref = '' 
                        ref = ref.split()
                        sin_espacios = ' '.join(ref)
                        ref = sin_espacios.encode('utf-8')
                         
                        impuesto = aal.get('impuesto') or ''
                         
                        ws.write(x, 1, aal.get('date'), cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 2, aal.get('code'), cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 3, move, cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 4, aal.get('tipo_comprobante'), cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 5, aal.get('ref2'), cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 6, aal.get('type_move') or '', cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 7, cedula, cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 8, partner, cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 9, employee, cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 10, project, cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 11, impuesto, cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 12, ref, cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 13, round(aal.get('debit'), 2), cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 14, round(aal.get('credit'), 2), cabacera_libro_mayor.style_cuenta)
                        ws.write(x, 15, round(saldo, 2), cabacera_libro_mayor.style_cuenta)
                         
                        x = x + 1
                             
                x = x + 1
                     
                ws.write(x, 11, round(debito, 2), cabacera_libro_mayor.style_cuarto_nivel)
                ws.write(x, 12, round(credito, 2), cabacera_libro_mayor.style_cuarto_nivel)
                ws.write(x, 13, round(saldo, 2), cabacera_libro_mayor.style_cuarto_nivel)
             
             
             
 
                     
        ws.col(1).width = 7500
        ws.col(2).width = 7500
        ws.col(4).width = 9500
        ws.col(6).width = 10500
        ws.col(7).width = 10500
        ws.col(8).width = 10500
        ws.col(9).width = 5500
         
         
        buf = cStringIO.StringIO()
         
        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'data':out, 'file_name':'libro_mayor.xls', 'state':'res'})
     
         
    def onchange_fiscalyear(self, cr, uid, ids, fiscalyear=False, context=None):
        res = {}
        if not fiscalyear:
            res['value'] = {'initial_balance': False}
        return res
     
    _columns = {
             
            'initial_balance': fields.boolean("Include initial balances",
                                              help='It adds initial balance row on report which display previous sum amount of debit/credit/balance'),
            'sortby': fields.selection([('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')], 'Sort By', required=True),
            'data': fields.binary(string='Arch'),
            'file_name':fields.char('Archivo', size=32),
            'date_start':fields.date("Fecha Inicio"),
            'partner_id': fields.many2one('res.partner', 'Empresa'),
            'invoice_id': fields.many2one('account.invoice', 'Factura'),
            'move_id': fields.many2one('account.move', 'Asiento'),
            'analytic_account_id': fields.many2one('account.analytic.account', 'Cuenta analítica'),
            'state':fields.selection([('ini', 'Inicial'),
                                       ('res', 'Resultado'),
                                      ], 'Estado'),
        }
    _defaults = {
#         'landscape': True,
#         'amount_currency': True,
        'sortby': 'sort_date',
        'initial_balance': False,
    }
 
 
 
 
wizard_report_general_ledger_xsl()
