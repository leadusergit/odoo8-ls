# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
import time

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    
    def _query_get(self, cr, uid, obj='l', context=None):
        query = super(account_move_line, self)._query_get(cr, uid, obj, context)
        if context.get('partner_id'):
            query += ' AND '+obj+'.partner_id=' + str(context['partner_id'])
        if context.get('invoice_id'):
            query += ' AND '+obj+'.invoice_id=' + str(context['invoice_id'])
        if context.get('move_id'):
            query += ' AND '+obj+'.move_id=' + str(context['move_id'])
        if context.get('analytic_account_id'):
            query += ' AND '+obj+'.analytic_account_id=' + str(context['analytic_account_ids'])
        return query
account_move_line()

class account_account(osv.osv):
    _inherit = 'account.account'
    
    
    """
    Obtener todas las cuentas a las que tengo que sumarles el valor
    """
    def get_accounts_add_value_profit_or_loss(self, cr, uid):
        cuenta_res = self.get_result_account(cr, uid)
        if not cuenta_res:
            raise osv.except_osv('MissingError', u'No ha definido una cuenta de resultado, por favor marcar el campo "cuenta_resultado" en la cuenta contable de resultado.')
        cuenta_id = cuenta_res['id']
        res = []
        self.get_all_parent_account(cr, uid, cuenta_id, res)
        # #print 'res  **** ', res
        return res
        
    def get_all_parent_account(self, cr, uid, account_id, res):
        parent_id = self.read(cr, uid, account_id, ['parent_id'])
        # #print ' parent_id ',parent_id 
        if parent_id and parent_id['parent_id']:
            # #print 'HOLA ***'
            res.append(parent_id['id'])
            self.get_all_parent_account(cr, uid, parent_id['parent_id'][0], res)
            
        else:
            # #print 'HOLA ******'
            return
    
    """
    Obtener el valor de perdida o utilidad para el balance general
    """
    def get_profit_or_loss(self, cr, uid, ctx):
        
        # #print ' ctx ', ctx
        ids = self.search(cr, uid, [('code', 'in', ['4.', '5.', '6.'])])
        accounts_data = self.browse(cr, uid, ids, ctx)
        
        incomes = 0
        expense = 0
        cost = 0
        
        for account_data in accounts_data:
            # #print ' account_data ', account_data.code
            saldo = account_data.balance
            if account_data.code == '4.':
                # print ' account_data 4 ', account_data.balance
                # incomes += saldo > 0 and saldo or (-1) * saldo
                incomes += (-1) * saldo
            if account_data.code == '5.':
                # print ' account_data 5 ', account_data.balance
                expense += saldo
            if account_data.code == '6.':
                # print ' account_data 6 ', account_data.balance
                cost += saldo
                 
        # #print ' incomes ', incomes
        # #print ' expense ', expense
        # #print ' cost ', cost
        profit_loss = incomes - expense - cost
        res = profit_loss > 0 and (-1) * profit_loss or (-1) * profit_loss
        # #print ' res ', res  
                
        return res     
    
    
    """
    Obtiene la cuenta que tiene la marca como cuenta de resultado
    """
    def get_result_account(self, cr, uid):
        company_id = self.pool['res.users'].browse(cr, uid, uid).company_id.id
        cr.execute("SELECT id, cuenta_resultado FROM account_account "
                   "WHERE cuenta_resultado = True and company_id=%s", (company_id,))
        res_cadena = None
        for res in cr.dictfetchall():
            res_cadena = res
        return res_cadena   
    
    
    """
    Obtiene una lista del plan de cuentas ordenadas
    """
    def get_list_char_account(self, cr, uid, ids, list_account):
        
        # print ' en el account '
        
        query = "with recursive nodes_cte(id, name, code,parent_id, depth) as ( \
        select aa.id, aa.name, aa.code,aa.parent_id, 1::INT AS depth \
        from account_account as aa \
        where aa.parent_id is null \
        union all \
        select aa.id, aa.name, aa.code,aa.parent_id, p.depth + 1 as depth \
        from nodes_cte as p, account_account as aa \
        where aa.parent_id = p.id \
        ) \
        select * \
        from nodes_cte as n \
        order by n.code,n.depth asc;"
        
        # print ' query ', query
        
        cr.execute(query)
        # account_ids = cr.fetchall()
        accounts_list_res = [x for x in cr.fetchall()]
        
        account_ids = []
        for account_list_res in accounts_list_res:
            if account_list_res[3]:
                inicio = account_list_res[2][0:1]
                if inicio in list_account:
                    # print ' account_list_res ', account_list_res
                    account_ids.append(account_list_res[0])
        
        return account_ids
        
        
        # for account_id in account_ids:
        #    #print ' account ', account_id  
        
    
    def get_list_account(self, cr, uid, ids, list_account, context):
        
        accounts_id = self.search(cr, uid, [])
        
        accounts_list_res = self.read(cr, uid, accounts_id, ['id', 'name', 'code', 'parent_id'])
        
        account_ids = []
        for account_list_res in accounts_list_res:
            if account_list_res['parent_id']:
                inicio = account_list_res['code'][0:1]
                if inicio in list_account:
                    # print ' account_list_res ', account_list_res
                    account_ids.append(account_list_res['id'])
        
        return account_ids
        
    
    def _order_list(self, accounts_data):
        for aux in accounts_data:
            if not aux.get('ordering'):
                raise osv.except_osv('ValidationError', u'Existe un error con la siguiente cuenta: %s'%aux)
        new_sorted = sorted(accounts_data, key=lambda code:code['ordering'])
        return new_sorted
    
        
    def get_list_account_ordering(self, cr, uid, ids, account_id , nivel, secuencial, res, context):
        
#        #print 'get list ', account_id 
        accounts_ids = self.search(cr, uid, [('parent_id', '=', account_id)])
        if not accounts_ids:
            return secuencial
        
        accounts_list_res = self.read(cr, uid, accounts_ids, ['id', 'name', 'code', 'parent_id', 'level'])
        # Poner el numero de orden
        for account_list_res in accounts_list_res:
            code = account_list_res['code']
            level = nivel
            code_cta = code.split('.')
            if code_cta[level]:
                account_list_res['ordering'] = int(code_cta[level])
                                
        # mando a ordenar
        new_sorted = self._order_list(accounts_list_res)
        for account_list_res in new_sorted:
            secuencial += 1  
            account_list_res['sec'] = secuencial
            res.append(account_list_res)
            secuencial = self.get_list_account_ordering(cr, uid, ids, account_list_res['id'], nivel + 1, secuencial, res, context)
                  
        return secuencial    
    
    def get_list_account_by_level(self, cr, uid, nivel, tipo, ctx):
        
        level = ''
          
        for aux in range(int(nivel or 100)):
            level += str(aux + 1)
            if aux + 1 < nivel:
                level += ','
        # level_data = level[0]
        
        # print ' level ', level
        # print ' level_data ', level_data
             
        query = """select aa.id 
         from account_list_account ala, account_report_bs arb, account_account aa
         where ala.report_bs_id = arb.id
         and ala.account_id = aa.id
         and arb.code ilike '%s'  
         and aa.level in (%s)  
         order by orden """ % (tipo, level)     
             
        
        
        #print ' query ', query     
        cr.execute(query)
        
        account_ids = [x[0] for x in cr.fetchall()]
       
        return self.browse(cr, uid, account_ids, ctx)
    
    
    _columns = {
        'clasificacion_flu_efe':fields.selection([('ninguno', 'Ninguno'), ('clie', 'Clientes'), ('prov', 'Proveedores'), ('otro', 'Otros'), ('inve', 'Inversion'), ('fina', 'Financiamiento')], 'Grupo', help='Marque las cuentas para el flujo de efectivo'),
    }
    
    
account_account()


class account_period(osv.osv):
    _inherit = 'account.period'
    
    def before(self, cr, uid, period, step, context=None):
        ids = self.search(cr, uid, [('date_start', '<', period.date_start), ('fiscalyear_id', '=', period.fiscalyear_id.id)], order='date_start desc')
        if len(ids) >= step:
            return ids[step - 1]
        return False
    
account_period()    
 
