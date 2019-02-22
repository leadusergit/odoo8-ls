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
from csv import reader, writer

def csv2xml(model, path, id=None, out_path=None, delimiter=','):
    spamreader = reader(open(path, 'rb'), delimiter=delimiter)
    out_path = out_path or (path.rpartition('/')[0] + '/')
    file = open(out_path + model.replace('.', '_') + '.xml', 'w')
    fields = []
    file.write('''<?xml version="1.0" encoding="utf-8"?>
<openerp>
    <data noupdate="True">
    ''')
    for index, row in enumerate(spamreader):
        if not fields:
            fields = row
            continue
        file.write('''
        <record model="%s" id="%s">'''%(model, (id or model.replace('.', '_')) + str(index)))
        for ind, field in enumerate(fields):
            value = ' '.join(row[ind].split())
            if row[ind]:
                if field.count('.'):
                    file.write('''
            <field name="{1}" {2}="{0}"/>'''.format(value, *field.split('.')))
                    continue
                file.write('''
            <field name="%s">%s</field>'''%(field, value))
        file.write('''
        </record>
        ''')
    file.write('''
    </data>
</openerp>''')
    file.close()
    
def parent_identificator(path, out_path=None, delimiter=','):
    out_path = out_path or (path.rpartition('/')[0] + '/cuentas_parent.csv')
    file = open(out_path, 'w')
    spamwriter = writer(file, delimiter=delimiter)
    spamreader = reader(open(path, 'rb'), delimiter=delimiter)
    fields = []
    parents = {}
    for index, aux in enumerate(spamreader):
        if not fields:
            fields = aux
            spamwriter.writerow(['id'] + fields + ['parent_id', 'type', 'user_type'])
            continue
        val = ['account_account_' + str(index)]
        for ind, field in enumerate(fields):
            if field == 'code':
                code = aux[ind] if aux[ind][-1] != '.' else aux[ind][:-1]
                type = 'other' if aux[ind][-1] != '.' else 'view'
                user_type = 'account_type_cash' if aux[ind][-1] != '.' else 'account_type_view'
            val.append(aux[ind])
        parents[code] = val[0]
        val.extend([parents.get(code.rpartition('.')[0], ''), type, user_type])
        spamwriter.writerow(val)
    file.close()