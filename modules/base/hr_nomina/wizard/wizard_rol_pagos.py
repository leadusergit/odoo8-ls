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
from openerp.osv import osv, fields
from xlrd import open_workbook
from xlwt import easyxf, Formula
from xlutils.copy import copy
from datetime import datetime
import cStringIO, openerp.modules as addons, base64, time

def GET_LETTER(index):
    COLUMNS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    aux = index / len(COLUMNS)
    aux2 = index - (aux * len(COLUMNS))
    return (aux and COLUMNS[aux-1] or '') + COLUMNS[aux2]

def get_style(bold=False, font_name='Calibri', height=12, font_color='black',
              rotation=0, align='center',
              border=True, color=None, format=None):
    str_style = 'font: bold %s, name %s, height %s, color %s;'%(bold, font_name, height*20, font_color)
    str_style += 'alignment: rotation %s, horizontal %s, vertical center, wrap True;'%(rotation, align)
    str_style += border and 'border: left thin, right thin, top thin, bottom thin;' or ''
    str_style += color and 'pattern: pattern solid, fore_colour %s;'%color or ''
    return easyxf(str_style, num_format_str = format)

class _Report_Rol_Pagos(osv.osv_memory):
    _name = "report.pay.roll"
    _columns = {
        'file':fields.binary('Archivo'),
        'file_name':fields.char('Nombre Archivo',size=64),
        'period_id':fields.many2one('hr.contract.period','Período',required=True),
        'departament_id':fields.many2one('hr.department','Departamento'),
        'category_ids':fields.many2many('hr.employee.category', string='Etiquetas'),
        'employee_id':fields.many2one('hr.employee','Empleado'),
        'ingresos_ids':fields.many2many('hr.adm.incomes','hr_ingresos_relation','report_id','ingreso_id'),
        'egresos_ids':fields.many2many('hr.expense.type','hr_egresos_relation','report_id','egreso_id'),
        'provisiones_ids':fields.many2many('hr.provision.type','hr_provision_relation','report_id','provision_id'),
        'ingresos':fields.boolean('Ingresos'),
        'egresos':fields.boolean('Egresos'),
        'provisiones':fields.boolean('Provisiones')
    }
    
    def _get_default_period(self, cr, uid, context):
        period_name = time.strftime('%m/%Y')
        period_id = self.pool.get('hr.contract.period').search(cr, uid, [('name', '=', period_name)], limit=1)
        return bool(period_id) and period_id[0]
    
    _defaults = {  
        'period_id': _get_default_period,
        'ingresos': lambda *a: True,
        'egresos': lambda *a: True
    }
    
    def adm_incomes(self, cr, uid, adm_incomes_ids, payroll_ids):
        adm_model = self.pool.get('hr.adm.incomes')
        adm_incomes_ids = adm_incomes_ids or adm_model.search(cr, uid, [])
        cr.execute('SELECT DISTINCT(adm_id) FROM hr_income '
                   'WHERE payroll_id=ANY(%s) AND adm_id=ANY(%s)', (payroll_ids, adm_incomes_ids))
        adm_incomes_ids = [aux[0] for aux in cr.fetchall()]
        return adm_model.read(cr, uid, adm_incomes_ids, ['payroll_label'])
    
    def adm_expenses(self, cr, uid, adm_expenses_ids, payroll_ids):
        adm_model = self.pool.get('hr.expense.type')
        adm_expenses_ids = adm_expenses_ids or adm_model.search(cr, uid, [])
        cr.execute('SELECT DISTINCT(expense_type_id) FROM hr_expense '
                   'WHERE payroll_id=ANY(%s) AND expense_type_id=ANY(%s)', (payroll_ids, adm_expenses_ids))
        adm_expenses_ids = [aux[0] for aux in cr.fetchall()]
        return adm_model.read(cr, uid, adm_expenses_ids, ['name'])
    
    def adm_provisions(self, cr, uid, adm_provisions_ids, payroll_ids):
        adm_model = self.pool.get('hr.provision.type')
        adm_provisions_ids = adm_provisions_ids or adm_model.search(cr, uid, [])
        adm_provisions_ids = adm_model.browse(cr, uid, adm_provisions_ids)
        adm_provisions_ids = dict((aux.field_name, aux) for aux in adm_provisions_ids)
        res = []
        for field_name in adm_provisions_ids.iterkeys():
            cr.execute('SELECT sum('+ field_name.name +') FROM hr_provision '
                       'WHERE payroll_id=ANY(%s)', (payroll_ids,))
            if cr.fetchone()[0]:
                res.append(adm_provisions_ids[field_name])
        return res
    
    def get_search_args(self, wizard):
        args = []
        if wizard.employee_id:
            args.append(('employee_id','=',wizard.employee_id.id))
        if wizard.category_ids:
            category_ids = [aux.id for aux in wizard.category_ids]
            args.append(('employee_id.category_ids','in',category_ids))    
        return args
    
    def get_sheet(self, cr, uid, ids, context=None):
        """RETORNA LA HOJA CON EL FORMATO PROPIO DE CADA IMPLEMENTACIÓN"""
        path_book = addons.get_module_resource('hr_nomina','data','Formato_Rol.xls')
        format_book = open_workbook(path_book, formatting_info = True, on_demand= True)
        book = copy(format_book)
        path_image = addons.get_module_resource('hr_nomina', 'image', 'company_logo.bmp')
        sheet = book.get_sheet(0)
        sheet.insert_bitmap(path_image, 0, 0, scale_x=0.254390934844193, scale_y=0.264448336252189)
        return book, sheet, 3

    def report_payroll(self,cr,uid,ids, context=None):
        book, sheet, aux_col = self.get_sheet(cr, uid, ids, context)
        for wizard in self.browse(cr,uid,ids):
            args = [('period_id','=',wizard.period_id.id)]
    
            args.extend(self.get_search_args(wizard))
            datos_ids = self.pool.get('hr.payroll').search(cr, uid, args, order='employee')
                
            col = aux_col
            adm_incomes_ids = [aux.id for aux in wizard.ingresos_ids]
            for tipo in self.adm_incomes(cr, uid, adm_incomes_ids, datos_ids):
                if (wizard.ingresos==True):
                    sheet.write(4, col, tipo['payroll_label'], get_style(height=8))
                    sheet.write(5, col, 'I', get_style(height=8))
                    col += 1
            if (wizard.ingresos==True and wizard.egresos==True and wizard.provisiones==True) or wizard.ingresos==True:
                sheet.write(4, col, 'TOTAL INGRESOS',get_style(height=8))
                col += 1
            adm_expenses_ids = [aux.id for aux in wizard.egresos_ids]
            for tipo in self.adm_expenses(cr, uid, adm_expenses_ids, datos_ids):
                if (wizard.egresos==True):
                    sheet.write(4, col, tipo['name'], get_style(height=8))
                    sheet.write(5, col, 'E', get_style(height=8))
                    col += 1
            if (wizard.egresos==True and wizard.egresos==True and wizard.egresos==True) or wizard.egresos==True:
                sheet.write(4, col, 'TOTAL EGRESOS',get_style(height=8))
                col += 1
                
            adm_provisions_ids = [aux.id for aux in wizard.provisiones_ids]
            for tipo in self.adm_provisions(cr, uid, adm_provisions_ids, datos_ids):
                if (wizard.provisiones==True):
                    sheet.write(4, col, tipo.name, get_style(height=8))
                    sheet.write(5, col, 'P', get_style(height=8))
                    col += 1
            if (wizard.ingresos==True and wizard.egresos==True) or wizard.provisiones==True:
                sheet.write(4, col, 'TOTAL A RECIBIR',get_style(height=8))
                
            
            fila = 6
            
            for payroll in self.pool.get('hr.payroll').browse(cr,uid,datos_ids):
                if (wizard.departament_id.id and wizard.departament_id.id == payroll.employee_id.department_id.id) or not wizard.departament_id:
                    col=3
                    sheet.write(fila,0, fila-5, get_style(height=8)) 
                    sheet.write_merge(fila,fila,1,2, payroll.employee, get_style(height=8,align='left'))
                    incomes = dict([(aux.adm_id.id, aux.value) for aux in payroll.incomes_ids])
                    for tipo_id in self.adm_incomes(cr, uid, adm_incomes_ids, datos_ids):
                        if (wizard.ingresos==True):
                            sheet.write(fila, col, incomes.get(tipo_id['id'], 0.0), get_style(height=8,format='0.00'))
                            col += 1
                    if (wizard.ingresos==True and wizard.egresos==True and wizard.provisiones==True) or wizard.ingresos==True:
                        sheet.write(fila, col, payroll.total_ingresos,get_style(height=8,format='0.00'))
                        col += 1
                    expenses = dict([(aux.expense_type_id.id, aux.value) for aux in payroll.expenses_ids])
                    for tipo_id in self.adm_expenses(cr, uid, adm_expenses_ids, datos_ids):
                        if (wizard.egresos==True):
                            sheet.write(fila, col, expenses.get(tipo_id['id'], 0.0), get_style(height=8,format='0.00'))
                            col+=1
                    if (wizard.ingresos==True and wizard.egresos==True and wizard.provisiones==True) or wizard.egresos==True:
                        sheet.write(fila, col, payroll.total_egresos,get_style(height=8,format='0.00'))
                        col += 1
                    provisions = self.pool.get('hr.provision').read(cr, uid, [aux.id for aux in payroll.provisiones_id])
                    for tipo_id in self.adm_provisions(cr, uid, adm_provisions_ids, datos_ids):
                        if (wizard.provisiones==True):
                            sheet.write(fila, col, provisions[0][tipo_id.field_name.name], get_style(height=8,format='0.00'))
                            col+=1
                    if (wizard.ingresos==True and wizard.egresos==True) or wizard.provisiones==True :
                        sheet.write(fila, col, payroll.total,get_style(height=8,format='0.00'))
                        col+=1
                    fila+=1                    
                sheet.write_merge(fila,fila,1,2,'TOTAL',get_style(height=8))    
            for col in range(3, col):
                sheet.write(fila, col, Formula('SUM(%s7:%s%s)'%(GET_LETTER(col), GET_LETTER(col), fila)),get_style(True,height=8,format='#,###.00'))
            
            buf = cStringIO.StringIO()
            book.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            period_date = datetime.strptime(wizard.period_id.name, '%m/%Y')
            name = period_date.strftime('NÓMINA DE EMPLEADOS DE %B DEL %Y').upper()
        return self.pool.get('base.file.report').show(cr, uid, out, name + '.xls')
        
_Report_Rol_Pagos()
    