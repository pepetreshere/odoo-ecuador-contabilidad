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
from dateutil.relativedelta import relativedelta
from lxml import etree
from osv import fields, osv
from tools import config
from tools.translate import _
import decimal_precision as dp

class sale_order(osv.osv):
    
    _inherit = 'sale.order'

    def onchange_shop_id(self, cr, uid, ids, shop_id, context=None):
        if not context: context = {}
        res = super(sale_order, self).onchange_shop_id(cr, uid, ids, shop_id)
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        printer_id = user.printer_default_id and user.printer_default_id.id or None
        if shop_id:
            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
            if not printer_id:
                for printer in shop.printer_point_ids:
                    printer_id = printer.id
                    break
            res['domain'] = {'printer_id' : [('shop_id.id','=',shop.id)]}
            res['value']['printer_id'] = printer_id
        return res

    def default_get(self, cr, uid, fields_list, context=None):
        if not context:
            context={}
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        values = super(sale_order, self).default_get(cr, uid, fields_list, context)
        shop_id = None
        printer_id = None
        if user.printer_default_id:
            shop_id = user.printer_default_id.shop_id.id
            printer_id = user.printer_default_id.id
        if not shop_id:
            for shop in user.shop_ids:
                shop_id = shop.id
                for printer in shop.printer_point_ids:
                    printer_id = printer.id
                    break
                break
        if not shop_id or not printer_id:
            raise osv.except_osv('Error!', _("Your User doesn't have shops assigned to make sales order"))
        values.update({
                       'shop_id':shop_id,
                       'printer_id': printer_id,
                       })
        return values
    
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        if not context:
            context={}
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        shop_obj = self.pool.get('sale.shop')
        shop_ids = [shop.id for shop in user.shop_ids]
        domain_shop = [('id','in', shop_ids)]
        res = super(sale_order, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if view_type == 'form' and uid != 1:
            for field in res['fields']:
                if field == 'shop_id':
                    doc = etree.XML(res['arch'])
                    nodes = doc.xpath("//field[@name='shop_id']")
                    for node in nodes:
                        node.set('widget', "selection")
                        node.set('domain', str(domain_shop))
                    res['arch'] = etree.tostring(doc)
                    shop_selection = shop_obj._name_search(cr, uid, '', [('id', 'in', shop_ids)], context=context, limit=None, name_get_uid=uid)
                    res['fields']['shop_id']['selection'] = shop_selection
        return res           

    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_unit * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'base_iva_0': 0.0,
                'base_iva_12': 0.0,
                'iva': 0.0,
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'total_descuento': 0.0,
                'total_descuento_per': 0.0,
                'total_ice': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            #TODO calcular el total del valor del ICE
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
                tax = self._amount_line_tax(cr, uid, line, context=context)
                if tax > 0.0:
                    res[order.id]['base_iva_12'] += cur_obj.round(cr, uid, cur, line.price_subtotal)
                    res[order.id]['iva'] += cur_obj.round(cr, uid, cur, tax)
                else:
                    res[order.id]['base_iva_0'] = cur_obj.round(cr, uid, cur, line.price_subtotal)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
            #TODO: calcular el total de descuento
            total_amount_discount = 0.0
            for line in order.order_line:
                total_amount_discount += line.price_unit - (line.price_unit * (1 - (line.discount or 0.0) / 100.0))
            res[order.id]['total_descuento'] = cur_obj.round(cr, uid, cur, total_amount_discount)
            res[order.id]['total_descuento_per'] = res[order.id]['amount_untaxed'] > 0 and res[order.id]['total_descuento'] / res[order.id]['amount_untaxed'] or 0.0
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'printer_id':fields.many2one('sri.printer.point', 'Printer Point', readonly=True, states={'draft':[('readonly',False)]}),
        'delivery_note_ids':fields.many2many('account.remision', 'sale_order_delivery_note_rel', 'sale_order_id', 'delivery_note_id', 'Delivery Notes', readonly=True, states={'draft':[('readonly',False)]}),
        'total_descuento': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Descuento Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),                
        'total_descuento_per': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),  
        'total_ice': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='ICE Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
        'base_iva_0': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Base IVA 0',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
        'base_iva_12': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Base IVA 12',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
        'iva': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='IVA',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax."),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Taxes',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Total',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
        }


    def _get_automatic(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.generate_automatic

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        res = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context)
        #TODO: Agregar paso de referencias de agencía y punto de impresion para guias de remision
        return res

    def _prepare_order_picking(self, cr, uid, order, context=None):
        res = super(sale_order, self)._prepare_order_picking(cr, uid, order, context)
        #TODO: Agregar paso de referencias de agencía y punto de impresion para guias de remision
        return res

    def action_check_ice(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        sale_order_obj = self.pool.get('sale.order')
        sale_orders = sale_order_obj.browse(cr, uid, ids, context)
        if context is None: context = {}
        ice = False
        count_normal_product = 0
        for order in sale_orders:
            for line in order.order_line:
                normal_product = True
                for tax in line.tax_id:
                    if tax.type_ec == 'ice':
                        ice = True
                        normal_product = False
                if normal_product:
                    count_normal_product += 1
            if not ice or count_normal_product == 0:
                wf_service.trg_validate(uid, 'sale.order', order.id, 'order_confirm', cr)
            else:
                wizard_id = self.pool.get("sale.order.ice.wizard").create(cr, uid, {}, context=dict(context, active_ids=ids))
                return {
                    'name':_("Sale Order Options"),
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'sale.order.ice.wizard',
                    'res_id': wizard_id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]',
                    'context': dict(context, active_ids=ids)
                }
        return True
sale_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: