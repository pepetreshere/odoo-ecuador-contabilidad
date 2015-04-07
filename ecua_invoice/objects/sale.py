# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Santiago Orozco, TRESCloud Cia Ltda.
# Copyright (C) 2013  TRESCloud Cia Ltda
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

from osv import fields, osv
import time
from tools import config
from tools.translate import _


class sale_order(osv.osv):
    _inherit = 'sale.order'
    _name = 'sale.order'

    _columns = {
        'printer_id': fields.many2one('sri.printer.point', 
                                      'Printer Point',
                                      required=False, #False por compatibilidad hacia atras 
                                      readonly=True, 
                                      help="SRI Printer Point",
                                      states={'draft': [('readonly', False)], 
                                              'sent': [('readonly', False)],
                                              }, 
                                      track_visibility='onchange')
    }

    def onchange_printer_id(self, cr, uid, ids, printer_id, context=None):
        """
        assigns the shop_id from the printer_id
        """
        res1 = {'value': {},'warning':{},'domain':{}}
        shop_id = False
        if printer_id:
            printer_obj = self.pool.get('sri.printer.point')
            printer = printer_obj.browse(cr, uid, printer_id, context)
            shop_id = printer.shop_id.id
        else:
            shop_id = False

        #usamos super porque en este modulo eliminamos la funcionalidad antigua para moverla a onchange_printer_id
        res2 = super(sale_order, self).onchange_shop_id(cr, uid, ids, shop_id, context=context)
        
        if res2.get('value',False):
            res1['value'].update(res2['value'])
        if res2.get('warning',False):
            res1['warning'].update(res2['warning'])
        if res2.get('domain',False):
            res1['domain'].update(res2['domain'])
            
        res1['value'].update({'shop_id': shop_id})

        return res1
        
    def onchange_shop_id(self, cr, uid, ids, shop_id, context=None):
        '''
        Este metodo ya no hace nada porque puede interferir con el metodo onchange_printer_id
        '''
        res1 = {'value': {},'warning':{},'domain':{}}
        return res1
        
    def _get_default_shop(self, cr, uid, context=None):
        '''
        Obtendremos la tienda asociada al usuario a traves del punto de impresion atado al usuario y a la 
        tienda asociada a dicho punto.
        La funcion base no nos sirve para este proposito ya que solo retorna la primera tienda de acuerdo 
        a la compania que esta atada al usuario.
        '''
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context)
        if user.printer_id:
            if user.printer_id.shop_id:
                return user.printer_id.shop_id.id
        return super(sale_order, self)._get_default_shop(cr, uid, context)

    def _default_printer_point(self, cr, uid, context=None):
        '''
        Nos apegamos a lo ya programado en facturas, debe seguir la misma logica
        '''
        invoice_obj = self.pool.get('account.invoice')
        return invoice_obj._default_printer_point(cr, uid, context=context)

    _defaults = {
        'shop_id': _get_default_shop,
        'printer_id': _default_printer_point,
    }
sale_order()


class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    
    def onchange_order_line_sale_order(self, cr, uid, ids, order_lines, context=None):
        '''
        Este metodo notifica al usuario cuando excede la cantidad de lineas definidas para sale order.
        '''
        res = {}
        #Obtenemos la cantidad de filas definidas para la tienda, por defecto son 20.
        user_obj = self.pool.get('res.users')
        printer_point_obj = self.pool.get('sri.printer.point')
        for user  in user_obj.browse(cr, uid, [uid], context):
            try:
                rows_sale_order = user.printer_id.shop_id.rows_sale_order
            except:
                raise osv.except_osv(_('¡Error!'),
                                     _('Debe configurar un punto de impresión por defecto para el usuario.'))
            
        #Obtenemos la cantidad de filas utilizadas en la vista tree.
        order_line = len(order_lines)+1        
        
        if(order_line >= rows_sale_order):
            raise osv.except_osv(_('¡Atención!'),
                                 _('Esta es la última línea válida, si agrega otra, puede alterar el formato de las facturas.\n' 
                                   'Si desea agregar más filas por favor consulte con el administrador del sistema.'))
        return res
    
sale_order_line()