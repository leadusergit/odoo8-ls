# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author :  Cristian Salamea cristian.salamea@gnuthink.com
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

import time
from openerp import pooler
from openerp.report import report_sxw
import re


class account_retention_obj(report_sxw.rml_parse):
     
    def _user(self):
        user = pooler.get_pool(self.cr.dbname).get('res.users').browse(self.cr, self.uid, self.uid)
        return user.name
    
    def direccion(self, obj):
        #print 'direccion'
        dir = ' '
        #print 'dir ',dir
        if obj:
            dir += str(obj.street.encode('UTF-8'))
            #print 'dir 2 ',dir
            if dir:
                if obj.street2:
                    dir += ' y '+str(obj.street2.encode('UTF-8'))
        return dir
    
    def _anio(self, obj):        
        return obj.name.split(" ")[-1]
    
    #Funcion que separa el punto en lugar de comas y pone a 2 decimales las cantidades
    def comma_me(self,amount):
        
        #print ' FORMATO a ret **** '
        if not amount:
            amount = 0.0
        if type(amount) is float:
            #print ' FORMATO b ret **** '
            amount = str('%.2f'%amount)
        else :
            #print ' FORMATO c ret **** '
            amount = str('%.2f'%amount)
        if (amount == '0'):
            return ' '
        orig = amount
        new = re.sub("^(-?\d+)(\d{3})", "\g<1>,\g<2>", amount)
        if orig == new:
            return new
        else:
            return self.comma_me(new)
    
    

    def __init__(self, cr, uid, name, context):
        #print ' INVOICE RETENTION '
        super(account_retention_obj, self).__init__(cr, uid, name, context)
        self.localcontext.update({
                 'user': self._user,
                 'direccion': self.direccion,    
                 'anio':self._anio,
                 'formato':self.comma_me        
                 })
        self.context = context
        

report_sxw.report_sxw('report.account.retention.obj', 'account.invoice_retention_obj', 'addons/account_invoice_retention/report/account_retention_obj.rml', parser=account_retention_obj, header=False)
