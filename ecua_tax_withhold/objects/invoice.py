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

import netsvc
from osv import osv
from osv import fields
from tools.translate import _
import time
import psycopg2
import re
from lxml import etree
import decimal_precision as dp

class account_invoice(osv.osv):

    _inherit = "account.invoice"
    
#    def _number(self, cr, uid, ids, name, args, context=None):
#        result = {}
#        for invoice in self.browse(cr, uid, ids, args):
#            #result[invoice.id] = invoice.invoice_number
#        return result
    _columns = {
                #'number': fields.function(_number, method=True, type='char', size=17, string='Invoice Number', store=True, help='Unique number of the invoice, computed automatically when the invoice is created in Sales.'),
                'address_invoice':fields.char("Invoice address"),
#                'total_retencion': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Total Retenido',
#                    store={
#                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
#                        'account.invoice.tax': (_get_invoice_tax, None, 20),
#                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
#                    },
#                    multi='all1'),
                }
    
    _defaults = {
               
                 }
    def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        partner_obj = self.pool.get('res.partner')
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        if partner_id:
            partner = partner_obj.browse(cr, uid, partner_id)
            address_invoice = partner.street 
            
        res['value']['address_invoice'] = address_invoice
        return res
    
account_invoice()