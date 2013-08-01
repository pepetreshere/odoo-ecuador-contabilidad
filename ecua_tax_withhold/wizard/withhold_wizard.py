# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2011  Ecuadorenlinea.net                                #
#            (Christopher Ormaza)                                       #
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

from osv import fields, osv
import decimal_precision as dp
from tools.translate import _
import time
import netsvc
import re
from lxml import etree
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class account_withhold_wizard(osv.osv_memory):
    
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
    
    def _transaction_type(self, cr, uid, ids, context=None):
        if context is None:
            context = {
                'transaction_type':'purchase',
                       }
        return context.get('transaction_type', False)

    _name = 'account.withhold.wizard'

    _columns = {
        'partner_id':fields.many2one('res.partner', 'Partner' ),
        'currency_id': fields.many2one('res.currency', 'Currency', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, change_default=True),
        'number':fields.char('Number', size=17,),
        'creation_date': fields.date('Creation Date'),
        'printer_id':fields.many2one('sri.printer.point', 'Printer Point'),
        'invoice_id': fields.many2one('account.invoice', 'Number of Invoice', readonly=True),
        'automatic':fields.boolean('Automatic', required=True),
        'transaction_type':fields.selection([
                                             ('purchase','Purchases'),
                                             ('sale','Sales'),
                                             ],  'Transaction type', required=True, readonly=True),
        'type':fields.selection([
                            ('automatic', 'Automatic'),
                            ('manual', 'Manual'),
                            ], 'type', required=True, readonly=True),
        'lines_ids': fields.one2many('account.withhold.wizard.line', 'withhold_id', 'Withhold line'),
                }

    _defaults = {
        'transaction_type': _transaction_type,
                 }
    
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
        ret_line_id=0
        users=self.pool.get('res.users')
        printer_id=users.browse(cr,uid,uid).printer_id.id
        if context.get('active_model'):
            objs = self.pool.get(context['active_model']).browse(cr , uid, context['active_ids'])
            if 'value' not in context.keys():
                for obj in objs:
                    if obj.type == 'out_invoice':
                        values = {
                                 'printer_id':printer_id,
                                 'partner_id': obj.partner_id.id,
                                 'invoice_id': obj.id,
                                 'creation_date': obj.date_invoice,#cambiar
                                 'type':'manual',
                                }
                    if obj.type in ('in_invoice'):
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
                                                 'tax_amount': tax_line['amount'],
                                                 'withhold_percentage':0
                                                 
                                                 }  
                                vals_ret_line['withhold_percentage']=self._withhold_percentaje(cr, uid, vals_ret_line, context)
                                res.append(vals_ret_line)  
                            elif tax_line['tax_amount'] == 0 and tax_line['type_ec'] == 'renta':
                                vals_ret_line = {'tax_base':tax_line.base,
                                                 'fiscalyear_id':fiscalyear_id,
                                                 'invoice_without_withhold_id': obj.id,
                                                 'description': tax_line.type_ec,
                                                 'tax_id': tax_line.base_code_id.id,
                                                 'tax_ac_id':tax_ac_id,
                                                 'creation_date_invoice': obj.date_invoice,
                                                 }
                        values = {
                                     'printer_id':printer_id,
                                     'invoice_id': obj.id,
                                     'creation_date': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                     'type':'manual',
                                     'transaction_type':"purchase",
                                     'currency_id':obj.currency_id.id,
                                     'partner_id':obj.partner_id.id,
                                     'company_id':obj.company_id.id,
                                     'lines_ids': res,
                                    }
            else:
                values = context['value']
        return values
    
    def create_withhold(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        withhold_obj = self.pool.get('account.retention')
        account_voucher_obj = self.pool.get('account.voucher')
        #acc_move_line_obj = self.pool.get('account.move.line')
        acc_vou_line_obj = self.pool.get('account.voucher.line')
        move_line_pool = self.pool.get('account.move.line')
        res_company=self.pool.get('res.company')
        move_pool = self.pool.get('account.move')
        ret_vals = {}
        ret_line_vals = {}
        objs = self.pool.get(context['active_model']).browse(cr , uid, context['active_ids'])[0]
        vouchers = []
        res=[]
        for withhold in self.browse(cr, uid, ids, context):
            if not withhold.number:
                raise osv.except_osv(_('Error!'), _('Number to be entered to approve the withhold'))
            if not withhold.creation_date:
                raise osv.except_osv(_('Error!'), _('Date to be entered to approve the withhold'))
            if not withhold.lines_ids:
                raise osv.except_osv(_('Error!'), _('must enter at least one tax to approve the withhold'))
            number = None
            auth_id = None
            company = res_company.browse(cr, uid, withhold.company_id.id)
            ret_vals = {
                 'number':withhold.number,
                 'creation_date': withhold.creation_date,
                 'transaction_type': withhold.transaction_type,
                 'invoice_id': withhold.invoice_id.id,
                 'period_id': objs.period_id.id,
                 'account_voucher_ids':[],
                 'withhold_line_ids':[],
                 'state':'approved',
                 }
            
            withhold_id = withhold_obj.create(cr, uid, ret_vals, context)

            self._create_withholds_lines(cr, uid, withhold_id, withhold.lines_ids, context)

            for line in withhold.lines_ids:
                move_id=withhold.invoice_id.move_id.id
                move_line_ids = move_line_pool.search(cr, uid, [('move_id', '=', move_id),('tax_code_id','=',line.tax_ac_id.id),('state','=','valid')], context=context)              
                move_line_pool.write(cr,uid,move_line_ids,{'withhold_id':withhold_id})
            #ret_vals['account_voucher_ids']=res
            
        return withhold_id
    
    def _create_withholds_lines(self, cr, uid, withhold_id, withhold_lines, context=None):

        # create a list with withholds in the wizard
        for line in withhold_lines:
            
            val = {
            'withhold_id': withhold_id,
            'fiscalyear_id': line.fiscalyear_id.id,
            'description': line.description,
            'tax_base': line.tax_base,
            'withhold_percentage': line.withhold_percentage,
            'tax_amount': line.tax_amount,
            'tax_id': line.tax_id.id,
            'tax_ac_id': line.tax_ac_id.id,
                   } 
            
            self.pool.get('account.withhold.line').create(cr, uid, val, context)
        
        return True
    
    def approve_now(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        withhold = self.create_withhold(cr, uid, ids, context)
        wf_service.trg_validate(uid, 'account.retention', retention, 'approve_signal', cr)
        return {'type': 'ir.actions.act_window_close'}
    
    def approve_late(self, cr, uid, ids, context=None):
        objs = self.pool.get(context['active_model']).browse(cr , uid, context['active_id'])
        for obj in self.browse(cr, uid, ids, context=None):
            if obj.type == 'manual':
                withhold = self.create_withhold(cr, uid, ids, context)
            if obj.type == 'automatic':
                if not obj.creation_date:
                    raise osv.except_osv(_('Error!'), _('Date to be entered to approve the withhold'))
                if not obj.automatic:
                    if not obj.number:
                        raise osv.except_osv(_('Error!'), _('number to be entered to approve the withhold'))
                #P.R: No se requiere?? el docuemnto origen me da el numero del invoice
                #self.pool.get('account.retention').write(cr, uid, [objs.withhold_ids[0].id, ], {'origin':obj.number}, context)
                self.pool.get('account.retention').write(cr, uid, [objs.withhold_ids[0].id, ], {'automatic': obj.automatic,'creation_date': obj.creation_date, 'authorization_purchase_id': obj.authorization_purchase.id, 'shop_id':obj.shop_id.id, 'printer_id':obj.printer_id.id}, context)
        return {'type': 'ir.actions.act_window_close'}
    
#    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
#        if not context: context = {}
#        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
#        res = super(withhold_wizard, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
#        if not context.get('sales', False):
#            if view_type == 'form':
#                for field in res['fields']:
#                    #if user.company_id.generate_automatic:
#                    if user.company_id:
#                        if field == 'automatic_number':
#                            doc = etree.XML(res['arch'])
#                            nodes = doc.xpath("//field[@name='automatic_number']")
#                            for node in nodes:
#                                node.set('invisible', "0")
#                            res['arch'] = etree.tostring(doc)
#                        if field == 'number':
#                            doc = etree.XML(res['arch'])
#                            nodes = doc.xpath("//field[@name='number']")
#                            for node in nodes:
#                                node.set('invisible', "1")
#                            res['arch'] = etree.tostring(doc)
#                    else:
#                        if field == 'automatic_number':
#                            doc = etree.XML(res['arch'])
#                            nodes = doc.xpath("//field[@name='automatic_number']")
#                            for node in nodes:
#                                node.set('invisible', "1")
#                            res['arch'] = etree.tostring(doc)
#                        if field == 'number':
#                            doc = etree.XML(res['arch'])
#                            nodes = doc.xpath("//field[@name='number']")
#                            for node in nodes:
#                                node.set('invisible', "0")
#                            res['arch'] = etree.tostring(doc)
#        return res
    
    def button_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

account_withhold_wizard()

class account_withhold_wizard_line(osv.osv_memory):
    _name = "account.withhold.wizard.line"

    _columns = {
            'withhold_id': fields.many2one('account.withhold.wizard', 'Wizard'),
            'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year'),
            'description': fields.selection([('iva', 'IVA'), ('renta', 'RENTA'), ], 'Impuesto'),
            'tax_base': fields.float('Tax Base', digits_compute=dp.get_precision('Account')),
            'withhold_percentage': fields.float('Percentage Value', digits_compute=dp.get_precision('Account')),
            'tax_amount':fields.float('Amount', digits_compute=dp.get_precision('Account')),
           # 'withhold_percentage': fields.function(_percentaje_retained, method=True, type='float', string='Percentaje Value',
            #                             store={'account.withhold.line': (lambda self, cr, uid, ids, c={}: ids, ['tax_id',], 1)},),
            #'withhold_percentage': fields.function(_percentaje_retained, method=True, type='float', string='Percentaje Value'),
            'tax_id':fields.many2one('account.tax.code', 'Tax Code'),
            'tax_ac_id':fields.many2one('account.tax.code', 'Tax Code'),
            }
    
account_withhold_wizard_line()
