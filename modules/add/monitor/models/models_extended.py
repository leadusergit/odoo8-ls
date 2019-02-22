# -*- encoding: utf-8 -*-

from openerp import fields, models, api


class res_partner(models.Model):
    _inherit = 'res.partner'

    is_online = fields.Boolean(string='Instancia Online', default=False)
    online = fields.Boolean(string='Instancia Online', default=False)
    init_date = fields.Date(string='Fecha inicio', required=False)
    end_date = fields.Date(string='Fecha final', required=False)
    user_quantity = fields.Integer(string='Cantidad de usuarios', required=False)
    multiples_session = fields.Boolean(string='Multiples sessiones', default=False, help="Permitir multiples sessiones por usuario")
    url = fields.Char(string='URL', required=False, help="URL a la instancia del cliente")
    db = fields.Char(string='Base de datos', required=False, help="Nombre de la BD del cliente")
    user_admin = fields.Char(string='Usuario', required=False, help="Usuario ADMIN de la instancia")
    user_passw = fields.Char(string='Clave', required=False, help="Clave del usuario")

    schedule_conf_id = fields.One2many(inverse_name='client_id', comodel_name='m.liquidation.schedule.conf', string='Config. Schedule')



class product_template(models.Model):
    _inherit = 'product.template'

    for_instance = fields.Boolean(string='Para instancia', default=False)


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def confirm_paid(self):
        self.set_liquidation_paid()
        return super(account_invoice, self).confirm_paid()

    def set_liquidation_paid(self):
        # buscar liquidacion y ponerla en estado pagada
        liq_id = self.env['m.liquidation'].search([('invoice_id', '=', self.id)])
        if liq_id:
            liq_id.wkf_action_paidout()
