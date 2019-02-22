# -*- coding: utf-8 -*-
#
#    Jamotion GmbH, Your Odoo implementation partner
#    Copyright (C) 2013-2017 Jamotion GmbH.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Created by Sebastien Pulver on 30.05.2017.
#
# imports of python lib
import logging

# imports of openerp
from openerp import models, api

# imports from odoo modules

# global variable definitions
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'
    _order = 'id'

    # Default methods

    # Fields declaration

    # compute and search fields, in the same order that fields declaration

    # Constraints and onchanges

    # CRUD methods

    # Action methods

    # Business methods

    @api.multi
    def _reconcile_payments(self):
        for order in self:
            aml = order.statement_ids.mapped('journal_entry_id').mapped(
                    'line_id') | order.account_move.line_id |\
                  order.invoice_id.move_id.line_id
            aml = aml.filtered(lambda r: not r.reconcile_id
                               and not r.reconcile_partial_id
                               and r.account_id.type == 'receivable'
                               and r.partner_id == order.partner_id
                               .commercial_partner_id)
            try:
                aml.reconcile()
            except:
                # There might be unexpected situations where the automatic
                # reconciliation won't work. We don't want the user to be
                # blocked because of this, since the automatic reconciliation
                # is introduced for convenience, not for mandatory accounting
                # reasons.
                _logger.error('Reconciliation did not work for order %s',
                              order.name)
                continue


class PosSession(models.Model):
    # Private attributes
    _inherit = 'pos.session'

    # Default methods

    # Fields declaration

    # compute and search fields, in the same order that fields declaration

    # Constraints and onchanges

    # CRUD methods

    # Action methods

    # Business methods

    @api.multi
    def _confirm_orders(self):
        self.ensure_one()
        result = super(PosSession, self)._confirm_orders()
        for session in self:
            orders = session.order_ids.filtered(
                    lambda order: order.state in ['invoiced', 'done'])
            orders.sudo()._reconcile_payments()

        return result





















