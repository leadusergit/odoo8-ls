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

from openerp.report import report_sxw
from openerp import pooler
import time, re
from openerp.tools import amount_to_text

class account_move(report_sxw.rml_parse):

    def _sum_total(self, move, data):
        suma = 0.0
        for line in move.line_id:
            suma += line.debit
        return suma


    def usuario(self, mov):
        perm = pooler.get_pool(self.cr.dbname).get('account.move').perm_read(self.cr, self.uid, [mov.id], self.context)
        if perm:
            return perm[0]['create_uid'][1]
        else:
            return ''
    
    def _data_deposit(self, mov, column):
        
        res = ''
        ##print ' _data_deposit 1 ', mov.id
        aml = pooler.get_pool(self.cr.dbname).get('account.move.line')
        abs = pooler.get_pool(self.cr.dbname).get('account.bank.statement')
        rpb = pooler.get_pool(self.cr.dbname).get('res.partner.bank')
        
        move_lines_ids = aml.search(self.cr, self.uid, [('move_id', '=', mov.id)])    
        ##print ' move_lines ', move_lines_ids
        if not move_lines_ids:
            return ''
        move_lines = aml.read(self.cr, self.uid, move_lines_ids, ['statement_id'])
        ##print ' move_lines 2 ', move_lines
        
        for move_line in move_lines:
            ##print ' move_line ', move_line
            if move_line['statement_id']:
                
                statement_id = move_line['statement_id'][0]
                statement_ids = abs.search(self.cr, self.uid, [('id', '=', statement_id)])
                ##print ' statement_ids  ', statement_ids
                statemen_infos = abs.read(self.cr, self.uid, statement_ids, ['has_deposit', 'num_deposit', 'date_deposit', 'amount_deposit', 'acc_deposit_id', 'payments'])
                ##print ' statemen_infos ', statemen_infos
                
                if column == 'deposit':
                    payments = statemen_infos[0]['payments'] or ''
                    res = 'Forma de Pago:' + str(payments)                    
                    break
                
                if column == 'num_deposit':
                    res = '  NUM COMPROBANTE: ' + str(statemen_infos[0]['num_deposit'])
                    break
                
                if column == 'date_deposit':    
                    res = ' FECHA: ' + str(statemen_infos[0]['date_deposit'])
                    break
                
                if column == 'amount_deposit':    
                    res = ' VALOR: ' + str(statemen_infos[0]['amount_deposit'])
                    break
                
                acc_deposit_id = statemen_infos[0]['acc_deposit_id'][0]
                bank_ids = rpb.search(self.cr, self.uid, [('id', '=', acc_deposit_id)])
                partner_bank_info = rpb.read(self.cr, self.uid, bank_ids, ['acc_number', 'bank'])
                ##print ' partner_bank_info ', partner_bank_info
                
                if column == 'acc_number':
                    res = ' CUENTA ' + str(partner_bank_info[0]['acc_number'])
                    break
                    
                if column == 'bank':
                    res = ' BANCO: ' + str(partner_bank_info[0]['bank'][1])
                    break                
                
            else:
                return res            
        return res
    
    def _get_lines(self, lines):
        res = []
        for line in lines:
            if not(line.debit == 0 and line.credit == 0):
                res.append(line)
        for i in range(len(res) - 1):
            for j in range(i + 1, len(res)):
                if res[i].debit < res[j].debit:
                    aux = res[i]
                    res[i] = res[j]
                    res[j] = aux
        return res
    
    def document(self, reference=None):
        if self.document_id == None:
            self.document_id = False
            aux = re.match(u'(Registro|Anulación) de documento: ', reference)
            state = {u'Registro de documento: ': 'active',
                     u'Anulación de documento: ': 'canceled'}
            if aux:
                model = pooler.get_pool(self.cr.dbname).get('payment.record.treasury')
                doc_name = reference.strip(aux.group(0))
                doc_id = model.search(self.cr, self.uid, [('name', '=', doc_name),
                                                          ('state', '=', state[aux.group(0)])], limit=1)
                self.document_id = bool(doc_id) and model.browse(self.cr, self.uid, doc_id[0])
        return self.document_id
        
    def __init__(self, cr, uid, name, context):
        super(account_move, self).__init__(cr, uid, name, context)
        self.localcontext.update({
                'time': time,
                'sum_credit': self._sum_total,
                'sum_debit': self._sum_total,
                'user_create':self.usuario,
                'data_deposit':self._data_deposit,
                'lines': self._get_lines,
                'doc': self.document,
                'amount_to_text': amount_to_text
                })
        self.document_id = None
        self.context = context

report_sxw.report_sxw('report.account.move',
                      'account.move',
                      'addons/account_invoice_retention/report/account_move.rml',
                      parser=account_move, header=False)
        
