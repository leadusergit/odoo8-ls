# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author :  Vinicio Llumiquinga vllumiquinga@atikasoft.com.ec
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
#*EG
from openerp.report import report_sxw
import time
from openerp import pooler
import datetime

class account_conciliation_report(report_sxw.rml_parse):
    _name ='account.conciliation.report'
    _description='Concilacion Bancaria'
    
    def __init__(self, cr, uid, name, context):
        self.balance = 0.00
        super(account_conciliation_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
                'time': time,
                'lines': self._get_lines_debit,
                'lines_credit':self._get_lines_credit,
                'deptransf':self._dep_transf,
                'num_cheque':self._get_num_cheque,
                'balance':self.line_total,
                'periodo':self.get_date,
                'formato':self._format_date,
                'user':self.get_user,
                'get_date':self.get_date_register
                })
        self.context = context
    
    def get_user(self):
        user = pooler.get_pool(self.cr.dbname).get('res.users').browse(self.cr, self.uid, self.uid)
        return str(user.name.encode('UTF-8'))
    
    def get_date_register(self, date):
        res =''
        if date:
            res = self._format_date(date).strftime('%d de %B del %Y')
        return res

    
    def _dep_transf(self, tipo, numero):
        retorno = ""  
        
        if (tipo and numero):
            if tipo == "depo":
                tipo = "Depto"
            elif tipo == "trans":
                tipo = "Transf "
            else:
                tipo = " "
            retorno = tipo
        return retorno
    
    def _format_date(self, date):
        if date:
            campos = date.split('-')
            date = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date
    
    def get_date(self, obj):
        res = ''
        if obj.period_id:
            date = obj.period_id.date_start 
            res = self._format_date(date).strftime('%B-%Y').upper()
        return res
    
    def _get_num_cheque(self, move_id):
        retorno = ""
        cheque_id = pooler.get_pool(self.cr.dbname).get('payment.cheque').search(self.cr, self.uid, [('move', '=', move_id)], order='payment_date Desc')
        if cheque_id:
            obj_cheque = pooler.get_pool(self.cr.dbname).get('payment.cheque').browse(self.cr, self.uid, cheque_id)
            for objeto in obj_cheque:
                if (objeto.num_cheque):
                    retorno = objeto.num_cheque
        return retorno
    
    def _get_lines_debit(self, lines):
        res = []
        ordenar =[]
        conciliados =[]
        pool = pooler.get_pool(self.cr.dbname)
        for line in lines:
            if not (line.conciliado):
                if not(line.debit == 0):
                    res.append(line)
                    ordenar.append(line.id)
        if ordenar:
            lineas = pool.get('account.conciliation.line').search(self.cr, self.uid, [('id','in',ordenar)], order='date DESC')
            if lineas:
                for item in pool.get('account.conciliation.line').browse(self.cr, self.uid, lineas):
                    conciliados.append(item) 
        return conciliados 
    
    def _get_lines_credit(self, lines):
        res = []
        ordenar =[]
        conciliados =[]
        pool = pooler.get_pool(self.cr.dbname)
        
        for line in lines:
            if not (line.conciliado):
                if not(line.credit == 0):
                    res.append(line)
                    ordenar.append(line.id)
        if ordenar:
            
            lineas = pool.get('account.conciliation.line').search(self.cr, self.uid, [('id','in',ordenar)], order='date DESC')
            if lineas:
                for item in pool.get('account.conciliation.line').browse(self.cr, self.uid, lineas):
                    conciliados.append(item)
        return conciliados
    
    def line_total(self, line_id, periodo):
        pool = pooler.get_pool(self.cr.dbname)
        ctx = self.context.copy()
        ctx['periods'] = [periodo]
        _total = 0.00
        acc = pool.get('account.account').browse(self.cr, self.uid,[line_id],ctx)[0]
        _total = round(acc.balance,2)
        self.balance = _total
        
        return  _total

report_sxw.report_sxw('report.account.conciliation.report', 
                      'account.conciliation', 
                      'addons/account_invoice_retention/report/account_conciliation_report.rml',
                      parser=account_conciliation_report, header=False)
        
