# -*- coding: utf-8 -*-
#############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
#############################################################################

{
    "name": "Laundry Management",
    "version": "1",
    "author": "LS",
    "images": [],
    "license": "",
    "category": "Generic Modules/Laundry",
    "website": "http://www.leadsolutions.ec",
    "depends": ['base','stock','product','account','account_tax_ivacat','sale','sale_stock',
                'board','laundry_configuration'],
    "data": [
        'security/laundry_security.xml',
        'security/ir.model.access.csv',
        'laundry_sequence.xml',
        'laundry_delivery_guide_sequence.xml',
        'laundry_dispatch_guide_sequence.xml',
        'report_laundry.xml',
        #"views/sale_make_invoice_advance.xml",
        "views/laundry_management_view.xml",
        "views/laundry_claim_view.xml",
        "views/laundry_guia_entrega_view.xml",
        "views/laundry_recibe_guia_entrega_view.xml",
        "views/laundry_guia_despacho_view.xml",
        "views/laundry_recibe_guia_despacho_view.xml",
        #"views/sale_view.xml",
        "views/report_laundry_order.xml",  
        "views/report_laundry_order_chofer.xml", 
        "views/report_laundry_delivery_guide.xml",
        "views/report_laundry_dispatch_guide.xml",
        "views/report_laundry_claim.xml",   
        "wizard/laundry_make_invoice.xml",      
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
