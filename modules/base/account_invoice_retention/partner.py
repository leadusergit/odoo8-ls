# -*- coding: utf-8 -*-
###################################################
#
#    BUILDING CRM Module
#    Copyright (C) 2012 Atikasoft Cia.Ltda. (<http://www.atikasoft.com.ec>).
#    $autor: Dairon Medina Caro <dairon.medina@gmail.com>
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
from openerp.osv import fields, osv
from utils import cedula_validation, ruc_validation

class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    def write(self, cr, uid, ids, vals, context=None):
        ids = ids if isinstance(ids, list) else [ids]
        if ids:
            partner = ids[0]
            obj_res_partner = self.browse(cr, uid, ids[0])
            tipo_pago = obj_res_partner.payment_type
            f = []
            if tipo_pago == 'CTA'and vals.has_key('payment_type') == False:
                lista = self.pool.get('res.partner.bank').search(cr, uid, [('partner_id', '=', ids[0]), ('has_payment', '=', True)])
                if not lista:
                    print "Write Tiene has_payment"
                else:
                    raise osv.except_osv(('Aviso'), ('Seleccione o Cree una cuenta Bancaria para este Tipo de Pago.'))
                 
            if vals.has_key('payment_type'):
                #print "vals.has_key('payment_type')", vals.has_key('payment_type')
                payment = ''
                if vals['payment_type']:
                    if vals['payment_type'] == 'CTA':
                        payment = 'Cash Management Cuenta Bancaria'
                    if vals['payment_type'] == 'CHQ':
                        payment = 'Cash Management Cheque Gerencia'
                    if vals['payment_type'] == 'EFE':
                        payment = 'Cash Management Efectivo'
                    if vals['payment_type'] == 'CHQINDV':
                        payment = 'Cheque'
                    if vals['payment_type'] == 'CARD':
                        payment = 'Tarjeta de Credito'
                    if vals['payment_type'] == 'CANJE':
                        payment = 'Canje'
    
                    cr.execute ('select id from account_invoice where partner_id= %s', (partner,))
                    consulta = cr.dictfetchall()
                    if consulta:
                        for i in consulta:
                            cr.execute ('update account_invoice set partner_payment = %s where id= %s', (payment, i['id']))
                            cr.execute(""" commit """) 
                
                if vals['payment_type'] == 'CTA':
                    if vals.has_key('bank_ids'):
                        if vals['bank_ids'] != []:
                            for aux in vals['bank_ids']:
                                #print "aux", aux[2]
                                if aux[2]:
                                    f.append(aux[2])
                            ##print "Imprime lista", f
                            if f:
                                if not f[0]['has_payment'] == 1:
                                    #print "Tiene cuenta seleccionada"
    #                             else:
                                    raise osv.except_osv(('Aviso'), (' Seleccione la cuenta Bancaria para este Tipo de Pago.'))
                            else:
                                raise osv.except_osv(('Aviso'), (' Cree una cuenta Bancaria para este Tipo de Pago.'))
                        else:
                            raise osv.except_osv(('Aviso'), (' Seleccione una cuenta Bancaria..!'))
                        
        id = super(res_partner, self).write(cr, uid, ids, vals, context=context)
        return id
    
    def onchange_id_num(self, cr, uid, ids, identification_number, tipo_doc):
        
        #print ' VALIDANDO LA CEDULA O EL RUCCCC '
        res = {'value':{}}
        if tipo_doc == 'c':
            cedula_validation(identification_number)
        elif tipo_doc == 'r':
            ruc_validation(identification_number)   
#         elif tipo_doc == 'p':
            #print 'tipo pasaporte'  
        return res
    
    
    def _check_num_ident(self, cr, uid, ids, context=None):
        
        try:
            res_partner_data = self.read(cr, uid, ids, ['ident_num', 'ident_type'])
            for partner in res_partner_data:
                if partner['ident_type'] == 'c':
                    cedula_validation(partner['ident_num'])
                    return True
                elif partner['ident_type'] == 'r':
                    ruc_validation(partner['ident_num'])
                    return True
                else:
                    return True    
        except:
            return False        
            
    
    def onchange_payment_type(self, cr, uid, ids, payment_type, context=None):
        res = {}
        if ids:
            res_partner = self.browse(cr, uid, ids[0])
            lista = self.pool.get('res.partner.bank').search(cr, uid, [('partner_id', '=', ids[0]), ('has_payment', '=', True)])
            if payment_type == 'CTA':
                if res_partner.bank_ids:
                    if not lista:
                        raise osv.except_osv(('Aviso'), ('Seleccione una Cuenta Bancaria.!'))
                else:
                    raise osv.except_osv(('Aviso'), ('Debe especificar Una Cuenta Bancaria para este Tipo de Pago.'))
        return res

    
    def _debit_total(self,cr,uid,ids,field_names,arg, context=None):
        
        res={}
        for obj in self.browse(cr, uid, ids, context=context):
            cr.execute("SELECT sum(f.residual) FROM account_move_line c left join (select * from account_account) as d on c.account_id = d.id left join (select * from account_invoice) as f on c.move_id = f.move_id and d.id = f.account_id where c.partner_id=%i and f.state = 'open' and f.type='in_invoice' " % (obj.id,))
            pendiente = cr.fetchone()[0]
            if pendiente:
                res[obj.id] = pendiente
            else:
                res[obj.id] = 0        
        return res

    
    _columns = {
        'auth_ids' : fields.one2many('account.authorisation', 'partner_id', 'Autorizaciones'),
        'ident_num':fields.char('Numero Identificacion', size=20, help='Numero de identificacion del proveedor'),
        'ident_type':fields.selection((('c', 'Cedula'), ('p', 'Pasaporte'), ('r', 'RUC'), ('s', 'S/N')), "Tipo ID"),
        'is_provider':fields.boolean('Propietario'),
        'name_comercial': fields.char('Nombre Comercial', size=128),
        'payment_type':fields.selection([('CTA','Transferencia-Cuenta'),
                                         ('CHQ','Cheque'),
                                         ],"Pago"),

        #'credit_new': fields.function(_credit_debit_get_new, method=True, string='Total Receivable', help="Total amount this customer owes you."),
        'debit_new': fields.function(_debit_total, method=True, string='Total Por Pagar', help="Total amount you have to pay to this supplier.",type="float"),
        'legal_representative':fields.char('Representante legal', size=128),
        'tipoprov_ext':fields.selection([('01', 'PERSONA NATURAL'),('02', 'SOCIEDAD')], 'Tipo identificacion Proveedor'),
        'parterel':fields.selection([('SI','SI'),('NO','NO')], 'Parte Relacionada')
      }
    
    
    _constraints = [
        (_check_num_ident, 'Error ! Numero de Identificación no válido.', ['ident_num']),
        
    ]
    
    _sql_constraints = [
        ('unique_iden', 'unique(ident_num,ident_type,company_id)', 'Los datos de identificacion ya estan registrados en el sistema.'),
    ]
    
res_partner()

class res_partner_bank(osv.osv):
    _name = 'res.partner.bank'
    _inherit = 'res.partner.bank'
      
    def onchange_has_payment(self, cr, uid, ids, has_payment, context=None):
        ##print "onchange has páyment", ids
        lista = []
        dic = {}
        if ids:
            for t in self.browse(cr, uid, ids):
                if not t.acc_type:
                    raise osv.except_osv(('Aviso'), ('El tipo de Cuenta Bancaria no esta seleccionado.'))

            res_partner = self.pool.get('res.partner').browse(cr, uid, t.partner_id.id)
            
            ids_cambiar = []
            if has_payment == 1:            
                for aux in res_partner.bank_ids:
                    if aux.id != ids[0]:
                        ids_cambiar.append(aux.id)
            ##print "ssssssssssssssssss",ids_cambiar
            self.write(cr, uid, ids_cambiar, {'has_payment': 0})
            cr.commit()
            if res_partner:
                for rpb in res_partner.bank_ids:
                    dic = {'id':rpb.id,
                           'has_payment':rpb.has_payment
                           }
                    lista.append(dic)                        
        return {}
     
    _columns = {
              'bank_statement_ids': fields.one2many('account.bank.statement', 'acc_deposit_id', 'Extractos'),
              'has_payment':fields.boolean('Pago'),
#              'view_check':fields.funtion(_view_check, string='Check', type='char', method=True, store=False, size=32)
              } 
    _defaults = {
        'has_payment': lambda * a : False,
      }
              
res_partner_bank()

# class res_partner_address(osv.osv):
#     _name = 'res.partner.address'
#     _inherit = 'res.partner.address'
#     
#     def onchange_id_num(self, cr, uid, ids, identification_number, tipo_doc):
#         res = {'value':{}}
#         if tipo_doc == 'c':
#             cedula_validation(identification_number)
#         elif tipo_doc == 'r':
#              ruc_validation(identification_number)   
# #         elif tipo_doc == 'p':
#                 #print 'tipo pasaporte'  
#         return res
#     
#     _columns = {
#                 'ident_num':fields.char('Numero Identificacion', size=20, help='Numero de identificacion del proveedor'),
#                 'ident_type':fields.selection((('c', 'Cedula'), ('p', 'Pasaporte'), ('r', 'RUC')), "Tipo ID"),
#                 }
# res_partner_address()
