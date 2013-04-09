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

class res_company(osv.osv):
    
    _inherit = "res.company"
    
    _columns = {
                'default_in_invoice_id':fields.many2one('sri.tax.support', 'Default Tax Support in Invoices', required=False), 
                'default_out_invoice_id':fields.many2one('sri.tax.support', 'Default Tax Support out Invoices', required=False), 
                'default_in_refund_id':fields.many2one('sri.tax.support', 'Default Tax Support Credit Notes Suppliers', required=False), 
                'default_out_refund_id':fields.many2one('sri.tax.support', 'Default Tax Support Credit Notes Customers', required=False), 
                'default_liquidation_id':fields.many2one('sri.tax.support', 'Default Tax Support Liquidation of Purchases', required=False), 
                    }
res_company()