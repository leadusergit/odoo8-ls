# -*- coding: utf-8 -*-

from openerp import tools, models, fields

class m_dashboard_liquidation(models.Model):
    _name = "m.dashboard.liquidation"
    _description = "Dashboard Liquidación"
    _auto = False

    generate_date = fields.Date(u'Fecha de Creación')
    state = fields.Selection([('draft', 'Borrador'),
                              ('confirm', 'Confirmado'),
                              ('liquidation', 'Liquidado'),
                              ('paidout', 'Pagado'),
                              ('cancel', 'Cancelado')])
    total_sale = fields.Float('Total de venta')
    total_dev = fields.Float('Total de devolución')
    total_liquidation = fields.Float('Total')
    total_payment = fields.Float('Total a facturar')
    cliente = fields.Char('Cliente', size=60)
    factura = fields.Char('Factura', size=60)


    def init(self, cr):
        tools.drop_view_if_exists(cr, 'm_dashboard_liquidation')
        cr.execute("""
                    create or replace view m_dashboard_liquidation as (
                        select
                            liq.id,
                            liq.generate_date,
                            liq.state,
                            liq.total_sale,
                            liq.total_liquidation,
                            liq.total_dev,
                            liq.total_payment,
                            r.name as cliente,
                            a.number as factura

                        from m_liquidation as liq
                        inner join res_partner r on liq.client_id = r.id
                        inner join account_invoice a on liq.invoice_id = a.id
                        where liq.state in ('confirm', 'liquidation', 'paidout'))
                 """)