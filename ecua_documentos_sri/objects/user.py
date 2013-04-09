# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Christopher Ormaza
# Copyright (C) 2013  Ecuadorenlinea.net
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

import time
import netsvc
from datetime import date, datetime, timedelta

from osv import fields, osv
from tools import config
from tools.translate import _

class res_users(osv.osv):
    _inherit = 'res.users'
    _columns = {
                'shop_ids':fields.many2many('sale.shop', 'rel_user_shop', 'user_id', 'shop_id', 'Shops'),
                'printer_default_id':fields.many2one('sri.printer.point', 'Printer Point Default', required=False),
                    }
res_users()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: