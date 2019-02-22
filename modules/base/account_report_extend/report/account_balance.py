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

class account_balance_fa(report_sxw.rml_parse):
        _name = 'report.account.account.balance.fa'
        def __init__(self, cr, uid, name, context):
            super(account_balance_fa, self).__init__(cr, uid, name, context)
            self.sum_debit = 0.00
            self.sum_credit = 0.00
    	    self.sum_balance_haber = 0.00
    	    self.sum_balance_debe = 0.00
    	    self.date_lst = []
            self.date_lst_string = ''
            self.localcontext.update({
                'time': time,
                'lines': self.lines,
                'sum_debit': self._sum_debit,
                'sum_credit': self._sum_credit,
                'get_fiscalyear':self.get_fiscalyear,
                'get_periods':self.get_periods,
        		'sum_balance_debe':self._sum_balance_debe,
        		'sum_balance_haber':self._sum_balance_haber,
                    })
            self.context = context

        def get_fiscalyear(self, form):
            res=[]
            if form.has_key('fiscalyear'):
                fisc_id = form['fiscalyear']
                if not (fisc_id):
                    return ''
                self.cr.execute("select name from account_fiscalyear where id = %s" , (int(fisc_id),))
                res=self.cr.fetchone()
            return res and res[0] or ''

        def get_periods(self, form):
            result=''
            if form.has_key('periods') and form['periods'][0][2]:
                period_ids = ",".join([str(x) for x in form['periods'][0][2] if x])
                self.cr.execute("select name from account_period where id in (%s)" % (period_ids))
                res = self.cr.fetchall()
                len_res = len(res) 
                for r in res:
                    if (r == res[len_res-1]):
                        result+=r[0]+". "
                    else:
                        result+=r[0]+", "
            else:
                fy_obj = self.pool.get('account.fiscalyear').browse(self.cr,self.uid,form['fiscalyear'])
                res = fy_obj.period_ids
                len_res = len(res)
                for r in res:
                    if r == res[len_res-1]:
                        result+=r.name+". "
                    else:
                        result+=r.name+", "
                
            return str(result and result[:-1]) or ''

        
        def lines(self, form, ids={}, done=None, level=1):
            if not ids:
                ids = self.ids
            if not ids:
                return []
            if not done:
                done={}
            if form.has_key('Account_list') and form['Account_list']:
                ids = [form['Account_list']]
                del form['Account_list']
            res={}
            result_acc=[]
            ctx = self.context.copy()
            ctx['state'] = form['context'].get('state','all')
            ctx['fiscalyear'] = form['fiscalyear']
            if form['state']=='byperiod' :
                ctx['periods'] = form['periods'][0][2]
            elif form['state']== 'bydate':
                ctx['date_from'] = form['date_from']
                ctx['date_to'] =  form['date_to'] 
            elif form['state'] == 'all' :
                ctx['periods'] = form['periods'][0][2]
                ctx['date_from'] = form['date_from']
                ctx['date_to'] =  form['date_to']
#            accounts = self.pool.get('account.account').browse(self.cr, self.uid, ids, ctx)
#            def cmp_code(x, y):
#                return cmp(x.code, y.code)
#            accounts.sort(cmp_code)
            
#            child_ids = self.pool.get('account.account')._get_children_and_consol(self.cr, self.uid, ids, ctx)
            nivel=form['nivel']+1
	    id_padre=ids
            child_ids = self.pool.get('account.account')._get_cuentas_hijas(self.cr, self.uid,ids,nivel,0)
            if child_ids:
                ids = child_ids
            accounts = self.pool.get('account.account').read(self.cr, self.uid, ids,['type','code','name','debit','credit','balance','parent_id'], ctx)
	    saldo_debe=0
	    saldo_haber=0
            for account in accounts:
                if account['id'] in done:
                    continue
                done[account['id']] = 1
		if account['balance']>0:
			saldo_debe=account['balance']
			saldo_haber=''
		elif account['balance']<0:
			saldo_haber=(account['balance'])*(-1)
			saldo_debe=''
		else:
			saldo_haber=''
			saldo_debe=''
                res = {
                        'id' : account['id'],
                        'type' : account['type'],
                        'code': account['code'],
                        'name': account['name'],
                        'level': level,
                        'debit': account['debit'],
                        'credit': account['credit'],	
                        'balance_d': saldo_debe,
			             'balance_h': saldo_haber,
                       # 'leef': not bool(account['child_id']),
                        'parent_id':account['parent_id'],
                        'bal_type':'',
                    }
		#print"cuenta", account['name'], "PARENT_ID", account['parent_id'], "IDS 0",ids[0]
		if account['parent_id'][0]==id_padre[0]:			
			self.sum_debit += account['debit']
			self.sum_credit += account['credit']
			if saldo_haber=='':
				self.sum_balance_haber += 0
			else:
				self.sum_balance_haber += saldo_haber
			if saldo_debe=='':
				self.sum_balance_debe += 0
			else:
				self.sum_balance_debe += saldo_debe
#                if account.child_id:
#                    def _check_rec(account):
#                        if not account.child_id:
#                            return bool(account.credit or account.debit)
#                        for c in account.child_id:
#                            if not _check_rec(c) or _check_rec(c):
#                                return True
#                        return False
#                    if not _check_rec(account) :
#                        continue
                if account['parent_id']:
#                    acc = self.pool.get('account.account').read(self.cr, self.uid, [ account['parent_id'][0] ] ,['name'], ctx)
                    for r in result_acc:
                        if r['id'] == account['parent_id'][0]:
                            res['level'] = r['level'] + 1
                            break
                if form['display_account'] == 'bal_mouvement':
                    if res['credit'] > 0 or res['debit'] > 0 or res['balance'] > 0 :
                        result_acc.append(res)
                elif form['display_account'] == 'bal_solde':
                    if  res['balance'] != 0:
                        result_acc.append(res)
                else:
                    result_acc.append(res)
#                if account.child_id:
#                    acc_id = [acc.id for acc in account.child_id]
#                    lst_string = ''
#                    lst_string = '\'' + '\',\''.join(map(str,acc_id)) + '\''
#                    self.cr.execute("select code,id from account_account where id IN (%s)"%(lst_string))
#                    a_id = self.cr.fetchall()
#                    a_id.sort()
#                    ids2 = [x[1] for x in a_id]
#
#                    result_acc += self.lines(form, ids2, done, level+1)
            #print "debit", self.sum_debit
            return result_acc
        
        def _sum_credit(self, form):
            return self.sum_credit

	def _sum_balance_debe(self, form):
            return round(self.sum_balance_debe * 0.001)/0.001

	def _sum_balance_haber(self, form):
            return round(self.sum_balance_haber * 0.001)/0.001

        def _sum_debit(self, form):
            return self.sum_debit

report_sxw.report_sxw('report.account.account.balance.report.fa', 'account.account', 'addons/account_report_extend/report/account_balance.rml', parser=account_balance_fa, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
