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
    _name = 'payment.cash.management'
    _description = 'Cash management de bancos'
    #===========================================================================
    # Columns
    name = fields.Char('Descripción', required=True, readonly=True, states={'draft':[('readonly', False)]})
    journal_id = fields.Many2one('account.journal', 'Diario', required=True, domain=[('type', '=', 'bank')], readonly=True, states={'draft':[('readonly', False)]})
    bank_account_id = fields.Many2one('res.partner.bank', required=True, domain=[('partner_id.is_provider', '=', True)], readonly=True, states={'draft':[('readonly', False)]})
    amount = fields.Float('Monto', required=True, readonly=True, states={'draft':[('readonly', False)]})
    date = fields.Date('Fecha', default=time.strftime('%Y-%m-%d'), required=True, readonly=True, states={'draft':[('readonly', False)]})
    state = fields.Selection([('draft', 'Borrador'), ('done', 'Validado')], 'Estado', required=True, readonly=True, default='draft')
    transfers = fields.One2many('payment.transfer', 'cash_id', 'Transferencias')
    company_id = fields.Many2one('res.company', 'Compañia', related='journal_id.company_id', readonly=True, store=True)
    #===========================================================================
    
    @api.multi
    def generar_cash_produbanco(self):
        file, filename = self.produbanco()
        return self.env['base.file.report'].show(file, filename)
    
    @api.multi
    def generar_cash_guayaquil(self):
        file, filename = self.guayaquil()
        return self.env['base.file.report'].show(file, filename)
    
    @api.multi
    def generar_cash_proamerica(self):
        file, filename = self.proamerica()
        return self.env['base.file.report'].show(file, filename)
    
    def produbanco(self, CODIF='Windows-1252', NEWLINE='\n'):
        string = ''
        TIPO_CUENTA = {'AHO': 'AHO', 'COR': 'CTE'}
        TIPO_IDENT = {'c': 'C', 'r': 'R', 'p': 'P'}
        DATE = datetime.strptime(self.date, '%Y-%m-%d').strftime('%y%m%d')
        string += 'D%s%s'%(self.company_id.name.upper().ljust(40, ' ')[:40], self.bank_account_id.acc_number.replace('-', '').rjust(11, '0'))
        string += '%s%sN1'%(str(int(round(self.amount, 2) * 100)).rjust(14, '0'), DATE)
        string += NEWLINE
        for sequence, transfer in enumerate(self.transfers, 1):
            string += 'C%s%s'%(transfer.name.upper().ljust(40, ' ')[:40], transfer.bank_account_id.acc_number.replace('-', '').rjust(11, '0'))
            string += '%s%sN1'%(str(int(round(transfer.amount, 2) * 100)).rjust(14, '0'), DATE)
            string += NEWLINE
        file = base64.encodestring(string.encode(CODIF))
        filename = time.strftime('CASH'+self.bank_account_id.bank_bic+'%Y%m%d.txt')
        return file, filename
    
    def proamerica(self, CODIF='Windows-1252', NEWLINE='\r\n'):
        string = ''
        for sequence, transfer in enumerate(self.transfers, 1):
            TIPO_CUENTA = {'AHO': 'AHO', 'COR': 'CTE'}
            TIPO_IDENT = {'c': 'C', 'r': 'R', 'p': 'P'}
            string += 'PA\t%s\t%s\t%s'%(self.bank_account_id.acc_number.replace('-', ''), sequence, '')
            string += '\t%s\tUSD'%transfer.ident_num.upper()#transfer.bank_account_id.acc_number.rjust(11, '0')
            string += '\t%s\tCTA'%str(int(round(transfer.amount, 2) * 100)).rjust(13, '0')
            string += '\t%s\t%s'%(transfer.bank_account_id.bank_bic[-4:].rjust(4, '0'), TIPO_CUENTA[transfer.bank_account_id.acc_type])
            string += '\t%s\t%s'%(transfer.bank_account_id.acc_number, TIPO_IDENT[transfer.ident_type])
            string += '\t%s\t%s'%(transfer.ident_num.upper(), transfer.name)
            string += '\t%s\t%s\t%s'%('', '', '') #DIRECCIÓN, CIUDAD, TELEFONO
            string += '\t%s\t|%s'%('\t', transfer.email or '')
            string += NEWLINE
        file = base64.encodestring(string.encode(CODIF))
        filename = time.strftime('CASH'+self.bank_account_id.bank_bic+'%Y%m%d.txt')
        return file, filename
    
    def guayaquil(self, CODIF='Windows-1252', NEWLINE='\r\n'):
        string = ''
        for sequence, transfer in enumerate(self.transfers, 1):
            TIPO_CUENTA = {'AHO': 'A', 'COR': 'C'}
            TIPO_IDENT = {'c': 'C', 'r': 'R', 'p': 'P'}
            IS_SAME_BANK = self.bank_account_id.bank == transfer.bank_account_id.bank
            string += '%s'%TIPO_CUENTA[transfer.bank_account_id.acc_type]
            string += '%s'%(IS_SAME_BANK and transfer.bank_account_id.acc_number[:10] or '').rjust(10, '0')
            string += '%sXXY01'%str(int(round(transfer.amount, 2) * 100)).rjust(15, '0')
            string += '%s'%(IS_SAME_BANK and '  ' or transfer.bank_account_id.bank_bic[-2:])
            string += '%s'%(IS_SAME_BANK and ''.rjust(18, ' ') or transfer.bank_account_id.acc_number[:18]).rjust(18, '0')
            string += '%sBJ1'%(IS_SAME_BANK and ''.rjust(18, ' ') or transfer.name[:18]).rjust(18, ' ')
            #===================================================================
            string += '%s'%('' if IS_SAME_BANK else transfer.bank_account_id.bank_bic[:3].rjust(3, '0'))
            string += '%s'%('' if IS_SAME_BANK else TIPO_IDENT[transfer.ident_type])
            string += '%s'%('' if IS_SAME_BANK else transfer.ident_num[:13].ljust(13, ' '))
            #===================================================================
            string = change_special_caracters(string.upper()) + NEWLINE
        file = base64.encodestring(string.encode(CODIF))
        filename = time.strftime('NCR%Y%m%dBJI_01.txt')
        return file, filename
    
    @api.one
    def borrador(self):
        self.state = 'draft'
        self.transfers.write({'state': 'draft'})
        
    @api.one
    def validar(self):
        line_total = sum([aux.amount for aux in self.transfers])
        if round(self.amount, 2) != round(line_total, 2):
            raise ValidationError(u'El valor del cash (%.2f), debe coincidir con el total de los registros (%.2f)'%(self.amount, line_total))
        for line in self.transfers:
            if not line.bank_account_id:
                raise ValidationError(u'%s, no posee una cuenta a la cual depositar.'%line.name)
        self.transfers.write({'state': 'done'})
        self.state = 'done'
    
class payment_transfer(models.Model):
    _inherit = 'payment.transfer'
    #===========================================================================
    # Columns
    cash_id = fields.Many2one('payment.cash.management', 'Cash Management', ondelete='cascade')
    ident_type = fields.Selection([('c', 'Cédula'), ('r', 'Ruc'), ('p', 'Pasaporte')], 'Tipo de identificación')
    ident_num = fields.Char('Número de identificación')
    email = fields.Char('Email de notificación')
    #===========================================================================
    
    def onchange_parnter_id(self, cr, uid, ids, partner_id):
        res = super(payment_transfer, self).onchange_parnter_id(cr, uid, ids, partner_id)
        if partner_id:
            partner = self.pool.get('res.partner').read(cr, uid, partner_id, ['ident_type', 'ident_num', 'email'])
            res['value']['ident_type'] = partner['ident_type']
            res['value']['ident_num'] = partner['ident_num']
            res['value']['email'] = partner['email']
        return res