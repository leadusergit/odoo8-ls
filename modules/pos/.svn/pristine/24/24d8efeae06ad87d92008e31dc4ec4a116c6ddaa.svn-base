from openerp import models, fields, api, _
from openerp.osv import osv
from openerp.exceptions import except_orm, ValidationError
from StringIO import StringIO
import urllib2, httplib, urlparse, gzip, requests, json
import openerp.addons.decimal_precision as dp
import logging
import datetime
from openerp.fields import Date as newdate
from datetime import datetime, timedelta, date
from dateutil import relativedelta
#Get the logger
_logger = logging.getLogger(__name__)

class account_tipo_tarjeta(models.Model):
	_name = 'account.tipo.tarjeta'
	_description = 'Tipo de tarjeta de credito'

	name = fields.Char('Nombre')

class account_journal(models.Model):
	_inherit = 'account.journal'

	is_credit_card = fields.Boolean('Tarjeta de Credito')


class account_voucher(models.Model):
	_inherit = 'account.voucher'

	is_credit_card = fields.Boolean('Es tarjeta de credito',related='journal_id.is_credit_card')
	nro_cupon = fields.Char('Nro Cupon')
	nro_tarjeta = fields.Char('Nro Tarjeta')
	cant_cuotas = fields.Integer('Cuotas')
	tipo_tarjeta = fields.Many2one('account.tipo.tarjeta',string='Tipo Tarjeta')

	@api.one
	@api.constrains('nro_cupon','nro_tarjeta','tipo_tarjeta')
	def _check_pago_tarjeta(self):
		if self.is_credit_card:
			if (not self.nro_cupon) or (not self.nro_tarjeta) or (not self.tipo_tarjeta):
				raise ValidationError("Debe ingresar los datos de pago de tarjeta")

