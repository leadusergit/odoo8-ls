# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv, fields
from openerp.addons.account.report.account_balance import account_balance
from cStringIO import StringIO
from base64 import encodestring
from xlwt import Workbook, Formula
from openerp.addons.base_ec.tools.xls_tools import *
from datetime import datetime, timedelta

def style(bold=False, font_name='Calibri', height=11, font_color='black',
          rotation=0, align='left', vertical='center', wrap=True,
          border=False, color=None, format=None):
    return get_style(bold, font_name, height, font_color, rotation, align, vertical, wrap, border, color, format)

styles = {
    'title': style(True, height=12, wrap=False),
    'header': style(True, align='center', color='indigo', font_color='white'),
    'body': style(),
    'parent_body': style(True),
    'number': style(format='0.00', align='right'),
    'parent_number': style(True, format='0.00', align='right'),
}

class account_balance_report(osv.osv_memory):
    _inherit = 'account.balance.report'
    _columns = {
        'state': fields.selection([('draft', 'draft'),('done', 'done')], 'Estado', required=True, readonly=True),
        'accounts_ids': fields.many2many('account.account', 'balance_account_rel', 'balance_id', 'account_id', 'Cuentas'),
        'file': fields.binary('Archivo generado'),
        'filename': fields.char('Archivo', size=64)
    }
    _defaults = {  
        'state': lambda *a: 'draft',  
    }
    
    def get_filter(self, report_dummy, data):
        filter = report_dummy._get_filter(data)
        res = filter
        if filter != 'Sin filtro':
            res += ' (Desde {0} hasta {1})'
            if filter == 'Fecha':
                res = res.format(report_dummy._get_start_date(data), report_dummy._get_end_date(data))
            else:
                res = res.format(report_dummy.get_start_period(data), report_dummy.get_end_period(data))
        return res
    
    def saldo_anterior(self, cr, uid, obj, report_name, datas, context={}):
        report_dummy = account_balance(cr, uid, report_name, context)
        form = datas['form'].copy()
        if datas['form']['filter'] == 'filter_no':
            return {}
        elif datas['form']['filter'] == 'filter_period':
            period_from = self.pool.get('account.period').browse(cr, uid, datas['form']['period_from'])
            period_ids = self.pool.get('account.period').search(cr, uid, [('fiscalyear_id', '=', period_from.fiscalyear_id.id)])
            aux = period_ids.index(period_from.id)
            if aux == period_ids[0]:
                return {}
            form['period_from'] = period_ids[0]
            form['period_to'] = period_ids[aux - 1]
        elif datas['form']['filter'] == 'filter_date':
            form['date_from'] = '{0}-01-01'.format(*datas['form']['date_from'].split('-'))
            if form['date_from'] == datas['form']['date_from']:
                return {}
            date_to = datetime.strptime(datas['form']['date_from'], '%Y-%m-%d')
            form['date_to'] = (date_to - timedelta(days=1)).strftime('%Y-%m-%d')
        return dict([(aux['code'], aux['balance']) for aux in report_dummy.lines(form, [obj['chart_account_id']])])
    
    def print_excel_report(self, cr, uid, ids, context=None):
        obj = self.read(cr, uid, ids, ['chart_account_id', 'accounts_ids'])[0]
        check = self.check_report(cr, uid, ids, context)
        type, datas, report_name = check['type'], check['datas'], check['report_name'] 
        report_dummy = account_balance(cr, uid, report_name, context)
        book = Workbook('utf-8')
        sheet = book.add_sheet('Hoja1')
        report_name = 'Balance de resultados'
        #50.12cm = 65535u ==> 1cm >< 1307,561851556u
        cm = 65535/50.12 #Basado en datos de libre office
        sheet.col(0).width = int(round(3.49*cm))
        sheet.col(1).width = int(round(10.79*cm))
        sheet.write(0, 0, report_name.upper(), styles['title'])
        for row, filtros in enumerate(['Ejercicio fiscal', 'Mostrar cuentas', 'Filtrar por', 'Seleccionar asientos'], 2):
            sheet.write(row, 0, filtros, styles['parent_body'])
        sheet.write(2, 1, report_dummy._get_fiscalyear(datas) or '', styles['body'])
        sheet.write(3, 1, (datas['form']['display_account']=='bal_all' and 'Todos') or  (datas['form']['display_account']=='bal_movement' and 'Con movimientos') or 'Con saldo diferente de 0.00', styles['body'])
        sheet.write(4, 1, self.get_filter(report_dummy, datas), styles['body'])
        sheet.write(5, 1, report_dummy._get_target_move(datas), styles['body'])
        row = 8
        for col, field in enumerate(['Código', 'Cuenta', 'Saldo anterior', 'Débito', 'Crédito', 'Saldo actual']):
            sheet.write(row-1, col, field, styles['header'])
        saldos_anteriores = self.saldo_anterior(cr, uid, obj, report_name, datas, context)
        for a in report_dummy.lines(datas['form'], [obj['chart_account_id']]):
            if not obj['accounts_ids'] or a['id'] in obj['accounts_ids']:
                sheet.write(row, 0, a['code'], styles['body' if a['type'] != 'view' else 'parent_body'])
                sheet.write(row, 1, a['name'], styles['body' if a['type'] != 'view' else 'parent_body'])
                sheet.write(row, 2, saldos_anteriores.get(a['code'], 0.0), styles['number' if a['type'] != 'view' else 'parent_number'])
                sheet.write(row, 4, a['debit'], styles['number' if a['type'] != 'view' else 'parent_number'])
                sheet.write(row, 3, a['credit'], styles['number' if a['type'] != 'view' else 'parent_number'])
                sheet.write(row, 5, a['balance'] + saldos_anteriores.get(a['code'], 0.0), styles['number' if a['type'] != 'view' else 'parent_number'])
                row += 1
        
        buf = StringIO()
        book.save(buf)
        out = encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'file': out, 'filename': report_name+'.xls', 'state': 'done'})
    
account_balance_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: