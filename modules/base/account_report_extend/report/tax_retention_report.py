# -*- encoding: utf-8 -*-
##############################################################################
#
#    HHRR Module
#    Copyright (C) 2009 GnuThink Software  All Rights Reserved
#    info@gnuthink.com
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.report import report_sxw

class taxretentionreport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(taxretentionreport,self).__init__(cr, uid, name, context)
        self.localcontext.update({
                'time':time,
            })

    def lines(self, header):
        result1 = {}
        res = {}
        for linea in header.lineas_ids:

            res = {
                'fecha': linea.fecha,
                'documento': linea.documento,
                'nombre': line.nombre,
                'ruc':linea.ruc,
                'b_imponible':linea.b_imponible,
                'porcentaje':linea.porcentaje,
                'valor':linea.valor,
                }
            if not (linea.impuesto in result1.keys()):
                result1[linea.impuesto] = []
            result1[linea.impuesto].append(res)
        return result1

report_sxw.report_sxw('report.account.tax', 'account.tax.header', 'addons/account_report_extend/report/tax_retention.rml', parser=taxretentionreport, header=False)
