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


class sale_order_ice_wizard(osv.osv_memory):
    _name = 'sale.order.ice.wizard'
    
    def split_action(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        print context
        wizard = self.browse(cr, uid, ids[0])
        act_obj = self.pool.get('ir.actions.act_window')
        mod_obj = self.pool.get('ir.model.data')
        sale_order_obj = self.pool.get('sale.order')
        sale_order = sale_order_obj.browse(cr, uid, context.get('active_id', False), context)
        new_sale_order = self._split_sale_order(cr, uid, context)
        xml_id = 'action_order_form'
        result = mod_obj.get_object_reference(cr, uid, 'sale', xml_id)
        id = result and result[1] or False
        result = act_obj.read(cr, uid, id, context=context)
        sale_order_domain = []
        sale_order_domain.append(('id', '=', new_sale_order))
        result['domain'] = sale_order_domain
        return result        
    
    def _split_sale_order(self, cr, uid, context=None):
        wf_service = netsvc.LocalService('workflow')
        sale_order_obj = self.pool.get('sale.order')
        print context
        if not context:
            context = {}
        ids = context.get('active_ids', [])
        order_id =False
        for order in sale_order_obj.browse(cr, uid, ids):
            order_values = sale_order_obj.read(cr, uid, order.id, [ 
                                                  'shop_id', 
                                                  'printer_id',
                                                  'date_order',
                                                  'client_order_ref', 
                                                  'partner_id', 
                                                  'partner_invoice_id', 
                                                  'pricelist_id', 
                                                  'partner_order_id', 
                                                  'partner_shipping_id', 
                                                  'project_id', 
                                                  'order_line', 
                                                  'user_id', 
                                                  'incoterm', 
                                                  'picking_police', 
                                                  'order_police', 
                                                  'invoice_quantity', 
                                                  'carrier_id', 
                                                  'payment_term',
                                                  'fiscal_position',
                                                  'note',])
            order_values.update({      
                'state': 'draft',
                'order_line': [],
            })
            del order_values['id']
            # take the id part of the tuple returned for many2one fields
            for field in ('shop_id', 'printer_id', 'partner_id', 'partner_invoice_id', 'pricelist_id', 'partner_order_id', 
                          'partner_shipping_id', 'project_id', 'user_id', 'carrier_id',):
                if order_values.get(field, False):
                    order_values[field] = order_values[field] and order_values[field][0]

            order_id = sale_order_obj.create(cr, uid, order_values)
            cont = 0
            order_lines = order.order_line
            lst = []
            for line in order_lines:
                ice = False
                for tax in line.tax_id:
                    if tax.type_ec == 'ice':
                        ice = True
                if ice:
                    lst.append(line)
            for il in lst:
                self.pool.get('sale.order.line').write(cr,uid,il.id,{'order_id':order_id})
            if order_id:
                wf_service.trg_validate(uid, 'sale.order', order_id, 'order_confirm', cr)
            wf_service.trg_validate(uid, 'sale.order', order.id, 'order_confirm', cr)
        return order_id
    
sale_order_ice_wizard()