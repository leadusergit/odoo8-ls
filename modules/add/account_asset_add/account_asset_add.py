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


class AccountAsset(osv.osv):
    _inherit = 'account.asset.asset' 
    
    _columns = {                
        #'partner_id': fields.many2one ('res.partner','Custodio',required=False,readonly=False,states={'open': [('readonly', True)]}),
        'employee_id': fields.many2one ('hr.employee','Custodio',required=False,readonly=False,states={'open': [('readonly', True)]}),
        'localization': fields.many2one ('hr.department','Localizacion',required=False,readonly=False,states={'open': [('readonly', True)]}),
       }
             

AccountAsset()