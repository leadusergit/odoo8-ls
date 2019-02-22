# -*- coding: utf-8 -*-
##############################################################################
#
#    E-Invoice Module - Ecuador
#    Copyright (C) 2014 VIRTUALSAMI CIA. LTDA. All Rights Reserved
#    alcides@virtualsami.com.ec
#    $Id$
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

from openerp.osv import osv, fields

class Company(osv.osv):
    
    _inherit = 'res.company'
    
    _columns = {
        'electronic_signature': fields.char('Firma Electrónica', size=128, required=True,help='Ubicación de carpeta que almacena Certificado Digital'),
        'password_electronic_signature': fields.char('Clave Firma Electrónica', size=128, required=True, help='Password de certificado digital'),
        'emission_code': fields.selection([('1','Normal'),
                                           ('2','Indisponibilidad')],
                                 string='Tipo de Emisión', required=True,help='Tipo de emisión que utiliza el sistema'),
        'contingency_key_ids': fields.one2many('res.company.contingency.key','company_id', 'Claves de Contingencia', help='Claves de contingencia relacionadas con esta empresa.'),
        ##Campos para configuración de paths de carpetas que almacenan comprobantes electrónicos
        'bills_generated': fields.char('Facturas Generadas', size=128, required=True,help='Ubicación de carpeta que almacena XML de facturas generadas'),
        'bills_signed': fields.char('Facturas Firmadas', size=128, required=True,help='Ubicación de carpeta que almacena XML de facturas firmadas'),
        'bills_authorized': fields.char('Facturas Autorizadas', size=128, required=True,help='Ubicación de carpeta que almacena XML de facturas autorizadas por el SRI'),
        'vouchers_generated': fields.char('Comprobantes de Retención Generados', size=128, required=True,help='Ubicación de carpeta que almacena XML de comprobantes generados'),
        'vouchers_signed': fields.char('Comprobantes de Retención Firmados', size=128, required=True,help='Ubicación de carpeta que almacena XML de comprobantes firmados'),
        'vouchers_authorized': fields.char('Comprobantes de Retención Autorizados', size=128, required=True,help='Ubicación de carpeta que almacena XML de comprobantes autorizados por el SRI'),
        'credit_note_generated': fields.char('Notas de Crédito Generadas', size=128, required=True,help='Ubicación de carpeta que almacena XML de notas de crédito generadas'),
        'credit_note_signed': fields.char('Notas de Crédito Firmadas', size=128, required=True,help='Ubicación de carpeta que almacena XML de notas de crédito firmadas'),
        'credit_note_authorized': fields.char('Notas de Crédito Autorizadas', size=128, required=True,help='Ubicación de carpeta que almacena XML de notas de crédito autorizadas por el SRI'),
        'ambiente_code': fields.selection([('1','Pruebas'),
                                           ('2','Producción')],
                                 string='Tipo de Ambiente', required=True,help='Selección de tipo de ambiente del sistema'),
        'fee_view': fields.boolean('fee', help="FEE-SRI Cada Factura pide autorizacion al SRI version Ecuador"),
        
        }
        
    _defaults = {
        'emission_code': '1',
        'ambiente_code':'1',
        'fee_view': True, 
        }

class CompanyContingencyKey(osv.osv):
  
    _name = 'res.company.contingency.key'
    _description = 'Clave de Contingencia'
    
    def _get_company(self, cr, uid, context):
        if context.get('company_id', False):
            return context.get('company_id')
        else:
            user = self.pool.get('res.users').browse(cr, uid, uid)
            return user.company_id.id
            
    _columns = {
        'key': fields.char('Clave', size=37, required=True),
        'used': fields.boolean('¿Utilizada?', readonly=True),
        'company_id': fields.many2one('res.company', 'Empresa', required=True),
        }
    
    _defaults = {
        'used': False,
        'company_id': _get_company,
        }
        
    _sql_constraints = [
        ('key_unique', 'unique(key)', u'Clave de contingencia asignada debe ser única.'),
        ]
