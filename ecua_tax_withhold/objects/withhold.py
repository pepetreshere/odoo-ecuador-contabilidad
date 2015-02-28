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
import math

from mx import DateTime
from datetime import datetime,timedelta

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class account_withhold_line(osv.osv):
   
    _name = "account.withhold.line"

    def _withhold_line_percentaje(self, cr, uid, description, tax_id):
        percentage = 0.0
        tax_code_brow = self.pool.get('account.tax.code').browse(cr, uid, tax_id)
        tax_obj = self.pool.get('account.tax')
        if tax_code_brow:
            if description == 'iva':
                tax = tax_obj.search(cr, uid, [('tax_code_id', '=', tax_code_brow.id), ('child_ids','=',False)])
            elif description == 'renta':
                tax = tax_obj.search(cr, uid, [('base_code_id', '=', tax_code_brow.id), ('child_ids','=',False)])
            if tax:
                percentage = (tax_obj.browse(cr, uid, tax[0])['amount'])*(-100)
                
        return percentage

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
            'tax_wi_id':fields.many2one('account.tax', 'Tax', help="Tax for withhold"),

            'tax_ac_id':fields.many2one('account.tax.code', 'Tax Code', help="Tax"),
            'transaction_type_line': fields.selection([
            ('purchase','Purchases'),
            ('sale','Sales'),
            ],'Transaction type', required=True, readonly=True, track_visibility='onchange'),
            }


    def default_get(self, cr, uid, fields, context=None):

        if context is None:
            context = {}
        
        values = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        
        if context.get('transaction_type') and context.get('transaction_type') == 'sale':
            transaction_type = context.get('transaction_type')
            

            if transaction_type == 'sale':
                values = {
                         'transaction_type_line': transaction_type,
                         'description': 'renta', #un valor por defecto, pudo haber sido iva sin problema
                         }
            
        return values


    
    def onchange_description(self, cr, uid, ids, description, invoice_amount_untaxed, invoice_vat_doce_subtotal):
        """ This function change the domain for tax_id using the description.
        Only show taxes according they description. Also add the tax base according the value in invoice
        """
    
        res = {'domain':{},
               'value': {
                         'tax_id': False,
                         'tax_ac_id': False,
                         'tax_base': False,
                         }
               }
        
        if not description:
            return res

        #check the description and select the tax base
        tax_base = 0.0
        if description == 'iva':
            res['value']['tax_base'] = invoice_vat_doce_subtotal
        elif description == 'renta':
            res['value']['tax_base'] = invoice_amount_untaxed

        #until check the filter using the type of tax
        return res

        #search the tax like description need
        account_tax_obj = self.pool.get('account.tax')
        list_tax = account_tax_obj.search(cr, uid, [('type_ec', '=', description),
                                                    ('tax_code_id', '!=', False)], context=context)

        code_id_list = []
        for tax in account_tax_obj.browse(cr, uid, list_tax, context=context):
            if tax.tax_code_id.id not in code_id_list:
                code_id_list.append(tax.tax_code_id.id)

        
        if code_id_list:
            res["value"].update({"tax_id": code_id_list[0]})
            domain = [('id', 'in', code_id_list)]
            res["domain"]={'tax_id': domain}
        
        return res
    
    def onchange_tax_id(self, cr, uid, ids, description, tax_id, tax_base):
        """ 
        This function calculate the amount using the percentage of tax, also return this percentage
        """
    
        res = {'value': {
                         'tax_amount': 0.0,
                         'withhold_percentage': 0.0,
                         }
               }
        
        if not description or not tax_id:
            return res
        
        #check the tax and extract the percentage
        tax = self.pool.get('account.tax').browse(cr, uid, tax_id)     
        withhold_percentage = abs(tax.amount) #TODO: Considerar los impuestos hijos en el caso del 332 por ejemplo
        tax_amount = (withhold_percentage * tax_base)
        res['value']['withhold_percentage'] = withhold_percentage 
        res['value']['tax_amount'] = tax_amount
        res['value']['tax_id'] = tax.base_code_id.id
        return res
    
account_withhold_line()

class account_withhold(osv.osv):
        
    _name = 'account.withhold'
    _rec_name='number'

    _inherit = ['mail.thread']

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
    
    def _withhold_percentaje(self, cr, uid, vals_ret_line, context=None):
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

                    #tax_wi_id = res_company.get_default(cr, uid, 'res.company', 'tax_wi_id') 
                    invoice_obj=self.pool.get('account.invoice')
                    printer_id = invoice_obj._default_printer_point(cr, uid, context)
                    printer=self.pool.get('sri.printer.point').browse(cr, uid, [printer_id], context)[0]
                    shop_id = printer.shop_id.id
                            
                    fiscalyear_id = None
                    
                    tax = self.pool.get('account.tax')
                    if not obj['period_id']:
                        period_ids = self.pool.get('account.period').search(cr, uid, [('date_start','<=',time.strftime('%Y-%m-%d')),('date_stop','>=',time.strftime('%Y-%m-%d')),])
                        if period_ids:
                            fiscalyear_id= self.pool.get('account.period').browse(cr, uid, [period_ids[0]], context)[0]['fiscalyear_id']['id']
                    else:
                        fiscalyear_id = obj['period_id']['fiscalyear_id']['id']
                    
                    tax_wi_id = obj.company_id.tax_wi_id.id
                    
                    if not tax_wi_id :
                       raise osv.except_osv(_('Invalid action !'), _('Configurar en la compania la cuenta de las retenciones.!'))  
                    bw_tax =tax.browse(cr, uid, tax_wi_id, context)
                    vals_ret_line = {}

                    vals_ret_line = {
                                     'fiscalyear_id':fiscalyear_id,  
                                     'description': bw_tax.type_ec,
                                     'tax_id': bw_tax.base_code_id.id  ,
                                     'tax_wi_id':tax_wi_id,
                                     'tax_base': context['amount_untaxed'],
                                     'tax_amount': context['amount_untaxed']*abs(obj.company_id.tax_wi_id.amount), #0 ,#
                                     'withhold_percentage':obj.company_id.tax_wi_id.amount,
                                     'transaction_type_line': transaction_type
                                     }
                    
                    res.append(vals_ret_line) 
                    
                    values = {
                         'shop_id': shop_id,
                         'printer_id': printer_id,
                         'partner_id': obj.partner_id.id,
                         'invoice_id': obj.id,
                         'creation_date': obj.date_invoice,
                         'transaction_type': transaction_type,
                         'company_id': obj.company_id.id,
                         'withhold_line_ids': res,
                            }
                    
                elif transaction_type == 'purchase':
                    tax_wi_id = False #no esta implementado para compras
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
                                             'tax_ac_id': tax_ac_id,
                                             'tax_base': tax_line['base'],
                                             'tax_amount': abs(tax_line['amount']),
                                             'withhold_percentage':0,
                                             'transaction_type_line': transaction_type
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
                                             'tax_wi_id': tax_wi_id,
                                             'tax_ac_id':tax_ac_id,
                                             'creation_date_invoice': obj.date_invoice,
                                             'transaction_type_line': transaction_type
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

        # add defaults if context have this values
        if context and 'amount_untaxed' in context:
            values['invoice_amount_untaxed'] = context['amount_untaxed']
        if context and 'amount_untaxed' in context:
            values['invoice_vat_doce_subtotal'] = context['vat_doce_subtotal']
            
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
                              help="Number of Withhold", track_visibility='onchange'),
        #'origin': fields.char('Origin Document', size=128, required=False),
        'creation_date': fields.date('Creation Date',states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]},
                                     help="Date of creation of Withhold", track_visibility='onchange'),

        #Campo utilizado para identificar el tipo de documento de origen y alterar su funcionamiento
        'transaction_type':fields.selection([
            ('purchase','Purchases'),
            ('sale','Sales'),
            ],  'Transaction type', required=True, readonly=True, track_visibility='onchange'),

        #TRESCLOUD - Removimos el "ondelete='cascade" del invoice_id, puede llevar a borrados inintencionales!
        'invoice_id': fields.many2one('account.invoice', 'Number of document', required=False, states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]},
                                      help="Invoice related with this withhold", track_visibility='onchange'),
        'partner_id': fields.related('invoice_id','partner_id', type='many2one', relation='res.partner', string='Partner', store=True,
                                     help="Partner related with this withhold", track_visibility='onchange'),

        #TRESCLOUD - Deberia guardarse el nombre del partner, su RUC, direccion, etc (ejemplo el año que viene el cliente cambia de direccion,
        # entonces el documento tributario del año 2012 no deberia verse afectado)  
        'company_id': fields.related('invoice_id','company_id', type='many2one', relation='res.company', string='Company', store=True, change_default=True,
                                     help="Company related with this withhold (in multi-company environment)", track_visibility='onchange'),
        'state':fields.selection([
            ('draft','Draft'),
            ('approved','Approved'),
            ('canceled','Canceled'),
            ],  'State', required=True, readonly=True, track_visibility='onchange'),
        'account_voucher_ids': fields.one2many('account.move.line', 'withhold_id', 'Withhold',
                                               help="List of account moves", track_visibility='onchange'),
        'automatic': fields.boolean('Automatic?',track_visibility='onchange'),
        'period_id': fields.related('invoice_id','period_id', type='many2one', relation='account.period', string='Period', store=True,
                                    help="Period related with this transaction", track_visibility='onchange'), 
        'shop_id': fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]},
                                   help="Shop related with this transaction, only need in Purchase", track_visibility='onchange'),
        'printer_id': fields.many2one('sri.printer.point', 'Printer Point', readonly=True,
                                      states={'draft':[('readonly',False)]}, ondelete='restrict',
                                      help="Printer Point related with this transaction, only need in Purchase", track_visibility='onchange'),
        #P.R: Required the authorization asociated depending if is purchase or sale
        'authorization_sri': fields.char('Authorization', readonly=True, states={'draft':[('readonly',False)]}, size=32,
                                         help="Number of authorization use by the withhold", track_visibility='onchange'),
        #P.R: Required in this format to generate the account moves using this lines
        'withhold_line_ids': fields.one2many('account.withhold.line', 'withhold_id', 'Withhold lines',
                                             help="List of withholds"),
        #P.R: Required to show in the printed report
        'total': fields.function(_total, method=True, type='float', string='Total Withhold', store = True,
                                 help="Total value of withhold", track_visibility='always'),
        #P.R: Required to show in the ats report
        'total_iva': fields.function(_total_iva, method=True, type='float', string='Total IVA', store = False,
                                 help="Total IVA value of withhold", track_visibility='always'),   
        'total_renta': fields.function(_total_renta, method=True, type='float', string='Total RENTA', store = False,
                                 help="Total renta value of withhold", track_visibility='always'),      
        #P.R: Required to show in the tree view
        'total_base_iva': fields.function(_total_base_iva, method=True, type='float', string='Total Base IVA', store = False,
                                 help="Total base IVA of withhold", track_visibility='always'),   
        'total_base_renta': fields.function(_total_base_renta, method=True, type='float', string='Total Base RENTA', store = False,
                                 help="Total base renta of withhold", track_visibility='always'),      
        'comment': fields.text('Additional Information', track_visibility='onchange',
                               help="Text can be use to comment the withhold, if it's necesary"),
        # auxiliar fields to hold the amounts to use in base tax
        'invoice_amount_untaxed': fields.float('Invoice amount untaxed', digits_compute=dp.get_precision('Account'),
                                     help="Invoice amount untaxed used like base for the compute of tax"),  
        'invoice_vat_doce_subtotal': fields.float('Invoice vat doce subtotal', digits_compute=dp.get_precision('Account'),
                                     help="Invoice vat doce subtotal used like base for the compute of tax"),
          
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
    #ELIMINAMOS ESTE CONSTRAINT (dejo el metodo por las dudas)
    #_constraints = [(check_withhold_number_uniq, _('There is another Withhold generated with this number, please verify'),['number']),]
    
    # Constrain Removed, only verify the number, don't check the case if a diferent customer have the same
    # withhold number
    #_sql_constraints = [
    #        ('withhold_number_transaction_uniq','unique(number, transaction_type)','There is another Withhold generated with this number, please verify'),
    #                    ]
    
    # Need to eliminate the old constrain, rewrite with this one
    # TODO: Could be Erase the next time we update the server  
    #===========================================================================
    # _sql_constraints = [
    #         ('withhold_number_transaction_uniq','1',''),
    #                     ]
    #===========================================================================
    
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
    
    def onchange_creation_date(self, cr, uid, ids, transaction_type, printer_id, partner_id, creation_date, invoice_id, context=None):    
        '''
        Valida fecha de retencion vs fecha de autorizacion
        '''
        res = {'value': {},'warning':{},'domain':{}}
        if not creation_date or not invoice_id:
            return res

        res2 = self._validate_period_date(cr, uid, creation_date, invoice_id, context=context)
        if "value" in res2:
            res["value"].update(res2["value"])
        if "domain" in res2:
            res["domain"].update(res2["domain"])
        if "warning" in res2:
            res["warning"]["message"] = res2.get('warning') and res2.get('warning').get('message')
        return res

    def onchange_printer_id(self, cr, uid, ids, transaction_type, printer_id, partner_id, creation_date, context=None):
        '''
        Actualiza el numero de retencion con el prefijo del punto de impresion y la tienda
        Este metodo se redefine con el modulo autorizaciones para cargar el numero de autorizacion
        '''
        
        res = {'value': {},'warning':{},'domain':{}}

        if transaction_type == 'purchase': #solo para retenciones emitidas
            if printer_id and partner_id and creation_date:
                printer = self.pool.get('sri.printer.point').browse(cr, uid, printer_id, context=context)
                number = printer.shop_id.number + "-" + printer.name + "-"
                res['value'].update({
                            'shop_id': printer.shop_id.id,
                            'number': number,
                            })
            else:
                res['value'].update({
                            'shop_id': False,
                            'number': False,
                            })   
        return res

    def _prepare_withhold_header(self, cr, uid, partner_id, type, date=None, context=None):
        """Retorna los valores ecuatorianos para el header de una retencion
           @partner_id es un objeto partner
           @type es el tipo de retencion, ej. purchase o sale
           @date es la fecha prevista de la retencion, si no se provee se asume hoy
        """
        #para hacerlo DRY utilizamos funciones ya definidas en account.invoice
        #TODO: De ser necesario desarrollar este metodo, inspirarse en account.invoice
        return True
    
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
        '''
        Valida que la retencion sea recibida 5 dias despues de la factura y dentro del mismo periodo
        '''
        
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

    def action_approve_validate(self, cr, uid, withhold_obj, withhold, context):

        # verify if exist a withhold approve for the invoice related
        if withhold_obj.search(cr, uid, [('invoice_id', '=', withhold.invoice_id.id),
                                         ('state', '=', 'approved'),
                                         ('id', '!=', withhold.id)], context=context):
            raise osv.except_osv('Error!', _("Ya existe una retención para esta factura!!"))

        self._validate_period_date(cr, uid, withhold.creation_date, withhold.invoice_id.id, raise_error=True, context=context)

    def action_aprove(self, cr, uid, ids, context=None):
        
        #depending the origin approve in diferent way
        withhold_obj = self.pool.get('account.withhold')
        
        for withhold in withhold_obj.browse(cr, uid, ids, context):

            self.action_approve_validate(cr, uid, withhold_obj, withhold, context)
                        
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
        '''
        Aprueba la retencion emitida por nuestros clientes
        Cuando el valor a retener es mayor al saldo de la factura (ejemplo una factura pagada) 
        el account.voucher creado usa la cuenta de desajuste por defecto
        '''
        acc_vou_obj = self.pool.get('account.voucher')
        acc_vou_line_obj = self.pool.get('account.voucher.line')
        acc_move_line_obj = self.pool.get('account.move.line')
        ret_line_obj = self.pool.get('account.withhold.line')
        #period_obj = self.pool.get('account.period')
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id #TODO: Cambiar por la compañia asociada al documento
        journal_iva = company.journal_iva_id
        journal_ir = company.journal_ir_id
                
        currency_pool = self.pool.get('res.currency')
        #ret_obj = self.pool.get('account.withhold') #TODO: eliminar esta variable, no hacia falta pues se tenia a self.
        
        for ret in self.browse(cr, uid, ids, context=None):
            #Calculamos los subtotales de la retencion
            #TODO: no recalcular el total sino tomarlo del campo de total que ya existe en la retencion
            
            total = 0
            sub_iva = 0
            sub_renta = 0
            
            for withhold in ret.withhold_line_ids:
                #Calculamos los valores totales a retener
                #TODO: no recalcular el total sino tomarlo del campo de total que ya existe en la retencion
                total = total + withhold.tax_amount
            
                if withhold.description == 'iva':
                    #TODO: no recalcular el total sino tomarlo del campo de total que ya existe en la retencion
                    sub_iva = sub_iva + withhold.tax_amount
                
                if withhold.description == 'renta':
                    #TODO: no recalcular el total sino tomarlo del campo de total que ya existe en la retencion
                    sub_renta = sub_renta + withhold.tax_amount
                
            #Realizamos validaciones para ventas
            #TODO: Mover estas validaciones a una seccion comun de validaciones para compras y ventas
            error = ''
            if not journal_iva.default_debit_account_id:
                error += 'El Diario de Retencion IVA debe tener una cuenta contable de debito asignada!'
                error += '\n'

            if not journal_iva.default_writeoff_acc_id:
                error += 'El Diario de Retencion IVA debe tener una cuenta contable de conciliacion de balance abierto por defecto!'
                error += '\n'
                
            if not journal_ir.default_debit_account_id:
                error += 'El Diario de Retencion I.R. (Impuesto a la Renta) debe tener una cuenta contable de debito asignada!'
                error += '\n'

            if not journal_ir.default_writeoff_acc_id:
                error += 'El Diario de Retencion I.R. (Impuesto a la Renta) debe tener una cuenta contable de conciliacion de balance abierto por defecto!'
                error += '\n'
                
            if sub_iva + sub_renta != total:
                error += 'El total a retener no coincide con el subtotal de retencion de IVA + el subtotal de retencion IR. Contacte a soporte tecnico.'
                error += '\n'
            if ret.creation_date < ret.invoice_id.date_invoice:
                error += 'La fecha de la retencion no puede ser menor que la fecha de la factura'
                error += '\n'
            if total == 0.0:
                error += 'La cantidad de la retencion no puede ser cero'
                error += '\n'
            #TODO: En la version 2015 se puede emitir retenciones en cantidad cero para empresas publicas, parece ser, se debe verificar
            if ret.invoice_id.amount_total < total:
                #TODO: Desarrollar 
                error += 'La cantidad a retener es mayor que el valor residual de la factura'
                error += '\n'

            if not ret.invoice_id.state in ['open','paid']:
                error += 'La factura no ha sido aprobada por lo que no se puede generar una retencion'
                error += '\n'
            #P.R. Una retencion puede afectar mas de una factura, hasta una mejor solucion se remueve el constraint
            #TODO: Permitir hacer retenciones de varias facturas a la vez
            #for withhold in ret_obj.search(cr, uid, [('invoice_id.partner_id.id', '=', ret.invoice_id.partner_id.id), ('transaction_type','=','sale'), ('id','not in',tuple(ids))]):
                #if ret_obj.browse(cr, uid, [withhold,], context)[0].number_sale == ret.number_sale:
                    #raise osv.except_osv(_('Error!'), _("There is an withhold with number %s of client %s") % (ret.number_sale, ret.invoice_id.partner_id.name))                        
            #Se verifica que el residuo de la factura no sea superior a lo que se va a retener
            #TRESCLOUD - TODO discutir si se elimina esta condicion, los saldos a favor del cliente podrian conciliarse con otras facturas.
            #if ret.invoice_id.residual < ret.total:
                #raise osv.except_osv('Error!', "The residual value of invoice is lower than total value of withholding")
            #Obtengo el periodo de la factura
            #TODO: El periodo debe ser el de la retencion, en ausencia del mismo puede usarse el de la factura
            if not ret.invoice_id.period_id.id == ret.period_id.id:
                error += 'La retencion y la factura deben pertenecer al mismo periodo contable'
                error += '\n'
                
            if not ret.period_id.state in ['draft']:
                error += 'El periodo contable ya se encuentra cerrado, no se puede crear nuevos documentos'
                error += '\n'
            
            if not ret_line_obj.search(cr, uid, [('withhold_id', '=', ret['id']),]): #verifico que existan lineas de retencion
                error += 'Debe existir al menos una linea de retencion'
                error += '\n'
            
            if error:
                #lanzamos todos los errores encontrados en un solo resultado
                raise osv.except_osv('Error!', error)
            
            #creacion de vouchers de pago con retencion
            line_ids = ret_line_obj.search(cr, uid, [('withhold_id', '=', ret['id']),])
            lines = ret_line_obj.browse(cr, uid, line_ids, context)
            
            #creo la cabecera del voucher para las retenciones de iva
            if sub_iva > 0:
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
                            #TODO: Se podria obtener con el onchange del diario o algo asi, 
                            #asi el modulo base del sistema podria encargarse del calculo de cuanto va a las lineas y
                            #cuanto al writeoff_amount
                            'writeoff_amount': 0.0, 
                            'payment_option': 'without_writeoff',
                            'writeoff_acc_id': False,
                            'comment': '',
                }            
                voucher_iva = acc_vou_obj.create(cr, uid, vals_vou_iva, context)
            
            #creo la cabecera del voucher para las retenciones de renta
            if sub_renta > 0:
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
                            #TODO: Se podria obtener con el onchange del diario o algo asi, 
                            #asi el modulo base del sistema podria encargarse del calculo de cuanto va a las lineas y
                            #cuanto al writeoff_amount
                            'writeoff_amount': 0.0, 
                            'payment_option': 'without_writeoff',
                            'writeoff_acc_id': False,
                            'comment': '',
                }
                voucher_ir = acc_vou_obj.create(cr, uid, vals_vou_ir, context)
            
            
            #recorro cada linea de retencion y creo lineas de account.voucher hasta cruzarlas
            vals_vou_iva_line = {}
            vals_vou_ir_line = {}
            total_to_compare = ret.invoice_id.residual
            #comparacion de floats de dimension conocida, comparamos si es menor o igual
            #TODO: Investigar otras opciones como assert_almost_equal
            if total < total_to_compare or abs(total < total_to_compare) < 0.0000000001 : #si hay saldo abierto mayor al valor retenido cruzamos el saldo abierto con la retencion 
                #TODO:
                # En este sprint se asume que el primer movimiento contable cubrira con éxito el valor a retener 
                # Se deberia reprogramar esta parte para q soporte por ejemplo plazos de pago o varios movimientos de cruce
                # Esta seccion se puede reprogramar basandose en el modulo sale_order_for_retail donde ya se hizo funcionalidad similar

                #Obtenemos las lineas contables con las que cruzaremos la retencion, si acaso alguna (si la factura esta pagada no hay ninguna)
                move_line_ids = acc_move_line_obj.search(cr, uid, [('invoice', 'in', [ret.invoice_id.id]), #TODO: Permitir varios ids para una retencion que afecta a varias facturas 
                                                                   ('state','=','valid'), 
                                                                   ('account_id.type', '=', 'receivable'), 
                                                                   ('reconcile_id', '=', False)], 
                                                         order='date_maturity ASC', 
                                                         context=context)

                move_line = acc_move_line_obj.browse(cr, uid, move_line_ids, context)[0]
                for line in lines: #creamos las lineas de account voucher
                    #verifico las lineas por tipo para seleccionar el diario correspondiente
                    if line.description == 'iva':
                        vals_vou_iva_line = {
                                    'voucher_id': voucher_iva, #fue definida dentro de un if (si esta out of scope es un error intencional)
                                    'move_line_id':move_line.id,
                                    'account_id':move_line.account_id.id,
                                    'amount':line.tax_amount,
                                         }
                        acc_vou_line_obj.create(cr, uid, vals_vou_iva_line, context)

                    if line.description == 'renta':
                        vals_vou_ir_line = {
                                    'voucher_id': voucher_ir, #fue definida dentro de un if (si esta out of scope es un error intencional)
                                    'move_line_id':move_line.id,
                                    'account_id':move_line.account_id.id,
                                    'amount':line.tax_amount,
                                         }
                        acc_vou_line_obj.create(cr, uid, vals_vou_ir_line, context)
            else: 
                #No generamos lineas de account.voucher pues no hay con que cruzar, en su lugar usamos la cuenta de desajuste
                #'writeoff_amount': 0.0, no se requiere porque al guardar el voucher este campo se calcula solo
                #TODO: El codigo actual no permite cruzar parte de la retencion con el saldo abierto y otra parte con la cuenta de desajuste
                payment_option = 'with_writeoff'
                if sub_iva:
                    res_onchange = acc_vou_obj.onchange_payment_option(cr, uid, voucher_ir, payment_option, journal_ir.id)
                    res_onchange['value'].update({'payment_option': payment_option,
                                                  'comment': 'SALDO RET. IVA: %s' % ret.number 
                                                  })
                    acc_vou_obj.write(cr, uid, voucher_iva, res_onchange['value'], context=context)
                if sub_renta:
                    res_onchange = acc_vou_obj.onchange_payment_option(cr, uid, voucher_ir, payment_option, journal_ir.id)
                    res_onchange['value'].update({'payment_option': payment_option,
                                                  'comment': 'SALDO RET. IR: %s' % ret.number 
                                                  })
                    acc_vou_obj.write(cr, uid, voucher_ir, res_onchange['value'], context=context)

            
            vouchers = [] #variable que guarda los ids de los voucher que se crean para su posterior uso desde retencion
            #agregamos las lineas a los account.voucher
            if sub_iva:
                self.action_move_line_create(cr, uid, [voucher_iva,], context={'tax':'iva', 'withhold_id':ret.id})
                vouchers.append(voucher_iva)
            if sub_renta:
                self.action_move_line_create(cr, uid, [voucher_ir,], context={'tax':'renta', 'withhold_id':ret.id})
                vouchers.append(voucher_ir)                    
            
            #se cambia el estado de la retencion
            #if vouchers: #comentado porque no hay razon por la que vouchers no existiria
            #acc_vou_obj.write(cr, uid, vouchers, {'withhold_id':ret.id},context)
            self.write(cr, uid, [ret.id,], {
                                            'state': 'approved',
                                            #'creation_date': ret.creation_date, #TODO: quiza ya no hace falta 
                                            #'number':ret.number, #TODO: quiza ya no hace falta 
                                            #'period_id': ret.invoice_id.period_id.id, #TODO: quiza ya no hace falta
                                            },
                       context=context)
        
        #codigo viejo a remover
        #else:
            #raise osv.except_osv('Error!', _("You can't aprove a withhold without withhold lines"))
        
        return True





    def _action_approve_purchase_validate(self, cr, uid, withhold, number, context):
        """
        Executes validation over a withhold (for purchase).
        """
        if self.search(cr, uid, [('id', '!=', withhold.id), ('number', '=', number)], context=context):
            raise osv.except_osv(_('Error!'), _('Number %d is occupied. Please choose another number or change the'
                                                'withhold sequence\'s number for the chosen printer point'))
        if not withhold.creation_date:
            raise osv.except_osv(_('Error!'), _('Date to be entered to approve the withhold'))
        if not withhold.withhold_line_ids:
            raise osv.except_osv(_('Error!'), _('must enter at least one tax to approve the withhold'))

    def _action_approve_purchase_update(self, cr, uid, withhold, move_line_obj, number, context=None):
        """
        Executes update over a withhold (for purchase).
        """
        self.write(cr, uid, withhold.id, {'state': 'approved', 'number': number})

        for line in withhold.withhold_line_ids:
            move_id = withhold.invoice_id.move_id.id
            move_line_ids = move_line_obj.search(cr, uid, [('move_id', '=', move_id),
                                                           ('tax_code_id', '=', line.tax_ac_id.id),
                                                           ('state', '=', 'valid')], context=context)
            move_line_obj.write(cr, uid, move_line_ids, {'withhold_id': withhold.id})

    def _action_approve_purchase_number(self, cr, uid, withhold, printer_point_obj, context):
        """
        Sets a number, based on the printer point, for the current purchase withhold document.
        """
        #if no invoice is found, we return the number as-is
        if withhold.printer_id:
            return printer_point_obj.get_next_sequence_number(cr, uid, withhold.printer_id,
                                                              'withhold', withhold.number, context)
        else:
            return withhold.number

    def action_approve_purchase(self, cr, uid, ids, context=None):
        
        if not context:
            context = {}

        move_line_pool = self.pool.get('account.move.line')
        printer_point_obj = self.pool.get('sri.printer.point')

        for withhold in self.browse(cr, uid, ids, context):
            number = self._action_approve_purchase_number(cr, uid, withhold, printer_point_obj, context)
            self._action_approve_purchase_validate(cr, uid, withhold, number, context)
            self._action_approve_purchase_update(cr, uid, withhold, move_line_pool, number, context)

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

    def only_print_withhold(self, cr, uid, ids, context=None):

        if ids:
            withhold = self.browse(cr, uid, ids[0])
            # check it's a purchase withhold
            if withhold.transaction_type == 'purchase':

                return {
                     'type': 'ir.actions.report.xml',
                     'report_name': 'withhold',    # the 'Service Name' from the report
                     'datas' : {
                             'model' : 'account.withhold',    # Report Model
                             'res_ids' : ids
                               }        
                      }

            elif withhold.transaction_type == 'sale':

                return {
                     'type': 'ir.actions.report.xml',
                     'report_name': 'withhold_sale',    # the 'Service Name' from the report
                     'datas' : {
                             'model' : 'account.withhold',    # Report Model
                             'res_ids' : ids
                               }        
                      }
        
        return {}
    
    def print_withhold(self, cr, uid, ids, context=None):
        
        # First Aprove the withhold
        self.button_aprove(cr, uid, ids, context=None)

        # Second Generate the pdf
        res = self.only_print_withhold(cr, uid, ids, context=context)
        
        return res 


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
