# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Andres Calle, Andrea García, Patricio Rangles
# Copyright (C) 2013  TRESCLOUD Cia Ltda
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

#TODO depurar las librerias...
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
    _name = "account.invoice"

  
    _columns = {
                #TODO hacer obligatorio el campo name que almacenara el numero de la factura
                'internal_number': fields.char('Invoice Number', size=17, readonly=False, help="Unique number of the invoice, computed automatically when the invoice is created."),
                #'supplier_invoice_number': fields.char('Supplier Invoice Number', size=18, help="The reference of this invoice as provided by the supplier.", readonly=True, states={'draft':[('readonly',False)]}),
               # 'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
                'printer_id':fields.many2one('sri.printer.point', 'Printer Point', required=False),
                'invoice_address':fields.char("Invoice address", help="Invoice address as in VAT document, saved in invoice only not in partner"),
                'invoice_phone':fields.char("Invoice phone", help="Invoice phone as in VAT document, saved in invoice only not in partner"),
               }


    def _check_number_invoice(self,cr,uid,ids, context=None):
            res = True

    def unlink(self, cr, uid, ids, context=None):
        """
        Allow delete a invoice in draft state
        """
        invoices = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        
        for inv in invoices:
            if inv['state'] == 'draft':
                unlink_ids.append(inv['id'])
                # write False in the invoice number, this allow eliminate the invoice
                self.write(cr, uid, inv['id'], {'internal_number':False}) 
            else:
                raise osv.except_osv(_('Invalid action!'), _('You can delete Invoice in state Draft'))
            
        return super(account_invoice, self).unlink(cr, uid, unlink_ids, context)


    def onchange_internal_number(self, cr, uid, ids, internal_number, context=None):
        
        value = {}
        
        if not internal_number:
            return {'value': value}
        
        number_split = str.split(internal_number,"-")

        if len(number_split) == 3 and number_split[2] !="":
            if len(number_split[2]) < 17:
                #require auto complete
                pos = 0
                fill = 9 - len(number_split[2])
                for car in number_split[2]:
                    if car != '0':
                        break
                    pos = pos + 1
                    
                number_split[2] = number_split[2][:pos] + "0" * fill + number_split[2][pos:] 
                
                value.update({
                    'internal_number': number_split[0] + "-" + number_split[1] + "-" + number_split[2],
                            })
            
        return {'value': value}
    
    def onchange_date_invoice(self, cr, uid, ids, date_invoice, context=None):
        '''
        Asigna un periodo fiscal acorde a la fecha
        '''
        res = {}  
        warning = {}
        periodo = ""
        if not date_invoice:
            return {}
        obj_period = self.pool.get('account.period')
        period_id = obj_period.search(cr,uid,[('date_start','<=',date_invoice),('date_stop','>=',date_invoice)])
        if not period_id:
            warning = {
                    'title': _('Warning!'),
                    'message': _('No existe un período contable para esta fecha. There is no date for this accounting period.')
                }
        else:
            period = obj_period.browse(cr, uid, period_id, context=context)
            periodo = period.pop().id
        res = {'value': {'period_id': periodo} ,
               'warning': warning, 
               'domain': {} }
        return res     

    
    def _default_printer_point(self, cr, uid, context=None):
        '''
        Si el usuario tiene configurado un printer point lo selecciona
        Caso contrario intenta con el 001-001
        '''
    
        printer_point_id = False
        #intenta el printer_point del usuario
        user_obj=self.pool.get('res.users')
        printer = user_obj.browse(cr,uid,uid).printer_id
        if printer:
            printer_point_id = printer.id
            return printer_point_id
        
        #si no esta definido usamos el primero que exista, usuallmente sera el 001-001
        printer_point_obj = self.pool.get('sri.printer.point')
        printer_point_id = printer_point_obj.search(cr,uid,[],limit = 1)

        if printer_point_id:
            return printer_point_id[0]

        return None
    
    def _suggested_internal_number(self, cr, uid, printer_id=None, type=None, company_id=None, context=None):
        '''Numero de factura sugerida para facturas de venta y compra, depende del punto de impresion
           Puede ser redefinida posteriormente por ejemplo para numeracion automatica
        '''
        if context is None:
            context = {}
        
        if context.has_key('type'):
            type = context ['type']
            
        if not printer_id:
            printer_id = _default_printer_point(cr, uid, context)
        
        number = '001-001-'

        if type in ['out_invoice','in_refund']:
            printer = self.pool.get('sri.printer.point').browse(cr, uid, printer_id, context=context)
            number = printer.shop_id.number + "-" + printer.name + "-"
        if type in ['in_invoice','out_refund']:
            number = '001-001-'
        return number


    def _default_internal_number(self, cr, uid, context=None):
        '''Numero de factura sugerida para facturas de venta y compra, depende del punto de impresion
           Puede ser redefinida posteriormente por ejemplo para numeracion automatica
        '''
        number = ''
        type = ''
        printer_id = None
        
        if context is None:
            context = {}
        
        if context.has_key('type'):
            type = context['type']
            
        if context.has_key('printer_id'):
            type = context['printer_id']
        
        if not printer_id:
            printer_id = self._default_printer_point(cr, uid, context)
        
        if printer_id and type:
            number = self._suggested_internal_number(cr, uid, printer_id, type, None, context)
        
        return number

    def _default_date_invoice(self, cr, uid, context=None):
        '''Fecha por defecto es hoy
        '''
        #TODO: Incluir el calculo de zona horaria
        #TODO: Colocar esta funcion en el default
        return str(lambda *a: time.strftime('%Y-%m-%d'),)
    
    _defaults = {
       'printer_id': _default_printer_point,
       'internal_number': _default_internal_number,
       'date_invoice': lambda *a: time.strftime('%Y-%m-%d'),
    } 
    
    def _prepare_invoice_header(self, cr, uid, partner_id, type, inv_date=None, context=None):
        """Retorna los valores ecuatorianos para el header de una factura
           Puede ser usado en ordenes de compra, venta, proyectos, facturacion desde bodegas, etc
           @partner_id es un objeto partner
           @type es el tipo de factura, ej. out_invoice
           @inv_date es la fecha prevista de la factura, si no se provee se asume hoy
        """

        if context is None:
            context = {}
        invoice_vals = {}
        
        partner_obj=self.pool.get('res.partner')
        invoice_address = partner_obj.get_company_address(cr,uid,partner_id) 
        invoice_phone = partner_obj.get_company_phone(cr,uid,partner_id)
        
        inv_obj=self.pool.get('account.invoice')
        printer_id=inv_obj._default_printer_point(cr,uid,uid)
        if printer_id:
            internal_number = inv_obj._suggested_internal_number(cr, uid, printer_id, type, context)
        
        invoice_vals.update({
                        'invoice_address': invoice_address or '',
                        'invoice_phone': invoice_phone or '',
                        'internal_number': internal_number or '',
                        'printer_id': printer_id
                        })
        return invoice_vals
account_invoice()
