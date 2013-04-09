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

from osv import fields,osv
import decimal_precision as dp
import re
import time
from tools.translate import _
import netsvc
import datetime

class account_retention_line(osv.osv):
    """This have the lines of values retained"""
    def _amount_retained(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            value_retined = float(line.tax_base * (line.retention_percentage/100))
            cur = self.pool.get('res.users').browse(cr, uid, [uid,], context)[0]['company_id']['currency_id']
            res[line.id] = cur_obj.round(cr, uid, cur, value_retined)
        return res
    
    def _amount_retained_manual(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            value_retined = float(line.tax_base * (line.retention_percentage_manual/100))
            cur = self.pool.get('res.users').browse(cr, uid, [uid,], context)[0]['company_id']['currency_id']
            res[line.id] = cur_obj.round(cr, uid, cur, value_retined)
        return res

    def _percentaje_retained(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        #tax_code = self.pool.get('account.tax.code').browse(cr, uid, ids, context)[0]['code']
        for line in self.browse(cr, uid, ids, context=context):
            tax_code_id = self.pool.get('account.tax.code').search(cr, uid, [('id', '=', line.tax_id.id)])
            tax_code = None
            if tax_code_id:
                tax_code = self.pool.get('account.tax.code').browse(cr, uid, tax_code_id, context)[0]['code']
            tax_obj = self.pool.get('account.tax')
            tax = tax_obj.search(cr, uid, [('tax_code_id', '=', tax_code), ('child_ids','=',False)])
            if line.description=="renta":
                tax = tax_obj.search(cr, uid, [('base_code_id', '=', tax_code), ('child_ids','=',False)])
            porcentaje= (tax_obj.browse(cr, uid, tax, context)[0]['amount'])*(-100)
            res[line.id]=porcentaje
        return res
    

    def validar_description(self ,cr, id, ids, context=None):
        for ref in self.browse(cr,id,ids,context=None):
            if (ref['description']=='iva'):
                if ref['tax_id']['code']['type_ec']=='iva':
                    return True
                else:
                    return False
            elif (ref['description']=='renta'):
                if ref['tax_id']['code']['type_ec']=='renta':
                    return True
                else:
                    return False

    def _get_date(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            if line.retention_id:
                res[line.id] = line.retention_id.creation_date
            elif line.invoice_without_retention_id:
                res[line.id] = line.invoice_without_retention_id.date_invoice
        return res
    
    def _get_invoice(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            if line.invoice_retention_id:
                res[line.id] = line.invoice_retention_id.id
            elif line.invoice_without_retention_id:
                res[line.id] = line.invoice_without_retention_id.id
        return res
    
    _name= 'account.retention.line'
    
    _columns = {
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', required=True),
        'description': fields.selection([('iva', 'IVA'),('renta', 'RENTA'),], 'Impuesto', required=True),
        'tax_id':fields.many2one('account.tax.code', 'Tax Code'), 
        'tax_base': fields.float('Tax Base', digits_compute=dp.get_precision('Account')),
        'retention_percentage_manual': fields.float('Percentaje Value', digits_compute=dp.get_precision('Account')), 
        'retained_value_manual': fields.function(_amount_retained_manual, method=True, type='float', string='Reatained Value',
                                          store={
                                                 'account.retention.line': (lambda self, cr, uid, ids, c={}: ids, ['tax_base','retention_percentage_manual'], 10)},), 
        'retention_percentage': fields.function(_percentaje_retained, method=True, type='float', string='Percentaje Value',
                                          store={
                                                 'account.retention.line': (lambda self, cr, uid, ids, c={}: ids, ['tax_id',], 1)},),
        'retained_value': fields.function(_amount_retained, method=True, type='float', string='Reatained Value',
                                          store={
                                                 'account.retention.line': (lambda self, cr, uid, ids, c={}: ids, ['tax_base','retention_percentage'], 10)},), 
        'sequence': fields.integer('Sequence'),
        'retention_id': fields.many2one('account.retention', 'Retention', ondelete='cascade'),
        'creation_date_retention': fields.related('retention_id','creation_date', type='date', relation='account.retention', string='Creation Date'), 
        'creation_date_invoice': fields.date('Creation Date'),
        'creation_date': fields.function(_get_date, method=True, store=True, string='Creation Date', type="date"), 
        'invoice_retention_id': fields.related('retention_id','invoice_id', type='many2one', relation='account.invoice', string='Invoice'), 
        'invoice_without_retention_id':fields.many2one('account.invoice', 'Document', required=False, ondelete="cascade"), 
        'invoice_id': fields.function(_get_invoice, method=True, store=True, string='Document', type="many2one", relation="account.invoice"), 
        'partner_id': fields.related('invoice_id', 'partner_id', type='many2one', relation='res.partner', string='Partner', store=True), 
        'period_id': fields.related('invoice_id', 'period_id', type='many2one', relation='account.period', string='Period', store=True), 
        'company_id': fields.related('invoice_id','company_id', type='many2one', relation='res.company', string='Company'),
        }
    
    _rec_name='sequence'
    
account_retention_line()