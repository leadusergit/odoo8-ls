# -*- coding: UTF-8 -*-
###################################################
#
#    HHRR Module
#    Copyright (C) 2011-2011 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
#    $autor: Dairon Medina Caro<dairon07@inbox.com>
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
from math import *

class formula_parser(object):
    '''
    Clase para evaluar formulas matemáticas
    '''
    formula=''

    functions = {'__builtins__':None};

    variables = {'__builtins__':None};

    def __init__(self):
        '''
        Constructor
        '''

    def evaluate(self):
        '''
        Evaluar la formula pasada en la variable formula.
        '''
        return eval(self.formula, self.variables, self.functions);

    def addDefaultVariables(self):
        '''
        Agregar variables predefinidas.
        '''
        self.variables['e']=e
        self.variables['pi']=pi

    def getVariableNames(self):
        '''
        Devuelve una lista de las variables definidas.
        '''
        mylist = list(self.variables.keys())
        try:
            mylist.remove('__builtins__')
        except ValueError:
            pass
        mylist.sort()
        return mylist


    def getFunctionNames(self):
        '''
        Devuelve una lista de los metodos definidos.
        '''
        mylist = list(self.functions.keys())
        try:
            mylist.remove('__builtins__')
        except ValueError:
            pass
        mylist.sort()
        return mylist
