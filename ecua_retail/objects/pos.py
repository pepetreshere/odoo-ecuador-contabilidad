# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Andres Calle, Patricio Rangles, Pablo Vizhnay
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
                'invoice_sequence_id' : fields.many2one('ir.sequence', 'Invoice IDs Sequence', readonly=True,
                                                        help="This sequence is automatically created by Odoo but you can change it "\
                                                        "to customize the generated invoice numbers of your orders."),
                'sri_printer_point' : fields.one2many('sri.printer.point', 'printer_point_id', 'SRI Printer Point', help='The related Tax Authority authorized printer point'),
                }    
        
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: