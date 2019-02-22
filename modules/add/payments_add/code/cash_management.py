# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from datetime import datetime
import base64, time

def change_special_caracters(text):
    characters = {
        u'Á': u'A', u'á': u'a',
        u'É': u'E', u'é': u'e',
        u'Í': u'I', u'í': u'i',
        u'Ó': u'O', u'ó': u'o',
        u'Ú': u'U', u'ú': u'u',
        u'Ü': u'U', u'ü': u'u',
        u'Ñ': u'N', u'ñ': 'n',
    }
    for ori, new in characters.iteritems():
        text = text.replace(ori, new)
    return text

class payment_cash_management(models.Model):
    _inherit = 'payment.cash.management'
    _description = 'Cash management de bancos'
    
    #============================================================
    orden_pago = fields.Many2one('payment.order', 'Orden de Pago')
    #============================================================
    
    @api.multi
    def unlink(self):
        """"Método que controla borrado de registros"""
        for cash in self:
            if cash.state not in ('draft'):
                 raise ValidationError('No puede borrar Cash en estado Validado"')
        return super(payment_cash_management, self).unlink()
   
    @api.multi
    def generar_cash_pichincha(self):
        file, filename = self.pichincha()
        return self.env['base.file.report'].show(file, filename)
    
    
    def pichincha(self, CODIF='Windows-1252', NEWLINE='\r\n'):
        string = ''
        DATE = datetime.strptime(self.date, '%Y-%m-%d').strftime('%y%m%d')
        #string += 'D%s%s'%(self.company_id.name.upper().ljust(40, ' ')[:40], self.bank_account_id.acc_number.replace('-', '').rjust(11, '0'))
        #string += '%s%sN1'%(str(int(round(self.amount, 2) * 100)).rjust(14, '0'), DATE)
        #string += NEWLINE

        for sequence, transfer in enumerate(self.transfers, 1):
            
            TIPO_CUENTA = {'AHO': 'AHO', 'COR': 'CTE'}
            TIPO_IDENT = {'c': 'C', 'r': 'R', 'p': 'P'}
            
            string += 'PA\t%s\t%s\t%s'%(self.bank_account_id.acc_number.replace('-', ''), sequence, '')
            string += '%s%s'%(transfer.ident_num.upper().ljust(13, ' ')[:13],' ')
            string += 'USD%s%s%s'%(' ',str(int(round(transfer.amount, 2) * 100)).rjust(14, '0'),' ')
            string += 'CTA%s%s%s'%(' ',transfer.bank_account_id.bank_bic.replace('-', '').rjust(4, '0'),' ')
            string += '%s%s%s'%(' ',TIPO_CUENTA[transfer.bank_account_id.acc_type],' ')      
            string += '%s%s%s%s%s%s%s%s'%(transfer.bank_account_id.acc_number.replace('-', '').rjust(11, '0'),' ',TIPO_IDENT[transfer.ident_type],' ',transfer.ident_num.upper().ljust(13, ' ')[:13],' ',transfer.name.upper().ljust(40, ' ')[:40],' ')
            string += '\t%s\t|%s'%('\t', transfer.email or '')
            string += NEWLINE
        file = base64.encodestring(string.encode(CODIF))
        filename = time.strftime('CASH'+self.bank_account_id.bank_bic+'%Y%m%d.txt')
        return file, filename
    
    
    
    def produbanco(self, CODIF='Windows-1252', NEWLINE='\r\n'):
        string = ''

        DATE = datetime.strptime(self.date, '%Y-%m-%d').strftime('%y%m%d')

        for sequence, transfer in enumerate(self.transfers, 1):
            TIPO_CUENTA = {'AHO': 'AHO', 'COR': 'CTE'}
            TIPO_IDENT = {'c': 'C', 'r': 'R', 'p': 'P'}

            string += 'PA\t%s\t%s\t%s'%(self.bank_account_id.acc_number.replace('-', ''), sequence, '')
            string += '%s%s'%(transfer.ident_num.upper().ljust(13, ' ')[:13],' ')
            string += 'USD%s%s%s'%(' ',str(int(round(transfer.amount, 2) * 100)).rjust(14, '0'),' ')
            string += 'CTA%s%s%s'%(' ',transfer.bank_account_id.bank_bic.replace('-', '').rjust(4, '0'),' ')
            string += '%s%s%s'%(' ',TIPO_CUENTA[transfer.bank_account_id.acc_type],' ')      
            string += '%s%s%s%s%s%s%s%s'%(transfer.bank_account_id.acc_number.replace('-', '').rjust(11, '0'),' ',TIPO_IDENT[transfer.ident_type],' ',transfer.ident_num.upper().ljust(13, ' ')[:13],' ',transfer.name.upper().ljust(40, ' ')[:40],' ')
            string += '\t%s\t|%s'%('\t', transfer.email or '')
            string += NEWLINE
        file = base64.encodestring(string.encode(CODIF))
        filename = time.strftime('CASH'+self.bank_account_id.bank_bic+'%Y%m%d.txt')
        return file, filename
    
    
    
    
    
    
    def clear_info(self, cr,cash_id):
        """Método para limpiar tabla payment.transfer ,esto permite cargar los datos una sola vez """
        cr.execute('DELETE FROM payment_transfer WHERE cash_id=ANY(%s)', (cash_id,))
         
    def get_inputs(self, cr, uid, ids, context=None):
        self.clear_info(cr, ids)
        cash = self.browse(cr,uid,ids[0])
        order= cash.orden_pago.id
        payment_obj = self.pool.get('payment.order')
        line_obj = self.pool.get('payment.line')
        transfer_obj = self.pool.get('payment.transfer')

        for pay in payment_obj.browse(cr,uid,order):
            for line in pay.line_ids:
                num=line.move_line_id.ref + '|' +'Fac#' + line.move_line_id.no_comp                   
                inputs = {  'cash_id':cash.id,
                            'partner_id': line.partner_id.id,
                            'name': line.partner_id.name,
                            'ident_type': line.partner_id.ident_type,
                            'ident_num': line.partner_id.ident_num,
                            'ruc': line.partner_id.ident_num,
                            'move':line.payment_move_id.id,
                            'amount':line.amount_currency,
                            'bank_account_id':line.bank_id.id,
                            'bank_account_dest_id':cash.bank_account_id.id,
                            'date_generation':pay.date_done,
                            'type':'out',
                            'email':line.partner_id.email,
                            'origin':line.move_line_id.name,
                            'invoice_num':line.move_line_id.no_comp,
                            'num_exit_voucher':num,
                            'detalle':line.move_line_id.name
                        }
                 
                print"inputs=%s"%inputs
                transfer_obj.create(cr, uid, inputs)

                    