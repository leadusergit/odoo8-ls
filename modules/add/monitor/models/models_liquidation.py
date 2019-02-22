# -*- encoding: utf-8 -*-

from openerp import models, fields, api
import xmlrpclib

# mapping invoice type to journal type
from openerp.exceptions import ValidationError
from openerp.osv import osv

TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale_refund',
    'in_refund': 'purchase_refund',
}

class m_liquidation(models.Model):
    _name = 'm.liquidation'
    _description = 'Liquidacion'
    _inherit = ['mail.thread']


    @api.one
    @api.depends('line_id.total')
    def _compute_amount(self):
        for line in self.line_id:
            if line.type == 'out_invoice':
                self.total_sale += line.total
            if line.type == 'out_refund':
                self.total_dev += line.total
        total = self.total_sale - self.total_dev
        self.total_liquidation = total
        # calcular total a facturar
        res = self.env['m.table.payment.conf'].calculate(total)
        self.total_payment = res
        # descripcion del caculo
        calc_table = self.env['m.table.payment.conf'].search([('mmin', '<=', total), ('mmax', '>=', total)])
        if calc_table:
            self.calc_min_max = str(calc_table.mmin) + " - " + str(calc_table.mmax)
            self.calc_rate = str(calc_table.rate)
            self.calc_percent = str(calc_table.percent)
            self.calc_formule = str(calc_table.rate) + " + " + str(calc_table.percent) + "%" + str(total) + " = " + str(res)

    @api.one
    @api.depends(
        'move_id.line_id.reconcile_id.line_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids',
    )
    def _compute_payments(self):
        partial_lines = lines = self.env['account.move.line']
        for line in self.move_id.line_id:
            if line.reconcile_id:
                lines |= line.reconcile_id.line_id
            elif line.reconcile_partial_id:
                lines |= line.reconcile_partial_id.line_partial_ids
            partial_lines += line
        self.payment_ids = (lines - partial_lines).sorted()

    @api.model
    def _default_journal(self):
        inv_type = 'out_invoice'
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self.env.user.company_id.id
        domain = [
            ('type', 'in', filter(None, map(TYPE2JOURNAL.get, inv_types))),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)

    @api.model
    def _default_currency(self):
        journal = self._default_journal()
        return journal.currency or journal.company_id.currency_id

    @api.one
    def _get_server_url(self):
        param = self.env['ir.config_parameter'].search([('key', '=', 'web.base.url')], limit=1)
        self.banner = param.value + '/monitor/static/src/img/lead.png'

    name = fields.Char(string='Referencia', required=True, default='/')
    state = fields.Selection([('draft', 'Borrador'),
                              ('confirm', 'Confirmado'),
                              ('liquidation', 'Liquidado'),
                              ('paidout', 'Pagado'),
                              ('cancel', 'Cancelado')],
                             string='Estado', default='draft')
    client_id = fields.Many2one('res.partner', string='Cliente', required=True,
                                domain=[('customer', '=', True), ('is_online', '=', True)],
                                states={'draft': [('readonly', False)]}, readonly=True)
    generate_date = fields.Date(string=u'Fecha creación', required=True, default=lambda *a: fields.Datetime.now(),
                              states={'draft': [('readonly', False)]}, readonly=True)
    liquidation_date = fields.Date(string=u'Fecha de liquidación', readonly=True)
    email = fields.Char(string='Email', required=True, states={'draft': [('readonly', False)]}, readonly=True)
    total_sale = fields.Float(string='Total de venta', readonly=True, compute='_compute_amount', store=True)
    total_dev = fields.Float(string=u'Total de devolución', readonly=True, compute='_compute_amount', store=True)
    total_liquidation = fields.Float(string='Total', readonly=True, compute='_compute_amount', store=True)
    total_payment = fields.Float(string='Total a facturar', readonly=True, compute='_compute_amount', store=True)
    line_id = fields.One2many(inverse_name='m_liquidation_id', comodel_name='m.liquidation.line', string='Facturas')
    invoice_id = fields.Many2one('account.invoice', string='Factura', readonly=True)
    invoice_date = fields.Date(string="Fecha", related='invoice_id.date_invoice', readonly=True)
    invoice_total = fields.Float(string="Total a Cobrar", related='invoice_id.amount_total', readonly=True)

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, readonly=True, states={'draft': [('readonly', False)]},
                                  default=_default_currency, track_visibility='always')

    calc_min_max = fields.Char(string="Rango de Venta", compute='_compute_amount', store=True)
    calc_rate = fields.Char(string="Fijo", compute='_compute_amount', store=True)
    calc_percent = fields.Char(string="Porciento", compute='_compute_amount', store=True)
    calc_formule = fields.Char(string="Formula", compute='_compute_amount', store=True)

    move_id = fields.Many2one('account.move', string='Asiento',
                              readonly=True, index=True, ondelete='restrict', copy=False,
                              help="Enlace al asiento generado automaticamente", related='invoice_id.move_id')
    payment_ids = fields.Many2many('account.move.line', string='Pagos', compute='_compute_payments')
    banner = fields.Char('Banner', compute=_get_server_url)

    execute_automatic = fields.Boolean(string='Ejecucion Automatica', default=False)



    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].get('m.liquidation') or '/'
        return super(m_liquidation, self).create(vals)

    @api.multi
    def unlink(self):
        for item in self:
            if item.state not in ['draft', 'cancel']:
                raise osv.except_osv('ValidationError',
                                     u'No puede eliminar la solicitud %s sino está en estado Borrador ó Cancelado.'% item.name)
            for l in item.line_id:
                l.unlink()
        return super(m_liquidation, self).unlink()

    @api.onchange('client_id')
    def onchange_interval_type(self):
        if self.client_id:
            self.email = self.client_id.email

    def wkf_action_confirm(self):
        # chequear que exista un valor a facturar.
        if self.total_payment <= 0 :
            raise ValidationError("No se puede confirmar la liquidación porque no existe valor a facturar, revise halla "
                                  "cargado las lineas o que no este fuera de rango el total de las ventas, Gracias!!")

        self.write({'state': 'confirm'})


    def wkf_action_paidout(self):
        # no hacer nada por ahora
        self.write({'state': 'paidout'})

    def wkf_action_liquidation(self):
        # generar factura de venta, con los datos del cliente
        inv = self.action_create_invoice()
        self.invoice_id = inv and inv.id
        self.liquidation_date = fields.Datetime.now()

        # enviar correo al cliente
        #self.automatic_send_mail()

        self.write({'state': 'liquidation'})

    def wkf_action_cancel(self):
        # tengo que liberar todos las lineas y notificar al cliente
        for l in self.line_id:
            l.unlink()

        self.write({'state': 'cancel'})

    def automatic_send_mail(self):
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('monitor', 'm_email_template_sale')[1]
        plantilla = self.env['email.template'].browse(template_id)
        plantilla.sudo().send_mail(self.id)

    @api.multi
    def m_send_mail(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        template = self.env.ref('monitor.m_email_template_sale', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='m.liquidation',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
        )
        return {
            'name': 'Compose Email',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def btn_reload(self):
        url = self.client_id.url
        db = self.client_id.db
        username = self.client_id.user_admin
        password = self.client_id.user_passw

        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
        common.version()
        uid = common.authenticate(db, username, password, {})

        # obtener modulos
        models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

        # factura de venta o rembolso de venta (out_invoice, out_refund)
        # estado abierta o pagada (open, paid)
        # no este en liquidacion
        result = models.execute_kw(db, uid, password,
                          'account.invoice', 'search_read',
                          [[
                            ['type', 'in', ['out_invoice', 'out_refund']],
                            ['state', 'in', ['open', 'paid']],
                            ['x_is_liquidation', '=', False]
                          ]],
                          {'fields': ['id', 'type', 'date_invoice', 'partner_id', 'number', 'state', 'amount_total']})

        res = []
        invoice_ids = []
        data = {}
        for r in result:
            data.update({
                'type': r['type'],
                'invoice_date': r['date_invoice'],
                'invoice': r['number'],
                'customer_id': r['partner_id'][1],
                'total': r['amount_total'],
                'invoice_id': r['id'],
                'invoice_state': r['state'],
                'm_liquidation_id': self.id
            })
            invoice_ids.append(r['id'])
            a = self.env['m.liquidation.line'].create(data)
            res.append(a.id)

        # actualizar en el cliente
        models.execute_kw(db, uid, password, 'account.invoice', 'write', [invoice_ids, {
            'x_id_liquidation': self.id,
            'x_is_liquidation': '1'
        }])
        return res


    def action_create_invoice(self):
        inv = self.invoice_create()
        return inv

    def _prepare_invoice_line(self):
        # obtener el producto especifico del tipo instancia en linea, y cargar los datos de ahi
        product = self.env['product.template'].search([('for_instance', '=', True)])

        account_id = product.property_account_income.id
        if not account_id:
            account_id = product.categ_id.property_account_income_categ.id

        #pu = self.total_liquidation
        pu = self.total_payment

        res = {
            'name': product.name,
            'account_id': account_id,
            'price_unit': pu,
            'quantity': 1,
            'product_id': product.id or False,
        }
        return res

    def invoice_line_create(self):
        create_ids = []
        vals = self._prepare_invoice_line()
        if vals:
            inv_id = self.env['account.invoice.line'].create(vals)
            create_ids.append(inv_id.id)
        return create_ids

    def invoice_create(self):
        journal = self._default_journal()

        lines = self.invoice_line_create()
        res = {
            'name': '',
            'type': 'out_invoice',
            'partner_id': self.client_id.id,
            'account_id': self.client_id.property_account_receivable.id,
            'currency_id': journal.currency or journal.company_id.currency_id.id,
            'journal_id': journal.id,
            'company_id': self.env.user.company_id.id,
            'date_invoice': fields.Datetime.now(),
            'invoice_line': [(6, 0, lines)],
            'comment': "facturar instancia online",
        }

        inv_id = self.env['account.invoice'].create(res)
        return inv_id


class m_liquidation_line(models.Model):
    _name = 'm.liquidation.line'
    _description = 'Linea de la Liquidacion'

    m_liquidation_id = fields.Many2one(comodel_name='m.liquidation', string='Liquidacion', ondelete='cascade')
    type = fields.Selection([('out_invoice', 'Venta'), ('out_refund', 'Devolucion')], string='Tipo', default='sale')
    invoice_date = fields.Date(string='Fecha de factura')
    invoice = fields.Char(string='Nro. Factura')
    customer_id = fields.Char(string='Cliente')
    total = fields.Float(string='Valor total')
    invoice_id = fields.Integer(string='ID Factura')
    invoice_state = fields.Selection([('open', 'Abierta'), ('paid', 'Pagada')], string='Estado de la Factura')


    @api.multi
    def unlink(self):
        url = self.m_liquidation_id.client_id.url
        db = self.m_liquidation_id.client_id.db
        username = self.m_liquidation_id.client_id.user_admin
        password = self.m_liquidation_id.client_id.user_passw

        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})
        models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

        for line in self:
            # liberar la factura en el cliente
            models.execute_kw(db, uid, password, 'account.invoice', 'write', [line.invoice_id, {
                'x_id_liquidation': 0,
                'x_is_liquidation': False
            }])

        return super(m_liquidation_line, self).unlink()

