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

class account_invoice_ice_wizard(osv.osv_memory):
    _name = 'account.invoice.ice.wizard'
    
    def split_action(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        wizard = self.browse(cr, uid, ids[0])
        act_obj = self.pool.get('ir.actions.act_window')
        mod_obj = self.pool.get('ir.model.data')
        inv_obj = self.pool.get('account.invoice')
        invoice = inv_obj.browse(cr, uid, context.get('active_id', False), context)
        new_invoice = self._split_invoice(cr, uid, context)
        xml_id = 'action_invoice_tree1'
        result = mod_obj.get_object_reference(cr, uid, 'account', xml_id)
        id = result and result[1] or False
        result = act_obj.read(cr, uid, id, context=context)
        invoice_domain = eval(result['domain'])
        invoice_domain.append(('id', '=', new_invoice))
        result['domain'] = invoice_domain
        return result        
    
    def _split_invoice(self, cr, uid, context=None):
        wf_service = netsvc.LocalService('workflow')
        inv_obj = self.pool.get('account.invoice')
        doc_obj = self.pool.get('sri.type.document')
        if not context:
            context = {}
        ids = context.get('active_ids', [])
        inv_id =False
        for inv in inv_obj.browse(cr, uid, ids):
            if inv.type in ["out_invoice"]:
                lst = []
                invoice = inv_obj.read(cr, uid, inv.id, ['name', 
                                                      'type', 
                                                      'number',
                                                      'invoice_number_out',
                                                      'reference', 
                                                      'comment', 
                                                      'date_due', 
                                                      'partner_id', 
                                                      'address_contact_id', 
                                                      'address_invoice_id', 
                                                      'partner_contact', 
                                                      'partner_insite', 
                                                      'partner_ref', 
                                                      'payment_term', 
                                                      'account_id', 
                                                      'currency_id', 
                                                      'invoice_line', 
                                                      'shop_id',
                                                      'printer_id',
                                                      'automatic',
                                                      'authorization_sales',
                                                      'tax_line', 
                                                      'journal_id', 
                                                      'period_id'])
                new_number = False
                if invoice.get('automatic', False):
                    new_number = doc_obj.get_next_value_secuence(cr, uid, 'invoice', False, inv.printer_id.id, 'account.invoice', 'invoice_number_out', context)
                invoice.update({
                    'state': 'draft',
                    'number': False,
                    'invoice_number_out':new_number,
                    'invoice_line': [],
                    'tax_line': []
                })
                # take the id part of the tuple returned for many2one fields
                for field in ('address_contact_id', 'address_invoice_id', 'partner_id', 
                              'shop_id', 'printer_id', 'authorization_sales',
                        'account_id', 'currency_id', 'payment_term', 'journal_id', 'period_id'):
                    if invoice.get(field, False):
                        invoice[field] = invoice[field] and invoice[field][0]

                inv_id = inv_obj.create(cr, uid, invoice)
                cont = 0
                invoice_lines = inv.invoice_line
                lst = []
                for line in invoice_lines:
                    ice = False
                    for tax in line.invoice_line_tax_id:
                        if tax.type_ec == 'ice':
                            ice = True
                    if ice:
                        lst.append(line)
                for il in lst:
                    self.pool.get('account.invoice.line').write(cr,uid,il.id,{'invoice_id':inv_id})
                inv_obj.button_compute(cr, uid, [inv.id], set_total=True)
            if inv_id:
                wf_service = netsvc.LocalService("workflow")
                inv_obj.button_compute(cr, uid, [inv_id], set_total=True)
                if invoice.get('automatic', False):
                    wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cr)
            wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_open', cr)
        return inv_id
    
account_invoice_ice_wizard()