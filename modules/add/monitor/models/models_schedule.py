# -*- encoding: utf-8 -*-
from datetime import datetime
from openerp import models, fields, api

from openerp.osv import osv


class m_liquidation_schedule_conf(models.Model):
    _name = 'm.liquidation.schedule.conf'
    _description = 'Configuracion del CRON'

    client_id = fields.Many2one('res.partner', string='Cliente', ondelete='cascade')
    date = fields.Date(string='A partir de', required=True)
    quantity_days = fields.Integer(string=u'Dias para la próxima ejecución', required=True)
    activo = fields.Boolean(string='Activo', default=True)

    @api.model
    def create(self, vals):
        confs = self.env['m.liquidation.schedule.conf'].search([('client_id', '=', vals['client_id'])])

        # solo puede haber un activo por Cliente
        for c in confs:
            if c.activo:
                raise osv.except_osv('ValidationError',
                                     u'Solo puede existir una configuración activa por cliente.')

        return super(m_liquidation_schedule_conf, self).create(vals)

    def _ready_to_create(self, date_actual, date_to_rest, days):
        date_format = "%Y-%m-%d"
        a = datetime.strptime(date_actual, date_format)
        b = datetime.strptime(date_to_rest, date_format)

        delta = a - b
        if delta.days >= days:
            return True
        else:
            return False

    def _execute(self):
        """
        ejecutada por el CRON,
         - Chequear todos los clientes Online
            Por cada uno
                - buscar si tiene configuracion de ejecucion, activa
                    - obtener la cantidad de dias
                    - buscar la ultima ejecucion en el historico
                      si existe:
                        - verificar que se cumpla la condicion para generar la liquidacion
                            Fecha actual - Fecha ultima ejecucion >= cantidad de dias
                      no existe:
                        - verificar que se cumpla la condicion para generar la liquidacion
                            Fecha actual - fecha configuracion >= cantidad de dias

        :return: Liquidation
        """
        m_liquidation = self.env['m.liquidation']
        m_history = self.env['m.liquidation.schedule.history']

        client_ids = self.env['res.partner'].search([('customer', '=', True), ('is_online', '=', True)])
        for client in client_ids:
            for conf in client.schedule_conf_id:
                if conf.activo:
                    days_to_execute = conf.quantity_days
                    history = self.env['m.liquidation.schedule.history'].search([('client_id', '=', client.id)], order="date_execute desc")

                    if len(history) > 0:
                        last_date_executed = history[0].date_execute
                        generate_liquidation = self._ready_to_create(fields.Date.today(), last_date_executed, days_to_execute)
                    else:
                        generate_liquidation = self._ready_to_create(fields.Date.today(), conf.date, days_to_execute)

                    if generate_liquidation:
                        res = {
                            'client_id': client.id,
                            'generate_date': fields.Date.today(),
                            'email': client.email or 'change@gmail.com'
                        }
                        liquidation_id = m_liquidation.create(res)
                        if liquidation_id:
                            # cargar las lineas a liquidar
                            liquidation_id.btn_reload()

                            # guardar en el historico
                            res = {
                                'm_liquidation_id': liquidation_id.id,
                                'date_execute': fields.Date.today()
                            }
                            m_history.create(res)
                    break

    @api.model
    def execute(self):
        self._execute()


class m_liquidation_schedule_history(models.Model):
    _name = 'm.liquidation.schedule.history'
    _description = 'historico de ejecucion automarica'

    date_execute = fields.Date(string=u'Fecha Ejecución')
    m_liquidation_id = fields.Many2one('m.liquidation', string=u'Liquidación', ondelete='cascade')
    client_id = fields.Many2one('res.partner', string='Cliente', ondelete='cascade',
                                related='m_liquidation_id.client_id', store=True)
    state = fields.Selection([('draft', 'Borrador'),
                              ('confirm', 'Confirmado'),
                              ('liquidation', 'Liquidado'),
                              ('paidout', 'Pagado'),
                              ('cancel', 'Cancelado')],
                             string='Estado', related='m_liquidation_id.state')

