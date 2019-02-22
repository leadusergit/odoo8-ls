# -*- coding: utf-8 -*-

import time
from openerp import netsvc
import StringIO
import xlwt
import csv
import re
import datetime
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.addons.hr_nomina import payroll_tools
from openerp import models, fields, api
import logging
from docutils.nodes import line_block
from openerp.exceptions import ValidationError
import base64, time
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
from mx import DateTime
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime
from xml.dom.minidom import Document
from time import strftime
from xlwt import Workbook
from openerp.addons.base_ec.tools.xls_tools import *

def change_special_caracters(text):
    characters = {
        u'Á': u'A', u'á': u'a',
        u'É': u'E', u'é': u'e',
        u'Í': u'I', u'í': u'i',
        u'Ó': u'O', u'ó': u'o',
        u'Ú': u'U', u'ú': u'u',
        u'Ü': u'U', u'ü': u'u',
        u'Ñ': u'N', u'ñ': u'n',
    }
    for ori, new in characters.iteritems():
        text = text.replace(ori, new)
    return text


class voucher_cash_wizard(models.TransientModel):
    """account.voucher cash"""
    _name = "voucher.cash.wizard"
    _description = "Genera Cash Management de vouchers seleccionados"

    voucher_ids=fields.Many2many('account.voucher', required=True, default=lambda self: self._context.get('active_ids', []))
    date=fields.Date('Fecha', required=True)
    bank_account_id=fields.Many2one('res.partner.bank', 'Cuenta', required=True ,domain=[('partner_id', '=', 1)])
   
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }
    
    @api.multi
    def generar_cash_pichincha(self):
        file, filename = self.pichincha()
        return self.env['base.file.report'].show(file, filename)
    
    @api.multi
    def generar_cash_produbanco(self):
        file, filename = self.produbanco()
        return self.env['base.file.report'].show(file, filename)
    
    @api.multi
    def generar_cash_internacional(self):
        file, filename = self.internacional()
        return self.env['base.file.report'].show(file, filename)
    
    
    
    @api.multi
    def run_sql_pichincha(self,voucher_ids):
        self = self[0]
        buf = StringIO.StringIO()
        writer = csv.writer(buf, delimiter=';')
        
        #vis=self.env['account.voucher'].search([('id', 'in',self.voucher_ids.id)]).ids      
        #print"//// nomina ids ////=%s"%vis
        x1=self.voucher_ids.ids
        print"//// nomina ids ////=%s"%str(x1)
        s=str(x1)
        s1=s.replace('[',' ')
        s2=s1.replace(']',' ')

        

        self.env.cr.execute("""select 'PA' nomb, row_number() over(order by av.id asc) as nomc ,'USD' nomf,to_char(av.amount*100,'000000') nomg,'CTA' nomd,ban.acc_type nome,ban.acc_number nomj,'PAGO' nomk,rp.ident_type nomh,rp.ident_num nomi,rp.name noml,ban.bank_bic nomm 
                                from account_voucher av,res_partner rp,res_partner_bank ban 
                                where av.partner_id=rp.id and av.partner_id= ban.partner_id and av.id in (%s) order by 11"""% (s2))
        
        res = self.env.cr.dictfetchall()
        print"res=%s"%res
        caracter = {'1','2','3','4','5','6','7','8','9','0'}    
        cadena= "".join(str(res))        
        cadena1 =cadena.replace("u'c'",'C')
        cadena2 =cadena1.replace("u'r'",'R')
        cadena3 =cadena2.replace("u'",'')
        cadena4 =cadena3.replace("'",'')
        cadena5 =cadena4.replace(":",'')
        cadena6 =cadena5.replace("]",'')
        cadena7 =cadena6.replace("[{",'')
        cadena8 =cadena7.replace("}",'')
        cadena9 =cadena8.replace("nomb",'') 
        cadena10=cadena9.replace("nomc",'') 
        cadena11=cadena10.replace("nomf",'') 
        cadena12=cadena11.replace("nome",'')   
        cadena13=cadena12.replace("nomd",'') 
        cadena14=cadena13.replace("nomg",'') 
        cadena15=cadena14.replace("nomh",'') 
        cadena16=cadena15.replace("nomi",'') 
        cadena17=cadena16.replace("nomj",'') 
        cadena18=cadena17.replace("nomk",'') 
        cadena19=cadena18.replace("noml",'')
        cadena20=cadena19.replace("nomm",'')
        cadena21=cadena20.replace(",",'\t') 
        cadena22=cadena21.replace('xf1','n')
        cadena23=cadena22.replace('COR','CTE')         
        cadena24=cadena23.replace("{",'\r\n') 
       
#        cadena26=cadena25.replace(cadena25,'' + '\r\n' + cadena25)
        print"cadena24%s"%cadena24

        out = base64.encodestring(cadena24)
        print"out=%s"%out
        name=time.strftime('CASHPichincha'+'%Y%m%d.xls')
        
        for recordp in self.voucher_ids:
            recordp.proforma_voucher()
            
        return self.env['base.file.report'].show(out, name)
    
    
    def pichincha(self, CODIF='Windows-1252', NEWLINE='\r\n'):
        string = ''
        DATE = datetime.strptime(self.date, '%Y-%m-%d').strftime('%y%m%d')

        for sequence, transfer in enumerate(self.voucher_ids, 1):
            
            TIPO_CUENTA = {'AHO': 'AHO', 'COR': 'CTE'}
            TIPO_IDENT = {'c': 'C', 'r': 'R', 'p': 'P'}
            print"transfer=%s"%transfer 
                          
            if transfer.partner_id.bank_ids:
                bank=self.env['res.partner.bank'].search([('id','=',transfer.partner_id.bank_ids.id)]).id
                banco=self.env['res.partner.bank'].search([('id','=',bank),('partner_id','=', transfer.partner_id.id)]).bank_bic
                tipo=self.env['res.partner.bank'].search([('id','=',bank),('partner_id','=', transfer.partner_id.id)]).acc_type
                numero=self.env['res.partner.bank'].search([('id','=',bank),('partner_id','=', transfer.partner_id.id)]).acc_number
                
        
                string += 'PA%s%s%s'%(' ',sequence,' ')
                string += 'USD%s%s%s'%(' ',str(int(round(transfer.amount, 2) * 100)).rjust(6, '0'),' ')
                string += 'CTA%s%s'%(' ',TIPO_CUENTA[tipo])
                string += '%s%s%s'%(' ',numero.replace('-', ''),' ')
                string += 'PAGO%s%s%s%s%s%s%s%s'%(' ',TIPO_IDENT[transfer.partner_id.ident_type],' ',transfer.partner_id.ident_num.upper().ljust(10, ' ')[:10],' ',banco.replace('-', '').rjust(2, '0'),' ',transfer.partner_id.name.upper().ljust(40, ' ')[:40])
                string += NEWLINE
                
#                 print"///////string////////=%s"%string
#                 columnas=string.split(' ',11)
#                 stringr ="".join(str(columnas))
#                 stringr0 = stringr.replace("u'",'')
#                 stringr1 = stringr0.replace("[",'')
#                 stringr2 = stringr1.replace("'",'')
#                 stringr3 = stringr2.replace("\r\n",'')
#                 stringc  = stringr3.replace("]",'\r\n')
#                 print"///////stringc////////=%s"%stringc
                
            else:
                continue
     
#         stringt =stringr.replace(stringr,'1,2,3,4,5,6,7,8,9,10,11,12' +'\r\n'+ stringr)
#         print"///////stringt////////=%s"%stringt

        #file = base64.encodestring(string.encode(CODIF))
        file = base64.encodestring(string)
        filename = time.strftime('CASH'+self.bank_account_id.bank_bic+'%Y%m%d.txt')
        for recordp in self.voucher_ids:
            recordp.proforma_voucher()
            
        return file, filename
        


    def produbanco(self, CODIF='Windows-1252', NEWLINE='\r\n'):
        string = ''

        DATE = datetime.strptime(self.date, '%Y-%m-%d').strftime('%y%m%d')

        for sequence, transfer in enumerate(self.voucher_ids, 1):
            TIPO_CUENTA = {'AHO': 'AHO', 'COR': 'CTE'}
            TIPO_IDENT = {'c': 'C', 'r': 'R', 'p': 'P'}

            if transfer.partner_id.bank_ids:
                string += 'PA\t%s\t%s\t%s'%(self.bank_account_id.acc_number.replace('-', ''), sequence, '')
                string += '%s%s'%(transfer.partner_id.ident_num.upper().ljust(13, ' ')[:13],' ')
                string += 'USD%s%s%s'%(' ',str(int(round(transfer.amount, 2) * 100)).rjust(14, '0'),' ')
                string += 'CTA%s%s%s'%(' ',transfer.partner_id.bank_ids.bank_bic.replace('-', '').rjust(4, '0'),' ')
                string += '%s%s%s'%(' ',TIPO_CUENTA[transfer.partner_id.bank_ids.acc_type],' ')      
                string += '%s%s%s%s%s%s%s'%(transfer.partner_id.bank_ids.acc_number.replace('-', '').rjust(11, '0'),' ',TIPO_IDENT[transfer.partner_id.ident_type],' ',transfer.partner_id.ident_num.upper().ljust(13, ' ')[:13],' ',transfer.partner_id.name.upper().ljust(40, ' ')[:40])
                string += '|%s'%(transfer.partner_id.email or '')
                string += NEWLINE
            else:
                continue
            
            
        file = base64.encodestring(string.encode(CODIF))
        filename = time.strftime('CASH'+self.bank_account_id.bank_bic+'%Y%m%d.txt')
        for recordp in self.voucher_ids:
            recordp.proforma_voucher()
            
        return file, filename
    
    
    @api.multi
    def run_sql_internacional(self,voucher_ids):
        self = self[0]
        buf = StringIO.StringIO()
        writer = csv.writer(buf, delimiter=';')
        
        #vis=self.env['account.voucher'].search([('id', 'in',self.voucher_ids.id)]).ids      
        #print"//// nomina ids ////=%s"%vis
        x1=self.voucher_ids.ids
        print"//// nomina ids ////=%s"%str(x1)
        s=str(x1)
        s1=s.replace('[',' ')
        s2=s1.replace(']',' ')

        

#         self.env.cr.execute("""select 'PA' nomb,ROW_NUMBER() over (order by av.id) as nomc,'USD' b,to_char(av.amount*100,'000000') nomf,'CTA' nomg,ban.acc_type nomd,ban.acc_number nome,'PAGO' nomj,rp.ident_type nomk,rp.ident_num nomh,rp.name nomi,LPAD(ban.bank_bic,5,'`00') as noml 
#                                 from account_voucher av,res_partner rp,res_partner_bank ban 
#                                 where av.partner_id=rp.id and av.partner_id= ban.partner_id and av.id in (%s) order by 2"""% (s2))
#         
        self.env.cr.execute("""select 'PA' nomb,row_number() over() as nomc,'USD' b,to_char(av.amount*100,'000000') nomf,'CTA' nomg,ban.acc_type nomd,ban.acc_number nome,'PAGO' nomj,rp.ident_type nomk,rp.ident_num nomh,rp.name nomi,ban.bank_bic noml 
                                from account_voucher av,res_partner rp,res_partner_bank ban 
                                where av.partner_id=rp.id and av.partner_id= ban.partner_id and av.id in (%s) order by 2"""% (s2))
        
        res = self.env.cr.dictfetchall()
        print"res=%s"%res
            
        cadena= "".join(str(res))        
        cadena1 =cadena.replace("u'c'",'C')
        cadena3 =cadena1.replace("u'r'",'R')
        cadena4 =cadena3.replace("u'",'')
        cadena5 =cadena4.replace("]",'')
        cadena6 =cadena5.replace("[{",'')
        cadena7 =cadena6.replace("}",'')
        cadena8 =cadena7.replace("nomb",'') 
        cadena9 =cadena8.replace("nomc",'') 
        cadena10=cadena9.replace("nomf",'') 
        cadena11=cadena10.replace("nome",'')   
        cadena12=cadena11.replace("nomd",'') 
        cadena13=cadena12.replace("nomg",'') 
        cadena14=cadena13.replace("nomh",'') 
        cadena15=cadena14.replace("nomi",'') 
        cadena16=cadena15.replace("nomj",'') 
        cadena17=cadena16.replace("nomk",'') 
        cadena18=cadena17.replace("noml",'')
        cadena19=cadena18.replace(",",'\t') 
        cadena20=cadena19.replace("'",'')
        cadena21=cadena20.replace(":",'')
        cadena22=cadena21.replace("b",'') 
        cadena23=cadena22.replace("COR",'CTE')    
        cadena24=cadena23.replace("xf1",'n')       
        cadena25=cadena24.replace("{",'\r\n')        

        print"cadena25=%s"%cadena25

        out = base64.encodestring(cadena25) #base64.encodestring(cadena24.encode('Windows-1252'))  
        print"out=%s"%out
        name=time.strftime('CASHInternacional'+'%Y%m%d.xls')

        for recordp in self.voucher_ids:
            recordp.proforma_voucher()
        
        return self.env['base.file.report'].show(out, name)

    
    
    
    def internacional(self, CODIF='Windows-1252', NEWLINE='\r\n'):
        string = ''
        DATE = datetime.strptime(self.date, '%Y-%m-%d').strftime('%y%m%d')

        for sequence, transfer in enumerate(self.voucher_ids, 1):
            
            TIPO_CUENTA = {'AHO': 'AHO', 'COR': 'CTE'}
            TIPO_IDENT = {'c': 'C', 'r': 'R', 'p': 'P'}
            print"transfer=%s"%transfer 
                          
            if transfer.partner_id.bank_ids:
                bank=self.env['res.partner.bank'].search([('id','=',transfer.partner_id.bank_ids.id)]).id
                banco=self.env['res.partner.bank'].search([('id','=',bank),('partner_id','=', transfer.partner_id.id)]).bank_bic
                tipo=self.env['res.partner.bank'].search([('id','=',bank),('partner_id','=', transfer.partner_id.id)]).acc_type
                numero=self.env['res.partner.bank'].search([('id','=',bank),('partner_id','=', transfer.partner_id.id)]).acc_number
                
                
                string += 'PA%s%s%s'%(' ',sequence,' ')
                string += 'USD%s%s%s'%(' ',str(int(round(transfer.amount, 2) * 100)).rjust(6, '0'),' ')
                string += 'CTA%s%s%s'%(' ',TIPO_CUENTA[tipo],' ')
                string += '%s%s%s'%(' ',numero.replace('-', ''),' ')      
                string += '%s%s%s%s%s%s%s%s%s'%(transfer.reference,' ',TIPO_IDENT[transfer.partner_id.ident_type],' ',transfer.partner_id.ident_num.upper().ljust(13, ' ')[:13],' ',transfer.partner_id.name.upper().ljust(32, ' ')[:32],banco.replace('-', '').rjust(4, '0'),' ')

                string += NEWLINE
            else:
                continue
        
        
        file = base64.encodestring(string.encode(CODIF))
        filename = time.strftime('CASH'+self.bank_account_id.bank_bic+'%Y%m%d.txt')
        for recordp in self.voucher_ids:
            recordp.proforma_voucher()
            
        return file, filename
