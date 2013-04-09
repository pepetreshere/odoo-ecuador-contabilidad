# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Ecuadorenlinea.net (<http://www.ecuadorenlinea.net>).
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

from osv import osv
from osv import fields
from tools.translate import _
import time
import re

class account_journal(osv.osv):
    _inherit = 'account.journal'
    
    _columns = {
                'liquidation':fields.boolean('Se usa para Liquidación de Compras?'),
                    }
account_journal()