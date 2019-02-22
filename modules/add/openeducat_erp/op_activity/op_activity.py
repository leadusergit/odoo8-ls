# -*- coding: utf-8 -*-
###############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech-Receptives(<http://www.techreceptives.com>).
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
###############################################################################

from openerp import models, fields


class OpActivity(models.Model):
    _name = 'op.activity'

#     name = fields.Char(string='Activity Name', size=128, required=True)
    student_id = fields.Many2one('op.student', 'Student', required=True)
    faculty_id = fields.Many2one('op.faculty', 'Faculty')
    type_id = fields.Many2one('op.activity.type', 'Activity Type')
    date = fields.Date('Date')


class OpActivityType(models.Model):
    _name = 'op.activity.type'

    name = fields.Char('Activity Type', size=128, required=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
