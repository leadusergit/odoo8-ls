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
    "name": "Hotel Housekeeping Management",
    "version": "0.05",
    "author": "OpenERP SA",
    "images": [],
    "license": "",
    "category": "Generic Modules/Hotel Housekeeping",
    "website": "http://www.leadsolutions.ec",
    "depends": ["hotel"],
    "demo": [
        "views/hotel_housekeeping_data.xml",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/hotel_housekeeping_report.xml",
        "views/activity_detail.xml",
        "wizard/hotel_housekeeping_wizard.xml",
        "views/hotel_housekeeping_workflow.xml",
        "views/hotel_housekeeping_view.xml",
    ],
    'installable': True,
    'auto_install': False,
}
