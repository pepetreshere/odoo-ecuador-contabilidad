# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2011  Christopher Ormaza, Ecuadorenlinea.net            #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

import netsvc
from osv import osv
from osv import fields
from tools.translate import _
from lxml import etree
import time
import psycopg2
import re
from lxml import etree
import decimal_precision as dp

class account_ice_type(osv.osv):
    
    _name = 'account.ice.type'
    
    _columns = {
                'code':fields.char('Code', size=5, required=True, ), 
                'name':fields.char('Name', size=255, required=True, ),
                'rate': fields.float('Rate', digits=(16, 2), required=True,), 
                    }
account_ice_type()

class product_product(osv.osv):

    _inherit = "product.product"
    
    _columns = {
                'sri_code':fields.char('SRI CODE', size=255),
                'ice_product':fields.boolean('ICE Product?', ), 
                'ice_type_id':fields.many2one('account.ice.type', 'ICE Type', required=False),
                }
    
product_product()

