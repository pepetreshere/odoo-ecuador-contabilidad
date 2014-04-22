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

import netsvc
from osv import osv
from osv import fields
from tools.translate import _
import decimal_precision as dp

class account_invoice(osv.osv):

    _inherit = "account.invoice"


    def _withhold_exist(self, cr, uid ,ids, filed_name, arg, context=None):
        """
        Check if the invoice have a withhold asociated, return True or False
        """
        value = {}
        exist = False
        
        for invoice in self.browse(cr, uid, ids, context):
            
            if invoice.withhold_id:
                 exist = True
                 
            value[invoice.id] = exist
        
        return value


    _columns = {
                'withhold_id': fields.many2one('account.withhold', 'Withhold', states={'paid':[('readonly',True)]},
                                               help="number of related withhold"),      
                'withhold_line_ids': fields.related('withhold_id', 'withhold_line_ids', 
                                                    type='one2many', relation='account.withhold.line',
                                                    string='Withhold Lines', 
                                                    states={'paid':[('readonly',True)]},
                                                    help="Lines description of related withhold"),      
                'address_invoice': fields.char("Invoice address",
                                               help="Address of invoice"),
                'withhold_exist': fields.function(_withhold_exist, type='boolean', method=True, store=False,
                                                  help="Show internally if a withhold asociated exist"),
               }

#    TRESCLOUD - En este sprint no necesitamos esta funcionalidad, solo lo basico
    def copy(self, cr, uid, id, default={}, context=None):
        if context is None:
            context = {}
        default.update({
            'withhold_ids':[],
            'withhold_line_ids':[],
        })
        return super(account_invoice, self).copy(cr, uid, id, default, context)
    
#    TRESCLOUD - En este sprint no necesitamos esta funcionalidad, solo lo basico
    def action_cancel(self, cr, uid, ids, *args):
     #   ret_line_obj = self.pool.get('account.withhold.line')
        context={}
        wf_service = netsvc.LocalService("workflow")
        invoices = self.pool.get('account.invoice')
        invoice_obj=invoices.browse(cr, uid, ids, context)[0]
        withhold=self.pool.get('account.withhold').search(cr,uid,[('invoice_id','=',invoice_obj.id)])
        withhold_obj=self.pool.get('account.withhold').browse(cr,uid,withhold)
        for lines in withhold_obj:
            if lines.state == 'approved':
                    wf_service.trg_validate(uid, 'account.withhold', lines.id, 'canceled_signal', cr)
        return super(account_invoice, self).action_cancel(cr, uid, ids, context)

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        if context is None:
            context = {}
        default = default.copy()
        default['withhold_line_ids'] = False
        default['withhold_id']=False
        
        return super(account_invoice, self).copy(cr, uid, id, default, context=context)
    
account_invoice()


#class account_invoice(osv.osv):
#
#    _inherit = "account.invoice"
#    
#    def _number(self, cr, uid, ids, name, args, context=None):
#        result = {}
#        for invoice in self.browse(cr, uid, ids, args):
#            #result[invoice.id] = invoice.invoice_number
#        return result
#    _columns = {
#                #'number': fields.function(_number, method=True, type='char', size=17, string='Invoice Number', store=True, help='Unique number of the invoice, computed automatically when the invoice is created in Sales.'),
#                'address_invoice':fields.char("Invoice address"),
#                'total_retencion': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Total Retenido',
#                    store={
#                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
#                        'account.invoice.tax': (_get_invoice_tax, None, 20),
#                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
#                    },
#                    multi='all1'),
#                }
#    
#    def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
#            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
#        partner_obj = self.pool.get('res.partner')
#        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
#        if partner_id:
#            partner = partner_obj.browse(cr, uid, partner_id)
#            address_invoice = partner.street 
#            
#        res['value']['address_invoice'] = address_invoice
#        return res
#    
#account_invoice()