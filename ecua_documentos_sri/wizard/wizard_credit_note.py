# -*- coding: UTF-8 -*- #
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011-2012 Christopher Ormaza (http://www.ecuadorenlinea.net>). 
#    All Rights Reserved
#    
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of 
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from osv import fields, osv
from tools.translate import _
import netsvc
from lxml import etree
import re

class credit_note_wizard(osv.osv_memory):
    
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

    _name="account.credit.note.wizard"
    _columns={
                'date': fields.date('Operation date', help='This date will be used as the date for Credit Note and Period will be chosen accordingly!'),
                'partner_id': fields.many2one('res.partner', 'Partner'),
                'period_id': fields.many2one('account.period', 'Force period'),
                'journal_id': fields.many2one('account.journal', 'Refund Journal', help='You can select here the journal to use for the refund invoice that will be created. If you leave that field empty, it will use the same journal as the current invoice.'),
                'description': fields.char('Description', size=128, required=True),
                'credit_note_ids':fields.many2many('account.invoice', 'credit_note_wizard_rel', 'credit_note_id', 'credit_note_wizard_id', 'Credit Notes'),
                'shop_id':fields.many2one('sale.shop', 'Shop'),
                'printer_id':fields.many2one('sri.printer.point', 'Printer Point',),
                'number':fields.char('Number', size=17,), 
                'authorization':fields.char('Number', size=10,),
                'authorization_credit_note_purchase_id':fields.many2one('sri.authorization.supplier', 'Authorization', readonly=True, states={'draft':[('readonly',False)]}), 
                'filter_credit_note':fields.selection([
                    ('modify','Modify'),
                    ('cancel','Cancel'),
                    ('multi','Multi Credit Note'),
                     ],    'Filter', select=True,),
                'automatic_number':fields.char('Number', size=17, readonly=True),
                'automatic':fields.boolean('Automatic', required=False),
              }

    _constraints = [(_check_number, _('The number is incorrect, it must be like 001-00X-000XXXXXX, X is a number'), ['number'])]

    def _get_automatic(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.generate_automatic
    
    def _get_journal(self, cr, uid, context=None):
        obj_journal = self.pool.get('account.journal')
        if context is None:
            context = {}
        journal = obj_journal.search(cr, uid, [('type', '=', 'sale_refund')])
        if context.get('type', False):
            if context['type'] in ('in_invoice', 'in_refund'):
                journal = obj_journal.search(cr, uid, [('type', '=', 'purchase_refund')])
        return journal and journal[0] or False

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        doc_obj=self.pool.get('sri.type.document')
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=context)
        values = {}
        res = []
        objs = self.pool.get(context['active_model']).browse(cr , uid, context['active_ids'])
        if 'value' not in context.keys():
            for obj in objs:
                if obj.type == 'out_invoice':
                    values = {
                             'shop_id': obj.shop_id.id,
                             'printer_id': obj.printer_id.id,
                             'automatic': self._get_automatic(cr, uid, context),
                            }
                    if obj.printer_id:
                        auth_line_id = doc_obj.search(cr, uid, [('name','=','credit_note'), ('printer_id','=',obj.printer_id.id), ('shop_id','=',obj.shop_id.id), ('state','=',True)])
                        if auth_line_id:
                            values['authorization'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.number
                            #values['autorization_credit_note_id'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.id
                    if values.get('automatic', False):
                        values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'credit_note', False, obj.printer_id.id, 'account.invoice', 'number_credit_note_out', context)
                        values['number'] = values['automatic_number']
                    values['date'] = time.strftime('%Y-%m-%d')
                    values['filter_credit_note'] = 'modify'
                    values['journal_id'] =  self._get_journal(cr, uid, context)
                if obj.type == 'in_invoice':
                    values['partner_id'] = obj.partner_id.id
        else:
            values = context['value']
        return values

    def onchange_data(self, cr, uid, ids, automatic, shop_id=None, printer_id=None, context=None):
        doc_obj = self.pool.get('sri.type.document')
        values = {}
        if context is None:
            context = {}
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=context)
        shop_ids = []
        curr_shop = False
        if shop_id:
            curr_shop = self.pool.get('sale.shop').browse(cr, uid, [shop_id, ], context)[0]
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        if curr_shop:
            if printer_id:
                auth_line_id = doc_obj.search(cr, uid, [('name','=','credit_note'), ('printer_id','=',printer_id), ('shop_id','=',curr_shop.id), ('state','=',True),])
                if auth_line_id:
                    if automatic:
                        values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'credit_note', False, printer_id, 'account.invoice', 'number_credit_note_out', context)
                        values['number'] = values['automatic_number']
                        values['date'] = time.strftime('%Y-%m-%d')
                else:
                    values['automatic'] = False
                    values['date'] = None
        return {'value': values, }

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        if not context: context = {}
        journal_obj = self.pool.get('account.journal')
        invoice_obj = self.pool.get('account.invoice')
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        res = super(credit_note_wizard,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        type = context.get('journal_type', 'sale_refund')
        type_credit_note = "out_refund"
       
        if type in ('sale', 'sale_refund'):
            type = 'sale_refund'
        else:
            type = 'purchase_refund'
            type_credit_note = "in_refund"

        domain_credit_notes = [('type', '=', type_credit_note),('state','=','wait_invoice')]

        partner_id = None
        if context.get('active_model', False) == "account.invoice":
            invoice = invoice_obj.browse(cr, uid, context.get('active_id', False), context)
            if invoice:
                domain_credit_notes.append(('partner_id','=', invoice.partner_id.id))
        for field in res['fields']:
            if field == 'journal_id':
                journal_select = journal_obj._name_search(cr, uid, '', [('type', '=', type)], context=context, limit=None, name_get_uid=1)
                res['fields'][field]['selection'] = journal_select
            if field == 'credit_note_ids':
                res['fields'][field]['domain'] = domain_credit_notes
            if context.get('sales', False):
                if user.company_id.generate_automatic:
                    if field == 'automatic_number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='automatic_number']")
                        for node in nodes:
                            node.set('invisible', "0")
                        res['arch'] = etree.tostring(doc)
                    if field == 'number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='number']")
                        for node in nodes:
                            node.set('invisible', "1")
                        res['arch'] = etree.tostring(doc)
                else:
                    if field == 'automatic_number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='automatic_number']")
                        for node in nodes:
                            node.set('invisible', "1")
                        res['arch'] = etree.tostring(doc)
                    if field == 'number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='number']")
                        for node in nodes:
                            node.set('invisible', "0")
                        res['arch'] = etree.tostring(doc)
        return res
    
   
    def get_option(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        wizard = self.browse(cr, uid, ids[0])
        obj_model = self.pool.get('ir.model.data')
        inv_obj = self.pool.get('account.invoice')
        option = wizard.filter_credit_note
        invoice = inv_obj.browse(cr, uid, context.get('active_id', False), context)
        if option == "modify" or option == "cancel":
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_account_credit_note_new')])
            if invoice.type == "in_invoice":
                model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_account_credit_note_new_provider')])
        else:
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_account_credit_note_multi')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        context['filter_credit_note'] = option
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.credit.note.wizard',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
    
    def new_credit_note(self, cr, uid, ids, context):
        if not context:
            context = {}
        wizard = self.browse(cr, uid, ids[0])
        inv_obj = self.pool.get('account.invoice')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        wf_service = netsvc.LocalService('workflow')
        inv_tax_obj = self.pool.get('account.invoice.tax')
        inv_line_obj = self.pool.get('account.invoice.line')
        res_users_obj = self.pool.get('res.users')
        auth_s_obj = self.pool.get('sri.authorization.supplier')
        invoice = inv_obj.browse(cr, uid, context.get('active_id', False), context)
        for form in  self.read(cr, uid, ids, context=context):
            values_credit_note = {}
            credit_note_id = inv_obj.refund(cr, uid, [invoice.id], form['date'], form['period_id'], form['description'], form['journal_id'])
            values_credit_note['invoice_rectification_id'] = invoice.id
            if invoice.type == "out_invoice":
                v = inv_obj.onchange_number_credit_note(cr, uid, None, form['number'], invoice.automatic, invoice.company_id.id, invoice.shop_id.id, invoice.printer_id.id, context)
                values_credit_note['automatic'] = form['automatic']
                values_credit_note['number_credit_note_out'] = form['number']
                values_credit_note['automatic_number'] = form['number']
                values_credit_note['autorization_credit_note_id'] = v['value']['autorization_credit_note_id']
            if invoice.type == "in_invoice":
                values_credit_note['number_credit_note_in'] = form['number']
                values_credit_note['authorization_credit_note_purchase_id'] = form['authorization_credit_note_purchase_id']
                auth_number = None
                if form['authorization_credit_note_purchase_id']:
                    auth_number = auth_s_obj.browse(cr, uid, form['authorization_credit_note_purchase_id'], context).number
                values_credit_note['authorization_credit_note_purchase'] = auth_number
            inv_obj.write(cr, uid, credit_note_id, values_credit_note ,context)
            if context.get('filter_credit_note', False) == 'cancel':
                wf_service.trg_validate(uid, 'account.invoice', credit_note_id[0], 'invoice_open', cr)

            if invoice.type in ('out_invoice', 'out_refund'):
                xml_id = 'action_customer_credit_note_menu'
            else:
                xml_id = 'action_supplier_credit_note_menu'
            result = mod_obj.get_object_reference(cr, uid, 'ecua_notas_credito_manual', xml_id)
            id = result and result[1] or False
            result = act_obj.read(cr, uid, id, context=context)
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', credit_note_id))
            result['domain'] = invoice_domain
            return result

    def compute_credit_notes(self, cr, uid, ids, context):
        if not context:
            context = {}
        wizard = self.browse(cr, uid, ids[0])
        inv_obj = self.pool.get('account.invoice')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        wf_service = netsvc.LocalService('workflow')
        inv_tax_obj = self.pool.get('account.invoice.tax')
        inv_line_obj = self.pool.get('account.invoice.line')
        res_users_obj = self.pool.get('res.users')
        invoice = inv_obj.browse(cr, uid, context.get('active_id', False), context)
        for form in  self.read(cr, uid, ids, context=context):
            for credit_note in form['credit_note_ids']:
                inv_obj.write(cr, uid, credit_note, {'invoice_rectification_id': invoice.id})
                wf_service.trg_validate(uid, 'account.invoice', credit_note, 'assing_invoice', cr)
        return True

    
credit_note_wizard()