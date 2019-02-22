from openerp.osv import osv, fields

class account_move_line(osv.osv):  
    _inherit = 'account.move.line'
    
    def init(self, cr, uid=1):
        cr.execute("SELECT column_name FROM information_schema.COLUMNS "
                   "WHERE table_name='account_move_line' and column_name='x_conciliado'")
        if not cr.fetchone():
            cr.execute('ALTER TABLE account_move_line ADD COLUMN x_conciliado BOOLEAN')
            
    def _get_move_lines(self, cr, uid, ids, context=None):
        result = []
        for move in self.pool.get('account.move').browse(cr, uid, ids, context=context):
            for line in move.line_id:
                result.append(line.id)
        return result
    
    _columns = {
        'x_conciliado': fields.boolean('Conciliado'),
        'ref': fields.char('Ref.', size=256),
        'debit': fields.float('Debit', digits=(16, 6)),
        'credit': fields.float('Credit', digits=(16, 6)),
        #Aumento los campos que necesito para Concilacion Bancaria y Reporte de Cartera.
        'revisado': fields.boolean('Revisado'),
        'seller_id':fields.many2one('res.users', 'Vendedor(a)'), #Este marca el vendedor en cada saldo inicial
        'type_move': fields.char('Tipo', size=256),
        'date': fields.related('move_id','date', string='Effective date', type='date', required=True, select=True,
                                store = {
                                    _inherit: (lambda self, cr, uid, ids, *a: ids, None, 10),
                                    'account.move': (_get_move_lines, ['date'], 20)
                                }),
    }
    _defaults = {
                'revisado':lambda * a: False,
    }
account_move_line()
