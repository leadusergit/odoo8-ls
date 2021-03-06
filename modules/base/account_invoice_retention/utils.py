# -*- coding: utf-8 -*-
###################################################
#
#    Account Invoice Retention MODULE
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

def cedula_validation(identification_number):
    
    #print ' EN EL UTILS '
    res = {'value':{}}
    if identification_number:
            numcc = identification_number
            suma = 0
            residuo = 0
            pri = False
            pub = False
            nat = False
            numeroProvincias = 24
            modulo = 11
            
            if len(numcc) < 10 or not identification_number.isdigit():
                resultado = 'Número ingresado no es valido'
                #print resultado
                raise osv.except_osv(('Atención !'), ('Número ingresado no es valido!'))
                # Los primeros dos digitos corresponden al codigo de la provincia
            elif len(numcc) > 10:
                 raise osv.except_osv(('Atención !'), ('Número ingresado no es valido!'))
            provincia = int(numcc[0:2])
            if (provincia < 1) or (provincia > numeroProvincias):
                resultado = 'El codigo de la provincia (dos primeros digitos) es invalido'
                #print resultado
                raise osv.except_osv(('Atención !'), ('El codigo de la provincia (dos primeros digitos) es invalido!'))
                # Aqui almacenamos los digitos de la cedula en variables.
            d1 = int(numcc[0:1])
            d2 = int(numcc[1:2])
            d3 = int(numcc[2:3])
            d4 = int(numcc[3:4])
            d5 = int(numcc[4:5])
            d6 = int(numcc[5:6])
            d7 = int(numcc[6:7])
            d8 = int(numcc[7:8])
            d9 = int(numcc[8:9])
            d10 = int(numcc[9:10])
            # El tercer digito es:
            # 9 para sociedades privadas y extranjeros
            # 6 para sociedades publicas
            # menor que 6 (0,1,2,3,4,5) para personas naturales
            if (d3 == 7 or d3 == 8):
                resultado = 'El tercer d\u00edgito ingresado es inv\u00e1lido'
                #print resultado
                raise osv.except_osv(('Atención !'), ('El tercer digito ingresado es invalido!'))
                #Solo para personas naturales (modulo 10)
            p1 = 0
            p2 = 0
            p3 = 0
            p4 = 0
            p5 = 0
            p6 = 0
            p7 = 0
            p8 = 0
            p9 = 0
            if d3 < 6:
                nat = True          
                p1 = d1 * 2
                if p1 >= 10: p1 -= 9    
                p2 = d2 * 1
                if p2 >= 10: p2 -= 9
                p3 = d3 * 2
                if p3 >= 10: p3 -= 9
                p4 = d4 * 1
                if p4 >= 10: p4 -= 9
                p5 = d5 * 2
                if p5 >= 10: p5 -= 9
                p6 = d6 * 1
                if p6 >= 10: p6 -= 9
                p7 = d7 * 2
                if p7 >= 10: p7 -= 9
                p8 = d8 * 1
                if p8 >= 10: p8 -= 9
                p9 = d9 * 2
                if p9 >= 10: p9 -= 9
                modulo = 10
                #Solo para sociedades publicas (modulo 11)
                #Aqui el digito verficador esta en la posicion 9, en las otras 2 en la pos. 10
            elif d3 == 6:
                pub = True
                p1 = d1 * 3
                p2 = d2 * 2
                p3 = d3 * 7
                p4 = d4 * 6                 
                p5 = d5 * 5
                p6 = d6 * 4
                p7 = d7 * 3
                p8 = d8 * 2
                p9 = 0
            #Solo para entidades privadas (modulo 11)
            elif d3 == 9:
                pri = True
                p1 = d1 * 4
                p2 = d2 * 3                     
                p3 = d3 * 2
                p4 = d4 * 7
                p5 = d5 * 6
                p6 = d6 * 5
                p7 = d7 * 4
                p8 = d8 * 3
                p9 = d9 * 2
            suma = p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            residuo = suma % modulo
            #Si residuo=0, dig.ver.=0, caso contrario 10 - residuo
            if residuo == 0:
                digitoVerificador = residuo
            else:
                digitoVerificador = modulo - residuo
                #ahora comparamos el elemento de la posicion 10 con el dig. ver.
            if pub == True:
                if digitoVerificador != d9:
                    resultado = 'El ruc de la empresa del sector p\u00fablico es incorrecto.'
                    #print resultado
                    raise osv.except_osv(('Atención !'), ('El ruc de la empresa del sector público es incorrecto!'))
                else:
                    resultado = 'Número de Identificación Correcto'
                    #print resultado
                    #raise osv.except_osv(('Atención !'), ('Número de Identificación Correcto!'))
                #El ruc de las empresas del sector público terminan con 0001*/
                if (int(numcc[9: 13])) != 0001:
                    resultado = 'El ruc de la empresa del sector p\u00fablico debe terminar con 0001'
                    #print resultado
                    raise osv.except_osv(('Atención !'), ('El ruc de la empresa del sector público debe terminar con 0001!'))
                else:
                    resultado = 'Número de Identificación Correcto'
                    #print resultado
                    #raise osv.except_osv(('Atención !'), ('Número de Identificación Correcto!'))
            elif pri == True:
                if digitoVerificador != d10:
                    resultado = 'El ruc de la empresa del sector privado es incorrecto.'
                    #print resultado
                    raise osv.except_osv(('Atención !'), ('El ruc de la empresa del sector privado es incorrecto!'))
                else:
                    resultado = 'Número de Identificación Correcto'
                    #print resultado
                    #raise osv.except_osv(('Atención !'), ('Número de Identificación Correcto!'))
                                                       
                if (int(numcc[10:13])) != 001:
                    resultado = 'El ruc de la empresa del sector privado debe terminar con 001'
                    #print resultado
                    raise osv.except_osv(('Atención !'), ('El ruc de la empresa del sector privado debe terminar con 001!'))
                else:
                    resultado = 'Número de Identificación Correcto'
                    #print resultado
                    #raise osv.except_osv(('Atención !'), ('Número de Identificación Correcto!'))
            elif nat == True:
                if digitoVerificador != d10:
                    resultado = 'El n\u00famero de c\u00e9dula de la persona natural es incorrecto.'
                    #print resultado
                    raise osv.except_osv(('Atención !'), ('El Número de cedula de la persona natural es incorrecto!'))
                else:
                    resultado = 'Número de Identificación Correcto'
                    #print resultado
                    #raise osv.except_osv(('Atención !'), ('Número de Identificación Correcto!'))
                if (len(numcc) > 10) and ((int(numcc[10:13])) != 001):
                    resultado = 'El ruc de la persona natural debe terminar con 001'
                    #print resultado 
                    raise osv.except_osv(('Atención !'), ('El ruc de la persona natural debe terminar con 001!'))                                                                          
                else:
                    resultado = 'Número de Identificación Correcto'
                    #print resultado
                    #raise osv.except_osv(('Atención !'), ('Número de Identificación Correcto!'))
                
    return res
    
def ruc_validation(identification_number):
    res = {'value':{}}
    if identification_number:
            numcc = identification_number
            suma = 0
            residuo = 0
            pri = False
            pub = False
            nat = False
            numeroProvincias = 24
            modulo = 11
            
            if len(numcc) < 13 or not identification_number.isdigit():
                resultado = 'Número ingresado no es valido'
                #print resultado
                raise osv.except_osv(('Atención !'), ('Número ingresado no es valido!'))
                # Los primeros dos digitos corresponden al codigo de la provincia
            elif len(numcc) > 13 or not identification_number.isdigit():
                raise osv.except_osv(('Atención !'), ('Número ingresado no es valido!'))
           
            provincia = int(numcc[0:2])
            if (provincia < 1) or (provincia > numeroProvincias):
                resultado = 'El codigo de la provincia (dos primeros digitos) es invalido'
                #print resultado
                raise osv.except_osv(('Atención !'), ('El codigo de la provincia (dos primeros digitos) es invalido!'))
                # Aqui almacenamos los digitos de la ruc en variables.
            d1 = int(numcc[0:1])
            d2 = int(numcc[1:2])
            d3 = int(numcc[2:3])
            d4 = int(numcc[3:4])
            d5 = int(numcc[4:5])
            d6 = int(numcc[5:6])
            d7 = int(numcc[6:7])
            d8 = int(numcc[7:8])
            d9 = int(numcc[8:9])
            d10 = int(numcc[9:10])
            # El tercer digito es:
            # 9 para sociedades privadas y extranjeros
            # 6 para sociedades publicas
            # menor que 6 (0,1,2,3,4,5) para personas naturales
            if (d3 == 7 or d3 == 8):
                resultado = 'El tercer d\u00edgito ingresado es inv\u00e1lido'
                #print resultado
                raise osv.except_osv(('Atención !'), ('El tercer digito ingresado es invalido!'))
                #Solo para personas naturales (modulo 10)
            p1 = 0
            p2 = 0
            p3 = 0
            p4 = 0
            p5 = 0
            p6 = 0
            p7 = 0
            p8 = 0
            p9 = 0
            if d3 < 6:
                nat = True          
                p1 = d1 * 2
                if p1 >= 10: p1 -= 9    
                p2 = d2 * 1
                if p2 >= 10: p2 -= 9
                p3 = d3 * 2
                if p3 >= 10: p3 -= 9
                p4 = d4 * 1
                if p4 >= 10: p4 -= 9
                p5 = d5 * 2
                if p5 >= 10: p5 -= 9
                p6 = d6 * 1
                if p6 >= 10: p6 -= 9
                p7 = d7 * 2
                if p7 >= 10: p7 -= 9
                p8 = d8 * 1
                if p8 >= 10: p8 -= 9
                p9 = d9 * 2
                if p9 >= 10: p9 -= 9
                modulo = 10
                #Solo para sociedades publicas (modulo 11)
                #Aqui el digito verficador esta en la posicion 9, en las otras 2 en la pos. 10
            elif d3 == 6:
                pub = True
                p1 = d1 * 3
                p2 = d2 * 2
                p3 = d3 * 7
                p4 = d4 * 6                 
                p5 = d5 * 5
                p6 = d6 * 4
                p7 = d7 * 3
                p8 = d8 * 2
                p9 = 0
            #Solo para entidades privadas (modulo 11)
            elif d3 == 9:
                pri = True
                p1 = d1 * 4
                p2 = d2 * 3                     
                p3 = d3 * 2
                p4 = d4 * 7
                p5 = d5 * 6
                p6 = d6 * 5
                p7 = d7 * 4
                p8 = d8 * 3
                p9 = d9 * 2
            suma = p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            residuo = suma % modulo
            #Si residuo=0, dig.ver.=0, caso contrario 10 - residuo
            if residuo == 0:
                digitoVerificador = residuo
            else:
                digitoVerificador = modulo - residuo
                #ahora comparamos el elemento de la posicion 10 con el dig. ver.
            if pub == True:
                if digitoVerificador != d9:
                    resultado = 'El ruc de la empresa del sector p\u00fablico es incorrecto.'
                    #print resultado
                    raise osv.except_osv(('Atención !'), ('El ruc de la empresa del sector público es incorrecto!'))
                else:
                    resultado = 'Número de Identificación Correcto'
                    #print resultado
                    #raise osv.except_osv(('Atención !'), ('Número de Identificación Correcto!'))
                #El ruc de las empresas del sector público terminan con 0001*/
                if (int(numcc[9: 13])) != 0001:
                    resultado = 'El ruc de la empresa del sector p\u00fablico debe terminar con 0001'
                    #print resultado
                    raise osv.except_osv(('Atención !'), ('El ruc de la empresa del sector público debe terminar con 0001!'))
                else:
                    resultado = 'Número de Identificación Correcto'
                    #print resultado
                    #raise osv.except_osv(('Atención !'), ('Número de Identificación Correcto!'))
            elif pri == True:
                if digitoVerificador != d10:
                    resultado = 'El ruc de la empresa del sector privado es incorrecto.'
                    #print resultado
                    raise osv.except_osv(('Atención !'), ('El ruc de la empresa del sector privado es incorrecto!'))
                else:
                    resultado = 'Número de Identificación Correcto'
                    #print resultado
                    #raise osv.except_osv(('Atención !'), ('Número de Identificación Correcto!'))
                                                       
                if (int(numcc[10:13])) != 001:
                    resultado = 'El ruc de la empresa del sector privado debe terminar con 001'
                    #print resultado
                    raise osv.except_osv(('Atención !'), ('El ruc de la empresa del sector privado debe terminar con 001!'))
                else:
                    resultado = 'Número de Identificación Correcto'
                    #print resultado
                    #raise osv.except_osv(('Atención !'), ('Número de Identificación Correcto!'))
            elif nat == True:
                if digitoVerificador != d10:
                    resultado = 'El n\u00famero de c\u00e9dula de la persona natural es incorrecto.'
                    #print resultado
                    raise osv.except_osv(('Atención !'), ('El Número de ruc de la persona natural es incorrecto!'))
                else:
                    resultado = 'Número de Identificación Correcto'
                    #print resultado
                    #raise osv.except_osv(('Atención !'), ('Número de Identificación Correcto!'))
                if (len(numcc) > 10) and ((int(numcc[10:13])) != 001):
                    resultado = 'El ruc de la persona natural debe terminar con 001'
                    #print resultado 
                    raise osv.except_osv(('Atención !'), ('El ruc de la persona natural debe terminar con 001!'))                                                                          
                else:
                    resultado = 'Número de Identificación Correcto'
                    #print resultado
                    #raise osv.except_osv(('Atención !'), ('Número de Identificación Correcto!'))
                
    return res
