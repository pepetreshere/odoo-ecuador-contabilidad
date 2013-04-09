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

from osv import osv
from osv import fields
import decimal_precision as dp
from tools.translate import _
import time

class account_invoice_tax(osv.osv):
    
    _inherit = "account.invoice.tax"

    def compute(self, cr, uid, invoice_id, context=None):
        if not context:
            context = {}
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = inv.company_id.currency_id.id
        for line in inv.invoice_line:
            tax_iva = []
            taxes = []
            ice = False
            for tax in line.invoice_line_tax_id:
                if tax.type_ec == "ice":
                    ice = True
            for tax in line.invoice_line_tax_id:
                if tax.type_ec == "iva":
                    tax_iva.append(tax)
                else:
                    taxes.append(tax)
            #computo de ice
            if ice:
                for tax in tax_obj.compute_all(cr, uid, taxes, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id)['taxes']:
                    tax_browse = tax_obj.browse(cr, uid, tax['id'], context)
                    val={}
                    val['invoice_id'] = inv.id
                    val['name'] = tax['name']
                    val['amount'] = tax['amount']
                    val['manual'] = False
                    val['sequence'] = tax['sequence']
                    val['base'] = tax['price_unit'] * line['quantity']
    
                    if inv.type in ('out_invoice','in_invoice'):
                        val['base_code_id'] = tax['base_code_id']
                        val['tax_code_id'] = tax['tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_collected_id'] or line.account_id.id
                        val['type_ec'] = tax_browse.type_ec
                        val['assets'] = tax_browse.assets
                        val['imports'] = tax_browse.imports
                        val['exports'] = tax_browse.exports
                    else:
                        val['base_code_id'] = tax['ref_base_code_id']
                        val['tax_code_id'] = tax['ref_tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_paid_id'] or line.account_id.id
                        val['type_ec'] = tax_browse.type_ec
                        val['assets'] = tax_browse.assets
                        val['imports'] = tax_browse.imports
                        val['exports'] = tax_browse.exports
    
                    key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                    if not key in tax_grouped:
                        tax_grouped[key] = val
                    else:
                        tax_grouped[key]['amount'] += val['amount']
                        tax_grouped[key]['base'] += val['base']
                        tax_grouped[key]['base_amount'] += val['base_amount']
                        tax_grouped[key]['tax_amount'] += val['tax_amount']
    
                #computo del IVA
                ice_value = 1
                if line.product_id.ice_type_id:
                    ice_value = 1+line.product_id.ice_type_id.rate
                for tax in tax_obj.compute_all(cr, uid, tax_iva, (line.price_unit * (ice_value) * (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id)['taxes']:
                    tax_browse = tax_obj.browse(cr, uid, tax['id'], context)
                    val={}
                    val['invoice_id'] = inv.id
                    val['name'] = tax['name']
                    val['amount'] = tax['amount']
                    val['manual'] = False
                    val['sequence'] = tax['sequence']
                    val['base'] = tax['price_unit'] * line['quantity']
    
                    if inv.type in ('out_invoice','in_invoice'):
                        val['base_code_id'] = tax['base_code_id']
                        val['tax_code_id'] = tax['tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_collected_id'] or line.account_id.id
                        val['type_ec'] = tax_browse.type_ec
                        val['assets'] = tax_browse.assets
                        val['imports'] = tax_browse.imports
                        val['exports'] = tax_browse.exports
                    else:
                        val['base_code_id'] = tax['ref_base_code_id']
                        val['tax_code_id'] = tax['ref_tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_paid_id'] or line.account_id.id
                        val['type_ec'] = tax_browse.type_ec
                        val['assets'] = tax_browse.assets
                        val['imports'] = tax_browse.imports
                        val['exports'] = tax_browse.exports
    
                    key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                    if not key in tax_grouped:
                        tax_grouped[key] = val
                    else:
                        tax_grouped[key]['amount'] += val['amount']
                        tax_grouped[key]['base'] += val['base']
                        tax_grouped[key]['base_amount'] += val['base_amount']
                        tax_grouped[key]['tax_amount'] += val['tax_amount']

            else:
                for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id)['taxes']:
                    tax_browse = tax_obj.browse(cr, uid, tax['id'], context)
                    val={}
                    val['invoice_id'] = inv.id
                    val['name'] = tax['name']
                    val['amount'] = tax['amount']
                    val['manual'] = False
                    val['sequence'] = tax['sequence']
                    val['base'] = tax['price_unit'] * line['quantity']
    
                    if inv.type in ('out_invoice','in_invoice'):
                        val['base_code_id'] = tax['base_code_id']
                        val['tax_code_id'] = tax['tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_collected_id'] or line.account_id.id
                        val['type_ec'] = tax_browse.type_ec
                        val['assets'] = tax_browse.assets
                        val['imports'] = tax_browse.imports
                        val['exports'] = tax_browse.exports
                    else:
                        val['base_code_id'] = tax['ref_base_code_id']
                        val['tax_code_id'] = tax['ref_tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_paid_id'] or line.account_id.id
                        val['type_ec'] = tax_browse.type_ec
                        val['assets'] = tax_browse.assets
                        val['imports'] = tax_browse.imports
                        val['exports'] = tax_browse.exports
    
                    key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                    if not key in tax_grouped:
                        tax_grouped[key] = val
                    else:
                        tax_grouped[key]['amount'] += val['amount']
                        tax_grouped[key]['base'] += val['base']
                        tax_grouped[key]['base_amount'] += val['base_amount']
                        tax_grouped[key]['tax_amount'] += val['tax_amount']
        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped
    
account_invoice_tax()
