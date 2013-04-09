# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Christopher Ormaza                                                                           
# Copyright (C) 2012  Ecuadorenlinea.net                                  
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
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  
########################################################################

from osv import fields,osv
import decimal_precision as dp
from tools.translate import _

class sustento_tributario(osv.osv):
    
    _name = 'sri.tax.support'
    
    _columns = {
                    'code':fields.char('Code', size=4, required=True,),
                    'name':fields.char('Name', size=255, required=True,),
                    'voucher_type_ids':fields.many2many('sri.voucher.type', 'voucher_support_rel', 'support_id', 'voucher_id', 'Voucher Types'), 
                    }
    
sustento_tributario()