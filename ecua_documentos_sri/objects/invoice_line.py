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

class account_invoice_line(osv.osv):
    
    _inherit = 'account.invoice.line' 

    def _price_unit_final(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            price = line.price_unit * (1-(line.discount or 0.0)/100.0)
            res[line.id] = price
            if line.invoice_id:
                cur = line.invoice_id.currency_id
                res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res

    def _taxes_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            tax_obj = self.pool.get('account.tax')
            cur_obj = self.pool.get('res.currency')
            for line in self.browse(cr, uid, ids, context):
                res[line.id] = {
                    'base_iva': 0.0,
                    'base_no_iva': 0.0,
                    'base_iva_0': 0.0,
                    'total_retencion': 0.0,
                    'total_iva': 0.0,
                }
                no_iva = True
                for tax in line.invoice_line_tax_id:
                    if tax.type_ec == 'iva' and tax.amount >= 0:
                        no_iva = False
                if no_iva:
                    res[line.id]['base_no_iva'] = line.price_subtotal
                for tax in line.invoice_line_tax_id:
                    if tax.type_ec == 'iva' and tax.amount > 0:
                        taxes = tax_obj.compute_all(cr, uid, [tax], line.price_unit_final, line.quantity)
                        res[line.id]['base_iva'] += taxes['total']
                        res[line.id]['total_iva'] += taxes['total_included'] - taxes['total']
                    if tax.type_ec == 'iva' and tax.amount == 0:
                        taxes = tax_obj.compute_all(cr, uid, [tax], line.price_unit_final, line.quantity)
                        res[line.id]['base_iva_0'] += taxes['total']
                    if tax.type_ec in ('renta', 'iva') and tax.amount < 0:
                        taxes = tax_obj.compute_all(cr, uid, [tax], line.price_unit_final, line.quantity)
                        res[line.id]['total_retencion'] += taxes['total_included'] - taxes['total']
        return res


    _columns = {
                'price_unit_final': fields.function(_price_unit_final, method=True, type='float', digits_compute= dp.get_precision('Account'), string='Price Unit Final', store=True),
                'base_iva': fields.function(_taxes_all, method=True, digits_compute=dp.get_precision('Account'), string='IVA Base',
                    store={
                        'account.invoice.line': (lambda self, cr, uid, ids, c={}: ids, ['price_unit','product_id','quantity','discount','invoice_line_tax_id'], 20),
                    },
                    multi='tax_all_line'),
                'base_no_iva': fields.function(_taxes_all, method=True, digits_compute=dp.get_precision('Account'), string='IVA Base',
                    store={
                        'account.invoice.line': (lambda self, cr, uid, ids, c={}: ids, ['price_unit','product_id','quantity','discount','invoice_line_tax_id'], 20),
                    },
                    multi='tax_all_line'),
                'base_iva_0': fields.function(_taxes_all, method=True, digits_compute=dp.get_precision('Account'), string='IVA Base',
                    store={
                        'account.invoice.line': (lambda self, cr, uid, ids, c={}: ids, ['price_unit','product_id','quantity','discount','invoice_line_tax_id'], 20),
                    },
                    multi='tax_all_line'),
                'total_retencion': fields.function(_taxes_all, method=True, digits_compute=dp.get_precision('Account'), string='IVA Base',
                    store={
                        'account.invoice.line': (lambda self, cr, uid, ids, c={}: ids, ['price_unit','product_id','quantity','discount','invoice_line_tax_id'], 20),
                    },
                    multi='tax_all_line'),
                'total_iva': fields.function(_taxes_all, method=True, digits_compute=dp.get_precision('Account'), string='IVA Base',
                    store={
                        'account.invoice.line': (lambda self, cr, uid, ids, c={}: ids, ['price_unit','product_id','quantity','discount','invoice_line_tax_id'], 20),
                    },
                    multi='tax_all_line'),
                    }
account_invoice_line()