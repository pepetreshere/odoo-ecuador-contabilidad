# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Christopher Ormaza                                                                           
# Copyright (C) 2012  Ecuadorenlinea.net                                  
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
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  
########################################################################

from osv import fields,osv
import decimal_precision as dp
from tools.translate import _

class account_invoice(osv.osv):
    
    _inherit = 'account.invoice' 
    
    _columns = {
                'voucher_type_id':fields.many2one('sri.voucher.type', 'Voucher Type', required=False),
                'tax_support_id':fields.many2one('sri.tax.support', 'Tax Support', required=False),
                'transaction_usage_id':fields.many2one('sri.transaction.usage', 'Transaction Usage', required=False),                
                    }
    
    def _get_tax_support(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        company = user.company_id
        support_tax_id = None
        if not context:
            context = {}
        type = context.get('type', False)
        if type == 'out_invoice':
            if company.default_out_invoice_id:
                support_tax_id = company.default_out_invoice_id.id
        elif type == 'in_invoice' and (not context.get('liquidation', False)):
            if company.default_in_invoice_id:
                support_tax_id = company.default_in_invoice_id.id
        elif type == 'in_invoice' and context.get('liquidation', True):
            if company.default_liquidation_id:
                support_tax_id = company.default_liquidation_id.id
        elif type == 'out_refund':
            if company.default_out_refund_id:
                support_tax_id = company.default_out_refund_id.id
        elif type == 'in_refund':
            if company.default_in_refund_id:
                support_tax_id = company.default_in_refund_id.id
        return support_tax_id
    
    def _get_voucher_type(self, cr, uid, context=None):
        vou_typ_obj = self.pool.get('sri.voucher.type')
        voucher_type_id = None
        if not context:
            context = {}
        type = context.get('type', False)
        if type == 'out_invoice':
            voucher_type_id = vou_typ_obj.search(cr, uid, [('code','=','18')])
        elif type == 'in_invoice' and (not context.get('liquidation', False)):
            voucher_type_id = vou_typ_obj.search(cr, uid, [('code','=','01')])
        elif type == 'in_invoice' and context.get('liquidation', True):
            voucher_type_id = vou_typ_obj.search(cr, uid, [('code','=','03')])
        elif type == 'out_refund':
            voucher_type_id = vou_typ_obj.search(cr, uid, [('code','=','04')])
        elif type == 'in_refund':
            voucher_type_id = vou_typ_obj.search(cr, uid, [('code','=','04')])
        
        if voucher_type_id:
            voucher_type_id = voucher_type_id[0]
        else:
            voucher_type_id = None
        return voucher_type_id
    
    _defaults = {  
        'tax_support_id': _get_tax_support,
        'voucher_type_id': _get_voucher_type,  
        }

    def onchange_partner_id(self, cr, uid, ids, type, partner_id, voucher_type,\
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False, context=None):
        if not context:
            context = {}
        partner_obj = self.pool.get('res.partner')
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        #Cambios de dominios para ats
        tt_obj = self.pool.get('sri.transaction.usage')
        partner_obj = self.pool.get('res.partner')
        transaction_type_id = None
        filter_type = None
        partner = partner_obj.browse(cr, uid, partner_id)
        if partner.type_ref == 'ruc':
            filter_type = 'ruc'
        elif partner.type_ref == 'consumidor':
            filter_type = 'consu_final'
        elif partner.type_ref == 'cedula':
            filter_type = 'cedula'
        elif partner.type_ref == 'pasaporte':
            filter_type = 'pasaporte'
        if type == 'out_invoice':
            transaction_type_id = tt_obj.search(cr, uid, [('type_identification','=',filter_type),('name','=','VENTA')])
        elif type == 'in_invoice' and (not context.get('liquidation', False)):
            transaction_type_id = tt_obj.search(cr, uid, [('type_identification','=',filter_type),('name','=','COMPRA')])
        elif type == 'in_invoice' and context.get('liquidation', True):
            transaction_type_id = tt_obj.search(cr, uid, [('type_identification','=',filter_type),('name','=','COMPRA')])
        elif type == 'out_refund':
            transaction_type_id = tt_obj.search(cr, uid, [('type_identification','=',filter_type),('name','=','VENTA')])
        elif type == 'in_refund':
            transaction_type_id = tt_obj.search(cr, uid, [('type_identification','=',filter_type),('name','=','COMPRA')])

        if transaction_type_id:
            transaction_type_id = transaction_type_id[0]
        else:
            transaction_type_id = None
        
        tc_obj = self.pool.get('sri.voucher.type')
        domain_tax_support = []
        if voucher_type:
            voucher_t = tc_obj.browse(cr, uid, voucher_type)
            lista = []
            for sustention in voucher_t.sustention_ids:
                lista.append(sustention.id)
            domain_tax_support.append(('id', 'in', lista))
        res['value']['transaction_usage_id'] = transaction_type_id
        res['domain'] = {'tax_support_id':domain_tax_support}
        return res
account_invoice()