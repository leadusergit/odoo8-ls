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

# import wizard
import base64
import StringIO
import csv
import time
from openerp.osv import fields, osv
import mx.DateTime
from mx.DateTime import RelativeDateTime

class wizard_report_account_balance_results(osv.osv_memory):
    _name='wizard.report.account.balance.results'
    _description='Wizard que muestra el estado de resultados'
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def generate_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        return self._print_report(cr, uid, ids, data, context=context) 
    
    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {'type':'ir.actions.report.xml',
                  'report_name':'account_balance_results',
                  'datas': data}
        return result
    
    def line_total(self, cr, uid, line_id,ctx):
        _total = 0
        bsline= self.pool.get('account.report.bs').browse(cr, uid,[line_id])[0]
        bsline_accids = bsline.account_id
        res =self.pool.get('account.report.bs').read(cr, uid,[line_id],['account_id','child_id'])[0]
        for acc_id in res['account_id']:
            acc = self.pool.get('account.account').browse(cr, uid,[acc_id],ctx)[0]
            _total += acc.balance
        bsline_reportbs = res['child_id']

        for report in bsline_reportbs:
            _total +=self.line_total(cr, uid, report,ctx)
        return  _total
    
    
    def export_excel(self, cr, uid, ids, context=None):
        ##print "ids", ids
        buf = StringIO.StringIO()
        writer = csv.writer(buf, delimiter=',')
        ##print "context", context
        context.get('active_ids', [])
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids)[0]
        report_objs = self.pool.get('account.report.bs').browse(cr, uid, data['ids'])
        ##print "report_objs", report_objs
        fila = ['','ESTADO DE RESULTADOS','']
        writer.writerow(fila)
        cabecera=['CUENTA', 'NOMBRE DE CUENTA', 'TOTAL']
        writer.writerow(cabecera)
        #Me saca el balance de todo un periodo
        for line in self._lines(cr, uid, form=data['form'],object=report_objs[0],context=context):
            if line:
                fila = []
                fila.append(line['code'])
                fila.append(line['name'].encode('UTF-8'))
                fila.append(line['balance'])
                fila.append(line['acumulado'])
                writer.writerow(fila)
        out = base64.encodestring(buf.getvalue())
        buf.close() 
        return self.write(cr, uid, ids, {'data':out, 'name':'balance_results.csv'}, context=context)
    
    def _lines(self, cr, uid, form, ids={}, done=None, level=1, object=False,context=None):
        #print "form", form
        if object:
            ids = [object.id]
        elif not ids:
            ids = self.ids    
        if not ids:
            return []
        if not done:
            done={}
        result = []
        ctx_1 ={}
        ctx = context.copy()
        ctx['fiscalyear'] = form['fiscalyear']
        ctx['periods'] = form['periods']
        report_objs = self.pool.get('account.report.bs').browse(cr, uid, ids)
        ##print "report_objs", report_objs
        title_name = False
        if level==1:
            title_name = report_objs[0].name
        def cmp_code(x, y):
            return cmp(x.code, y.code)
        report_objs.sort(cmp_code)

        for report_obj in report_objs:
            if report_obj.id in done:
                continue
            done[report_obj.id] = 1
            color_font = ''
            color_back = ''
            if report_obj.color_font:
                color_font = report_obj.color_font.name
            if report_obj.color_back:
                color_back = report_obj.color_back.name
            res = {
                'code': report_obj.code,
                'name': report_obj.name,
                'level': level,
                'balance': 0,
                'acumulado':self.line_total(cr, uid,report_obj.id,ctx),
                'parent_id':False,
                'color_font':color_font,
                'color_back':color_back,
                'font_style' : report_obj.font_style
            }
            result.append(res)
            report_type = report_obj.report_type
            if report_type != 'only_obj':
                account_ids = self.pool.get('account.report.bs').read(cr,uid,[report_obj.id],['account_id'])[0]['account_id']
                if report_type == 'acc_with_child':
                    acc_ids = self.pool.get('account.account')._get_children_and_consol(cr, uid, account_ids )
                    account_ids = acc_ids
                account_objs = self.pool.get('account.account').browse(cr,uid,account_ids,ctx)
                for acc_obj in account_objs:
                    ##print "acc_obj", acc_obj
                    ctx_1['fiscalyear'] = form['fiscalyear']
                    ctx_1['date_from'] = time.strftime('2011-07-01')#tomar desde este periodo
                    ctx_1['date_to'] = time.strftime('%Y-%m-%d')
                    acumulados = self.pool.get('account.account').browse(cr,uid,acc_obj.id,ctx_1)
                    tbalance = round (acumulados.balance,2)
                    res1={}
                    if acc_obj.type =='view':
                        if acc_obj.balance != 0:
                            res1 = {
                                    'code': acc_obj.code,
                                    'name': acc_obj.name,
                                    'level': level+1,
                                    'balance': acc_obj.balance,
                                    'acumulado': tbalance,
                                    'parent_id':acc_obj.parent_id,
                                    'color_font' : 'black',
                                    'color_back' :'white',
                                    'font_style' : 'Helvetica-Bold',
                                    }
                    else:
                        if acc_obj.balance != 0:
                            res1 = {
                                    'code': acc_obj.code,
                                    'name': acc_obj.name,
                                    'level': level+1,
                                    'balance': acc_obj.balance,
                                    'acumulado': tbalance,
                                    'parent_id':acc_obj.parent_id,
                                    'color_font' : 'black',
                                    'color_back' :'white',
                                    'font_style' : 'Helvetica',
                                    }
                    if acc_obj.parent_id:
                        for r in result:
                            if r['name']== acc_obj.parent_id.name:
                                res1['level'] = r['level'] + 1
                            break
                    result.append(res1)
                    #res1 = self.check_child_id(account_id,level,ctx,report_type)
            if report_obj.child_id:
                ids2 = [(x.code,x.id) for x in report_obj.child_id]
                ids2.sort()
                result += self.lines(form,[x[1] for x in ids2], done, level+1,object=False)
                
        return result
    
    def _get_fiscalyears(self, cr, uid, context={}):
        fecha = time.strftime('%Y-%m-%d')
        anio = time.strftime('%Y')
        year = self.pool.get('account.fiscalyear').search(cr, uid,[('date_start','<=', fecha),
                                                                   ('date_stop','>=',fecha),
                                                                   ('code','=',anio),])
        return year[0]
    
    _columns={
              'fiscalyear':fields.many2one('account.fiscalyear', 'Año Fiscal'),
              'periods':fields.many2many('account.period', 'period_rel', 'report_id', 'period_id', 'Periodos', help="Seccione el Periodo"),
              'data': fields.binary(string='Export'),
              'name':fields.char('Nombre', size=60),
    }
    _defaults = {
        'fiscalyear': _get_fiscalyears,
    }

wizard_report_account_balance_results()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

