
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Christopher                                                                           
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
#along with this program.  If not, see http://www.gnu.org/licenses.
########################################################################

from osv import osv
from osv import fields
import decimal_precision as dp
from tools.translate import _

class account_move_line(osv.osv):

    _inherit = 'account.move.line'

    _columns = {
                
        }
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        result = []
        types = {
                'out_invoice': 'FACT-CLI: ',
                'in_invoice': 'FACT-PROV: ',
                'out_refund': 'NC-CLI: ',
                'in_refund': 'NC-PROV: ',
                'liquidation': 'LIQ-COMP: ',
                }
        for line in self.browse(cr, uid, ids, context=context):
            name = line.move_id.name
            if line.ref:
                name = (line.move_id.name or '') + ' ('+line.ref+')' 
            if line.invoice:
                type = line.invoice.type
                number = ''
                if type == 'out_invoice':
                    number = line.invoice.invoice_number_out or ''
                if type == 'in_invoice':
                    number = line.invoice.invoice_number_in or ''
                if type == 'out_refund':
                    number = line.invoice.number_credit_note_out or ''
                if type == 'in_refund':
                    number = line.invoice.number_credit_note_in or ''
                if line.invoice.liquidation:
                    number = line.invoice.number_liquidation or ''
                name = types[type] + number + (line.ref and ' ('+line.ref+')' or '')
            result.append((line.id, name))
        return result
account_move_line()