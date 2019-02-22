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
from openerp import models, fields, api

class hr_employee(models.Model):
    _inherit = 'hr.employee'
    #===============================================================================================
    #Columns
    tipo_discapacidad = fields.Char('Tipo Discapacidad')
    porcentaje_discapacidad = fields.Float('Porcentaje de Discapacidad')
    carnet_conadis = fields.Char('Carnet Conadis')
    formacion_ids = fields.One2many('hr.employee.formacion','employee_id',string="Formación Academica")
    experiencia_laboral_ids = fields.One2many('hr.employee.experiencia','employee_id',string="Experiencia Laboral")
    cursos_realizados_ids = fields.One2many('hr.employee.cursos','employee_id',string="Cursos Realizados")
    idiomas_ids = fields.One2many('hr.employee.idiomas','employee_id',string="Idiomas")
    #===============================================================================================

class hr_employee_formacion(models.Model):
    _name = 'hr.employee.formacion'
    _description = 'Formacion Academica'
    #===============================================================================================
    #Columns
    employee_id = fields.Many2one('hr.employee',string="Empleado")
    name = fields.Char('Nombre de la Institucion')
    nivel_estudios = fields.Selection([('primaria','Primaria'),('secundaria','Secundaria'),('tecnico','Tecnico'),('superior','Superior'),('postgrado','Postgrado')],'Nivel de Estudios')
    estado = fields.Selection([('graduado','Graduado'),('egresado','Egresado'),('en_curso','En Curso'),('abandonado','Abandonados')],'Estado')
    titulo_obtenido = fields.Char('Titulo Obtenido')
    #===============================================================================================
    
class hr_employee_cursos(models.Model):
    _name = 'hr.employee.cursos'
    _description = 'Cursos de Empleado'
    #===============================================================================================
    #Columns
    employee_id = fields.Many2one('hr.employee',string="Empleado")
    name = fields.Char('Tema')
    nivel = fields.Char('Nivel')
    terminado = fields.Boolean('Terminado')
    fecha = fields.Date('Fecha')
    horas = fields.Integer('Horas')
    #===============================================================================================

class hr_employee_experiencia(models.Model):
    _name = 'hr.employee.experiencia'
    _description = 'Experiencia Profesional'
    #===============================================================================================
    #Columns
    employee_id = fields.Many2one('hr.employee',string="Empleado")
    name = fields.Char('Nombre empresa',help="Nombre de la empresa en la que laboro")
    cargo = fields.Char('Cargo')
    fecha_inicio = fields.Date('Fecha Desde')
    fecha_fin = fields.Date('Fecha Fin')
    motivo_salida = fields.Text('Motivo de Salida')
    #===============================================================================================
    
class hr_employee_idiomas(models.Model):
    _name = 'hr.employee.idiomas'
    _description = 'Idiomas de Empleado' 
    #===============================================================================================
    #Columns
    employee_id = fields.Many2one('hr.employee',string="Empleado")
    name = fields.Char('Idioma')
    #===============================================================================================