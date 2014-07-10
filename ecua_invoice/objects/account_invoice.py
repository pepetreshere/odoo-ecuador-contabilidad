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
    
    #DR cambia el valor automaticamente del periodo fiscal sgun la secha
    def onchange_date(self, cr, uid, ids, date_invoice, context=None):
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
        res = {'value': {'period_id': periodo} ,'warning': warning }
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
        printer_point_id = printer_point_obj.search(cr,uid,[])[0]

        if printer_point_id:
            return printer_point_id 

        return printer_point_id
    
    def _suggested_internal_number(self, cr, uid, printer_id, company_id=None, context=None):
        '''Numero de factura sugerida para facturas de venta y compra, depende del punto de impresion
           Puede ser redefinida posteriormente por ejemplo para numeracion automatica
        '''
        printer = self.pool.get('sri.printer.point').browse(cr, uid, printer_id, context=context)
        number = printer.name + "-" + printer.shop_id.number + "-"
        return number
    
    _defaults = {
       'printer_id': _default_printer_point,
    } 
account_invoice()
