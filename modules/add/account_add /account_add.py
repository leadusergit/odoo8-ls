# -*- coding: utf-8 -*-

import time
import datetime
from datetime import date
from datetime import datetime
from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging
import openerp.addons.decimal_precision as dp


class Account(osv.osv):
    _inherit = 'account.account' 
    __logger = logging.getLogger(_inherit) 
    
    _columns = {                
        'partner_id': fields.many2one ('res.partner','Partner',readonly=False,required=False),
       }
             
       
    _defaults = {

        }
Account()