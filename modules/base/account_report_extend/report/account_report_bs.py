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

#from addons.account.wizard import wizard_account_balance_report

parents = {
    'tr':1,
    'li':1,
    'story': 0,
    'section': 0
}

class account_report_bs_fa(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(account_report_bs_fa, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'indicadores': self.indicadores,
            'lines': self.lines,
            'periodos':self.periodos,
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

    def periodos(self, form, ids={}, done=None, level=1, object=False):
        #print"form", form
        result = ""
        ctx = self.context.copy()
        ctx['periods'] = form['periods'][0][2]
        for p in ctx['periods']:
            nom = self.pool.get('account.period').browse(self.cr,self.uid,p)
            nom1 = self.pool.get('account.period').read(self.cr, self.uid, p,['name'],context=None)
            result += nom1['name'] + ", " 
        return result

    def lines(self, form, ids={}, done=None, level=1, object=False):
        if object:
            ids = [object.id]
        elif not ids:
            ids = self.ids    
        if not ids:
            return []
        if not done:
            done={}
        result = []
        ctx = self.context.copy()
        ctx['fiscalyear'] = form['fiscalyear']
        ctx['periods'] = form['periods'][0][2]
        report_objs = self.pool.get('account.report.bs').browse(self.cr, self.uid, ids)
        title_name = False
        if level==1:
            title_name = report_objs[0].name
        def cmp_code(x, y):
            return cmp(x.code, y.code)
        report_objs.sort(cmp_code)

        for report_obj in report_objs:
            vector = []
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
                'balance': self.line_total(report_obj.id,ctx),
                'parent_id':False,
                'color_font':color_font,
                'color_back':color_back,
                'font_style' : report_obj.font_style
            }
            result.append(res)
            report_type = report_obj.report_type
            if report_type != 'only_obj':
                aux = self.pool.get('account.report.bs').read(self.cr,self.uid,[report_obj.id],['account_id','nivel'])
                account_ids=aux[0]['account_id']
                nivel=aux[0]['nivel']
                if report_type == 'acc_with_child':
                    acc_ids = self.pool.get('account.account')._get_cuentas_hijas(self.cr, self.uid, account_ids,nivel,0)
                    account_ids = account_ids + acc_ids

                    lista=self.pool.get('account.account').read(self.cr, self.uid, account_ids,['id', 'code'])
                    lista_aux = sorted(lista, key=lambda k: k['code'])
                    for linea in lista_aux:
                        vector.append(linea['id'])

                account_objs = self.pool.get('account.account').browse(self.cr,self.uid,vector,ctx)
                for acc_obj in account_objs:
                    res1={}
                    res1 = {
                        'code': acc_obj.code,
                        'name': acc_obj.name,
                        'level': level+1,
                        'balance': acc_obj.balance,
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
                ids2 = [(x.code,x.id) for x in report_obj.child_id]
                ids2.sort()
                result += self.lines(form,[x[1] for x in ids2], done, level+1,object=False)
                
        return result

    def indicadores(self, form, ids={}, done=None, level=1, object=False):
        if object:
            ids = [object.id]
        elif not ids:
            ids = self.ids    
        if not ids:
            return []
        if not done:
            done={}
        result = []
        ctx = self.context.copy()
        #print "indicadores", ctx
        ctx['fiscalyear'] = form['fiscalyear']
        ctx['periods'] = form['periods'][0][2]
        report_objs = self.pool.get('account.report.bs').browse(self.cr, self.uid, ids)
        title_name = False
        if level==1:
            title_name = report_objs[0].name
        def cmp_code(x, y):
            return cmp(x.code, y.code)
        report_objs.sort(cmp_code)

        for report_obj in report_objs:
            vector = []
            if report_obj.id in done:
                continue
            done[report_obj.id] = 1
            color_font = ''
            color_back = ''
            if report_obj.color_font:
                color_font = report_obj.color_font.name
            if report_obj.color_back:
                color_back = report_obj.color_back.name
            
            aux = self.pool.get('account.report.bs').read(self.cr,self.uid,[report_obj.id],['account_report_ids'])[0]['account_report_ids']
            #print "aux", aux
            if ctx['periods']:
                indicadores_ids=self.pool.get('account.report.history').search(self.cr, self.uid,[('period_id','in',ctx['periods']),
                                                                                                  ('fiscalyear_id','=', ctx['fiscalyear']),
                                                                                                  ('name','in',aux)])
            else:
                indicadores_ids=self.pool.get('account.report.history').search(self.cr, self.uid,[('fiscalyear_id','=', ctx['fiscalyear']),
                                                                                                  ('name','in',aux)])
            result_aux = {}
            id = 0
            for indicador in self.pool.get('account.report.history').browse(self.cr, self.uid,indicadores_ids):
                res1={}
                res1 = {
                    'id': id,
                    'code': indicador.name.code,
                    'name': indicador.name.name,
                    'balance': indicador.valor,
                    'color_font' : 'black',
                    'color_back' :'white',
                    'font_style' : 'Helvetica',
                    }
                id += 1
                if indicador.name.code in result_aux.keys():
                    result_aux[indicador.name.code]['balance'] = result_aux[indicador.name.code]['balance'] + indicador.valor
                else:
                    result_aux[indicador.name.code]=res1
            for aux in result_aux.keys():
                result.append(result_aux[aux])
            result_aux2 = sorted(result, key=lambda k: k['id'])
        return result_aux2

report_sxw.report_sxw('report.account.report.bs.fa', 'account.report.bs', 'addons/account_report_extend/report/account_report_bs.rml', parser=account_report_bs_fa, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

