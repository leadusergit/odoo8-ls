# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Asset work
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
#creador  *EG
# import wizard
import cStringIO
import base64
import StringIO
import csv
import openerp.pooler
import time
import openerp.netsvc
from openerp.osv import fields, osv
import mx.DateTime
from mx.DateTime import RelativeDateTime
import openerp.tools
import datetime
import xlwt as pycel #Libreria que Exporta a Excel
from openerp.tools import config


class wizard_payment_transfer_excel(osv.osv_memory):
    _name = "wizard.payment.transfer.excel"
    _description = 'Archivo de Cash' 
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    def _get_company(self, cr, uid, context={}):
        users_obj = self.pool.get('res.users')
        user = users_obj.browse(cr, uid, uid, context)
        return user.company_id.id
    
    def _get_cuenta(self, cr, uid, context={}):
        cuenta = ''
        users_obj = self.pool.get('res.users')
        user = users_obj.browse(cr, uid, uid, context)
        partner_obj = self.pool.get('res.partner')
        partner_info = partner_obj.browse(cr, uid, user.company_id.partner_id.id)
        if partner_info.bank_ids:
            for x in partner_info.bank_ids:
                cuenta = x.acc_number or ''
                if cuenta:
                    break
        return cuenta
    
    def query_group(self, cr, uid, context=None):
        ##print 'context',context
        result = []
        cr.execute("""select partner, sum(amount_total) as total 
                        from invoice_line_transfer
                        where transfer_id = %s 
                        group by partner
                        """, (context.get('active_id'),)
                        )
        
        result = cr.dictfetchall()
        
        return result
    
    def on_change_tipo(self, cr, uid, ids, tipo):
        res = {'value':{}}
        if tipo in ('RP', 'PR', 'PO', 'RU'):
            res['value'] = {'referencia':'PAGO'}
        else:
            res['value'] = {'referencia':'COBRO'}
        return res
    
    
    def get_info_employee(self, cr, uid, ids, context):
        #detalle.append({'partner':x.partner,
        #                        'total':x.amount_total,
        #                        'identificacion':x.account_mov_id and x.account_mov_id.move_id and x.account_mov_id.move_id.no_comp or '',
        #                        'ref':x.account_mov_id and x.account_mov_id.move_id and x.account_mov_id.move_id.name or ''  })
        #print 'context', context
        hr_payroll_obj = self.pool.get('hr.payroll')
        hr_payrolls_data = hr_payroll_obj.browse(cr, uid, context.get('actives_id'))
        detalle = []
        for hr_payroll_data in hr_payrolls_data:
            vals = {'partner':hr_payroll.employee_id, 'total':hr_payroll_data.total,
                    'identificacion':'ORDEN 1', 'ref':'ROL DE PAGOS'}
            detalle.append(vals)  
        
        return detalle
    
        
    def get_info_destinatario(self, cr, uid, ids, item, context):
        
        hr_employee_obj = self.pool.get('hr.employee')
        
        employee_data = hr_employee_obj.browse(cr, uid, item.get('partner'))
        
        if employee_data.modo_pago == 'transferencia':
            if not employee_data.bank_account_id:
                raise osv.except_osv("Inconsistencia", 'El empleado ' + employee_data.name + ' no tiene cuenta contable registrada ')
            else:
                cuenta = 'CU'
                concta += 1
            
    def validacion_cuentas_repetidas(self, cr, uid, ids):
        
        hr_employee_obj = self.pool.get('hr.employee')
        
        query = "select count(1) as num, bank_account_id as bank_account_id \
            from hr_employee \
            where bank_account_id is not null \
            and state_emp = 'active' \
            group by bank_account_id \
            having count(1) > 1"
        
        ##print ' query ', query
        cr.execute(query)
        
        resultados = cr.dictfetchall()
        cadena = ''
        for resultado in resultados:
            bank_account_id = resultado['bank_account_id']
            hr_employee_ids = hr_employee_obj.search(cr, uid, [('bank_account_id', '=', bank_account_id)])
            hr_employees_data = hr_employee_obj.read(cr, uid, hr_employee_ids, ['name'])
            ##print ' validacion de cuentas ', hr_employees_data
            cadena += '(' 
            for hr_employee_data in hr_employees_data:
                cadena += hr_employee_data['name'] + ' , ' + '\n'
            
            cadena += ')'
            
        if cadena != '':
            raise osv.except_osv("Cuentas Repetidas", ' Estos empleados tienen la misma cuenta bancaria: ' + '\n' + cadena)
                

    
    def get_data_payroll(self, cr, uid, ids, context):
        
        hr_proceso_remuneracion_obj = self.pool.get('hr.proceso.remuneracion')
        procesos_remuner_data = hr_proceso_remuneracion_obj.read(cr, uid, context.get('active_ids'), ['remuneraciones_id'])
        res = []
        for proc in procesos_remuner_data:
            res.extend(proc['remuneraciones_id'])
        #print ' res ', res
        return res
        
    
    
    
    def act_generate_excel_nomina(self, cr, uid, ids, context=None):
        wb = pycel.Workbook(encoding='utf-8')
        if context is None:
            context = {}
        
        data = {}
        data['form'] = self.read(cr, uid, ids)[0]
        form = data['form']
        
        #print "form", form
        #print "context", context
        
        #Formato de la Hoja de Excel
#        style_cabecera = pycel.easyxf('font: colour black, bold True;'
#                                        'align: vertical center, horizontal center;'
#                                        )
            
        style_cabecerader = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal right;'
                                    )
        
        style_cabeceraizq = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal left;'
                                    )
        
        style_vertical = pycel.easyxf('font: bold True;'
                                     'align: rotation +90,vertical center, horizontal center;'
                                     'borders: left 1, right 1, top 1, bottom 1;'
                                  )
        
        style_cabecera = pycel.easyxf('font: colour white, bold True;'
                                    'align: vertical center, horizontal right;'
                                    'pattern: pattern solid, fore_colour ocean_blue;'
                                    )
        
        style_header = pycel.easyxf('font: colour white, bold True;'
                                    'align: vertical center, horizontal center;'
                                    'borders: left 1, right 1, top 1, bottom 1;'
                                    'pattern: pattern solid, fore_colour ocean_blue;')
        
        
        linea = pycel.easyxf('borders:bottom 1;')
        
        linea_center = pycel.easyxf('font: colour black;'
                                   'align: vertical center, horizontal center;'
                                   )
        
        linea_izq = pycel.easyxf('font: colour black;'
                                   'align: vertical top, horizontal left,wrap true;'
                                   'borders: left 1, right 1, top 1, bottom 1;'
                                   )
        linea_der = pycel.easyxf('font: colour black;'
                                 'align: vertical top, horizontal right,wrap true;'
                                  )

        ws = wb.add_sheet("Transferencia")
        #ws.panes_frozen = True
        #ws.horz_split_pos = 8
        #ws.vert_split_pos = 3
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresión: &D Hora: &T&RPágina &P de &N"
        ws.footer_str = u"" 
        x0 = 11
        #sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)
        
        hr_payroll_obj = self.pool.get('hr.payroll')
        
        ws.fit_num_pages = 1
        ws.fit_height_to_pages = 0
        ws.fit_width_to_pages = 1
        #ws.paper_size_code = 1
        ws.portrait = 1
        
        align = pycel.Alignment()
        align.horz = pycel.Alignment.HORZ_CENTER
        align.vert = pycel.Alignment.VERT_CENTER
        
        font1 = pycel.Font()
        font1.colour_index = 0x0
        
        #Formato de Numero
        style = pycel.XFStyle()
        style.alignment = align
        style.font = font1
        
        #ws.insert_bitmap('banco_pacifico.bmp', 2, 0)

        ws.write_merge(2, 3, 3, 8, u'TRANSFERENCIAS INTERBANCARIAS')
        
        ws.write_merge(4, 4, 0, 2, u'Empresa', style_cabecera)
        ws.write_merge(4, 4, 3, 4, u'Coviprov S.A.', linea_izq)
        
        ws.write_merge(5, 5, 0, 2, u'SERVICIO', style_cabecera)
        ws.write_merge(5, 5, 3, 4, form.get('type') or '', linea_izq)
        
        ws.write_merge(6, 6, 0, 2, u'FECHA DE PROCESO', style_cabecera)
        ws.write_merge(6, 6, 3, 4, form.get('fecha_proceso') or '', linea_izq)
        
        ws.write_merge(7, 7, 0, 2, u'FECHA DE VENCIMIENTO', style_cabecera)
        ws.write_merge(7, 7, 3, 4, form.get('fecha_vencimiento') or '', linea_izq)
        
        ws.write_merge(4, 4, 5, 6, u'TIPO DE CTA(Emp.)', style_cabecera)
        ws.write_merge(4, 4, 7, 8, form.get('tipo_cuenta') or '', linea_izq)
        ws.write_merge(5, 5, 5, 6, u'NUMERO DE CTA(Emp.)', style_cabecera)
        ws.write_merge(5, 5, 7, 8, form.get('nro_cuenta') or '', linea_izq)
        ws.write_merge(6, 6, 5, 6, u'REFERENCIA', style_cabecera)
        ws.write_merge(6, 6, 7, 8, form.get('referencia') or '', linea_izq)
        ws.write_merge(7, 7, 5, 6, u'NOMBRE ARCHIVO', style_cabecera)
        if form.get('name'):
            name = form.get('name') + '.xls'
        else:
            name = form.get('name') or 'archivo.xls'
        ws.write_merge(7, 7, 7, 8, name, linea_izq)
        
        x0 = 0
        x2 = 10
        ws.write(x2, x0, u'Forma Pag/Cob', style_header)
        x0 += 1
        ws.write(x2, x0, u'Banco', style_header)
        x0 += 1
        ws.write(x2, x0, u'Tip.Cta/Che', style_header)
        x0 += 1
        ws.write(x2, x0, u'Num.Cta/Che', style_header)
        x0 += 1
        ws.write(x2, x0, u'Valor', style_header)
        x0 += 1
        ws.write(x2, x0, u'Identificación', style_header)
        x0 += 1
        ws.write(x2, x0, u'Tip.Doc.', style_header)
        x0 += 1
        ws.write(x2, x0, u'NUC', style_header)
        x0 += 1
        ws.write(x2, x0, u'Beneficiario', style_header)
        x0 += 1
        ws.write(x2, x0, u'Teléfono', style_header)
        x0 += 1
        ws.write(x2, x0, u'Referencia', style_header)
        #x0 += 1
        #ws.write(x2, x0, u'Base Imponible', style_header)
        
        destinatario_obj = self.pool.get('res.partner')
        res_partner_bank_obj = self.pool.get('res.partner.bank')
        detalle = []
        if form.get('group_by') == 'by_partner':
            detalle = self.query_group(cr, uid, context)
        else:
            self.validacion_cuentas_repetidas(cr, uid, ids)
           
            if form['type'] == 'RPS':
                payrolls_data = hr_payroll_obj.browse(cr, uid, context.get('active_ids'))
            elif form['type'] == 'RPP':
                payrolls_data = hr_payroll_obj.browse(cr, uid, self.get_data_payroll(cr, uid, ids, context))
            else:
                raise osv.except_osv("Configuracion", 'Debe escoger Primera o Segunda Quincena')
                
                
            
            for payroll_data in payrolls_data:
                detalle.append(
                    {'partner':payroll_data.employee_id,
                     'total':payroll_data.total,
                     'identificacion':'ORDEN 1',
                     'ref':'ROL DE PAGOS',
                     'payment_type':payroll_data.employee_id.modo_pago,
                     'bank_ids':payroll_data.employee_id.bank_account_id,
                     'ident_type':payroll_data.employee_id.tipoid,
                     'ident_num':payroll_data.employee_id.identification_id,
                     'name':payroll_data.employee_id.name,
                     }
                )
                
                empleado = payroll_data.employee_id
                if not payroll_data.employee_id.modo_pago:
                    raise osv.except_osv("Configuracion", 'El empleado ' + empleado.last_name + ' ' + empleado.name + ' no tiene configurado el modo de pago')
                else:
                    if payroll_data.employee_id.modo_pago == 'transferencia':
                        if not payroll_data.employee_id.bank_account_id:
                            raise osv.except_osv("Configuracion", 'El empleado ' + empleado.last_name + ' ' + empleado.name + ' no tiene configurado la cuenta bancaria')
                
                
                
        if detalle:
            xm = 11
            total = 0.00
            totalcta = 0.00
            totalchq = 0.00
            totalefe = 0.00
            totalre = 0.00
            totalsn = 0.00
            
            concta = 0
            contchq = 0
            contefe = 0
            contre = 0
            contsn = 0
            
            for item in detalle:
                xf = 0
                
                if item['payment_type'] == 'transferencia':
                    cuenta = 'CU'
                    concta += 1
                    totalcta += item.get('total')
                elif item['payment_type'] == 'cheque':
                    cuenta = 'CH'
                    contchq += 1
                    totalchq += item.get('total')
                elif item['payment_type'] == 'EFE':
                    cuenta = 'EF'
                    contefe += 1
                    totalefe += item.get('total')
                else:
                    cuenta = ''
                    contsn += 1
                    totalsn += item.get('total')
                #Cuenta
                ws.write(xm, xf, cuenta, linea_izq)
                
                #Banco
                xf += 1
                banco = ''
                cuenta = ''
                nro_cuenta = ''
                
                if item['bank_ids']:
                    info_banco = item['bank_ids'] 
                    banco = info_banco.res_bank_id and info_banco.res_bank_id.code 
                    nro_cuenta = info_banco.name
                    
                    if info_banco.type == 'cte':
                        cuenta = '00' 
                    else:
                        cuenta = '10'
                        
                
                ws.write(xm, xf, banco, linea_izq)
                #Tip.Cta/Che
                xf += 1
                ws.write(xm, xf, cuenta, linea_izq)
                #Nro Cuenta
                xf += 1
                ws.write(xm, xf, nro_cuenta, linea_izq)
                #Valore
                xf += 1
                ws.write(xm, xf, item.get('total'), linea_izq)
                total += item.get('total')
                #Identificacion
                xf += 1
                #ws.write(xm,xf,destinatario_info.ref, linea_izq)
                ws.write(xm, xf, item.get('identificacion'), linea_izq)
                #Tipo Documento
                xf += 1
                identificacion = ''
                if item['ident_type'] == 'c':
                    identificacion = 'C'
                elif item['ident_type'] == 'r':
                    identificacion = 'R'
                elif item['ident_type'] == 'p':
                    identificacion = 'P'
                elif item['ident_type'] == 's':
                    identificacion = 'X'
                else:
                    identificacion = 'X'
                
                ws.write(xm, xf, identificacion, linea_izq)
                
                #Ruc
                xf += 1
                ws.write(xm, xf, item['ident_num'], linea_izq)
                
                #Beneficiario
                xf += 1
                ws.write(xm, xf, item['name'], linea_izq)
                
                #Telefono
                xf += 1
                telefono = ''    
                ws.write(xm, xf, telefono, linea_izq)
                xf += 1
                ws.write(xm, xf, item.get('ref'), linea_izq)
                xm += 1
                
                xi = xf
                xj = xm
                #
            
            #Subtotales
            xm = xj + 1
            xf = 1
            ws.write(xm, xf, 'SUBTOTALES', linea_izq)
            xf = 1
            xm += 1
            ws.write(xm, xf, 'TOTAL', linea_izq)
            xf += 1
            ws.write(xm, xf, 'FORMA', linea_izq)
            xf += 1
            ws.write(xm, xf, 'CANT.', linea_izq)
            
            xm += 1
            
            
            if concta:
                xf = 1
                ws.write(xm, xf, 'USD', linea_izq)
                xf += 1
                ws.write(xm, xf, 'CU', linea_izq)
                xf += 1
                ws.write(xm, xf, concta, linea_izq)
                xf += 1
                ws.write(xm, xf, totalcta, linea_izq)
                xm += 1
            if contchq:
                xf = 1
                ws.write(xm, xf, 'USD', linea_izq)
                xf += 1
                ws.write(xm, xf, 'CH', linea_izq)
                xf += 1
                ws.write(xm, xf, contchq, linea_izq)
                xf += 1
                ws.write(xm, xf, totalchq, linea_izq)
                xm += 1
            if contefe:
                xf = 1
                ws.write(xm, xf, 'USD', linea_izq)
                xf += 1
                ws.write(xm, xf, 'EF', linea_izq)
                xf += 1
                ws.write(xm, xf, concta, linea_izq)
                xf += 1
                ws.write(xm, xf, totalefe, linea_izq)
                xm += 1
            if contre:
                xf = 1
                ws.write(xm, xf, 'USD', linea_izq)
                xf += 1
                ws.write(xm, xf, 'RE', linea_izq)
                xf += 1
                ws.write(xm, xf, contre, linea_izq)
                xf += 1
                ws.write(xm, xf, totalre, linea_izq)
                xm += 1
            
            if contsn:
                xf = 1
                ws.write(xm, xf, 'USD', linea_izq)
                xf += 1
                ws.write(xm, xf, 'OTRO', linea_izq)
                xf += 1
                ws.write(xm, xf, contsn, linea_izq)
                xf += 1
                ws.write(xm, xf, totalsn, linea_izq)
                xm += 1
                    
            xm += 1
            xf = 1
            ws.write(xm, xf, 'TOTAL GENERAL', linea_izq)
            xf += 1
            ws.write(xm, xf, 'DOLARES', linea_izq)
            xf += 1
            ws.write(xm, xf, concta + contchq + contefe + contre + contsn, linea_izq)
            xf += 1
            ws.write(xm, xf, total, linea_izq)
            
        ws.col(1).width = 5000 #codigo                       
        buf = cStringIO.StringIO()
        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'data':out, 'name':name})





    def act_generate_excel(self, cr, uid, ids, context=None):
        wb = pycel.Workbook(encoding='utf-8')
        if context is None:
            context = {}
        
        data = {}
        data['form'] = self.read(cr, uid, ids)[0]
        form = data['form']
        ##print "form", form
        ##print "context", context
        
        #Formato de la Hoja de Excel
#        style_cabecera = pycel.easyxf('font: colour black, bold True;'
#                                        'align: vertical center, horizontal center;'
#                                        )
            
        style_cabecerader = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal right;'
                                    )
        
        style_cabeceraizq = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal left;'
                                    )
        
        style_vertical = pycel.easyxf('font: bold True;'
                                     'align: rotation +90,vertical center, horizontal center;'
                                     'borders: left 1, right 1, top 1, bottom 1;'
                                  )
        
        style_cabecera = pycel.easyxf('font: colour white, bold True;'
                                    'align: vertical center, horizontal right;'
                                    'pattern: pattern solid, fore_colour ocean_blue;'
                                    )
        
        style_header = pycel.easyxf('font: colour white, bold True;'
                                    'align: vertical center, horizontal center;'
                                    'borders: left 1, right 1, top 1, bottom 1;'
                                    'pattern: pattern solid, fore_colour ocean_blue;')
        
        
        linea = pycel.easyxf('borders:bottom 1;')
        
        linea_center = pycel.easyxf('font: colour black;'
                                   'align: vertical center, horizontal center;'
                                   )
        
        linea_izq = pycel.easyxf('font: colour black;'
                                   'align: vertical top, horizontal left,wrap true;'
                                   'borders: left 1, right 1, top 1, bottom 1;'
                                   )
        linea_der = pycel.easyxf('font: colour black;'
                                 'align: vertical top, horizontal right,wrap true;'
                                  )

        ws = wb.add_sheet("Transferencia")
        #ws.panes_frozen = True
        #ws.horz_split_pos = 8
        #ws.vert_split_pos = 3
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresión: &D Hora: &T&RPágina &P de &N"
        ws.footer_str = u"" 
        x0 = 11
        #sintaxis write_merge(fila_inicio, fila_fin, columna_inicio, colunma_fin)
        
        
        transfer_payment_obj = self.pool.get('payment.transfer')
        
        transfer_payment_line_obj = self.pool.get('payment.transfer.line')
        
        transfer_payment_info = transfer_payment_obj.browse(cr, uid, context.get('active'))
        
        payment_transfer_obj = self.pool.get('payment.transfer.payment')
        
        payment_transfer_info = payment_transfer_obj.browse(cr, uid, context.get('active_id'))
        
        ws.fit_num_pages = 1
        ws.fit_height_to_pages = 0
        ws.fit_width_to_pages = 1
        #ws.paper_size_code = 1
        ws.portrait = 1
        
        align = pycel.Alignment()
        align.horz = pycel.Alignment.HORZ_CENTER
        align.vert = pycel.Alignment.VERT_CENTER
        
        font1 = pycel.Font()
        font1.colour_index = 0x0
        
        #Formato de Numero
        style = pycel.XFStyle()
        style.alignment = align
        style.font = font1
        
        #ws.insert_bitmap('banco_pacifico.bmp', 2, 0)

        ws.write_merge(2, 3, 3, 8, u'TRANSFERENCIAS INTERBANCARIAS')
        
        ws.write_merge(4, 4, 0, 2, u'Empresa', style_cabecera)
        ws.write_merge(4, 4, 3, 4, u'Coviprov S.A.', linea_izq)
        
        ws.write_merge(5, 5, 0, 2, u'SERVICIO', style_cabecera)
        ws.write_merge(5, 5, 3, 4, form.get('type') or '', linea_izq)
        
        ws.write_merge(6, 6, 0, 2, u'FECHA DE PROCESO', style_cabecera)
        ws.write_merge(6, 6, 3, 4, form.get('fecha_proceso') or '', linea_izq)
        
        ws.write_merge(7, 7, 0, 2, u'FECHA DE VENCIMIENTO', style_cabecera)
        ws.write_merge(7, 7, 3, 4, form.get('fecha_vencimiento') or '', linea_izq)
        
        ws.write_merge(4, 4, 5, 6, u'TIPO DE CTA(Emp.)', style_cabecera)
        ws.write_merge(4, 4, 7, 8, form.get('tipo_cuenta') or '', linea_izq)
        ws.write_merge(5, 5, 5, 6, u'NUMERO DE CTA(Emp.)', style_cabecera)
        ws.write_merge(5, 5, 7, 8, form.get('nro_cuenta') or '', linea_izq)
        ws.write_merge(6, 6, 5, 6, u'REFERENCIA', style_cabecera)
        ws.write_merge(6, 6, 7, 8, form.get('referencia') or '', linea_izq)
        ws.write_merge(7, 7, 5, 6, u'NOMBRE ARCHIVO', style_cabecera)
        if form.get('name'):
            name = form.get('name') + '.xls'
        else:
            name = form.get('name') or 'archivo.xls'
        ws.write_merge(7, 7, 7, 8, name, linea_izq)
        
        x0 = 0
        x2 = 10
        ws.write(x2, x0, u'Forma Pag/Cob', style_header)
        x0 += 1
        ws.write(x2, x0, u'Banco', style_header)
        x0 += 1
        ws.write(x2, x0, u'Tip.Cta/Che', style_header)
        x0 += 1
        ws.write(x2, x0, u'Num.Cta/Che', style_header)
        x0 += 1
        ws.write(x2, x0, u'Valor', style_header)
        x0 += 1
        ws.write(x2, x0, u'Identificación', style_header)
        x0 += 1
        ws.write(x2, x0, u'Tip.Doc.', style_header)
        x0 += 1
        ws.write(x2, x0, u'NUC', style_header)
        x0 += 1
        ws.write(x2, x0, u'Beneficiario', style_header)
        x0 += 1
        ws.write(x2, x0, u'Teléfono', style_header)
        x0 += 1
        ws.write(x2, x0, u'Referencia', style_header)
        x0 += 1
        ws.write(x2, x0, u'Base Imponible', style_header)
        
        destinatario_obj = self.pool.get('res.partner')
        res_partner_bank_obj = self.pool.get('res.partner.bank')
        detalle = []
        if form.get('group_by') == 'by_partner':
            detalle = self.query_group(cr, uid, context)
        else:
            cabecera = payment_transfer_obj.browse(cr, uid, context.get('active_id'))
            for x in cabecera.invoce_line_ids:
                detalle.append({'partner':x.partner,
                                'total':x.amount_total,
                                'identificacion':x.account_mov_id and x.account_mov_id.move_id and x.account_mov_id.move_id.no_comp or '',
                                'ref':x.account_mov_id and x.account_mov_id.move_id and x.account_mov_id.move_id.name or ''  })
            
        if detalle:
            xm = 11
            total = 0.00
            totalcta = 0.00
            totalchq = 0.00
            totalefe = 0.00
            totalre = 0.00
            totalsn = 0.00
            
            concta = 0
            contchq = 0
            contefe = 0
            contre = 0
            contsn = 0
            
            for item in detalle:
                xf = 0
                
                destinatario_info = destinatario_obj.browse(cr, uid, item.get('partner'))
                
                if destinatario_info.payment_type and destinatario_info.payment_type == 'CTA':
                    cuenta = 'CU'
                    concta += 1
                    totalcta += item.get('total')
                elif destinatario_info.payment_type and destinatario_info.payment_type == 'CHQ':
                    cuenta = 'CH'
                    contchq += 1
                    totalchq += item.get('total')
                elif destinatario_info.payment_type and destinatario_info.payment_type == 'EFE':
                    cuenta = 'EF'
                    contefe += 1
                    totalefe += item.get('total')
                elif destinatario_info.payment_type and destinatario_info.payment_type == 'RE':
                    cuenta = 'RE'
                    contre += 1
                    totalre += item.get('total')
                else:
                    cuenta = ''
                    contsn += 1
                    totalsn += item.get('total')
                #Cuenta
                ws.write(xm, xf, cuenta, linea_izq)
                #Banco
                xf += 1
                banco = ''
                cuenta = ''
                nro_cuenta = ''
                if destinatario_info.bank_ids:
                    for x in destinatario_info.bank_ids:
                        banco = x.bank and x.bank.code
                        nro_cuenta = x.acc_number
                        if x.acc_type and x.acc_type == 'COR':
                            cuenta = '00' 
                        else:
                            cuenta = '10'
                        if x.has_payment:
                            banco = x.bank and x.bank.code
                            nro_cuenta = x.acc_number
                            if x.acc_type and x.acc_type == 'COR':
                                cuenta = '00' 
                            else:
                                cuenta = '10'
                            break
                
                ws.write(xm, xf, banco, linea_izq)
                #Tip.Cta/Che
                xf += 1
                ws.write(xm, xf, cuenta, linea_izq)
                #Nro Cuenta
                xf += 1
                ws.write(xm, xf, nro_cuenta, linea_izq)
                #Valore
                xf += 1
                ws.write(xm, xf, item.get('total'), linea_izq)
                total += item.get('total')
                #Identificacion
                xf += 1
                #ws.write(xm,xf,destinatario_info.ref, linea_izq)
                ws.write(xm, xf, item.get('identificacion'), linea_izq)
                #Tipo Documento
                xf += 1
                identificacion = ''
                if destinatario_info.ident_type == 'c':
                    identificacion = 'C'
                elif destinatario_info.ident_type == 'r':
                    identificacion = 'R'
                elif destinatario_info.ident_type == 'p':
                    identificacion = 'P'
                elif destinatario_info.ident_type == 's':
                    identificacion = 'X'
                else:
                    identificacion = 'X'
                
                ws.write(xm, xf, identificacion, linea_izq)
                
                #Ruc
                xf += 1
                ws.write(xm, xf, destinatario_info.ident_num, linea_izq)
                
                #Beneficiario
                xf += 1
                ws.write(xm, xf, destinatario_info.name, linea_izq)
                
                #Telefono
                xf += 1
                telefono = ''
                if destinatario_info.address:
                    telefono = destinatario_info.address[0].phone or ''
                else:
                    telefono = ''
                    
                ws.write(xm, xf, telefono, linea_izq)
                xf += 1
                ws.write(xm, xf, item.get('ref'), linea_izq)
                xm += 1
                
                xi = xf
                xj = xm
                #
            
            #Subtotales
            xm = xj + 1
            xf = 1
            ws.write(xm, xf, 'SUBTOTALES', linea_izq)
            xf = 1
            xm += 1
            ws.write(xm, xf, 'TOTAL', linea_izq)
            xf += 1
            ws.write(xm, xf, 'FORMA', linea_izq)
            xf += 1
            ws.write(xm, xf, 'CANT.', linea_izq)
            
            xm += 1
            
            
            if concta:
                xf = 1
                ws.write(xm, xf, 'USD', linea_izq)
                xf += 1
                ws.write(xm, xf, 'CU', linea_izq)
                xf += 1
                ws.write(xm, xf, concta, linea_izq)
                xf += 1
                ws.write(xm, xf, totalcta, linea_izq)
                xm += 1
            if contchq:
                xf = 1
                ws.write(xm, xf, 'USD', linea_izq)
                xf += 1
                ws.write(xm, xf, 'CH', linea_izq)
                xf += 1
                ws.write(xm, xf, contchq, linea_izq)
                xf += 1
                ws.write(xm, xf, totalchq, linea_izq)
                xm += 1
            if contefe:
                xf = 1
                ws.write(xm, xf, 'USD', linea_izq)
                xf += 1
                ws.write(xm, xf, 'EF', linea_izq)
                xf += 1
                ws.write(xm, xf, concta, linea_izq)
                xf += 1
                ws.write(xm, xf, totalefe, linea_izq)
                xm += 1
            if contre:
                xf = 1
                ws.write(xm, xf, 'USD', linea_izq)
                xf += 1
                ws.write(xm, xf, 'RE', linea_izq)
                xf += 1
                ws.write(xm, xf, contre, linea_izq)
                xf += 1
                ws.write(xm, xf, totalre, linea_izq)
                xm += 1
            
            if contsn:
                xf = 1
                ws.write(xm, xf, 'USD', linea_izq)
                xf += 1
                ws.write(xm, xf, 'OTRO', linea_izq)
                xf += 1
                ws.write(xm, xf, contsn, linea_izq)
                xf += 1
                ws.write(xm, xf, totalsn, linea_izq)
                xm += 1
                    
            xm += 1
            xf = 1
            ws.write(xm, xf, 'TOTAL GENERAL', linea_izq)
            xf += 1
            ws.write(xm, xf, 'DOLARES', linea_izq)
            xf += 1
            ws.write(xm, xf, concta + contchq + contefe + contre + contsn, linea_izq)
            xf += 1
            ws.write(xm, xf, total, linea_izq)
            
        ws.col(1).width = 5000 #codigo                       
        buf = cStringIO.StringIO()
        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'data':out, 'name':name})

        
    _columns = {
              'type':fields.selection([('RPS', 'Segunda Quincena'),
                                       ('RPP', 'Primera Quincena'),
                                       #('OC', 'Ordenes de Cobro'),
                                       #('PR', 'Pago Proveedores'),
                                       #('PO', 'Solicitud Tarjetas Pagomatico'),
                                       #('RU', 'Transferencias interbancarias'),
                                       ], 'Servicio', help="Servicio"),
              
              #Cuenta
              'tipo_cuenta':fields.selection([('10', 'Cuenta de Ahorro'),
                                              ('00', 'Cuenta Corriente'),
                                              ], 'Tipo de Cuenta'),
              

              'data': fields.binary(string='Archivo'),
              'name':fields.char('Nombre del Archivo', size=100),
              'fecha_proceso':fields.date('Fecha Proceso'),
              'fecha_vencimiento':fields.date('Fecha Vencimiento'),
              'company_id':fields.many2one('res.company', 'Empresa'),
              'nro_cuenta':fields.char('Numero de Cuenta', size=100),
              'referencia':fields.char('Referencia', size=100),
              'group_by':fields.selection([('by_partner', 'Proveedor'),
                                           ('by_none', 'Sin Agrupar'),
                                          ], 'Agrupar por', help='Proveedor: Agrupa el pago por proveedor.\n Sin Agrupar'),
              'payable_to':fields.char('Pago a Nombre', size=100, help='Nombre de la persona que saldra el pago'), #Cheque
              'transfer_to':fields.selection([('partner_to', 'Proveedor'),
                                              ('employee_to', 'Empleado')
                                              ], 'Pago A un', help='Escoja aqui el nombre de persona que recibira el pago'), #Tranferencias a Nombre de 
              'supplier_to':fields.many2one('res.partner', 'Proveedor', help='Nombre del proveedro que se realizar la Transfencia', ondelete="cascade"),
#               'employee_to':fields.many2one('hr.employee', 'Empleado', help='Nombre del Empleado que se realizar la Transfencia', ondelete="cascade"),
              
    }
    
    _defaults = {
        'company_id':_get_company,
        'type': lambda * a: 'RP',
        'fecha_proceso': lambda * a: time.strftime('%Y-%m-%d'),
        'fecha_vencimiento': lambda * a: time.strftime('%Y-%m-%d'),
        'group_by':'by_none',
        'transfer_to':lambda * a: 'partner_to',
        'tipo_cuenta':'00',
        'name':'PACIFIC',
        'nro_cuenta':_get_cuenta,
        'referencia':'PAGO',
        'nro_cuenta':'19'
    }

    
wizard_payment_transfer_excel()
