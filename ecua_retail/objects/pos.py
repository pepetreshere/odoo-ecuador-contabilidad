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

class pos_config(osv.osv):
    _inherit = 'pos.config'

    _columns = {
                'sri_printer_point_id': fields.many2one('sri.printer.point', 'SRI Printer Point',
                                                        help="SRI Authorized Printer Point"),
                'invoice_sequence_id': fields.related(
                                            'sri_printer_point_id',
                                            'invoice_sequence_id',
                                            type="many2one",
                                            relation="sri.printer.point",
                                            string="Invoice IDs Sequence",
                                            store=False),
                }
        
pos_config()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: