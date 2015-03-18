# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 David  Romero,
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
##############################################################################

import time
import netsvc
from datetime import date, datetime, timedelta
import decimal_precision as dp

import tools
from osv import fields, osv
from tools import config
from tools.translate import _

class account_tax(osv.osv):
    _inherit = "account.tax"

    def name_get(self, cr, uid, ids, context=None):
        '''
        Redefinimos el metodo original
        Agrega el codigo del impuesto cuando existe
        '''

        if not ids:
            return []
        res = []
        
        reads = self.read(cr, uid, ids, ['name','amount','type','description'], context=context)
        res = []
        for record in reads:
            #TODO: Trabajar con la version en espanol del nombre....
            if record['description']:
                name = '[' + record['description'] + '] ' + record['name']
            else: #
                name = record['name']
            res.append((record['id'], name))
        return res

account_tax()