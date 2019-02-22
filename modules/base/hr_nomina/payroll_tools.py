# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution.
#    Module for basic payroll in Ecuador.
#    Copyright (C) 2010-2013 Israel Paredes Reyes. All Rights Reserved.
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
FORMAT = '%Y-%m-%d'
DIAS_PERIODO = 30

def DATE(date=None, format=FORMAT):
    import time, datetime
    date = date or time.strftime(format)
    return datetime.datetime.strptime(date, format).date()

def FECHAS_PERIODO(period, format='%m/%Y'):
    from calendar import monthrange
    date_start = DATE(period, format)
    dias = monthrange(date_start.year, date_start.month)[1]
    date_end = DATE('%s-%s-%s' % (date_start.year, date_start.month, dias), FORMAT)
    return date_start, date_end

def PERIODOS(fecha_inicio, fecha_fin, format=FORMAT):
    "DEVUELVE UN DICCIONARIO CON LOS PERIODOS QUE SE ENCUENTRAN ENTRE LAS FECHAS DADAS"
    from calendar import monthrange
    from datetime import date, timedelta
    fecha_inicio = DATE(fecha_inicio, format)
    fecha_fin = DATE(fecha_fin, format)
    res = {}
    valor = (fecha_inicio - fecha_fin).days
    while valor <= 0:
        dias_periodo = monthrange(fecha_inicio.year, fecha_inicio.month)[1]
        date_period = date(fecha_inicio.year, fecha_inicio.month, dias_periodo)
        res[fecha_inicio.strftime('%m/%Y')] = DIAS_LABORADOS((fecha_inicio.strftime(FORMAT), fecha_fin.strftime(FORMAT)),
                                                             (fecha_inicio.strftime('%Y-%m-01'), date_period.strftime(FORMAT)))
        fecha_inicio = date_period + timedelta(days=1)
        valor = (fecha_inicio - fecha_fin).days
    return res


def DIAS_LABORADOS(contract_id, period_id, format=FORMAT, DIAS_PERIODO=DIAS_PERIODO):
    """DEVUELVE LA INTERSECCIÓN EN DÍAS ENTRE LOS PERIODOS DADOS. LOS PERIODOS SON TUPLAS DE DOS FECHAS LA INICIAL Y FINAL"""
    date_start = max(DATE(period_id[0], format), DATE(contract_id[0], format))
    date_end = min(DATE(period_id[1], format), DATE(contract_id[1] or period_id[1], format))
    dias_periodo = DATE(period_id[1], format).day
    dias_laborados = max(0, (date_end - date_start).days + 1)
    return {'dias_periodo': DIAS_PERIODO or dias_periodo,
            'dias_laborados': int(round((DIAS_PERIODO or dias_periodo) * dias_laborados / float(dias_periodo)))}

def EDAD_ANIO(date_from, date_to=None, format=FORMAT):
    "DEVUELVE LA EDAD EN AÑOS PASANDO LAS FECHAS"
    date_from = DATE(date_from, format)
    date_to = DATE(date_to, format)
    if (date_from.month == date_to.month and date_to.day >= date_from.day) or (date_to.month > date_from.month):
        num = date_to.year - date_from.year
    else:
        num = date_to.year - date_from.year - 1
    return num

def DIAS_PERIODOS_INTERSECAN(periodo_contenido, periodo_contenedor, format=FORMAT):
    """
    DEVUELVE EL NUMERO DE DIAS QUE EL PERIODO CONTENIDO ESTA DENTRO DEL PERIODO CONTENEDOR 
    """
    from datetime import date, timedelta
        
    fecha_inicio_periodo_contenido = DATE(periodo_contenido[0], format)
    fecha_fin_periodo_contenido = DATE(periodo_contenido[1], format)
    
    dias_periodo = (fecha_fin_periodo_contenido - fecha_inicio_periodo_contenido).days
    
    periodo_inicio_contenedor = periodo_contenedor[0]
    periodo_fin_contenedor = periodo_contenedor[1]
    periodo_inicio_contenedor = periodo_inicio_contenedor.split(' ')[0]
    periodo_fin_contenedor = periodo_fin_contenedor.split(' ')[0]
        
    fecha_inicio_periodo_contenedor = DATE(periodo_inicio_contenedor, format)
    fecha_fin_periodo_contenedor = DATE(periodo_fin_contenedor, format)
    #fecha_fin_periodo_contenedor = fecha_fin_periodo_contenedor + timedelta(days=90)
    #print 'fecha_fin_periodo_contenedor ', fecha_fin_periodo_contenedor
    
    if fecha_fin_periodo_contenido < fecha_inicio_periodo_contenedor:
        """
            EL PERIODO CONTENIDO ESTA FUERA DEL PERIODO CONTENEDOR 
        """
        return 0
    
    if fecha_inicio_periodo_contenido > fecha_fin_periodo_contenedor:
        """
            EL PERIODO CONTENIDO ESTA FUERA DEL PERIODO CONTENEDOR 
        """
        return 0 
            
    
    #print ' fecha_fin_periodo_contenido ', fecha_fin_periodo_contenido
    #print ' fecha_inicio_periodo_contenedor ', fecha_inicio_periodo_contenedor
    #print ' fecha_fin_periodo_contenedor ', fecha_fin_periodo_contenedor
    
    # Si el periodo esta al inicio del permiso
    #if fecha_fin_periodo_contenido < fecha_fin_periodo_contenedor and fecha_fin_periodo_contenido > fecha_inicio_periodo_contenedor and fecha_inicio_periodo_contenido < fecha_inicio_periodo_contenedor:
    if fecha_inicio_periodo_contenedor >= fecha_inicio_periodo_contenido and fecha_inicio_periodo_contenedor <= fecha_fin_periodo_contenido and fecha_fin_periodo_contenedor >= fecha_fin_periodo_contenido:
        # print 'INICIO DEL PERIODO ', dias_periodo
        res_dias = (fecha_fin_periodo_contenido - fecha_inicio_periodo_contenedor).days
        if dias_periodo == 31:
            res_dias = res_dias - 1
        elif dias_periodo == 29:
            res_dias = res_dias + 1
        elif dias_periodo == 28:
            res_dias = res_dias + 2     
        return res_dias  
            
    # Si el permiso esta dentro del periodo
    #elif fecha_inicio_periodo_contenido < fecha_fin_periodo_contenedor and fecha_fin_periodo_contenido < fecha_fin_periodo_contenedor:
    elif fecha_inicio_periodo_contenedor > fecha_inicio_periodo_contenido and fecha_fin_periodo_contenedor < fecha_fin_periodo_contenido:     
        return (fecha_fin_periodo_contenedor - fecha_inicio_periodo_contenedor).days
    #si el periodo esta dentro del permiso
    elif fecha_inicio_periodo_contenedor < fecha_inicio_periodo_contenido and fecha_fin_periodo_contenedor > fecha_fin_periodo_contenido:
        res_dias = (fecha_fin_periodo_contenido - fecha_inicio_periodo_contenido).days
        if dias_periodo == 31:
            res_dias = res_dias - 1
        elif dias_periodo == 29:
            res_dias = res_dias + 1
        elif dias_periodo == 28:
            res_dias = res_dias + 2  
        return res_dias
    # Si el periodo esta al final del permiso
    #elif fecha_fin_periodo_contenedor < fecha_fin_periodo_contenido and fecha_inicio_periodo_contenedor < fecha_fin_periodo_contenedor and fecha_inicio_periodo_contenido > fecha_inicio_periodo_contenedor and fecha_fin_periodo_contenido > fecha_inicio_periodo_contenedor:
    elif  fecha_inicio_periodo_contenedor < fecha_inicio_periodo_contenido and fecha_fin_periodo_contenedor < fecha_fin_periodo_contenido:
        #print 'FIN DEL PERIODO'
        res_dias = (fecha_fin_periodo_contenedor - fecha_inicio_periodo_contenido).days 
        #print 'FIN PERDIO ', res_dias
        if dias_periodo == 31:
            res_dias = res_dias + 1
        elif dias_periodo == 29:
            res_dias = res_dias - 1
        elif dias_periodo == 28:
            res_dias = res_dias - 2 
        return res_dias
        
    else:
        #print 'EN NINGUN IF'
        return 0
        
        
 
def OBTIENE_DIAS_PERMISO_ENFERMEDAD(periodo_contenido, periodo_contenedor, hours_permission, format=FORMAT):
    """
    DEVUELVE EL NUMERO DE DIAS QUE EL PERIODO CONTENIDO ESTA DENTRO DEL PERIODO CONTENEDOR 
    """
    from datetime import date, timedelta
    
    fecha_inicio_periodo_contenido = DATE(periodo_contenido[0], format)
    fecha_fin_periodo_contenido = DATE(periodo_contenido[1], format)
    
    dias_periodo = (fecha_fin_periodo_contenido - fecha_inicio_periodo_contenido).days + 1
    
    fecha_inicio_periodo_contenedor = DATE(periodo_contenedor[0], format)
    fecha_inicio_periodo_contenedor = fecha_inicio_periodo_contenedor + timedelta(days=3)
    # print 'fecha_inicio_permiso ', fecha_inicio_periodo_contenedor
    fecha_fin_periodo_contenedor = DATE(periodo_contenedor[1], format)
    dias_permiso = hours_permission / 8
    fecha_fin_periodo_contenedor = fecha_fin_periodo_contenedor + timedelta(days=dias_permiso)
    # print 'fecha_fin_permiso ', fecha_fin_periodo_contenedor

    if fecha_fin_periodo_contenido < fecha_inicio_periodo_contenedor:
        """
            EL PERIODO CONTENIDO ESTA FUERA DEL PERIODO CONTENEDOR 
        """
        return 0
    
    if fecha_inicio_periodo_contenido > fecha_fin_periodo_contenedor:
        """
            EL PERIODO CONTENIDO ESTA FUERA DEL PERIODO CONTENEDOR 
        """
        return 0 
    
    # Si el permiso está entre dos periodos del rol de pagos
    if fecha_fin_periodo_contenedor > fecha_fin_periodo_contenido:
        # Si esta entre el periodo del rol de pagos y el siguiente periodo.
        return 0;
    elif fecha_fin_periodo_contenedor > fecha_inicio_periodo_contenido and fecha_inicio_periodo_contenedor < fecha_inicio_periodo_contenido:
        # Si está entre el periodo del rol de pagos y el anterior periodo        
        res_dias = (fecha_fin_periodo_contenedor - fecha_inicio_periodo_contenedor).days + 1
        return res_dias
        
    elif fecha_fin_periodo_contenedor < fecha_fin_periodo_contenido and fecha_inicio_periodo_contenedor > fecha_inicio_periodo_contenido:
        # Si el permiso está incluido en el periodo del rol de pagos
        res_dias = (fecha_fin_periodo_contenedor - fecha_inicio_periodo_contenedor).days + 1
        return res_dias
    else:
        return 0
    
