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
    "name": "Hotel Restaurant Management",
    "version": "0.05",
    "author": "OpenERP SA",
    "images": [],
    "license": "",
    "category": "Generic Modules/Hotel Restaurant",
    "website": "http://www.leadsolutions.ec",
    "depends": ["hotel", "hotel_report_layout"],
    "demo": [
        "views/hotel_restaurant_data.xml",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/hotel_restaurant_report.xml",
        "wizard/hotel_restaurant_wizard.xml",
        "views/res_table.xml",
        "views/kot.xml",
        "views/bill.xml",
        "views/folio_order_report.xml",
        "views/hotel_restaurant_workflow.xml",
        "views/hotel_restaurant_sequence.xml",
        "views/hotel_restaurant_view.xml",
    ],
    "installable": True
}
