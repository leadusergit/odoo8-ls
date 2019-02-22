# -*- encoding: utf-8 -*-
##############################################################################
#
#    Payments module
#    Copyright (C) 2010-2010 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
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
import datetime
from openerp.osv import osv, fields
import StringIO
import base64
from string import upper, join


class wizard_regenerate_cash_management(osv.osv_memory):
    _name = "wizard.regenerate.cash"
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    
    
    def obtener_formato(self):
        #formato banco guayaquil
        linea = []
        detalle_linea0 = {}
        detalle_linea0['nombre'] = 'tipo_cuenta'
        detalle_linea0['dato'] = 'employee.bank_account_id.type'
        detalle_linea0['orden'] = 1
        detalle_linea0['numero_espacios'] = 1
        detalle_linea0['separador'] = ''
        detalle_linea0['tipo'] = 'obtenido'
        
        linea.append(detalle_linea0)
        
        detalle_linea1 = {}
        detalle_linea1['nombre'] = 'numero_cuenta_guayaquil'
        detalle_linea1['dato'] = 'employee.bank_account_id.name'
        detalle_linea1['orden'] = 2
        detalle_linea1['numero_espacios'] = 10
        detalle_linea1['separador'] = ''
        detalle_linea1['tipo'] = 'obtenido'
        
        linea.append(detalle_linea1)
        
        detalle_linea2 = {}
        detalle_linea2['nombre'] = 'valor'
        detalle_linea2['dato'] = 'debit'
        detalle_linea2['orden'] = 3
        detalle_linea2['numero_espacios'] = 15
        detalle_linea2['separador'] = ''
        detalle_linea2['tipo'] = 'obtenido'
        
        linea.append(detalle_linea2)
        
        detalle_linea3 = {}
        detalle_linea3['nombre'] = 'codigo'
        detalle_linea3['dato'] = '7S'
        detalle_linea3['orden'] = 4
        detalle_linea3['numero_espacios'] = 2
        detalle_linea3['separador'] = ''
        detalle_linea3['tipo'] = 'fijo'
        
        linea.append(detalle_linea3)
        
        detalle_linea4 = {}
        detalle_linea4['nombre'] = 'nota'
        detalle_linea4['dato'] = 'Y'
        detalle_linea4['orden'] = 5
        detalle_linea4['numero_espacios'] = 1
        detalle_linea4['separador'] = ''
        detalle_linea4['tipo'] = 'fijo'
        
        linea.append(detalle_linea4)
        
        detalle_linea5 = {}
        detalle_linea5['nombre'] = 'agencia'
        detalle_linea5['dato'] = '01'
        detalle_linea5['orden'] = 6
        detalle_linea5['numero_espacios'] = 2
        detalle_linea5['separador'] = ''
        detalle_linea5['tipo'] = 'fijo'
        
        linea.append(detalle_linea5)
        
        detalle_linea6 = {}
        detalle_linea6['nombre'] = 'banco'
        detalle_linea6['dato'] = 'employee.bank_account_id.res_bank_id.code'
        detalle_linea6['orden'] = 7
        detalle_linea6['numero_espacios'] = 2
        detalle_linea6['separador'] = ''
        detalle_linea6['tipo'] = 'obtenido'
        
        linea.append(detalle_linea6)
    
        detalle_linea7 = {}
        detalle_linea7['nombre'] = 'numero_cuenta_otros'
        detalle_linea7['dato'] = 'employee.bank_account_id.name'
        detalle_linea7['orden'] = 8
        detalle_linea7['numero_espacios'] = 18
        detalle_linea7['separador'] = ''
        detalle_linea7['tipo'] = 'obtenido'
        
        linea.append(detalle_linea7)
        
        detalle_linea8 = {}
        detalle_linea8['nombre'] = 'empleado'
        detalle_linea8['dato'] = 'employee.name'
        detalle_linea8['orden'] = 9
        detalle_linea8['numero_espacios'] = 21
        detalle_linea8['separador'] = ''
        detalle_linea8['tipo'] = 'obtenido'
        
        linea.append(detalle_linea8)
        
        return linea
    
    
    
    def get_data(self, employee, data, formato):
        
        esp = ['á', 'à', 'â', 'ã', 'ª', 'Á', 'À', 'Â', 'Ã', 'Í', 'Ì', 'Î', 'í', 'ì', 'î', 'é', 'è', 'ê', 'É', 'È', 'Ê', 'ó', 'ò', 'ô', 'õ', 'º', 'Ó', 'Ò', 'Ô', 'Õ', 'ú', 'ù', 'û', 'Ú', 'Ù', 'Û', 'ç', 'Ç', 'ñ', 'Ñ', 'Ñ']
        nor = ['a', 'a', 'a', 'a', 'a', 'A', 'A', 'A', 'A', 'I', 'I', 'I', 'i', 'i', 'i', 'e', 'e', 'e', 'E', 'E', 'E', 'o', 'o', 'o', 'o', 'o', 'O', 'O', 'O', 'O', 'u', 'u', 'u', 'U', 'U', 'U', 'c', 'C', 'n', 'N', 'N']        
        
        #print ' formato ', formato
        
        #print ' nombre ', formato['nombre']
        
        if formato['nombre'] == 'tipo_cuenta':
            espacios = formato['numero_espacios']
            #print ' get_data tipo_cuenta ', employee.bank_account_id.type.strip().upper()
            return employee.bank_account_id.type.upper()[0:espacios]
        
        if formato['nombre'] == 'numero_cuenta_guayaquil' and employee.bank_account_id.res_bank_id.id == 1:
            cta_gye = employee.bank_account_id.name.strip()
            #print ' get_data numero_cuenta_guayaquil ', cta_gye
            return cta_gye.zfill(formato['numero_espacios'])
        elif formato['nombre'] == 'numero_cuenta_guayaquil' and employee.bank_account_id.res_bank_id.id != 1:
            cta_otros = ''
            return cta_otros.zfill(formato['numero_espacios'])
        
        if formato['nombre'] == 'valor':
            #print ' ingreso AAA', data.debit
            tot = '{0:.2f}'.format(data.debit) 
            #print ' tot ', tot
            val = tot.split('.')
            l = ""
            for item in val[0]:
                l += item
            if len(val[1]) < 2:
               val[1] += '0'
            #print 'val[1] ', val[1]
            for item in val[1]:
                l += item
            #print ' get_date valor ', l
            return l.zfill(formato['numero_espacios'])
        
        
        if formato['nombre'] == 'banco' and employee.bank_account_id.res_bank_id.id == 1:
            return '  '
        elif formato['nombre'] == 'banco' and employee.bank_account_id.res_bank_id.id != 1:
            return employee.bank_account_id.res_bank_id.code.strip().zfill(formato['numero_espacios'])    
        
        
        if formato['nombre'] == 'numero_cuenta_otros' and employee.bank_account_id.res_bank_id.id == 1:
            return '                  '
        elif formato['nombre'] == 'numero_cuenta_otros' and employee.bank_account_id.res_bank_id.id != 1:
            return employee.bank_account_id.name.strip().zfill(formato['numero_espacios'])
            
        
        if formato['nombre'] == 'empleado':
            nom = str(employee.name.encode('"UTF-8"').strip())
            for indi in range(40):
                nom = nom.replace(esp[indi], nor[indi])
            nombre = str(nom)
             
            if len(nombre) < 21:
                tam = len(nombre)
                num_espacion = 21 - tam
                for i in range(21):
                    nombre = nombre + ' '
                
            #print ' get data nombre emple ', nombre
            return nombre[0:formato['numero_espacios']]
    
    
    
    
    def obtener_cadena(self, employee, data, cont, context):
        #metodo que obtiene la cadena segun formato del banco que se configure
        #TODO Hacer la configuracion del banco con el que se va ha pagar y del formato
        #En este caso hacemos solo para el banco de guayaquil
        
        esp = ['á', 'à', 'â', 'ã', 'ª', 'Á', 'À', 'Â', 'Ã', 'Í', 'Ì', 'Î', 'í', 'ì', 'î', 'é', 'è', 'ê', 'É', 'È', 'Ê', 'ó', 'ò', 'ô', 'õ', 'º', 'Ó', 'Ò', 'Ô', 'Õ', 'ú', 'ù', 'û', 'Ú', 'Ù', 'Û', 'ç', 'Ç', 'ñ', 'Ñ', 'Ñ']
        nor = ['a', 'a', 'a', 'a', 'a', 'A', 'A', 'A', 'A', 'I', 'I', 'I', 'i', 'i', 'i', 'e', 'e', 'e', 'E', 'E', 'E', 'o', 'o', 'o', 'o', 'o', 'O', 'O', 'O', 'O', 'u', 'u', 'u', 'U', 'U', 'U', 'c', 'C', 'n', 'N', 'N']
        forma_pago = "CTA"
        cur = "USD"
        ref = "NOMINA "
        
        if True:
            #Si es banco de guayaquil
            cadena = ''
            cadena_formato = self.obtener_formato()
            #print ' cadena_formato ', cadena_formato
            for dato in cadena_formato:
                if dato['tipo'] == 'fijo':
                    cadena = cadena + dato['dato'] + dato['separador']
                    #print '  cadena ', cadena
                else:
                    cadena = cadena + self.get_data(employee, data, dato) + dato['separador']
                    #print '  cadena2 ', cadena
                    
            #print ' cadenaMMM ', cadena        
            return cadena + '\n'
      

    
    def act_regenerate_cash(self, cr, uid, ids, context=None):
        #print 'ids', ids
        #print 'context', context
        res = []
        unlink_ids = []
        
        cont = 1
        cont_trans = 0
        total_transferencia = 0
        buf = StringIO.StringIO()
        
        
        payment_transfer_data = self.pool.get('payment.transfer').browse(cr, uid, context.get('active_ids'))
        
        #La cabecera de las transferencias
        for item in payment_transfer_data:
            transferencias_line = item.transfer_ids
            #Los detalles de la transferencia
            for line_trans in transferencias_line:
                #Si tiene relacion con el move_line
                if line_trans.line_id:
                    move_line = line_trans.line_id
                    employee = move_line.employee_id
                    cadena = ""
                    lista = []
                    
                    #Los empleados con cuenta bancario y del banco de guayaquil
                    if employee.active and employee.bank_account_id:
                        if employee.bank_account_id.res_bank_id.id == 1:
                            if move_line.debit:
                                cadena = self.obtener_cadena(employee, move_line, cont, context)
                                buf.write(upper(cadena))
                                cont_trans = cont_trans + 1
                                total_transferencia = total_transferencia + move_line.debit 
                                #print '*/***///**///**////**cadena ', cadena
            
            
            #Los detalles de la transferencia        
            for line_trans_others in transferencias_line:
                #Si tiene relacion con el move line
                if line_trans_others.line_id:
                    move_line = line_trans_others.line_id
                    employee = move_line.employee_id
                    cadena = ""
                    lista = []
                    #Si tiene cuenta en otros bancos
                    if employee.active and employee.bank_account_id:
                        if employee.bank_account_id.res_bank_id.id != 1:
                            if move_line.debit:
                                cadena = self.obtener_cadena(employee, move_line, cont, context)
                                buf.write(upper(cadena))
                                cont_trans = cont_trans + 1
                                total_transferencia = total_transferencia + move_line.debit
                                #print '*/***///**///**////**cadena ', cadena         
                            
                    
        
        
            out = base64.encodestring(buf.getvalue())
            
        buf.close()
        name = "%s%s%s.TXT" % ("NCR", time.strftime('%Y%m%d'), "7S_01")
        #return {'data': out, 'name': name, 'transferencias': cont_trans, 'cheques': cont_cheq, 'tipo':type_hr, 'total_transferencia':total_transferencia, 'total_cheques':total_cheques }
        
        result = {'data': out,
                    'registros_generados' : cont_trans,
                    'valor_total':total_transferencia,
                    'state' : 'get'}
        return self.write(cr, uid, ids, result, context=context)
        
   
    _columns = {
            'data':fields.binary('Cash Nomina'), 
            'registros_generados' : fields.integer('Numero Quicenas Generadas'),
            'valor_total' : fields.float('Total Quincena'),
            'state': fields.selection((('choose', 'choose'), # choose the file
                                         ('get', 'get'), # get the data and finish
                                       )),
    }
   
    _defaults = {
        'state': lambda * a: 'choose',
    }
    
wizard_regenerate_cash_management()
