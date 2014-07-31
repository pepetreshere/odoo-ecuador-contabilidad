# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Andres Calle
# Copyright (C) 2013  TRESCLOUD Cia Ltda
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see http://www.gnu.org/licenses.
########################################################################

from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class sri_printer_point(osv.osv):
    _inherit = "sri.printer.point"
    
    _columns = {
                'pos_config_ids' : fields.one2many('pos.config', 'sri_printer_point_id', 'Retail Point of Sale Terminals',
                                        help="From the point of sale terminal you can issue automatically numbered documents"),
                }
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        d = {
            'invoice_sequence_id' : False,
            'pos_config_ids' : False,
        }
        d.update(default)
        return super(sri_printer_point, self).copy(cr, uid, id, d, context=context)
        
sri_printer_point()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: