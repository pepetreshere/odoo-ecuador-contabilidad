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
import time
import psycopg2
import re
from lxml import etree
import decimal_precision as dp

class account_invoice(osv.osv):

    def onchange_data(self, cr, uid, ids, invoice_number, type=None, shop_id=None, printer_id=None, date=None, context=None):
        if context is None: context = {}
        if not invoice_number and not shop_id and not printer_id:
            return {}
        values = {
                    'authorization': None,
                    'authorization_sales': None,
                    'automatic':False,
                    'date_invoice': None,
                  }
        domain = {}
        warning = {}
        liquidation = context.get('liquidation_purchase', False)
        printer_obj = self.pool.get('sri.printer.point')
        doc_obj=self.pool.get('sri.type.document')
        auth_obj = self.pool.get('sri.authorization')
        shop_obj = self.pool.get('sale.shop')
        curr_user = self.pool.get('res.users').browse(cr, uid, uid, context)
        shops_domain_ids = []
        type_invoice = type
        if liquidation: type_invoice = 'liquidation_purchase'
        if not printer_id and invoice_number:
            warning = {
                       'title': _('Warning!!!'),
                       'message': _('Document must have a printer point selected to validate number!!!'),
                       }
            return {'warning': warning}
        curr_shop = shop_id and shop_obj.browse(cr, uid, shop_id, context) or None
        journal_id = None
        name_document = None
        name_field = None
        if curr_shop:
            if type_invoice == 'out_invoice':
                journal_id = curr_shop.sales_journal_id and curr_shop.sales_journal_id.id or None
                name_document = 'invoice'
                name_field = 'invoice_number_out'
            if type_invoice == 'out_refund':
                journal_id = curr_shop.credit_note_sale_journal_id and curr_shop.credit_note_sale_journal_id.id or None
                name_document = 'credit_note'
                name_field = 'number_credit_note_out'
            if type_invoice == 'liquidation_purchase':
                journal_id = curr_shop.liquidation_journal_id and curr_shop.liquidation_journal_id.id or None
                name_document = 'liquidation'
                name_field = 'number_liquidation'
            values['journal_id'] = journal_id
        if invoice_number and printer_id:
            auth = self.pool.get('sri.authorization').check_if_seq_exist(cr, uid, name_document, invoice_number, printer_id, date, context)
            authorization = auth and auth_obj.browse(cr, uid, auth['authorization'], context) or None
            values['authorization'] = authorization.number
            #TODO asignar dependiendo del tipo de documento
            values['authorization_sales'] = authorization.id
        else:
            curr_user.printer_default_id and curr_user.printer_default_id.shop_id and shops_domain_ids.append(curr_user.printer_default_id.shop_id.id)
            for shop_allowed in curr_user.shop_ids:
                shops_domain_ids.append(shop_allowed.id)
            auth_line_id = doc_obj.search(cr, uid, [('name','=',name_document), ('printer_id','=',printer_id), ('state','=',True)])
            if auth_line_id:
                auth_line = doc_obj.browse(cr, uid, auth_line_id[0],context)
                values['authorization'] = auth_line.sri_authorization_id.number
                #TODO asignar dependiendo del tipo de documento
                values['authorization_sales'] = auth_line.sri_authorization_id.id
                next_number = doc_obj.get_next_value_secuence(cr, uid, name_document, False, printer_id, 'account.invoice', name_field, context)
                values[name_field] = next_number
                values['date_invoice'] = time.strftime('%Y-%m-%d')
            else:
                if printer_id and curr_shop:
                    printer = printer_obj.browse(cr, uid, printer_id, context)
                    warning = {
                               'title': _("There's not any authorization for generate documents for data input: Agency %s Printer Point %s") % (curr_shop.number, printer.name)
                               }
        domain['shop_id'] = [('id','in', shops_domain_ids)]
        return {'value': values, 'domain':domain, 'warning': warning}

    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        printer_obj = self.pool.get('sri.printer.point')
        doc_obj=self.pool.get('sri.type.document')
        values = super(account_invoice, self).default_get(cr, uid, fields_list, context=context)
        if not values:
            values={}
        automatic = context.get('automatic', False)
        type = context.get('type', False)
        curr_user = self.pool.get('res.users').browse(cr, uid, uid, context)
        printer = None
        if curr_user.printer_default_id:
            printer = curr_user.printer_default_id
        if not printer:
            for shop in curr_user.shop_ids:
                for printer_id in shop.printer_point_ids:
                    printer = printer_id
                    break
        if printer:
            values['shop_id'] = printer.shop_id.id
            values['printer_id'] = printer.id
            if type == 'out_invoice' and ('invoice_number_out') in fields_list:
                auth_line_id = doc_obj.search(cr, uid, [('name','=','invoice'), ('printer_id','=',printer.id), ('state','=',True)])
                if auth_line_id:
                    auth_line = doc_obj.browse(cr, uid, auth_line_id[0],context)
                    values['authorization'] = auth_line.sri_authorization_id.number
                    values['authorization_sales'] = auth_line.sri_authorization_id.id
                    if automatic:
                        values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'invoice', False, printer.id, 'account.invoice', 'invoice_number_out', context)
                        values['invoice_number_out'] = values['automatic_number']
                        values['date_invoice'] = time.strftime('%Y-%m-%d')
        return values


    def copy(self, cr, uid, id, default={}, context=None):
        inv_obj = self.pool.get('account.invoice')
        doc_obj=self.pool.get('sri.type.document')
        original_invoice = inv_obj.browse(cr, uid, id, context)
        new_number = False
        autorization_number = False
        authorization_id = False
        if original_invoice and original_invoice.shop_id and original_invoice.printer_id and original_invoice.company_id and original_invoice.type == "out_invoice":
            new_number = doc_obj.get_next_value_secuence(cr, uid, 'invoice', False, original_invoice.printer_id.id, 'account.invoice', 'invoice_number_out', context)
            authorization_id = original_invoice.authorization_sales.id
            autorization_number = original_invoice.authorization_sales.number
        if context is None:
            context = {}
        default.update({
            'state':'draft',
            'number':False,
            'move_id':False,
            'move_name':False,
            'internal_number': False,
            'invoice_number_in': False,
            'automatic_number': new_number,
            'invoice_number_out': new_number,
            'invoice_number': False,
            'authorization_purchase_id': False,
            'authorization_sales': authorization_id,
            'authorization': autorization_number,
        })
        if 'date_invoice' not in default:
            default.update({
                'date_invoice':False
            })
        if 'date_due' not in default:
            default.update({
                'date_due':False
            })
        return super(account_invoice, self).copy(cr, uid, id, default, context)


    def onchange_authorization_supplier(self, cr, uid, ids, authorization, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        if authorization:
            auth = self.pool.get('sri.authorization.supplier').browse(cr, uid, authorization, context)
            number = auth and auth.agency + "-" + auth.printer_point+"-"
            value['invoice_number_in'] = number or ''
        return {'value': value, 'domain': domain }

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        if not context: context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        res = super(account_invoice,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        type = context.get('type', 'out_invoice')
        client = context.get('client','gtk')
        liquidation = context.get('liquidation',False)
        if view_type == 'search':
            doc = etree.XML(res['arch'])
            for field in res['fields']:
                if field == 'number':
                    nodes = doc.xpath("//field[@name='number']")
                    for node in nodes:
                        if type and not liquidation:
                            node.getparent().remove(node)
                if field == 'invoice_number_out':
                    nodes = doc.xpath("//field[@name='invoice_number_out']")
                    for node in nodes:
                        if type != 'out_invoice':
                            node.getparent().remove(node)
                if field == 'invoice_number_in':
                    nodes = doc.xpath("//field[@name='invoice_number_in']")
                    for node in nodes:
                        if type != 'in_invoice' and not liquidation:
                            node.getparent().remove(node)
            res['arch'] = etree.tostring(doc)
        if view_type == 'tree':
            for field in res['fields']:
                if type == 'out_invoice':
                    if field == 'number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='number']")
                        for node in nodes:
                            node.getparent().remove(node)
                        res['arch'] = etree.tostring(doc)
                    if field == 'invoice_number_in':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='invoice_number_in']")
                        for node in nodes:
                            node.getparent().remove(node)
                        res['arch'] = etree.tostring(doc)
                else:
                    if type == 'in_invoice':
                        if field == 'number':
                            doc = etree.XML(res['arch'])
                            nodes = doc.xpath("//field[@name='number']")
                            for node in nodes:
                                node.getparent().remove(node)
                            res['arch'] = etree.tostring(doc)
                        if field == 'invoice_number_out':
                            doc = etree.XML(res['arch'])
                            nodes = doc.xpath("//field[@name='invoice_number_out']")
                            for node in nodes:
                                node.getparent().remove(node)
                            res['arch'] = etree.tostring(doc)
                    else:
                        if field == 'invoice_number_out':
                            doc = etree.XML(res['arch'])
                            nodes = doc.xpath("//field[@name='invoice_number_out']")
                            for node in nodes:
                                node.getparent().remove(node)
                            res['arch'] = etree.tostring(doc)
                        if field == 'invoice_number_in':
                            doc = etree.XML(res['arch'])
                            nodes = doc.xpath("//field[@name='invoice_number_in']")
                            for node in nodes:
                                node.getparent().remove(node)
                            res['arch'] = etree.tostring(doc)
                    
        if view_type == 'form':
            for field in res['fields']:
                if user.company_id.generate_automatic:
                    if field == 'invoice_number_out':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='invoice_number_out']")
                        for node in nodes:
                            node.getparent().remove(node)
                        res['arch'] = etree.tostring(doc)
                else:
                    if field == 'automatic_number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='automatic_number']")
                        for node in nodes:
                            node.getparent().remove(node)
                        res['arch'] = etree.tostring(doc)
        return res
    
    def _get_automatic(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        return user.company_id.generate_automatic
    
    def create(self, cr, uid, vals, context=None):
        auth_obj = self.pool.get('sri.authorization')
        doc_obj=self.pool.get('sri.type.document')
        company_id = vals.get('company_id', False)
        if not context:
            context = {}
        if vals.get('invoice_number_out', False):
            if context.get('type', False) == 'out_invoice':
                number_out = vals.get('invoice_number_out', False)
                company_id = vals.get('company_id', False)
                doc_obj.validate_unique_value_document(cr, uid, number_out, company_id, 'account.invoice', 'invoice_number_out', 'Factura', context)
                vals['automatic_number'] = vals.get('invoice_number_out', False)
                if vals.get('authorization_sales', False):
                    vals['authorization'] = auth_obj.browse(cr, uid, vals['authorization_sales'], context).number
        res = super(account_invoice, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        doc_obj = self.pool.get('sri.type.document')
        inv_obj = self.pool.get('account.invoice')
        if not context:
            context={}
        for invoice in inv_obj.browse(cr, uid, ids, context):
            if vals.get('invoice_number_out', False):
                if context.get('type', False) == 'out_invoice':
                    number_out = vals.get('invoice_number_out', False)
                    company_id = vals.get('company_id', False)
                    if not company_id:
                        company_id = invoice.company_id.id
                    doc_obj.validate_unique_value_document(cr, uid, number_out, company_id, 'account.invoice', 'invoice_number_out', 'Factura', context)
        res = super(account_invoice, self).write(cr, uid, ids, vals, context)
        return res 
     
    def button_reset_taxes(self, cr, uid, ids, context=None):
        for inv in self.browse(cr, uid, ids, context):
            if inv.type == "out_invoice":
                vals = {'automatic_number':inv.invoice_number_out}
                if inv.authorization_sales:
                    vals['authorization'] = inv.authorization_sales.number
                self.write(cr, uid, [inv.id], vals)
        return super(account_invoice, self).button_reset_taxes(cr, uid, ids, context)

    def _number(self, cr, uid, ids, name, args, context=None):
        result = {}
        for invoice in self.browse(cr, uid, ids, args):
            result[invoice.id] = invoice.invoice_number
        return result

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'total_sin_descuento':0.0,
                'amount_untaxed': 0.0,
                'base_no_iva': 0.0,
                'base_iva': 0.0,
                'base_iva_0': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'total_retencion': 0.0,
                'total_iva': 0.0,
                'total_ice': 0.0,
                'total_descuento': 0.0,
                'total_descuento_per': 0.0,
            }
            contador = 0;
            desc_per = 0.0
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
                res[invoice.id]['total_sin_descuento'] += line.price_unit * line.quantity
                res[invoice.id]['total_descuento'] += line.price_unit * line.quantity * line.discount * 0.01
                res[invoice.id]['base_no_iva'] += line.base_no_iva
                if line.discount != 0:
                    contador += 1
                    desc_per += line.discount
            for line in invoice.tax_line:
                    res[invoice.id]['amount_tax'] += line.amount
                    if line.amount > 0:
                        if line.type_ec == 'iva' and line.amount > 0:
                            res[invoice.id]['base_iva'] += line.base
                        if line.type_ec == 'ice':
                            res[invoice.id]['total_ice'] += line.amount
                        else:
                            res[invoice.id]['total_iva'] += line.amount           
                    else:
                        if line.type_ec == 'iva' and line.amount == 0:
                            res[invoice.id]['base_iva_0'] += line.base
                        res[invoice.id]['total_retencion'] += line.amount
            if contador != 0:
                res[invoice.id]['total_descuento_per'] = desc_per / contador
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
        return res

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()
    
    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    _inherit = "account.invoice"
        
    _columns = {
                'automatic_number': fields.char('Number', size=17, readonly=True,),
                'create_date': fields.date('Creation date', readonly=True),
                'authorization_sales':fields.many2one('sri.authorization', 'Authorization', required=False),
                #TODO: este campo debe ser calculado, funcionara de igual manera con los eventos onchange, pero se guardara segun sea el tipo de documento
                'authorization':fields.char('Authorization', size=10, readonly=True),
                'authorization_supplier_purchase_id':fields.many2one('sri.authorization.supplier', 'Authorization', readonly=True, states={'draft':[('readonly',False)]}), 
                'authorization_purchase_id':fields.char('Authorization', size = 10, required=False, readonly=True, states={'draft':[('readonly',False)]}, help='This Number is necesary for SRI reports'),
                'number': fields.function(_number, method=True, type='char', size=17, string='Invoice Number', store=True, help='Unique number of the invoice, computed automatically when the invoice is created in Sales.'),
                'invoice_number': fields.char('Invoice Number', size=17, readonly=True, help="Unique number of the invoice, computed automatically when the invoice is created."),
                'invoice_number_in': fields.char('Invoice Number', size=17, required=False, readonly=True, states={'draft':[('readonly',False)]}, help="Unique number of the invoice."),
                'invoice_number_out': fields.char('Invoice Number', size=17, required=False, readonly=True, states={'draft':[('readonly',False)]}, help="Unique number of the invoice."),
                'prints_number': fields.integer('Prints Number', help = "You can't reprint a invoice twice or more times"),
                'automatic':fields.boolean('Automatic?',),
                'flag':fields.boolean('Flag',),
                'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
                'printer_id':fields.many2one('sri.printer.point', 'Printer Point', readonly=True, states={'draft':[('readonly',False)]}),
                'base_iva': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='IVA Base',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'base_no_iva': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='IVA 0 Base',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'base_iva_0': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='IVA 0 Base',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'total_retencion': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Total Retenido',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'total_iva': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Total IVA',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'total_descuento': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Descuento Total',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),                
                'total_descuento_per': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Total',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),  
                'total_ice': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='ICE Total',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'total_sin_descuento': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Sub Total',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),  
                'foreign': fields.related('partner_id','foreing', type='boolean', relation='res.partner', string='Foreing?'),
                'normal_process':fields.boolean('Proceso Normal', required=False),
                'liquidation_number':fields.char('Number', size=17, required=False, readonly=True, states={'draft':[('readonly', False)]}),
                'liquidation':fields.boolean('Liquidation'),
                'authorization_liquidation':fields.many2one('sri.authorization', 'Authorization', required=False),
                'invoice_rectification_id':fields.many2one('account.invoice', 'Canceled Invoice', readonly=True, states={'draft':[('readonly', False)]}),
                'number_credit_note_in':fields.char('Number', size=17, readonly=True, states={'draft':[('readonly', False)]}),
                'number_credit_note_out':fields.char('Number', size=17, readonly=True, states={'draft':[('readonly', False)]}),
                'autorization_credit_note_id':fields.many2one('sri.authorization', 'Autorizationnumber_liquidation', required=False, states={'draft':[('readonly', False)]}),
                'authorization_credit_note_purchase_id':fields.many2one('sri.authorization.supplier', 'Authorization', readonly=True, states={'draft':[('readonly',False)]}), 
                'credit_note_ids':fields.one2many('account.invoice', 'invoice_rectification_id', 'Credit Notes', required=False),
                'state': fields.selection([
                ('draft','Draft'),
                ('proforma','Pro-forma'),
                ('proforma2','Pro-forma'),
                ('open','Open'),
                ('paid','Paid'),
                ('wait_invoice','Waiting Invoice'),
                ('cancel','Cancelled')
                ],'State', select=True, readonly=True,
                help=' * The \'Draft\' state is used when a user is encoding a new and unconfirmed Invoice. \
                \n* The \'Pro-forma\' when invoice is in Pro-forma state,invoice does not have an invoice number. \
                \n* The \'Open\' state is used when user create invoice,a invoice number is generated.Its in open state till user does not pay invoice. \
                \n* The \'Paid\' state is set automatically when invoice is paid.\
                \n* The \'Cancelled\' state is used when user cancel invoice.'),                    
               }
    
    _defaults = {
                 'prints_number': lambda *a: 0,
                 'flag': lambda *a: False,
                 }

    def check_invoice_type(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
            if o.type == 'in_invoice':
                return True
            if o.type == 'out_invoice':
                return True
        return False

    def check_refund_with_invoice(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
            if o.type == 'in_refund' and o.invoice_rectification_id!=False:
                return True
            if o.type == 'out_refund' and o.invoice_rectification_id!=False:
                return True
        return False

    def check_refund_without_invoice(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
            if o.type == 'in_refund' and not o.invoice_rectification_id:
                return True
            if o.type == 'out_refund' and not o.invoice_rectification_id:
                return True
        return False
    
    def action_wait_invoice(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
            self.write(cr, uid, [o.id], {'state': 'wait_invoice',})
        return True

    def action_move_credit_note_create(self, cr, uid, ids, *args):
        """Creates invoice related analytics and financial move lines"""
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        inv_obj = self.pool.get('account.invoice')
        context = {}
        for credit_note in self.browse(cr, uid, ids):
            if not credit_note.invoice_rectification_id:
                #Se crea el movimiento para que quede en libros el valor de la nota de credito
                inv_obj.action_move_create(cr, uid, ids, *args)
            else:
                #Si ya tiene movimiento, quiere decir que estuvo en espera y ahora se va a usar para conciliar otra factura
                if credit_note.move_id:
                    self._create_voucher(cr, uid, credit_note.invoice_rectification_id, credit_note, context)
                #Si no tiene movimiento se debera crear el movimiento y hacer la conciliacion
                else:
                    inv_obj.action_move_create(cr, uid, ids, *args)
                    self._create_voucher(cr, uid, credit_note.invoice_rectification_id, credit_note, context)
        self._log_event(cr, uid, ids)
        return True
                
    def _create_voucher(self, cr, uid, invoice, credit_note, context):
        self._validate_credit_note(cr, uid, invoice, credit_note, context)
        if context is None:
            context = {}
        acc_move_line_obj = self.pool.get('account.move.line')
        acc_vou_obj = self.pool.get('account.voucher')
        acc_vou_line_obj = self.pool.get('account.voucher.line')
        currency_obj = self.pool.get('res.currency')
        partner_id = credit_note.partner_id.id
        journal_id = credit_note.journal_id.id
        company_currency = credit_note.journal_id.company_id.currency_id.id
        currency_id = credit_note.currency_id.id
        line_cr_ids = []
        line_dr_ids = []
        line_ids = []
        total_credit = 0.0
        total_debit = 0.0
        ids = []
        period_id = credit_note.period_id and credit_note.period_id.id or False
        if not period_id:
            period_ids = self.pool.get('account.period').search(cr, uid, [('date_start','<=',credit_note.date_invoice or time.strftime('%Y-%m-%d')),('date_stop','>=',credit_note.date_invoice or time.strftime('%Y-%m-%d')), ('company_id', '=', credit_note.company_id.id)])
            if period_ids:
                period_id = period_ids[0]
        domain = [('state','=','valid'), ('account_id.type', 'in', ('payable', 'receivable')), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)]
        domain.append(('invoice', 'in', (invoice.id, credit_note.id)))
        for id in acc_move_line_obj.search(cr, uid, domain, context=context):
            ids.append(id)
        ids.reverse()
        moves = acc_move_line_obj.browse(cr, uid, ids, context=context)
        for line in moves:
            total_credit += line.credit or 0.0
            total_debit += line.debit or 0.0
        for line in moves:
            original_amount = line.credit or line.debit or 0.0
            amount_unreconciled = currency_obj.compute(cr, uid, line.currency_id and line.currency_id.id or company_currency, currency_id, abs(line.amount_residual_currency), context=context)
            rs = {
                'name':line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': currency_obj.compute(cr, uid, line.currency_id and line.currency_id.id or company_currency, currency_id, line.currency_id and abs(line.amount_currency) or original_amount, context=context),
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
            }
            if line.credit:
                amount = min(amount_unreconciled, currency_obj.compute(cr, uid, company_currency, currency_id, abs(total_debit), context=context))
                rs['amount'] = amount
                total_debit -= amount
            else:
                amount = min(amount_unreconciled, currency_obj.compute(cr, uid, company_currency, currency_id, abs(total_credit), context=context))
                rs['amount'] = amount
                total_credit -= amount

            if rs['type'] == 'cr':
                line_cr_ids.append((0,0,rs))
            else:
                line_dr_ids.append((0,0,rs))
                        
        type_voucher = "receipt"
        if credit_note.type == "in_refund":
            type_voucher = "payment"
        
        vals_vou = {
                    'type':type_voucher,
                    'period_id': period_id,
                    'journal_id': journal_id,
                    'account_id': credit_note.journal_id.default_debit_account_id.id,
                    'company_id' : self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
                    'amount': 0.0,
                    'currency_id': currency_id,
                    'partner_id': partner_id,
                    'line_dr_ids':line_dr_ids,
                    'line_cr_ids':line_cr_ids,
                    'line_ids':line_ids,
        }
        voucher_id = acc_vou_obj.create(cr, uid, vals_vou, context)
        acc_vou_obj.action_move_line_create(cr, uid, [voucher_id,], context=context)
        return True

    def _validate_credit_note(self, cr, uid, invoice, credit_note, context):
        inv_obj = self.pool.get('account.invoice')
        #La nota de credito no puede ser superior al total de la factura
        if credit_note.amount_total > invoice.amount_total:
            raise osv.except_osv(_('Warning!'), _("The amount total of credit note %s %s, can't be bigger than amount total of invoice %s %s!, Can't Validate" %(credit_note.number, credit_note.amount_total, invoice.number, invoice.amount_total)))
        #Si ya se encuentra parcialmente conciliada y es mayor al residual debe lanzar un error
        if invoice.state == open:
            if credit_note.amount_total > invoice.residual:
                raise osv.except_osv(_('Warning!'), _("The amount total of credit note %s is %s, can't be bigger than residual of invoice %s %s! Can't Validate" %(credit_note.number, credit_note.amount_total, invoice.number, invoice.residual)))
        else:
            #Se verifica que no se emita notas de credit para devolucion que superen el valor total de la nota de credito
            credit_notes_ids = inv_obj.search(cr, uid, [('invoice_rectification_id','=', invoice.id), ('id', '!=', credit_note.id), ('state', '=', 'open')])
            if credit_notes_ids:
                total = 0
                for cn in inv_obj.browse(cr, uid, credit_notes_ids):
                    total += cn.amount_total
                total += credit_note.amount_total
                if total > invoice.amount_total:
                    raise osv.except_osv(_('Warning!'), _("The sum of total amounts of Credit Notes in Invoice %s %s, can't be bigger than total %s! Can't Validate" %(invoice.number, total, invoice.amount_total)))                    
        return True

    def action_check_ice(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        inv_obj = self.pool.get('account.invoice')
        invoices = inv_obj.browse(cr, uid, ids, context)
        if context is None: context = {}
        ice = False
        count_normal_product = 0
        for invoice in invoices:
            for line in invoice.invoice_line:
                normal_product = True
                for tax in line.invoice_line_tax_id:
                    if tax.type_ec == 'ice':
                        ice = True
                        normal_product = False
                if normal_product:
                    count_normal_product += 1
            if not ice or count_normal_product == 0:
                wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
            else:
                wizard_id = self.pool.get("account.invoice.ice.wizard").create(cr, uid, {}, context=dict(context, active_ids=ids))
                return {
                    'name':_("Invoice Options"),
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'account.invoice.ice.wizard',
                    'res_id': wizard_id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]',
                    'context': dict(context, active_ids=ids)
                }
        return True

    def action_number(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        inv_obj = self.pool.get('account.invoice')
        auth_obj = self.pool.get('sri.authorization')
        auth_s_obj = self.pool.get('sri.authorization.supplier')
        document_obj = self.pool.get('sri.type.document')
        for invoice in self.browse(cr, uid, ids, context):
            context['automatic'] = invoice.automatic
            if not invoice.partner_id.foreing and not invoice.partner_id.ref:
                raise osv.except_osv(_('Error!'), _("Partner %s doesn't have CEDULA/RUC, you must input for validate.") % invoice.partner_id.name)
            if invoice.type=='out_invoice':
                auth_data = self.pool.get('sri.authorization').check_if_seq_exist(cr, uid, 'invoice', invoice.invoice_number_out, invoice.printer_id.id, invoice.date_invoice, context)
                auth = auth_obj.browse(cr, uid, auth_data['authorization'])
                document_obj.add_document(cr, uid, [auth_data['document_type_id']], context)
                self.write(cr, uid, [invoice.id], {'authorization_sales': auth.id, 'invoice_number': invoice.invoice_number_out, 'authorization': auth.number }, context)
            elif invoice.type=='in_invoice':
                if invoice.invoice_number_in:
                    auth_s_obj.check_number_document(cr, uid, invoice.invoice_number_in, invoice.authorization_supplier_purchase_id, invoice.date_invoice, 'account.invoice', 'invoice_number_in', _('Invoice'), context, invoice.id, invoice.foreign)
                    if not invoice.foreign:
                        self.write(cr, uid, [invoice.id], {'invoice_number': invoice.invoice_number_in,'authorization_purchase': invoice.authorization_supplier_purchase_id.number}, context)
                    else:
                        self.write(cr, uid, [invoice.id], {'invoice_number': invoice.invoice_number_in}, context)
        result = super(account_invoice, self).action_number(cr, uid, ids, context)
        self.write(cr, uid, ids, {'internal_number': False,}, context)
        return result
    
    def action_cancel_draft(self, cr, uid, ids, *args):
        document_obj = self.pool.get('sri.type.document')
        for invoice in self.browse(cr, uid, ids):
            if invoice.type=='out_invoice':
                if invoice.flag:
                    for doc in invoice.authorization_sales.type_document_ids:
                        if doc.name=='invoice':
                            document_obj.rest_document(cr, uid, [doc.id,])
                    self.write(cr, uid, [invoice.id], {'flag': False}, context=None)
            return super(account_invoice, self).action_cancel_draft(cr, uid, ids)

    def split_invoice(self, cr, uid, invoice_id, context=None):
        '''
        Split the new_invoice_data when the lines exceed the maximum set for the shop
        '''
        doc_obj=self.pool.get('sri.type.document')
        invoice = self.browse(cr, uid, invoice_id)
        new_invoice_id = False
        if invoice.type == 'out_invoice':
            if invoice.shop_id.invoice_lines != 0 and len(invoice.invoice_line) > invoice.shop_id.invoice_lines:
                lst = []
                new_invoice_data = self.read(cr, uid, invoice.id, [
                                                      'name',
                                                      'origin',
                                                      'fiscal_position',
                                                      'date_invoice',
                                                      'user_id',
                                                      'shop_id',
                                                      'printer_id',
                                                      'authorization_sales',
                                                      'authorization',
                                                      'company_id',
                                                      'type', 
                                                      'reference', 
                                                      'comment', 
                                                      'date_due', 
                                                      'partner_id', 
                                                      'address_contact_id', 
                                                      'address_invoice_id', 
                                                      'payment_term', 
                                                      'account_id', 
                                                      'currency_id', 
                                                      'invoice_line', 
                                                      'tax_line', 
                                                      'journal_id', 
                                                      'period_id',
                                                      ])
                new_number = doc_obj.get_next_value_secuence(cr, uid, 'invoice', False, invoice.printer_id.id, 'account.invoice', 'invoice_number_out', context)
                new_invoice_data.update({
                    'automatic_number': new_number,
                    'invoice_number_out': new_number,
                    'state': 'draft',
                    'number': False,
                    'invoice_line': [],
                    'tax_line': []
                })
                # take the id part of the tuple returned for many2one fields
                for field in new_invoice_data:
                    if isinstance(new_invoice_data[field], tuple):
                        new_invoice_data[field] = new_invoice_data[field] and new_invoice_data[field][0]

                new_invoice_id = self.create(cr, uid, new_invoice_data)
                count = 0
                lst = invoice.invoice_line
                while count < invoice.shop_id.invoice_lines:
                    lst.pop(0)
                    count += 1
                for il in lst:
                    self.pool.get('account.invoice.line').write(cr,uid,il.id,{'invoice_id':new_invoice_id})
                self.button_compute(cr, uid, [invoice.id])
        
            if new_invoice_id:
                wf_service = netsvc.LocalService("workflow")
                self.button_compute(cr, uid, [new_invoice_id])
                wf_service.trg_validate(uid, 'account.invoice', new_invoice_id, 'invoice_open', cr)
        return new_invoice_id
    
    
    def _check_number_invoice(self,cr,uid,ids, context=None):
        res = True
        for invoice in self.browse(cr, uid, ids):
            cadena='(\d{3})+\-(\d{3})+\-(\d{9})'
            if invoice.invoice_number_out:
                ref = invoice.invoice_number_out
                if re.match(cadena, ref):
                    res = True
                else:
                    res = False
            if invoice.invoice_number_in and not invoice.foreign:
                ref = invoice.invoice_number_in
                if re.match(cadena, ref):
                    res = True
                else:
                    res = False
            return res
    
            if invoice.number_liquidation:
                ref = invoice.number_liquidation
                if re.match(cadena, ref):
                    res = True
                else:
                    res = False
            return res

    def unlink(self, cr, uid, ids, context=None):
        invoices = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for inv in invoices:
            if inv['state'] == 'draft':
                unlink_ids.append(inv['id'])
            else:
                raise osv.except_osv(_('Invalid action!'), _('You can delete Invoice in state Draft'))
        return super(account_invoice, self).unlink(cr, uid, unlink_ids, context)


    _constraints = [(_check_number_invoice,_('The number of Document is incorrect, it must be like 00X-00X-000XXXXXX, X is a number'),['invoice_number_out','invoice_number_in','number_liquidacion'])]
    
    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        partner_obj = self.pool.get('res.partner')
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        foreing = False
        if partner_id:
            partner = partner_obj.browse(cr, uid, partner_id)
            foreing = partner and partner.foreing or False
        res['value']['foreign'] = foreing
        return res

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        types = {
                'out_invoice': 'FACT-CLI: ',
                'in_invoice': 'FACT-PROV: ',
                'out_refund': 'NC-CLI: ',
                'in_refund': 'NC-PROV: ',
                'liquidation': 'LIQ-COMP: ',
                }
        res = []
        for r in self.read(cr, uid, ids, ['type', 'number', 'invoice_number_out', 'invoice_number_in', 'number_credit_note_in', 'number_credit_note_out','number_liquidation','name', 'liquidation'], context, load='_classic_write'):
            name = r['number'] or types[r['type']]  or ''
            if r['type'] == 'out_invoice':
                name = r['invoice_number_out'] or types[r['type']] or ''
            if r['type'] == 'in_invoice':
                name = r['invoice_number_in'] or types[r['type']] or ''
            if r['type'] == 'out_refund':
                name = r['number_credit_note_out'] or types[r['type']] or ''
            if r['type'] == 'in_refund':
                name = r['number_credit_note_in'] or types[r['type']] or ''
            if r['liquidation']:
                name = r['number_liquidation'] or types['liquidation']  or ''
            res.append((r['id'], name ))
        return res

    
account_invoice()