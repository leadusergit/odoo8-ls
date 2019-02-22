# -*- encoding: utf-8 -*-
##############################################################################
#
#    Reporting
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
#Creado por *EG

import time
import wizard

dates_form = '''<?xml version="1.0"?>
<form string="Select Period">
    <field name="date1"/>
    <field name="date2"/>
</form>'''

dates_fields = {
    'date1': {'string':'Start of Period', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-01-01')},
    'date2': {'string':'End of Period', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-%d')},
}


class wiz_analytic(wizard.interface):
    states = {
        'init': {
            'actions': [], 
            'result': {'type':'form', 'arch':dates_form, 'fields':dates_fields, 'state':[('end','Cancel'), ('report','print')]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'analytic.plans', 'state':'end'}
        }
    }
wiz_analytic('analytic.plans.report')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

