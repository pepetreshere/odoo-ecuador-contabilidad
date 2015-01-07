# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Andres Calle, TRESCloud Cia Ltda.
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

from osv import fields, osv
from tools import config
from tools.translate import _


class sale_shop(osv.osv):
    _inherit = 'sale.shop'
    _columns = {
                'number':fields.char('SRI Number', size=3, help='This number is assigned by the SRI'),
                'printer_point_ids':fields.one2many('sri.printer.point', 'shop_id', 'Printer Points',),
                'user_ids':fields.many2many('res.users', 'rel_user_shop', 'shop_id', 'user_id', 'Users'),
                'sales_journal_id':fields.many2one('account.journal', 'Sales Journal', domain=[('type','=','sale')]), 
                'purchases_journal_id':fields.many2one('account.journal', 'Purchases Journal', domain=[('type','=','purchase')]), 
               # 'liquidation_journal_id':fields.many2one('account.journal', 'Liquidation of Purchases Journal', domain=[('type','=','purchase'),('liquidation','=',True)]),
                'credit_note_purchase_journal_id':fields.many2one('account.journal', 'Credit Note Purchases Journal', domain=[('type','=','purchase_refund')]),           
                'credit_note_sale_journal_id':fields.many2one('account.journal', 'Credit Note Sales Journal', domain=[('type','=','sale_refund')]),
                #'address_id':fields.many2one('res.partner.address', 'Address', ),
                'invoice_lines': fields.integer('Número de Líneas x Factura'),
                'establishment_address':fields.related('warehouse_id','partner_id',type='many2one',relation='res.partner',string='Establishment Address',help='The address of the property, used for tax purposes as generating electronic documents')  
                    }
    
    _defaults = {
        'invoice_lines': 15,  
        }
    
#    def _check_number(self,cr,uid,ids,context=None):
#        for n in self.browse(cr, uid, ids):
#            if not n.number:
#                return True
#            a=0
#            b= True
#            while (a<len(n.number)):
#                if(n.number[a]>='0' and n.number[a]<='9'):
#                    a=a+1
#                else:
#                    b=False
#                    break
#            return b
#
#    _constraints = [(_check_number,_('This field is only for numbers'), ['number'])]
#    
    
sale_shop()


class sri_printer_point(osv.osv):
    
    _name = 'sri.printer.point'
    
    _columns = {
                'name': fields.char('Name', size=3, required=True,help='This number is assigned by the SRI'),
                'shop_id': fields.many2one('sale.shop', 'Shop'),
                'invoice_sequence': fields.many2one('ir.sequence', string='Customer Invoices sequential', required=False,
                                                    help='If specified, will be used by the printer point to specify '
                                                         'the next number for the invoices'),
                'refund_sequence': fields.many2one('ir.sequence', string='Customer Refunds sequential', required=False,
                                                   help='If specified, will be used by the printer point to specify '
                                                        'the next number for the credit notes'),
                'debit_note_sequence': fields.many2one('ir.sequence', string='Debit Notes sequential', required=False,
                                                       help='If specified, will be used by the printer point to specify'
                                                            ' the next number for the debit notes'),
                'withhold_sequence': fields.many2one('ir.sequence', string='Withholds sequential', required=False,
                                                     help='If specified, will be used by the printer point to specify '
                                                          'the next number for the withholds'),
                'waybill_sequence': fields.many2one('ir.sequence', string='Waybills sequential', required=False,
                                                    help='If specified, will be used by the printer point to specify '
                                                         'the next number for the waybills'),
    }

    def _verify_repeated_sequences(self, cr, uid, ids, context=None):
        """
        This constraint checks whether the specified sequences are in use by other printer points.

        The logic comes as follows:
            * We collect the assigned sequences, and check whether values are not repeated.
              * It is an error to have repeated values among the sequence fields in the same object.
            * We check that the specified sequence values are not used in any other object. For
              that, we check for each object whether any of its sequence fields has a sequence IN the
              generated list from the current sequence, and has a distinct id (i.e. we're not including
              the current instance in the same criteria).
              * It is an error to find another object which shares either of the sequences in either of
                the fields.
        """

        for instance in self.browse(cr, uid, ids, context=None):
            values = [p and p.id for p in [
                instance.invoice_sequence,
                instance.refund_sequence,
                instance.debit_note_sequence,
                instance.withhold_sequence,
                instance.waybill_sequence
            ] if p]

            if values:
                #We evaluate this because we set at least one of
                #such fields to an existent ir.sequence reference.

                if len(values) != len(set(values)):
                    #If the length of the list is not the same as the length of a set
                    #with the same elements, it means that the list has REPEATED elements.
                    #
                    #We must get pissed off if that's the case.
                    return False
                found = self.search(cr, uid, ['&', ('id', '!=', instance.id),
                                              '|', ('invoice_sequence', 'in', values),
                                              '|', ('refund_sequence', 'in', values),
                                              '|', ('debit_note_sequence', 'in', values),
                                              '|', ('withhold_sequence', 'in', values),
                                                   ('waybill_sequence', 'in', values)], context=None)
                if found:
                    #We found an ID which is distinct to the current instance's ID AND
                    #also it has at least one sequence field with value among the values of
                    #the same fields in the current instance.
                    #
                    #We must get pissed off if that's the case.
                    return False
        return True
    
    def name_get(self,cr,uid,ids, context=None):
        if not context:
            context = {}
        res = []
        shop_id=False
        for r in self.read(cr,uid,ids,['name','shop_id'], context):
            name = r['name']
            if r['shop_id']:
                shop_id = r['shop_id'][0] or False
                name_shop = None
                if shop_id:
                    name_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id, context).number
                if name_shop:
                    name_shop+="-"+name
                res.append((r['id'], name_shop))
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.invoice_sequence_id:
                obj.invoice_sequence_id.unlink()
        return super(sri_printer_point, self).unlink(cr, uid, ids, context=context)

    _constraints = (
        (_verify_repeated_sequences,
         'Error: Al menos uno de los secuenciales está repetido o en uso dentro de otro Punto de Impresión',
         ['invoice_sequence', 'refund_sequence', 'debit_note_sequence', 'withhold_sequence', 'waybill_sequence']),
    )
    
sri_printer_point()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: