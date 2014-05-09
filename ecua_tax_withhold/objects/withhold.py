# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: TRESCLOUD CIA. LTDA.
# Copyright (C) 2013  trescloud.com
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
import decimal_precision as dp
from tools.translate import _
import time
import netsvc
import re

from mx import DateTime
from datetime import datetime,timedelta

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class account_withhold_line(osv.osv):
   
    _name = "account.withhold.line"

    _columns = {
            'withhold_id': fields.many2one('account.withhold', 'Withhold',
                                           help="Number of related withhold"),
            'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year',
                                             help="Fiscal Year of transaction"),
            'description': fields.selection([('iva', 'IVA'), ('renta', 'RENTA'), ], 'Tax',
                                            help="Type of Tax (IVA/RENTA)"),
            'tax_base': fields.float('Tax Base', digits_compute=dp.get_precision('Account'),
                                     help="Base Value for the compute of tax"),
            'withhold_percentage': fields.float('Percentaje Value (%)', digits_compute=dp.get_precision('Account'),
                                                help="Percentage Value of tax withhold"),
            'tax_amount':fields.float('Amount', digits_compute=dp.get_precision('Account'),
                                      help="Amount of tax withhold"),
           # 'withhold_percentage': fields.function(_percentaje_retained, method=True, type='float', string='Percentaje Value',
            #                             store={'account.withhold.line': (lambda self, cr, uid, ids, c={}: ids, ['tax_id',], 1)},),
            #'withhold_percentage': fields.function(_percentaje_retained, method=True, type='float', string='Percentaje Value'),
            'tax_id':fields.many2one('account.tax.code', 'Tax Code', help="Tax"),
            'tax_ac_id':fields.many2one('account.tax.code', 'Tax Code', help="Tax"),

            }
    
account_withhold_line()

class account_withhold(osv.osv):
        
    _name = 'account.withhold'
    _rec_name='number'

#    _inherit = ['mail.thread']
#    _track = {
#        'type': {
#        },
#        'state': {
#            'account.mt_invoice_paid': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'paid' and obj['type'] in ('out_invoice', 'out_refund'),
#            'account.mt_invoice_validated': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'open' and obj['type'] in ('out_invoice', 'out_refund'),
#        },
#    }
    
    def _check_number(self, cr, uid, ids, context=None):
        cadena = '(\d{3})+\-(\d{3})+\-(\d{9})'
        for obj in self.browse(cr, uid, ids):
            ref = obj['number']
            if obj['number']:
                if re.match(cadena, ref):
                    return True
                else:
                    return False
            else:
                return True
    
    def _withhold_percentaje(self, cr, uid,vals_ret_line, context=None):
        res = {}
        tax_code_id = self.pool.get('account.tax.code').search(cr, uid, [('id', '=', vals_ret_line['tax_id'])])
        tax_code = None
        if tax_code_id:
            tax_code = self.pool.get('account.tax.code').browse(cr, uid, tax_code_id, context)[0]['code']
        tax_obj = self.pool.get('account.tax')
        tax = tax_obj.search(cr, uid, [('tax_code_id', '=', tax_code), ('child_ids','=',False)])
        if vals_ret_line['description']=="renta":
            tax = tax_obj.search(cr, uid, [('base_code_id', '=', tax_code), ('child_ids','=',False)])
        porcentaje= (tax_obj.browse(cr, uid, tax, context)[0]['amount'])*(-100)
        return porcentaje

    def default_get(self, cr, uid, fields, context=None):

        if context is None:
            context = {}
        
        values = {}
        res = []
        ret_line_id = 0
        printer_id = False
        shop_id = False
        
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        
        if context.get('transaction_type') and context.get('active_id'):
            
            transaction_type = context.get('transaction_type')
            obj = self.pool.get('account.invoice').browse(cr, uid, context['active_id'])
            
            if 'value' not in context.keys():
                if transaction_type == 'sale':

                    values = {
                         'shop_id': shop_id,
                         'printer_id': printer_id,
                         'partner_id': obj.partner_id.id,
                         'invoice_id': obj.id,
                         'creation_date': obj.date_invoice,
                         'transaction_type': transaction_type,
                         'company_id': obj.company_id.id,
                            }
                    
                if transaction_type == 'purchase':

                    if user.printer_id:
                        printer_id = user.printer_id.id
                        if user.printer_id.shop_id:
                            shop_id = user.printer_id.shop_id.id

                    for tax_line in obj.tax_line:
                        
                        fiscalyear_id = None
                        
                        if not obj['period_id']:
                            period_ids = self.pool.get('account.period').search(cr, uid, [('date_start','<=',time.strftime('%Y-%m-%d')),('date_stop','>=',time.strftime('%Y-%m-%d')),])
                            if period_ids:
                                fiscalyear_id= self.pool.get('account.period').browse(cr, uid, [period_ids[0]], context)[0]['fiscalyear_id']['id']
                        else:
                            fiscalyear_id = obj['period_id']['fiscalyear_id']['id']
                        
                        if (tax_line['tax_amount']< 0):
                            
                            porcentaje= (float(tax_line['tax_amount']/tax_line['base']))*(-100)
                            tax_id = tax_line['tax_code_id']['id']
                            tax_ac_id=tax_id
                        
                            if tax_line['type_ec'] == 'renta':
                                tax_id = tax_line['base_code_id']['id']                           

                            vals_ret_line = {
                                             'fiscalyear_id':fiscalyear_id,  
                                             'description': tax_line['type_ec'],
                                             'tax_id': tax_id,
                                             'tax_ac_id':tax_ac_id,
                                             'tax_base': tax_line['base'],
                                             'tax_amount': abs(tax_line['amount']),
                                             'withhold_percentage':0
                                             }  
                            
                            vals_ret_line['withhold_percentage'] = self._withhold_percentaje(cr, uid, vals_ret_line, context)
                            res.append(vals_ret_line)  
                        
                        elif tax_line['tax_amount'] == 0 and tax_line['type_ec'] == 'renta':
                            
                            # Por que el amount deberia ser 0?
                            tax_ac_id = tax_line['tax_code_id']['id']

                            vals_ret_line = {
                                             'tax_base':tax_line.base,
                                             'fiscalyear_id':fiscalyear_id,
                                             'invoice_without_withhold_id': obj.id,
                                             'description': tax_line.type_ec,
                                             'tax_id': tax_line.base_code_id.id,
                                             'tax_ac_id':tax_ac_id,
                                             'creation_date_invoice': obj.date_invoice,
                                             }
                    values = {
                         'shop_id': shop_id,
                         'printer_id':printer_id,
                         'invoice_id': obj.id,
                         'creation_date': obj.date_invoice,
                         'transaction_type': transaction_type,
                         'currency_id':obj.currency_id.id,
                         'partner_id':obj.partner_id.id,
                         'company_id':obj.company_id.id,
                         'withhold_line_ids': res,
                                }
                #Initial state 
                values['state'] = 'draft'
            
            else:
                values = context['value']
                
        return values
    
    def _total(self, cr, uid, ids, field_name, arg, context=None):
        
        cur_obj = self.pool.get('res.currency')
        res = {}
        
        for ret in self.browse(cr, uid, ids, context=context):
            
            val = 0.0
            cur = ret.invoice_id.currency_id
            
            for line in ret.withhold_line_ids:
                    val += line.tax_amount
            if cur:
                res[ret.id] = cur_obj.round(cr, uid, cur, abs(val))
            else:
                # if the invoice is delete, show val
                res[ret.id] = abs(val)
               
        return res
    
    def _total_iva(self, cr, uid, ids, field_name, arg, context=None):
        
        cur_obj = self.pool.get('res.currency')
        res = {}
        
        for ret in self.browse(cr, uid, ids, context=context):
            
            val_iva = 0.0
            cur = ret.invoice_id.currency_id
            
            for line in ret.withhold_line_ids:
                if line.description == 'iva':
                    val_iva += line.tax_amount
            if cur:
                res[ret.id] = cur_obj.round(cr, uid, cur, abs(val_iva))
            else:
                # if the invoice is delete, show val_iva
                res[ret.id] = abs(val_iva)
                
        return res
    
    def _total_renta(self, cr, uid, ids, field_name, arg, context=None):
        
        cur_obj = self.pool.get('res.currency')
        res = {}
        
        for ret in self.browse(cr, uid, ids, context=context):
            
            val_renta = 0.0
            cur = ret.invoice_id.currency_id
            
            for line in ret.withhold_line_ids:
                if line.description == 'renta':
                    val_renta += line.tax_amount
            if cur:
                res[ret.id] = cur_obj.round(cr, uid, cur, abs(val_renta))
            else:
                # if the invoice is delete, show val_renta
                res[ret.id] = abs(val_renta)
                
        return res

    def _total_base_iva(self, cr, uid, ids, field_name, arg, context=None):
        
        cur_obj = self.pool.get('res.currency')
        res = {}
        
        for ret in self.browse(cr, uid, ids, context=context):
            
            val_base_iva = 0.0
            cur = ret.invoice_id.currency_id
            
            for line in ret.withhold_line_ids:
                if line.description == 'iva':
                    val_base_iva += line.tax_base
            if cur:
                res[ret.id] = cur_obj.round(cr, uid, cur, val_base_iva)
            else:
                # if the invoice is delete, show val_iva
                res[ret.id] = val_base_iva
                
        return res

    def _total_base_renta(self, cr, uid, ids, field_name, arg, context=None):
        
        cur_obj = self.pool.get('res.currency')
        res = {}
        
        for ret in self.browse(cr, uid, ids, context=context):
            
            val_base_renta = 0.0
            cur = ret.invoice_id.currency_id
            
            for line in ret.withhold_line_ids:
                if line.description == 'renta':
                    val_base_renta += line.tax_base
            if cur:
                res[ret.id] = cur_obj.round(cr, uid, cur, val_base_renta)
            else:
                # if the invoice is delete, show val_renta
                res[ret.id] = val_base_renta
                
        return res

    
#    def _get_withhold(self, cr, uid, ids, context=None):
#        result = {}
#        for line in self.pool.get('account.withhold.line').browse(cr, uid, ids, context=context):
#            result[line.withhold_id.id] = True
#        return result.keys()
    
#     #TRESCLOUD - Definir funcion total_vat_withhold en su lugar o como alias
#    #retorna el valor total de la funcion
#    def _total_iva(self, cr, uid, ids, field_name, arg, context=None):
#        cur_obj = self.pool.get('res.currency')
#        res = {}
#        for ret in self.browse(cr, uid, ids, context=context):
#            val = 0.0
#            cur = ret.invoice_id.currency_id
#            for line in ret.withhold_line_ids:
#                if line.description == 'iva':
#                    #TRESCLOUD - solo debería haber un campo line.retained_value (borrar line.retained_value_manual)
#                    if ret.transaction_type == 'purchase':
#                        val += line.retained_value
#                    else:
#                        val += line.retained_value_manual
#            if cur:
#                res[ret.id] = cur_obj.round(cr, uid, cur, val)
#        return res
#
#    #TRESCLOUD - Definir funcion total_utilities_withhold en su lugar o como alias
#    # Valor total a retener por impuesto a la renta
#    def _total_renta(self, cr, uid, ids, field_name, arg, context=None):
#        cur_obj = self.pool.get('res.currency')
#        res = {}
#        for ret in self.browse(cr, uid, ids, context=context):
#            val = 0.0
#            cur = ret.invoice_id.currency_id
#            for line in ret.withhold_line_ids:
#                if line.description == 'renta':
#                    #TRESCLOUD - solo debería haber un campo line.retained_value (borrar line.retained_value_manual)
#                    if ret.transaction_type == 'purchase':
#                        val += line.retained_value
#                    else:
#                        val += line.retained_value_manual
#            if cur:
#                res[ret.id] = cur_obj.round(cr, uid, cur, val)
#        return res
    
#    def _transaction_type(self, cr, uid, context = None):
#        if context is None:
#            context = {}
#        return context.get('transaction_type', False)
                
#    def _printer_id(self, cr, uid, context = None):
#        
#        if context is None:
#            context = {}
#        
#        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
#        
#        if user.printer_id:
#            return user.printer_id.id
#        else:
#            return False
    
    _columns = {
        'number': fields.char('Number', size=17, required=False, 
                              help="Number of Withhold"),
        #'origin': fields.char('Origin Document', size=128, required=False),
        'creation_date': fields.date('Creation Date',states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]},
                                     help="Date of creation of Withhold"),

        #Campo utilizado para identificar el tipo de documento de origen y alterar su funcionamiento
        'transaction_type':fields.selection([
            ('purchase','Purchases'),
            ('sale','Sales'),
            ],  'Transaction type', required=True, readonly=True),

        #TRESCLOUD - Removimos el "ondelete='cascade" del invoice_id, puede llevar a borrados inintencionales!
        'invoice_id': fields.many2one('account.invoice', 'Number of document', required=False, states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]},
                                      help="Invoice related with this withhold"),
        'partner_id': fields.related('invoice_id','partner_id', type='many2one', relation='res.partner', string='Partner', store=True,
                                     help="Partner related with this withhold"),

        #TRESCLOUD - Deberia guardarse el nombre del partner, su RUC, direccion, etc (ejemplo el año que viene el cliente cambia de direccion,
        # entonces el documento tributario del año 2012 no deberia verse afectado)  
        'company_id': fields.related('invoice_id','company_id', type='many2one', relation='res.company', string='Company', store=True, change_default=True,
                                     help="Company related with this withhold (in multi-company environment)"),
        'state':fields.selection([
            ('draft','Draft'),
            ('approved','Approved'),
            ('canceled','Canceled'),
            ],  'State', required=True, readonly=True),
        'account_voucher_ids': fields.one2many('account.move.line', 'withhold_id', 'Withhold',
                                               help="List of account moves"),
        'automatic': fields.boolean('Automatic?',),
        'period_id': fields.related('invoice_id','period_id', type='many2one', relation='account.period', string='Period', store=True,
                                    help="Period related with this transaction"), 
        'shop_id': fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]},
                                   help="Shop related with this transaction, only need in Purchase"),
        'printer_id': fields.many2one('sri.printer.point', 'Printer Point', readonly=True, states={'draft':[('readonly',False)]},
                                      help="Printer Point related with this transaction, only need in Purchase"),
        #P.R: Required the authorization asociated depending if is purchase or sale
        'authorization_sri': fields.char('Authorization', readonly=True, states={'draft':[('readonly',False)]}, size=32,
                                         help="Number of authorization use by the withhold"),
        #P.R: Required in this format to generate the account moves using this lines
        'withhold_line_ids': fields.one2many('account.withhold.line', 'withhold_id', 'Withhold lines',
                                             help="List of withholds"),
        #P.R: Required to show in the printed report
        'total': fields.function(_total, method=True, type='float', string='Total Withhold', store = True,
                                 help="Total value of withhold"),
        #P.R: Required to show in the ats report
        'total_iva': fields.function(_total_iva, method=True, type='float', string='Total IVA', store = False,
                                 help="Total IVA value of withhold"),   
        'total_renta': fields.function(_total_renta, method=True, type='float', string='Total RENTA', store = False,
                                 help="Total renta value of withhold"),      
        #P.R: Required to show in the tree view
        'total_base_iva': fields.function(_total_base_iva, method=True, type='float', string='Total Base IVA', store = False,
                                 help="Total base IVA of withhold"),   
        'total_base_renta': fields.function(_total_base_renta, method=True, type='float', string='Total Base RENTA', store = False,
                                 help="Total base renta of withhold"),      
        'comment': fields.text('Additional Information'), 
    }

# Existe un default get, reemplaza al defaults       
#    _defaults = {
#        'number': '',
#        'transaction_type': _transaction_type,
#        'state': lambda *a: 'draft',
#        'printer_id': _printer_id,
#                 }
    def check_withhold_number_uniq(self, cr, uid, ids):
        """
        Check if the withhold number is unique under this conditions:
        1) if the transaction type is "sale", verify that the number and RUC is unique
        2) if the transaction type is "purchase", verify that only the number be unique
        """
        for withhold in self.browse(cr, uid, ids):
            
            number = withhold['number']
            type = withhold['transaction_type']
            partner = withhold.partner_id.id
            search_param = []

            search_param.append(('id', '!=', withhold.id))
            search_param.append(('number', '=', number))
            search_param.append(('transaction_type', '=', type))

            if type == "sale":
                search_param.append(('partner_id', '=', partner))

            resul = self.search(cr, uid, search_param)
            
            if resul:
                return False
            else:
                return True
            
    # General check of number of withhold
    _constraints = [(check_withhold_number_uniq, _('There is another Withhold generated with this number, please verify'),['number']),]
    
    # Constrain Removed, only verify the number, don't check the case if a diferent customer have the same
    # withhold number
    #_sql_constraints = [
    #        ('withhold_number_transaction_uniq','unique(number, transaction_type)','There is another Withhold generated with this number, please verify'),
    #                    ]
    
    # Need to eliminate the old constrain, rewrite with this one
    # TODO: Could be Erase the next time we update the server  
    _sql_constraints = [
            ('withhold_number_transaction_uniq','1',''),
                        ]
    
    def onchange_number(self, cr, uid, ids, number, context=None):
        
        value = {}
        
        if not number:
            return {'value': value}
        
        number_split = str.split(number,"-")

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
                    'number': number_split[0] + "-" + number_split[1] + "-" + number_split[2],
                            })
            
        return {'value': value}
    
    def onchange_creation_date(self, cr, uid, ids, creation_date, invoice_id, context=None):    
        
        value = {}
        if not creation_date or not invoice_id:
            return {'value': value}

        return self._validate_period_date(cr, uid, creation_date, invoice_id, context=context)
    
    
#    TRESCLOUD - En este sprint no necesitamos esta funcionalidad, solo lo basico
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        withhold = self.pool.get('account.withhold').browse(cr, uid, ids, context)
        flag = context.get('invoice', False)
        unlink_ids = []
        for r in withhold:
            if not flag:
                if r['state'] == 'draft':
                    unlink_ids.append(r['id'])
                else:
                    if r['state'] == 'canceled':
                        if r['transaction_type'] == 'sale':
                            unlink_ids.append(r['id'])
                        else:
                            raise osv.except_osv(_('Invalid action !'), _('Cannot delete withhold(s) that are already assigned Number!'))
            else:
                unlink_ids.append(r['id'])
        return super(account_withhold, self).unlink(cr, uid, unlink_ids, context)
    
    def action_move_line_create(self, cr, uid, ids, context=None):

        def _get_payment_term_lines(term_id, amount):
            term_pool = self.pool.get('account.payment.term')
            if term_id and amount:
                terms = term_pool.compute(cr, uid, term_id, amount)
                return terms
            return False
        
        if context is None:
            context = {}
        
        withhold_id = False
        
        if 'withhold_id' in context:
            withhold_id = context['withhold_id']
            
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        currency_pool = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        seq_obj = self.pool.get('ir.sequence')
        
        for inv in self.pool.get('account.voucher').browse(cr, uid, ids, context=context):
        
            if inv.move_id:
                continue
            
            context_multi_currency = context.copy()
            context_multi_currency.update({'date': inv.date})

            if inv.number:
                name = inv.number
            elif inv.journal_id.sequence_id:
                name = seq_obj.get_id(cr, uid, inv.journal_id.sequence_id.id)
            else:
                raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal !'))
            if not inv.reference:
                ref = name.replace('/','')
            else:
                ref = inv.reference

            move = {
                'name': name,
                'journal_id': inv.journal_id.id,
                'narration': inv.narration,
                'date': inv.date,
                'ref': ref,
                'period_id': inv.period_id and inv.period_id.id or False
            }
            move_id = move_pool.create(cr, uid, move)

            #create the first line manually
            company_currency = inv.journal_id.company_id.currency_id.id
            current_currency = inv.currency_id.id
            debit = 0.0
            credit = 0.0
            # TODO: is there any other alternative then the voucher type ??
            # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
            if inv.type in ('purchase', 'payment'):
                credit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
            elif inv.type in ('sale', 'receipt'):
                debit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
            if debit < 0:
                credit = -debit
                debit = 0.0
            if credit < 0:
                debit = -credit
                credit = 0.0
            sign = debit - credit < 0 and -1 or 1
            #create the first line of the voucher
            #TODO: se debe especificar el codigo de impuesto para la realizacion del informe de impuestos
            tax_code_obj = self.pool.get('account.tax.code')
            move_line = {}
            try:
                if context['tax']=='iva':
                    move_line = {
                        'name': inv.name or '/',
                        'debit': debit,
                        'credit': credit,
                        'account_id': inv.account_id.id,
                        'move_id': move_id,
                        'journal_id': inv.journal_id.id,
                        'period_id': inv.period_id.id,
                        'partner_id': inv.partner_id.id,
                        'currency_id': company_currency <> current_currency and  current_currency or False,
                        'amount_currency': company_currency <> current_currency and sign * inv.amount or 0.0,
                        'date': inv.date,
                        'date_maturity': inv.date_due,
                    }
                    
                elif context['tax']=='renta':
                    move_line = {
                        'name': inv.name or '/',
                        'debit': debit,
                        'credit': credit,
                        'account_id': inv.account_id.id,
                        'move_id': move_id,
                        'journal_id': inv.journal_id.id,
                        'period_id': inv.period_id.id,
                        'partner_id': inv.partner_id.id,
                        'currency_id': company_currency <> current_currency and  current_currency or False,
                        'amount_currency': company_currency <> current_currency and sign * inv.amount or 0.0,
                        'date': inv.date,
                        'date_maturity': inv.date_due,
                    }

            except:
                raise osv.except_osv('Error!', _("The residual value of invoice is lower than total value of withholding"))
                    
            # Add the id of withhold
            if withhold_id:
                move_line['withhold_id'] = withhold_id

            move_line_pool.create(cr, uid, move_line)
            rec_list_ids = []
            line_total = debit - credit
            if inv.type == 'sale':
                line_total = line_total - currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)
            elif inv.type == 'purchase':
                line_total = line_total + currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)

            for line in inv.line_ids:
                #create one move line per voucher line where amount is not 0.0
                if not line.amount:
                    continue
                #we check if the voucher line is fully paid or not and create a move line to balance the payment and initial invoice if needed
                if line.amount == line.amount_unreconciled:
                    amount = line.move_line_id.amount_residual #residual amount in company currency
                else:
                    amount = currency_pool.compute(cr, uid, current_currency, company_currency, line.untax_amount or line.amount, context=context_multi_currency)
                move_line = {
                    'journal_id': inv.journal_id.id,
                    'period_id': inv.period_id.id,
                    'name': line.name and line.name or '/',
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'currency_id': company_currency <> current_currency and current_currency or False,
                    'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': inv.date
                }
                #print 'Por cada linea del voucher'
                #print move_line
                if amount < 0:
                    amount = -amount
                    if line.type == 'dr':
                        line.type = 'cr'
                    else:
                        line.type = 'dr'

                if (line.type=='dr'):
                    line_total += amount
                    move_line['debit'] = amount
                else:
                    line_total -= amount
                    move_line['credit'] = amount

                if inv.tax_id and inv.type in ('sale', 'purchase'):
                    move_line.update({
                        'account_tax_id': inv.tax_id.id,
                    })
                if move_line.get('account_tax_id', False):
                    tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
                    if not (tax_data.base_code_id and tax_data.tax_code_id):
                        raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))
                sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                move_line['amount_currency'] = company_currency <> current_currency and sign * line.amount or 0.0
                    
                # Add the id of withhold
                if withhold_id:
                    move_line['withhold_id'] = withhold_id
                
                voucher_line = move_line_pool.create(cr, uid, move_line)
                if line.move_line_id.id:
                    rec_ids = [voucher_line, line.move_line_id.id]
                    rec_list_ids.append(rec_ids)

            if not currency_pool.is_zero(cr, uid, inv.currency_id, line_total):
                diff = line_total
                account_id = False
                if inv.payment_option == 'with_writeoff':
                    account_id = inv.writeoff_acc_id.id
                elif inv.type in ('sale', 'receipt'):
                    #account_id = inv.partner_id.property_account_receivable.id
                    account_id = inv.journal_id.default_debit_account_id.id
                else:
                    #account_id = inv.partner_id.property_account_payable.id
                    account_id = inv.journal_id.default_credit_account_id.id
                move_line = {
                    'name': name,
                    'account_id': account_id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'date': inv.date,
                    'credit': diff > 0 and diff or 0.0,
                    'debit': diff < 0 and -diff or 0.0,
                    #'amount_currency': company_currency <> current_currency and currency_pool.compute(cr, uid, company_currency, current_currency, diff * -1, context=context_multi_currency) or 0.0,
                    #'currency_id': company_currency <> current_currency and current_currency or False,
                }
                    
                # Add the id of withhold
                if withhold_id:
                    move_line['withhold_id'] = withhold_id
                
                move_line_pool.create(cr, uid, move_line)
                #print 'asiento con desajuste'
                #print move_line
            self.pool.get('account.voucher').write(cr, uid, [inv.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            move_pool.post(cr, uid, [move_id], context={})
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    move_line_pool.reconcile_partial(cr, uid, rec_ids)
        return True

    def _validate_period_date(self, cr, uid, creation_date, invoice_id, raise_error=False, context=None):
        
        value = {}
        
        if not creation_date or not invoice_id:
            return {'value':value}
        
        invoice_brow = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        date_invoice = datetime.strptime(invoice_brow.date_invoice, DEFAULT_SERVER_DATE_FORMAT)
        date_withhold = datetime.strptime(creation_date, DEFAULT_SERVER_DATE_FORMAT)
        delta_withhold = date_withhold - date_invoice
        
        #Check if the date is in the same period
        if date_invoice.year != date_withhold.year or date_invoice.month != date_withhold.month:
            message = _('The withhold must be in the same period that the invoice.!')
            if raise_error:
                raise osv.except_osv(_('Error !'), message)
            else:
                warning = {
                       'title': _('Warning!!!'),
                       'message': message,
                           }
                return {
                    'warning': warning,
                    }
        
        #Check if the date is more than 5 days from invoice date
        if delta_withhold.days > 5:
            if not raise_error:
                message = _('The withhold should be issued up to 5 days of invoice. Currently the system allows you to record this withhold at your own risk')
                warning = {
                       'title': _('Warning!!!'),
                       'message': message,
                           }
                return {
                    'warning': warning,
                    }

            
        return {'value':value}

    def action_aprove(self, cr, uid, ids, context=None):
        
        #depending the origin approve in diferent way
        withhold_obj = self.pool.get('account.withhold')
        
        for withhold in withhold_obj.browse(cr, uid, ids, context):
        
            # verify if exist a withhold approve for the invoice related
            if withhold_obj.search(cr, uid, [('invoice_id','=',withhold.invoice_id.id),('state','=','approved')], context):
                raise osv.except_osv('Warning!', _("Withhold for this invoice already exist!!"))
           
            self._validate_period_date(cr, uid, withhold.creation_date, withhold.invoice_id.id, raise_error=True, context=context)
                        
            if withhold.transaction_type == 'sale':
                self.action_approve_sale(cr, uid, ids, context=context)
            
            if withhold.transaction_type == 'purchase':
                self.action_approve_purchase(cr, uid, ids, context=context)
        
            #asign the id in the invoice
            self.pool.get('account.invoice').write(cr, uid, [withhold.invoice_id.id, ], {'withhold_id': withhold.id})
            
        return True
     
    # All actions exist because this work througth wizars and to prevent freezeing the screen 
    # the buttons call object function that execute the transition in workflow   
    def action_approve_sale(self, cr, uid, ids, context=None):

        acc_vou_obj = self.pool.get('account.voucher')
        acc_vou_line_obj = self.pool.get('account.voucher.line')
        acc_move_line_obj = self.pool.get('account.move.line')
        ret_line_obj = self.pool.get('account.withhold.line')
        period_obj = self.pool.get('account.period')
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        journal_iva = company.journal_iva_id
        journal_ir = company.journal_ir_id
        
        if not journal_iva.default_debit_account_id:
            raise osv.except_osv('Error!', _("Iva Retention Journal doesn't have debit account assigned!, can't complete operation"))
        
        if not journal_ir.default_debit_account_id:
            raise osv.except_osv('Error!', _("IR Retention Journal doesn't have debit account assigned!, can't complete operation"))
        
        currency_pool = self.pool.get('res.currency')
        ret_obj = self.pool.get('account.withhold')
        
        for ret in self.browse(cr, uid, ids, context=None):
            #lineas contables no conciliadas que pertenecen a la factura
            # Se requiere la suma de los haberes a cancelar
            total = 0
            sub_iva = 0
            sub_renta = 0
            
            for withhold in ret.withhold_line_ids:
                total = total + withhold.tax_amount
            
                if withhold.description == 'iva':
                    sub_iva = sub_iva + withhold.tax_amount
                
                if withhold.description == 'renta':
                    sub_renta = sub_renta + withhold.tax_amount
                
            # TRESCLOUD - TODO - days deberia seleccionarse en una seccion de configuracion contable
            day = timedelta(days=5)
            add_date = datetime(*time.strptime(ret.invoice_id.date_invoice,'%Y-%m-%d')[:5])+ day
            if ret.invoice_id.amount_total < total:
                raise osv.except_osv('Error!', _("Amount of withhold is bigger than residual value of invoice, please verify"))
            if ret.creation_date < ret.invoice_id.date_invoice:
                raise osv.except_osv('Error!', _("The date of withhold can not be least than the date of invoice"))
            # P.R: Esta parte se controla con los onchage ya que es solo una advertencia
            #if ret.creation_date > add_date.strftime('%Y-%m-%d'):
                #raise osv.except_osv('Error!', _("The date of withhold can not be more than 5 days from the date of the invoice"))
            if total == 0.0:
                raise osv.except_osv('Error!', _("Amount of withhold can't be zero, please verify"))
            #P.R. puede emitirse mas de 1 retencion, una por el iva y otra por la renta
            #for withhold in ret_obj.search(cr, uid, [('invoice_id.partner_id.id', '=', ret.invoice_id.partner_id.id), ('transaction_type','=','sale'), ('id','not in',tuple(ids))]):
                #if ret_obj.browse(cr, uid, [withhold,], context)[0].number_sale == ret.number_sale:
                    #raise osv.except_osv(_('Error!'), _("There is an withhold with number %s of client %s") % (ret.number_sale, ret.invoice_id.partner_id.name))                        
            move_line_ids = acc_move_line_obj.search(cr, uid, [('invoice', '=', ret.invoice_id.id),('state','=','valid'), ('account_id.type', '=', 'receivable'), ('reconcile_id', '=', False)], context=context)
            #se asume que solo existira un movimiento sin conciliar por factura 
            #TODO ->>> Esto debe ser verificado mediante pruebas
            move_line = acc_move_line_obj.browse(cr, uid, move_line_ids, context)[0]
            #se comprueba que la factura se encuentre abierta
            if not ret.invoice_id.state == 'open':
                raise osv.except_osv('Error!', "The invoice is not open, you cannot add a withhold")
            #Se verifica que el residuo de la factura no sea superior a lo que se va a retener
            #TRESCLOUD - TODO discutir si se elimina esta condicion, los saldos a favor del cliente podrian conciliarse con otras facturas.
            #if ret.invoice_id.residual < ret.total:
                #raise osv.except_osv('Error!', "The residual value of invoice is lower than total value of withholding")
            #Obtengo el periodo de la factura
            period=ret.invoice_id.period_id.id
            #creacion de vauchers de pago con retencion
            line_ids = ret_line_obj.search(cr, uid, [('withhold_id', '=', ret['id']),])
            lines = ret_line_obj.browse(cr, uid, line_ids, context)
            
            #variable que guarda los ids de los voucher que se crean para su posterior uso desde retencion
            vouchers = []
            #verifico que existan lineas de retencion
            if lines:
                #creo la cabecera del voucher para las retenciones de iva
                vals_vou_iva = {
                            'type':'receipt',
                            #periodo de la factura
                            'period_id': ret.invoice_id.period_id.id,
                            #fecha de la retencion
                            'date': ret.creation_date,
                            #el diario de iva de la compania
                            'journal_id': journal_iva.id,
                            #numero de retencion como referencia
                            'reference':_('RET CLI: %s') % ret.invoice_id.number,
                            #la cuenta de debido que va a registrar el impuesto
                            'account_id': journal_iva.default_debit_account_id.id,
                            'company_id' : company.id,
                            'amount': sub_iva,
                            'currency_id': ret.invoice_id.currency_id.id,
                            #'withhold_id': ret.id,
                            'partner_id': ret.invoice_id.partner_id.id,
                            'withhold_id': ret.id,
                }
                #creo la cabecera del voucher para las lineas de iva
                voucher_iva = acc_vou_obj.create(cr, uid, vals_vou_iva, context)
                vouchers.append(voucher_iva)
                #creo la cabecera del voucher para las retenciones de renta
                vals_vou_ir = {'type':'receipt',
                            #periodo de la factura
                            'period_id': ret.invoice_id.period_id.id,
                            #fecha de la retencion
                            'date': ret.creation_date,
                            #el diario de iva de la compania
                            'journal_id': journal_ir.id,
                            #numero de retencion como referencia
                            'reference':_('RET CLI: %s') % ret.invoice_id.number,
                            #la cuenta de debido que va a registrar el impuesto
                            'account_id': journal_ir.default_debit_account_id.id,
                            'company_id' : company.id,
                            'amount': sub_renta,
                            'currency_id': ret.invoice_id.currency_id.id,
                            #'withhold_id': ret.id,
                            'partner_id': ret.invoice_id.partner_id.id,
                            'withhold_id': ret.id,
                }
                #creo la cabecera del voucher para las lineas de renta
                voucher_ir = acc_vou_obj.create(cr, uid, vals_vou_ir, context)
                vouchers.append(voucher_ir)
                #recorro cada linea de retencion
                #variables de control para verificar que existen lineas de cada tipo
                renta = False
                iva = False
                for line in lines:
                    #verifico las lineas por tipo para seleccionar el diario correspondiente
                    if line.description == 'iva':
                        vals_vou__iva_line = {
                                    'voucher_id': voucher_iva,
                                    'move_line_id':move_line.id,
                                    'account_id':move_line.account_id.id,
                                    'amount':line.tax_amount,
                                         }
                        acc_vou_line_obj.create(cr, uid, vals_vou__iva_line, context)
                        #se cambia el valor de la variable ya que se encontro al menos una linea de retencion
                        iva = True
                        
                    if line.description == 'renta':
                        vals_vou_ir_line = {
                                    'voucher_id': voucher_ir,
                                    'move_line_id':move_line.id,
                                    'account_id':move_line.account_id.id,
                                    'amount':line.tax_amount,
                                         }
                        acc_vou_line_obj.create(cr, uid, vals_vou_ir_line, context)
                        #se cambia el valor de la variable ya que se encontro al menos una linea de retencion
                        renta = True
                #se aprueba los voucher de rentencion, y se verifica que existan lineas
                #acc_vou_obj.proforma_voucher(cr, uid, [voucher_iva, voucher_ir,], context)
                if iva:
                    #por medio de la variable contexto se especifica que tipo de impuesto es del voucher
                    self.action_move_line_create(cr, uid, [voucher_iva,], context={'tax':'iva', 'withhold_id':ret.id})
                #en caso de no existir lineas en el voucher se elimina el que se creo anteriormente
                else:
                    acc_vou_obj.unlink(cr, uid,[voucher_iva,])
                    vouchers.remove(voucher_iva)
                
                if renta:
                    #por medio de la variable contexto se especifica que tipo de impuesto es del voucher
                    self.action_move_line_create(cr, uid, [voucher_ir,], context={'tax':'renta', 'withhold_id':ret.id})
                #en caso de no existir lineas en el voucher se elimina el que se creo anteriormente
                else:
                    acc_vou_obj.unlink(cr, uid,[voucher_ir,])
                    vouchers.remove(voucher_ir)
                #print vouchers
                #se cambia el estado de la retencion
                if vouchers:
                    acc_vou_obj.write(cr, uid, vouchers, {'withhold_id':ret.id},context)
                date_ret = None
                if not ret.creation_date:
                    date_ret = time.strftime('%Y-%m-%d')
                else:
                    date_ret = ret.creation_date
                self.write(cr, uid, [ret.id,], { 'state': 'approved','creation_date': date_ret,'number':ret.number, 'period_id': period}, context)
            else:
                raise osv.except_osv('Error!', _("You can't aprove a withhold without withhold lines"))
            
        return True
    
    def action_approve_purchase(self, cr, uid, ids, context=None):
        
        if not context:
            context = {}
        
        #account_voucher_obj = self.pool.get('account.voucher')
        #acc_vou_line_obj = self.pool.get('account.voucher.line')
        move_line_pool = self.pool.get('account.move.line')
        #res_company=self.pool.get('res.company')
        #move_pool = self.pool.get('account.move')
        #vouchers = []
        #res=[]

        for withhold in self.browse(cr, uid, ids, context):
            if not withhold.number:
                raise osv.except_osv(_('Error!'), _('Number to be entered to approve the withhold'))
            if not withhold.creation_date:
                raise osv.except_osv(_('Error!'), _('Date to be entered to approve the withhold'))
            if not withhold.withhold_line_ids:
                raise osv.except_osv(_('Error!'), _('must enter at least one tax to approve the withhold'))
            
            self.write(cr, uid, withhold.id, {'state':'approved'})
            
            for line in withhold.withhold_line_ids:
                move_id = withhold.invoice_id.move_id.id
                move_line_ids = move_line_pool.search(cr, uid, [('move_id', '=', move_id),
                                                                ('tax_code_id','=',line.tax_ac_id.id),
                                                                ('state','=','valid')], context=context)              
                move_line_pool.write(cr, uid, move_line_ids, {'withhold_id': withhold.id})
            
        return True
    
    def action_cancel(self,cr,uid,ids,context=None):

        for withhold in self.pool.get('account.withhold').browse(cr, uid, ids, context):

            if withhold.state == "draft":
                self.unlink(cr, uid, [withhold.id,], context)
            
            else:
            
                if withhold.transaction_type == "purchase":
                    move_line_pool = self.pool.get('account.move.line')
                    move_line_ids = move_line_pool.search(cr, uid, [('withhold_id', '=', withhold.id)])
                    move_line_pool.write(cr, uid, move_line_ids, {'withhold_id': False})
            
                if withhold.transaction_type == "sale":

                    moves = []
                    vouchers = []
                    
                    for line in withhold.account_voucher_ids:
                        if not line.move_id.id in moves:
                            moves.append(line.move_id.id)
                    
                    for move in moves:
                        vou = self.pool.get('account.voucher').search(cr, uid, [('move_id','=',move)])
                        vouchers.append(vou[0])
                    
                    self.pool.get('account.voucher').cancel_voucher(cr, uid, vouchers, context)
                    self.pool.get('account.voucher').unlink(cr, uid, vouchers, context)
                
                self.pool.get('account.withhold').write(cr, uid, [withhold.id, ], {'state':'canceled'}, context)
                
        return True
    
    def approve_late(self, cr, uid, ids, context=None):

        for obj in self.browse(cr, uid, ids, context=None):
            
            if obj.transaction_type == 'purchase':
                if not obj.creation_date:
                    raise osv.except_osv(_('Error!'), _('Date to be entered to approve the withhold'))
                
                if not obj.automatic:
                    if not obj.number:
                        raise osv.except_osv(_('Error!'), _('number to be entered to approve the withhold'))

            self.pool.get('account.invoice').write(cr, uid, [obj.invoice_id.id, ], {'withhold_id': obj.id})
                
        return {'type': 'ir.actions.act_window_close'}

    def print_withhold(self, cr, uid, ids, context=None):
        
        # First Aprove the withhold
        self.button_aprove(cr, uid, ids, context=None)

        # Second Generate the pdf
        return {
             'type': 'ir.actions.report.xml',
             'report_name': 'withhold', 
             'datas' : {
                     'model' : 'account.withhold',
                     'res_ids' : ids
                       }        
              }

    # Buttons to operate the workflow to prevet troubles whit double workflow
    def button_aprove(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_validate(uid, 'account.withhold', id, 'approve_signal', cr)
        return True
    
    def button_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_validate(uid, 'account.withhold', id, 'canceled_signal', cr)
        return True
    
    def button_set_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_delete(uid, 'account.withhold', id, cr)
            wf_service.trg_create(uid, 'account.withhold', id, cr)
        return True

account_withhold()
