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
        ALlow delete a invoice in draft state
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


#    _constraints = [(_check_number_invoice,_('The number of Document is incorrect, it must be like 00X-00X-000XXXXXX, X is a number'),['invoice_number_out','invoice_number_in','number_liquidacion'])]
    
    #TRESCLOUD - se removio las lineas de la funcion ya que la evaluacion de extranjero se debe realizar en las posicioens fiscales
#    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
#        # no hacemos nada
#        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
#        
#        # actualizamos los campos nuevos de direccion y telefono
#        partner_obj = self.pool.get('res.partner')
#        address_invoice=False
#        address_phone=False
#        if partner_id:
#            partner = partner_obj.browse(cr, uid, partner_id)
#            #TODO - Deberia ser la direccion y telefono de facturacion
#            address_invoice = partner.street
#            address_phone = partner.phone
#        res['value']['invoice_address'] = address_invoice
#        res['value']['invoice_phone'] = address_phone
#
#        return res
    

account_invoice()
