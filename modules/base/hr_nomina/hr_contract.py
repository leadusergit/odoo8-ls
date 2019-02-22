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
from openerp.osv import osv, fields
from openerp.tools import email_send, config
import datetime, logging

_logger = logging.getLogger(__name__)

now = datetime.datetime.now()

class hr_contract_type(osv.osv):
    _inherit = 'hr.contract.type' 
    _columns = {
        'description': fields.char('Descripción', size=60),
        # LO NUEVO
        'dias_vigencia': fields.integer('Dias de Vigencia', help="Colocar 0 si el contrato tiene vigencia indefinida"),
        'dias_alerta': fields.integer('Dias de alerta', help='Ingresar el numero de dias de anterioridad para alertar la caducidad del contrato. Si se coloca 0, el sistema no alertará'),
        'next_type_id': fields.many2one('hr.contract.type', 'Siguiente Tipo', help="Define a que tipo de contrato cambia una vez que ha caducado"),
        'report_jefatura': fields.text('Reporte Para Jefaturas'),
        'report_otros': fields.text('Reporte para operativos, administrativos y de planta'),
        'template': fields.binary('Plantilla de contrato'),
        'parcial': fields.boolean('Parcial', help="Marcar si en el contrato el empleado puede registrar Entradas y Salidas")
        }
    _defaults = {  
        'dias_vigencia': lambda * a: 0,
        'dias_alerta': lambda * a: 0
    }
hr_contract_type()

class hr_contract_wage(osv.osv):
    _name = "hr.contract.wage"
    _description = "wage history"
    _columns = {
        'name': fields.char("Fecha", size=30),
        'wage': fields.float("Anterior Salario", digits=(8, 2)),
        'contract_id': fields.many2one('hr.contract', 'Contrato'),
        }
hr_contract_wage()

class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    
    def _compute_cost_hour(self, cr, uid, ids, field_name, arg, context):
        res = {}
        contracts = self.browse(cr, uid, ids)
        for contract in contracts:
            value = contract.wage / contract.working_hours_per_day / 30
            res[contract.id] = value
        return res
    
    def _get_name(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for contract in self.browse(cr, uid, ids):
            text = "%s" % (contract.type_id.name)
            res[contract.id] = text
        return res
    
    def _get_date_end(self, cr, uid, ids, fields_name, arg, context):
        res = {}
        contratos = self.browse(cr, uid, ids)
        for contrato in contratos:
            res[contrato.id] = False
            if contrato.type_id.dias_vigencia:
                date_start = datetime.datetime.strptime(contrato.date_start, '%Y-%m-%d').date()
                res[contrato.id] = str(date_start + datetime.timedelta(contrato.type_id.dias_vigencia - 1))
        return res
    
    _columns = {
        'type_id': fields.many2one('hr.contract.type', 'Tipo Contrato'),
        'costo_hora': fields.function(_compute_cost_hour, method=True, string='Valor Hora', type='float', digits=(16,4)),
#         'name': fields.function(_get_name, method=True, string='Descripcion de Contrato', type='char', size=80,
#                                 store={'hr.contract': (lambda self, cr, uid, ids, *a: ids, None, 10)}),
        'sueldo_basico': fields.float('Sueldo Basico', digits=(8, 2)),
        'wage_line': fields.one2many('hr.contract.wage', 'contract_id', 'Historial de Salarios'),
        #LO NUEVO
        'state': fields.selection([('vigente', 'Vigente'), ('por_caducar', 'Por Caducar'), ('caducado', 'Caducado'), ], 'Estado', readonly=True),
        #'date_end': fields.function(_get_date_end, method=True, type="date", string="End Date", store=False),
        'date_end': fields.date('End Date'),
        'working_hours_per_day':fields.integer("Horas por Dias", required=True),
    }
    _defaults = {
        'state': lambda * a: 'vigente',
        'working_hours_per_day': lambda *a: 8
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        self.create_history(cr, uid, ids, vals)
        res = super(hr_contract, self).write(cr, uid, ids, vals, context)
        self.update_states(cr, uid, ids)
        return res

    def create_history(self, cr, uid, ids, vals):
        if vals.has_key('state') and vals['state']:
            contratos = self.read(cr, uid, ids)
            for contrato in contratos:
                if contrato['state'] != vals['state']:
                    estados = {'vigente': 'Vigente', 'por_caducar': 'Por Caducar', 'caducado': 'Caducado'}
                    self.pool.get('hr.history.department').create(cr, uid, {
                        'tipo_contrato': contrato['type_id'][1],
                        'employee_id': contrato['employee_id'][0],
                        'date': str(datetime.date.today()),
                        'tipo_novedad':'Cambio de Estado',
                        'valor_nuevo': estados[vals['state']],
                        'valor_anterior': estados[contrato['state']],
                        'sueldo': contrato['wage']
                    })
        if vals.has_key('type_id') and vals['type_id']:
            contratos = self.read(cr, uid, ids)
            for contrato in contratos:
                #print ' contrato ',contrato 
                if contrato['type_id'] and contrato['type_id'][0] != vals['type_id']:            
                    tipo_contrato = self.pool.get('hr.contract.type').read(cr, uid, vals['type_id'], ['name'])
                    self.pool.get('hr.history.department').create(cr, uid, {
                        'tipo_contrato': contrato['type_id'][1],
                        'employee_id': contrato['employee_id'][0],
                        'date': str(datetime.date.today()),
                        'tipo_novedad':'Cambio de Tipo de Contrato',
                        'valor_nuevo': tipo_contrato['name'],
                        'valor_anterior': contrato['type_id'][1],
                        'sueldo': contrato['wage'],
                    })

        if vals.has_key('wage') and vals['wage']:
            contratos = self.read(cr, uid, ids)
            for contrato in contratos:
                if contrato['wage'] != vals['wage']:
                    self.pool.get('hr.history.department').create(cr, uid, {
                        'tipo_contrato': contrato['type_id'][1],
                        'employee_id': contrato['employee_id'][0],
                        'date': str(datetime.date.today()),
                        'tipo_novedad':'Cambio Sueldo',
                        'valor_nuevo': vals['wage'],
                        'valor_anterior': contrato['wage'],
                        'sueldo': vals['wage'],
                    })
        if vals.has_key('function') and vals['function']:
            contratos = self.read(cr, uid, ids)
            for contrato in contratos:
                if contrato.has_key('function') and contrato['function']:
                    if contrato['function'][0] != vals['function']:
                        funcion = self.pool.get('res.partner.function').read(cr, uid, vals['function'], ['name'])
                        self.pool.get('hr.history.department').create(cr, uid, {
                            'tipo_contrato': contrato['type_id'][1],
                            'employee_id': contrato['employee_id'][0],
                            'date': str(datetime.date.today()),
                            'tipo_novedad':'Cambio de Cargo',
                            'valor_nuevo': funcion['name'],
                            'valor_anterior': contrato['function'][1],
                            'sueldo': contrato['wage'],
                        })
    
    def onchange_name(self, cr, uid, ids, type_id):
        return {}
    
    def onchange_wage(self, cr, uid, ids, wage):
        v = {}
        iess = wage * 0.0935
        aal = wage * 0.20
        cost_hour = (wage + aal) / 240
        v['costo_hora'] = cost_hour
        return {'value': v}

    def send_notification_mail(self, cr, uid):
        ids_por_caducar = self.update_states(cr, uid)
        state = True
        if ids_por_caducar:
            _logger.info('SE HA ENCONTRADO CONTRATOS POR CADUCAR, ENVIANDO MAIL...')
            notifications_id = self.pool.get('hr.notification.mail.settings').search(cr, uid, [('default', '=', True)])
            state = False
            if notifications_id:
                notification = self.pool.get('hr.notification.mail.settings').browse(cr, uid, notifications_id)[0]
                company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id
                html = """<HTML><HEAD><META HTTP-EQUIV="CONTENT-TYPE" CONTENT="text/html; charset=utf-8"></HEAD><BODY>
<P ALIGN="CENTER"><BIG><B>%s %d</BIG></B></P>
<TABLE BORDER=20 ALIGN="CENTER">
<TR><TD ALIGN="CENTER"><P><SMALL><B>Empleado</TD><TD ALIGN="CENTER"><P><SMALL><B>Departamento</TD><TD ALIGN="CENTER"><P><SMALL><B>Tipo de Contrato</TD><TD ALIGN="CENTER"><P><SMALL><B>Fecha Inicial</TD><TD ALIGN="CENTER"><P><SMALL><B>Fecha Final</TD><TD ALIGN="CENTER"><P><SMALL><B>Dias del Contrato</TD><TD ALIGN="CENTER"><P><SMALL><B>Finaliza en</TD></TR>
""" % (company_id.name, now.year)
                contratos = self.read(cr, uid, ids_por_caducar, ['id', 'employee_id', 'type_id', 'date_start', 'date_end'])
                for contrato in contratos:
                    
                    employee_data = self.pool.get('hr.employee').read(cr, uid, contrato['employee_id'][0], ['name', 'state_emp','department_id'])
                    
                    employee_name = employee_data['name']
                    employee_state = employee_data['state_emp']
                    departamento = employee_data['department_id'][1]
                    #print ' employee_state ', employee_state , ' employee_name ', employee_name
                    if employee_state in ('inactive', 'sold_out'):
                        continue
                    
                    date_start = map(lambda x: int(x), contrato['date_start'].split('-'))
                    dias_total = (datetime.date.today() - datetime.date(date_start[0], date_start[1], date_start[2])).days + 1
                    date_end = map(lambda x: int(x), contrato['date_end'].split('-'))
                    dias_restantes = (datetime.date(date_end[0], date_end[1], date_end[2]) - datetime.date.today()).days
                    html += """<TR><TD ALIGN="CENTER"><P><SMALL>%s</SMALL></P></TD><TD ALIGN="CENTER"><P><SMALL>%s</SMALL></P></TD><TD ALIGN="CENTER"><P><SMALL>%s</SMALL></P></TD><TD ALIGN="CENTER"><P><SMALL>%s</SMALL></P></TD><TD ALIGN="CENTER"><P><SMALL>%s</SMALL></P></TD><TD ALIGN="CENTER"><P><SMALL>%s dias</SMALL></P></TD><TD ALIGN="CENTER" BGCOLOR="YELLOW"><P><SMALL>%s dias</SMALL></P></TD></TR>
""" % (contrato['employee_id'][1],departamento, contrato['type_id'][1], contrato['date_start'], contrato['date_end'], dias_total, dias_restantes)
                html += """</TABLE></BODY></HTML>"""
                if notification.employees_ids:
                    state = email_send(email_from=config['email_from'],
                                       email_to=[aux.work_email for aux in notification.employees_ids],
                                       subject=notification.subject,
                                       body=html,
                                       subtype='html')
            _logger.info("ENVIO DE MAIL EXITOSO" if(state) else "ENVIO DE MAIL FALLIDO")
        return state                
    
    def update_states(self, cr, uid, ids=[]):
        ids_caducados = []
        ids_por_caducar = []
        ids_vigentes = []
        hoy = datetime.date.today()
        contratos_ids = self.search(cr, uid, ids) if not ids else ids
        if contratos_ids:
            contratos = self.browse(cr, uid, contratos_ids)
            for contrato in contratos:
                if contrato.date_end:
                    campos = map(lambda x: int(x), contrato.date_end.split('-'))
                    date_end = datetime.date(campos[0], campos[1], campos[2])
                    if (date_end - hoy).days <= contrato.type_id.dias_alerta and (date_end - hoy).days > 0:
                        ids_por_caducar.append(contrato.id)
                    elif (date_end - hoy).days <= 0:
                        ids_caducados.append(contrato.id)
                    else:
                        ids_vigentes.append(contrato.id)
                else:
                    ids_vigentes.append(contrato.id)
            if ids_por_caducar:
                self.create_history(cr, uid, ids_por_caducar, {'state': 'por_caducar'})
                super(hr_contract, self).write(cr, uid, ids_por_caducar, {'state': 'por_caducar'})
            if ids_caducados:
                contratos = self.browse(cr, uid, ids_caducados)
                for contrato in contratos:
                    if contrato.type_id.next_type_id and contrato.type_id.next_type_id.id:
                        self.create_history(cr, uid, [contrato.id], {'type_id': contrato.type_id.next_type_id.id})
                        super(hr_contract, self).write(cr, uid, [contrato.id], {'type_id': contrato.type_id.next_type_id.id})
                        ids_caducados.remove(contrato.id)
                        ids_vigentes.append(contrato.id)
                self.create_history(cr, uid, ids_caducados, {'state': 'caducado'})
                super(hr_contract, self).write(cr, uid, ids_caducados, {'state': 'caducado'})
            if ids_vigentes:
                self.create_history(cr, uid, ids_vigentes, {'state': 'vigente'})
                super(hr_contract, self).write(cr, uid, ids_vigentes, {'state': 'vigente'})
        return ids_por_caducar

hr_contract()
