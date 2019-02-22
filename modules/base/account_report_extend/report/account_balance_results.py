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

import time
import locale
from openerp.report import report_sxw
import re # comma_me 
#from addons.account.wizard import wizard_account_balance_report

parents = {
    'tr':1,
    'li':1,
    'story': 0,
    'section': 0
}

class account_report_balance_results(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_report_balance_results, self).__init__(cr, uid, name, context=context)
        
        self.monthly = 0.00
        self.amount = 0.00
        
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'separador':self.comma_me,
            'get_periods':self.get_periods,
            'subtotal':self._subtotales,
        })
        self.context = context
        

    def line_total(self,line_id,ctx):
        _total = 0
        bsline= self.pool.get('account.report.bs').browse(self.cr,self.uid,[line_id])[0]
        bsline_accids = bsline.account_id
        res =self.pool.get('account.report.bs').read(self.cr,self.uid,[line_id],['account_id','child_id'])[0]
        for acc_id in res['account_id']:
            acc = self.pool.get('account.account').browse(self.cr,self.uid,[acc_id],ctx)[0]
            _total += acc.balance
        bsline_reportbs = res['child_id']

        for report in bsline_reportbs:
            _total +=self.line_total(report,ctx)
        return  _total
    
    def get_periods(self, form):
        ##print "get_periods",form
        ctx = self.context.copy()
        res = ''
        ctx['periods'] = form['periods']
        ##print "ctx['periods']", ctx['periods']
        if len(ctx['periods'])==1:
            obj_period = self.pool.get('account.period').browse(self.cr,self.uid,ctx['periods'][0])
            res = 'Mes de '+str(time.strftime('%B %Y', time.strptime(obj_period.date_start, '%Y-%m-%d'))).upper()
            ##print "fecha", res
        elif len(ctx['periods'])>1:
            periods = self.pool.get('account.period').search(self.cr, self.uid, [('id','in',ctx['periods'])],order="date_start")
            ##print "periods", periods
            if periods:
                obj_period_start = self.pool.get('account.period').browse(self.cr,self.uid,periods[0])
                obj_period_finish = self.pool.get('account.period').browse(self.cr,self.uid,periods[-1])
                fecha1 = 'Mes de '+str(time.strftime('%B %Y', time.strptime(obj_period_start.date_start, '%Y-%m-%d'))).upper()
                fecha2 = 'hasta Mes de '+str(time.strftime('%B %Y', time.strptime(obj_period_finish.date_stop, '%Y-%m-%d'))).upper()
                res = fecha1 +' '+fecha2
        else:
            self.cr.execute("select id from account_period order by date_start")
            periods = [aux[0] for aux in self.cr.fetchall()]
            ##print "periods", periods
            if periods:
                obj_period_start = self.pool.get('account.period').browse(self.cr,self.uid,periods[0])
                obj_period_finish = self.pool.get('account.period').browse(self.cr,self.uid,periods[-1])
                fecha1 = 'Mes de '+str(time.strftime('%B %Y', time.strptime(obj_period_start.date_start, '%Y-%m-%d'))).upper()
                fecha2 = 'hasta Mes '+str(time.strftime('%B %Y', time.strptime(obj_period_finish.date_stop, '%Y-%m-%d'))).upper()
                res = fecha1 +' '+fecha2
        ##print 'res', res 
        return res
    
    #Funcion que separa el punto en lugar de comas y pone a 2 decimales las cantidades
    def comma_me(self,amount):
#        #print "amount", amount
#        #print "#" + str(amount) + "#"
        if not amount:
            amount = 0.0
        if  type(amount) is float :
            amount = str('%.2f'%amount)
        else :
            amount = str(amount)
        if (amount == '0'):
             return ' '
        orig = amount
        new = re.sub("^(-?\d+)(\d{3})", "\g<1>,\g<2>", amount)
#        #print "new", type(new)
        if orig == new:
            if new =='0.00':
                return ''
            else:
                return new
        else:
            return self.comma_me(new) 

    def lines(self, form, ids={}, done=None, level=1, object=False):
        ##print "form", form
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
        ctx = self.context.copy()
        ctx['fiscalyear'] = form['fiscalyear']
        ctx['periods'] = form['periods']
        #ctx['state'] = 'posted'
        ##print "ids", ids
        report_objs = self.pool.get('account.report.bs').browse(self.cr, self.uid, ids)
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
                'balance':'',
                'balance2':self.line_total(report_obj.id,ctx),
                'parent_id':False,
                'color_font':color_font,
                'color_back':color_back,
                'font_style' : report_obj.font_style
            }
            ##print "redsssssssss", res
            result.append(res)
            report_type = report_obj.report_type
            if report_type != 'only_obj':
                account_ids = self.pool.get('account.report.bs').read(self.cr,self.uid,[report_obj.id],['account_id'])[0]['account_id']
                ##print "account_ids1", account_ids
                account_ids = self.pool.get('account.account').search(self.cr, self.uid, [('id','in', account_ids)], order='code,name')
                ##print "account_ids2", account_ids 
                if report_type == 'acc_with_child':
                    acc_ids = self.pool.get('account.account')._get_children_and_consol(self.cr, self.uid, account_ids )
                    account_ids = acc_ids
                ##print "ctx", ctx
                account_objs = self.pool.get('account.account').browse(self.cr,self.uid,account_ids,ctx)
                
                for acc_obj in account_objs:
                    ##print "acc_obj", acc_obj
                    tacumulado = 0.0
                    ##print "ctx", ctx
                    ctx_1['fiscalyear'] = form['fiscalyear']
                    ctx_1['date_from'] = time.strftime('2011-07-01')#tomar desde este periodo
                    ctx_1['date_to'] = time.strftime('%Y-%m-%d')
                    #ctx_1['state'] = 'posted'
                    ##print "ctx2", ctx_1
                    acumulado = self.pool.get('account.account').browse(self.cr,self.uid,acc_obj.id,ctx_1)
                    ##print "todo", acumulado.balance
                    tacumulado = round(acumulado.balance,2)
                    res1={}
                    ##print "acc_obj.code[:1]", acc_obj.code[:1]
                    if int(acc_obj.code[:1])>=4 and tacumulado !=0 and acc_obj.balance!=0:
                        if acc_obj.type =='view':
                            if len(acc_obj.code)==1:
                                self.monthly += acc_obj.balance
                                self.amount += tacumulado
                                res1 = {
                                        'code': acc_obj.code,
                                        'name': acc_obj.name,
                                        'level': level+1,
                                        'balance': acc_obj.balance,
                                        'balance2':tacumulado,
                                        'parent_id':acc_obj.parent_id,
                                        'color_font' : 'black',
                                        'color_back' :'white',
                                        'font_style' : 'Helvetica-Bold',
                                    }
                            elif len(acc_obj.code)== 4:
                                res1 = {
                                    'code': acc_obj.code,
                                    'name': acc_obj.name,
                                    'level': level+1,
                                    'balance': acc_obj.balance,
                                    'balance2':tacumulado,
                                    'parent_id':acc_obj.parent_id,
                                    'color_font' : 'black',
                                    'color_back' :'white',
                                    'font_style' : 'Helvetica-Bold',
                                }
                            elif len(acc_obj.code)== 6:
                                res1 = {
                                    'code': acc_obj.code,
                                    'name': acc_obj.name,
                                    'level': level+1,
                                    'balance': acc_obj.balance,
                                    'balance2':tacumulado,
                                    'parent_id':acc_obj.parent_id,
                                    'color_font' : 'black',
                                    'color_back' :'white',
                                    'font_style' : 'Helvetica-Bold',
                                }
                            else:
                                res1 = {
                                    'code': acc_obj.code,
                                    'name': acc_obj.name,
                                    'level': level+1,
                                    'balance': acc_obj.balance,
                                    'balance2':tacumulado,
                                    'parent_id':acc_obj.parent_id,
                                    'color_font' : 'black',
                                    'color_back' :'white',
                                    'font_style' : 'Helvetica-Bold',
                                }
                        else:
                            res1 = {
                                    'code': acc_obj.code,
                                    'name': acc_obj.name,
                                    'level': level+1,
                                    'balance': acc_obj.balance,
                                    'balance2':tacumulado,
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
                    #result += res1
            if report_obj.child_id:
                ##print "child_id", report_obj.child_id
                ids2 = [(x.code,x.id) for x in report_obj.child_id]
                ids2.sort()
                result += self.lines(form,[x[1] for x in ids2], done, level+1,object=False)
                
        return result

    def _subtotales(self):
        res =[self.monthly, self.amount]
        return res
        

report_sxw.report_sxw('report.account_balance_results',
                      'account.report.bs',
                      'addons/account_report_extend/report/account_balance_results.rml',
                      parser=account_report_balance_results,
                      header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

