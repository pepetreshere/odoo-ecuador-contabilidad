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
from osv import fields,osv
from tools.translate import _
import time
import re

class stock_partial_picking(osv.osv_memory):
    
    def _check_number(self,cr,uid,ids,context=None):
        cadena='(\d{3})+\-(\d{3})+\-(\d{9})'
        for obj in self.browse(cr, uid, ids):
            ref = obj['number']
            if obj['number']:
                if re.match(cadena, ref):
                    return True
                else:
                    return False
            else:
                return True
                
    _inherit = 'stock.partial.picking'
    _columns = {
                'delivery_note':fields.boolean('Make Delivery Note'),
                'carrier_id': fields.many2one('delivery.carrier', 'Carrier'),
                'placa':fields.char('Placa', size=8, required=False, readonly=False),
                'number': fields.char ('Number', size=17, required=False),
                'automatic':fields.boolean('Automatic?', required=False),
                'automatic_number': fields.char ('Number', size=17, readonly="2"),
                'shop_id':fields.many2one('sale.shop', 'Shop'),
                'printer_id':fields.many2one('sri.printer.point', 'Printer Point',),
                }
    
    _defaults = {
                 'delivery_note': False,
                 }
    
    _constraints = [(_check_number, _('The number is incorrect, it must be like 001-00X-000XXXXXX, X is a number'),['number'])]

        
    def do_partial(self, cr, uid, ids, context=None):
        #TODO: paso de referencias, y datos para crear guia de remision
        res = super(stock_partial_picking, self).do_partial(cr, uid, ids, context)
        return res

    def default_get(self, cr, uid, fields, context=None):
        doc_obj = self.pool.get('sri.type.document')
        if context is None:
            context = {}
        values = {}
        pick_obj = self.pool.get('stock.picking')
        res = super(stock_partial_picking, self).default_get(cr, uid, fields, context)
        picking_ids = context.get('active_ids', [])
        if not picking_ids:
            return res
        objs = pick_obj.browse(cr , uid, picking_ids)
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'stock.picking', context=context)
        automatic = False #self._get_automatic(cr, uid, context)
        for obj in objs:
            if obj.type in ('out', 'internal'):
                if 'automatic_number' in fields and 'number' in fields:
                    auth_line_id = doc_obj.search(cr, uid, [('name','=','delivery_note'), ('printer_id','=',obj.printer_id.id), ('shop_id','=',obj.shop_id.id), ('state','=',True),])
                    if auth_line_id:
                        if automatic:
                            automatic_number = doc_obj.get_next_value_secuence(cr, uid, 'delivery_note', False, obj.printer_id.id, 'account.remision', 'number_out', context)                            
                            res.update({'automatic_number': automatic_number})
                            res.update({'number': automatic_number})
#                if 'carrier_id' in fields:
#                    placa = obj.placa or obj.carrier_id.placa
#                    res.update({'carrier_id': obj.carrier_id.id, 'placa': placa})                
#                if 'delivery_note' in fields:
#                    res.update({'delivery_note': obj.delivery_note})
#                if 'shop_id' in fields:
#                    res.update({'shop_id': obj.shop_id.id})
#                if 'printer_id' in fields:
#                    res.update({'printer_id': obj.printer_id.id})
        return res

    def onchange_data(self, cr, uid, ids, automatic, shop_id=None, printer_id=None, context=None):
        doc_obj = self.pool.get('sri.type.document')
        values = {}
        if context is None:
            context = {}
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'stock.picking', context=context)
        shop_ids = []
        curr_shop = False
        if shop_id:
            curr_shop = self.pool.get('sale.shop').browse(cr, uid, [shop_id, ], context)[0]
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        if curr_shop:
            if printer_id:
                auth_line_id = doc_obj.search(cr, uid, [('name','=','delivery_note'), ('printer_id','=',printer_id), ('shop_id','=',curr_shop.id), ('state','=',True),])
                if auth_line_id:
                    if automatic:
                        values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'delivery_note', False, printer_id, 'account.remision', 'number_out', context)
                        values['number'] = values['automatic_number']
                        values['date'] = time.strftime('%Y-%m-%d')
                else:
                    values['automatic'] = False
                    values['date'] = None
        return {'value': values, }

stock_partial_picking()
