# -*- encoding: utf-8 -*-

from openerp import models, fields


class m_table_payment_conf(models.Model):
    _name = 'm.table.payment.conf'
    _description = 'Tabla de configuracion de cobro'
    _inherit = ['mail.thread']

    mmin = fields.Float(string=u'Mínimo', required=True)
    mmax = fields.Float(string=u'Máximo', required=True)
    rate = fields.Float(string=u'Tarifa', required=True)
    percent = fields.Float(string=u'Porciento', required=True)

    def calculate(self, valueTotal):
        # buscar cual rango le corresponde
        ranges = self.search([('mmin', '<=', valueTotal), ('mmax', '>=', valueTotal)])
        res = 0.0

        # tomar la primera coincidencia
        tarifa = porciento = 0.0
        for r in ranges:
            tarifa = r.rate
            porciento = r.percent

            # (tarifa + porciento del valorTotal)
            res = tarifa + self.porcentaje(porciento, valueTotal)
            break

        return res

    def porcentaje(self, x, y):
        return x * y / 100


