# -*- coding: utf-8 -*-
###################################################
#
#    BUILDING CRM Module
#    Copyright (C) 2012 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
#    $autor: Dairon Medina Caro <dairon.medina@gmail.com>
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
###################################################

from openerp.osv import osv, fields
import base64
import StringIO
from time import strftime
import time
import datetime
from string import upper, join

class wizard_generar_cash_banco(osv.osv_memory):
    """
    Wizard to cancel payments transfers
    """
    _name = 'wizard.generar.cash.banco'
    
    def create_cash(self, cr, uid, ids, context=None):
        """
        Generate cash file
        """
        data = {}        
        data['form'] = self.read(cr, uid, ids)[0]
        this = data['form']
        
        tranfer_id = this.get('n_transfer_id')
        #print 'tranfer_id:', tranfer_id
        cur = "USD"
        cont = 1
        diferencia = 0
        secuencia = ''
        buf = StringIO.StringIO()
        nr_fact = ''
        
        suma = 0 

        """Contador del Pago """
        """Pagos en el mismo dia generado el pago"""
        cr.execute('select generation_date as pago from payment_transfer_payment where id = %s', (tranfer_id,))
        fila = cr.dictfetchall()
        for clave in fila:
             fecha = clave['pago']
             campos = fecha.split('-')
             fecha = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
             hoy =datetime.date.today()
             diferencia = (hoy - fecha).days
             cr.execute('select max(contador)as contador from payment_transfer_payment where generation_date=%s', (hoy,))
             contadores = cr.dictfetchall()
             for llave in contadores:
                 contador =llave['contador']
                 if diferencia == 0:
                     if contador == 0:
                         contador = 1
                         self.pool.get('payment.transfer.payment').write(cr, uid,[tranfer_id],{'contador':contador})                   
                         #print "contador1",contador
                     else:
                         contador = contador+1
                         seq = contador
                         self.pool.get('payment.transfer.payment').write(cr, uid,[tranfer_id],{'contador':contador})
                         #print "contador2", contador
                 else:
                     """Pagos en diferente dia del generado el pago"""                 
                     cr.execute('select max(contador) as ultimo from payment_transfer_payment where payment_date = %s', (hoy,))
                     ultimo = cr.dictfetchall()
                     for u in ultimo:
                         max = u['ultimo']
                         #print "max",max
                         if max != None:
                             if max != 0 :
                                 contador = max + 1
                                 seq = contador
                                 self.pool.get('payment.transfer.payment').write(cr, uid,[tranfer_id],{'contador':contador})
                                 #print "contador3", contador
                         else:
                              contador =1
                              self.pool.get('payment.transfer.payment').write(cr, uid,[tranfer_id],{'contador':contador})
                              #print "contador4", contador
                         
        secuencia = str(contador).zfill(2)
        payment ='_' + secuencia
        
        #Actualizo la fecha de Pago de Comprobante
        self.pool.get('payment.transfer.payment').write(cr, uid,[tranfer_id],{'payment_date':time.strftime('%Y-%m-%d')})
               
        #Los que tengan Banco de Guayaquil para completar el numero de 10 digitos de la cuenta!
        cr.execute("""SELECT partner as codigo, sum(amount_total) as total 
                          FROM invoice_line_transfer
                      WHERE 
                          has_transfer = %s
                          AND transfer_id = %s 
                          AND payment_type in ('CTA','CHQ','EFE')
                      GROUP BY codigo""", (True,tranfer_id))
        consulta = cr.dictfetchall()
        
        if consulta:
            ilt = pool.get('invoice.line.transfer')
            
            correo = ''
            for key in consulta:
                esp=['á','à','â','ã','ª','Á','À','Â','Ã','Í','Ì','Î','í','ì','î','é','è','ê','É','È','Ê','ó','ò','ô','õ','º','Ó','Ò','Ô','Õ','ú','ù','û','Ú','Ù','Û','ç','Ç','ñ','Ñ','Ñ']
                nor=['a','a','a','a','a','A','A','A','A','I','I','I','i','i','i','e','e','e','E','E','E','o','o','o','o','o','O','O','O','O','u','u','u','U','U','U','c','C','n','N','N']
                espacios = ['\n',',']
                
                id_partner = key['codigo']
                total = key['total']
                suma += total
                partner = self.pool.get('res.partner').browse(cr, uid, id_partner)
                
                for c in partner.address:
                    if c.email != "Por Definir" and c.email:
                        mail = str(c.email).replace(',', '; ').replace('\n', '')
                        correo = 'PAGO DE FACTURAS VARIAS|'+mail
                #print "correo", correo
                
                cedula = str(partner.cedula)
                tam_ced = len(cedula)
                
                if tam_ced < 13:
                    for i in range(13-tam_ced):
                        cedula +=' '
                
                if partner.ref:
                    codigo = str(partner.ref).replace('\n', '')
                else:
                    codigo = 'S/C'
                
                tipo_pago = ''
                num_cta = ''
                t_cta = '' 
                t_cod = ''
                
                if partner.payment_type:
                    tipo_pago = partner.payment_type
                    
                #print "tipo_pago", tipo_pago
                
                if tipo_pago == 'EFE' or tipo_pago == 'CHQ':
                    num_cta=''
                    t_cta =''
                    t_cod='0017'
                    
                tot = str(round(total,2))
                val = tot.replace(".","")
                valor = str(val).zfill(13)
                
                if tipo_pago == 'CTA':
                    if partner.bank_ids:
                        for cuentas in partner.bank_ids:
                            if cuentas.has_payment:
                                if cuentas.bank.code == '17':
                                    if cuentas.acc_number:
                                        num_cta = str(cuentas.acc_number).replace('\n', '').zfill(10)
                                        
                                else:
                                    if cuentas.acc_number:
                                        num_cta = str(cuentas.acc_number).replace('\n', '')
                                if cuentas.acc_type:
                                    if cuentas.acc_type=='COR':
                                        t_cta= 'CTE'
                                        t_cod = str(cuentas.bank.code).replace('\n', '').zfill(4)
                                    else:
                                        t_cta = str(cuentas.acc_type).upper()
                                        t_cod = str(cuentas.bank.code).replace('\n', '').zfill(4)
                                break
                            
                t_em = str(partner.ident_type).upper()
                nom = partner.name.encode('"UTF-8"')                
                
                for indi in range(40):
                    nom = nom.replace(esp[indi],nor[indi])
                    nombre = str(nom).replace('\n', '')
                nombre = str(nom)
                tam_nom = len(nombre)
                if tam_nom < 45:
                   for i in range(45-tam_nom):
                       nombre+=' '
                else:
                    nombre = nombre[:41]
                    
                num = str(cont)
                tam_cont = len(num)
                
                if tam_cont < 3:
                   for i in range(3-tam_cont):
                       num+=' '
                
                """Comprobante de pago"""
                res = self.pool.get('invoice.line.transfer').search(cr, uid, [('transfer_id','=', tranfer_id),
                                                                                               ('has_transfer','=',1),
                                                                                               ('partner','=',id_partner)])
                if res:
                    """Escoger el ultimo como referencia para el Nro de Comprobante"""
                    comprobante = self.pool.get('invoice.line.transfer').browse(cr, uid, res[-1])
                    if comprobante:
                        nro_cp = comprobante.account_mov_id.move_id.id
                        obj_move =  self.pool.get('account.move').browse(cr, uid, nro_cp)
                        if obj_move and obj_move.number_entries:
                            numero = str(obj_move.number_entries)
                        else:
                            numero = ' '
                    lista = []
                    numeros = []
                    for invoices in res:
                        invoice =  self.pool.get('invoice.line.transfer').browse(cr, uid, invoices)
                        if invoice.account_mov_id.inv_type == 'invoice':
                           lista.append(invoice.account_mov_id.invoice_id)
                    """Union por numero de facturas """
                    facturas = list(set(lista))
                    for nrs in facturas:
                        obj_invoice = self.pool.get('account.invoice').browse(cr, uid, int(nrs))
                        numeros.append(str(obj_invoice.number_inv_supplier))
                    
                    nr_fact =','.join(numeros)
                             
                cadena = "PA\t" +"0005805929\t"+ num + '\t' +numero+'\t'+codigo+'\t'+ cur + '\t' + valor + '\t' + tipo_pago + \
                         '\t' + t_cod +'\t'+ t_cta + '\t' + num_cta + '\t' + t_em + '\t' + cedula + '\t' + nombre + \
                         '\t'+""+'\t'+""+'\t'+""+'\t'+""+'\t'+nr_fact+'\t'+correo+'\t\n'
                #print cadena
                buf.write(upper(cadena))
                cont=cont+1
                      
        out = base64.encodestring(buf.getvalue())
        buf.close()
        name = "%s%s%s.txt" % ("PAGOS_MULTICASH_", strftime('%Y%m%d'),payment)
        monto = "%s"% (round(suma, 2))
        
        return {'data': out, 'name': name, 'state': 'done'}

    
    _columns = {
                'n_transfer_id': fields.many2one('payment.transfer.payment', 'Transferencia', required=True),
                'data': fields.binary(string="Archivo Banco Guayaquil", readonly=True),
                'name': fields.char('Nombre', size=60),
                'state': fields.selection([('init', 'init'), ('done', 'done')]),
    }
    
wizard_generar_cash_banco()