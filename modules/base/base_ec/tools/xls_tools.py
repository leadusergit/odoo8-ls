# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
from xlwt import easyxf, Formula

def get_style(bold=False, font_name='Calibri', height=12, font_color='black',
              rotation=0, align='center', vertical='center', wrap=True,
              border=True, color=None, format=None):
    str_style = ''
    if bold or font_name or height or font_color:
        str_style += 'font: '
        str_style += bold and ('bold %s, '%bold) or ''
        str_style += font_name and ('name %s, '%font_name) or ''
        str_style += height and ('height %s, '%(height*20)) or ''
        str_style += font_color and ('color %s, '%font_color) or ''
        str_style = str_style[:-2] + ';'
    if rotation or align or vertical or wrap:
        str_style += 'alignment: '
        str_style += rotation and ('rotation %s, '%rotation) or ''
        str_style += align and ('horizontal %s, '%align) or ''
        str_style += vertical and ('vertical %s, '%vertical) or ''
        str_style += wrap and ('wrap %s, '%wrap) or ''
        str_style = str_style[:-2] + ';'
    str_style += border and 'border: left thin, right thin, top thin, bottom thin;' or ''
    str_style += color and 'pattern: pattern solid, fore_colour %s;'%color or ''
    return easyxf(str_style, num_format_str = format)

def GET_LETTER(index):
    COLUMNS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    aux = index / len(COLUMNS)
    aux2 = index - (aux * len(COLUMNS))
    return (aux and COLUMNS[aux-1] or '') + COLUMNS[aux2]