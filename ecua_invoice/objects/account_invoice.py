# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Andres Calle
# Copyright (C) 2013  TRESCLOUD Cia Ltda
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

#TODO depurar las librerias...
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

    _inherit = "account.invoice"

#    TRESCLOUD - TODO - Evaluar la necesidad de estos valores automaticos
#    def default_get(self, cr, uid, fields_list, context=None):
#        if context is None:
#            context = {}
#        printer_obj = self.pool.get('sri.printer.point')
#        doc_obj=self.pool.get('sri.type.document')
#        values = super(account_invoice, self).default_get(cr, uid, fields_list, context=context)
#        if not values:
#            values={}
#        automatic = context.get('automatic', False)
#        type = context.get('type', False)
#        curr_user = self.pool.get('res.users').browse(cr, uid, uid, context)
#        printer = None
#        if curr_user.printer_default_id:
#            printer = curr_user.printer_default_id
#        if not printer:
#            for shop in curr_user.shop_ids:
#                for printer_id in shop.printer_point_ids:
#                    printer = printer_id
#                    break
#        if printer:
#            values['shop_id'] = printer.shop_id.id
#            values['printer_id'] = printer.id
#            if type == 'out_invoice' and ('invoice_number_out') in fields_list:
#                auth_line_id = doc_obj.search(cr, uid, [('name','=','invoice'), ('printer_id','=',printer.id), ('state','=',True)])
#                if auth_line_id:
#                    auth_line = doc_obj.browse(cr, uid, auth_line_id[0],context)
#                    values['authorization'] = auth_line.sri_authorization_id.number
#                    values['authorization_sales'] = auth_line.sri_authorization_id.id
#                    if automatic:
#                        values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'invoice', False, printer.id, 'account.invoice', 'invoice_number_out', context)
#                        values['invoice_number_out'] = values['automatic_number']
#                        values['date_invoice'] = time.strftime('%Y-%m-%d')
#        return values

#    TRESCLOUD - Al momento no se ha encontrado necesidad de reemplazar la funcion de copia original
#    def copy(self, cr, uid, id, default={}, context=None):
#        inv_obj = self.pool.get('account.invoice')
#        doc_obj=self.pool.get('sri.type.document')
#        original_invoice = inv_obj.browse(cr, uid, id, context)
#        new_number = False
#        autorization_number = False
#        authorization_id = False
#        if original_invoice and original_invoice.shop_id and original_invoice.printer_id and original_invoice.company_id and original_invoice.type == "out_invoice":
#            new_number = doc_obj.get_next_value_secuence(cr, uid, 'invoice', False, original_invoice.printer_id.id, 'account.invoice', 'invoice_number_out', context)
#            authorization_id = original_invoice.authorization_sales.id
#            autorization_number = original_invoice.authorization_sales.number
#        if context is None:
#            context = {}
#        default.update({
#            'state':'draft',
#            'number':False,
#            'move_id':False,
#            'move_name':False,
#            'internal_number': False,
#            'invoice_number_in': False,
#            'automatic_number': new_number,
#            'invoice_number_out': new_number,
#            'invoice_number': False,
#            'authorization_purchase_id': False,
#            'authorization_sales': authorization_id,
#            'authorization': autorization_number,
#        })
#        if 'date_invoice' not in default:
#            default.update({
#                'date_invoice':False
#            })
#        if 'date_due' not in default:
#            default.update({
#                'date_due':False
#            })
#        return super(account_invoice, self).copy(cr, uid, id, default, context)

#    # TRESCLOUD - Esta fue movida al modulo de retencion (withhold)
#    def onchange_authorization_supplier(self, cr, uid, ids, authorization, context=None):

#    # TRESCLOUD - TODO - Revisar si es necesario
#    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
#        if not context: context = {}
#        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
#        res = super(account_invoice,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
#        type = context.get('type', 'out_invoice')
#        client = context.get('client','gtk')
#        liquidation = context.get('liquidation',False)
#        if view_type == 'search':
#            doc = etree.XML(res['arch'])
#            for field in res['fields']:
#                if field == 'number':
#                    nodes = doc.xpath("//field[@name='number']")
#                    for node in nodes:
#                        if type and not liquidation:
#                            node.getparent().remove(node)
#                if field == 'invoice_number_out':
#                    nodes = doc.xpath("//field[@name='invoice_number_out']")
#                    for node in nodes:
#                        if type != 'out_invoice':
#                            node.getparent().remove(node)
#                if field == 'invoice_number_in':
#                    nodes = doc.xpath("//field[@name='invoice_number_in']")
#                    for node in nodes:
#                        if type != 'in_invoice' and not liquidation:
#                            node.getparent().remove(node)
#            res['arch'] = etree.tostring(doc)
#        if view_type == 'tree':
#            for field in res['fields']:
#                if type == 'out_invoice':
#                    if field == 'number':
#                        doc = etree.XML(res['arch'])
#                        nodes = doc.xpath("//field[@name='number']")
#                        for node in nodes:
#                            node.getparent().remove(node)
#                        res['arch'] = etree.tostring(doc)
#                    if field == 'invoice_number_in':
#                        doc = etree.XML(res['arch'])
#                        nodes = doc.xpath("//field[@name='invoice_number_in']")
#                        for node in nodes:
#                            node.getparent().remove(node)
#                        res['arch'] = etree.tostring(doc)
#                else:
#                    if type == 'in_invoice':
#                        if field == 'number':
#                            doc = etree.XML(res['arch'])
#                            nodes = doc.xpath("//field[@name='number']")
#                            for node in nodes:
#                                node.getparent().remove(node)
#                            res['arch'] = etree.tostring(doc)
#                        if field == 'invoice_number_out':
#                            doc = etree.XML(res['arch'])
#                            nodes = doc.xpath("//field[@name='invoice_number_out']")
#                            for node in nodes:
#                                node.getparent().remove(node)
#                            res['arch'] = etree.tostring(doc)
#                    else:
#                        if field == 'invoice_number_out':
#                            doc = etree.XML(res['arch'])
#                            nodes = doc.xpath("//field[@name='invoice_number_out']")
#                            for node in nodes:
#                                node.getparent().remove(node)
#                            res['arch'] = etree.tostring(doc)
#                        if field == 'invoice_number_in':
#                            doc = etree.XML(res['arch'])
#                            nodes = doc.xpath("//field[@name='invoice_number_in']")
#                            for node in nodes:
#                                node.getparent().remove(node)
#                            res['arch'] = etree.tostring(doc)
#                    
#        if view_type == 'form':
#            for field in res['fields']:
#                if user.company_id.generate_automatic:
#                    if field == 'invoice_number_out':
#                        doc = etree.XML(res['arch'])
#                        nodes = doc.xpath("//field[@name='invoice_number_out']")
#                        for node in nodes:
#                            node.getparent().remove(node)
#                        res['arch'] = etree.tostring(doc)
#                else:
#                    if field == 'automatic_number':
#                        doc = etree.XML(res['arch'])
#                        nodes = doc.xpath("//field[@name='automatic_number']")
#                        for node in nodes:
#                            node.getparent().remove(node)
#                        res['arch'] = etree.tostring(doc)
#        return res

    # Indica si la empresa es auto-impresor    
    def _get_automatic(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        return user.company_id.generate_automatic
        return False 
    
    # TRESCLOUD - TODO - Dejar solo la parte del numero automatico de factura / importante
    # Carga automaticamente el numero de factura para venta
    def create(self, cr, uid, vals, context=None):
        company_id = vals.get('company_id', False)
        if not context:
            context = {}
        if vals.get('invoice_number_out', False):
            if context.get('type', False) == 'out_invoice':
                number_out = vals.get('invoice_number_out', False)
                company_id = vals.get('company_id', False)
                vals['automatic_number'] = vals.get('invoice_number_out', False)
        res = super(account_invoice, self).create(cr, uid, vals, context)
        return res
    
    # TRESCLOUD - Las validaciones de RUC y documentos se deben realizar al aprobar la factura, no al guardar
    # por eso se removio en esta funcion las validaciones. 
    def write(self, cr, uid, ids, vals, context=None):
        # no hacemos nada
        res = super(account_invoice, self).write(cr, uid, ids, vals, context)
        return res 
    
    # TRESCLOUD - Esta funcion ya es provista por OpenERP en el boton actualizar, fue removida.
    # def button_reset_taxes(self, cr, uid, ids, context=None):

    # TRESCLOUD - Innecesario al usar el name como el numero de factura, fue removido.
    #    def _number(self, cr, uid, ids, name, args, context=None):
    #        result = {}
    #        for invoice in self.browse(cr, uid, ids, args):
    #            result[invoice.id] = invoice.invoice_number
    #        return result

    # TRESCLOUD - Esta funcion ya es provista por OpenERP en el boton actualizar, fue removida.
    # def _amount_all(self, cr, uid, ids, name, args, context=None):

    # TRESCLOUD - Esta funcion ya es provista por OpenERP en el boton actualizar, fue removida.
    # def _get_invoice_tax(self, cr, uid, ids, context=None):
    
    # TRESCLOUD - No le vemos la necesidad, fue removida
    # def _get_invoice_line(self, cr, uid, ids, context=None):
        
    _columns = {
                #TODO hacer obligatorio el campo name que almacenara el numero de la factura
                #TODO remover el campo create_date
                'create_date': fields.date('Creation date', readonly=True),
                'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
                'invoice_address':fields.char("Invoice address as in VAT document, saved in invoice only not in partner"),
                'invoice_phone':fields.char("Invoice phone as in VAT document, saved in invoice only not in partner"),
               }

    _defaults = {
                 }


    #    TRESCLOUD - No le encontramos necesidad, se elimino
    #    def check_invoice_type(self, cr, uid, ids, *args):

    #    TRESCLOUD - No le encontramos necesidad, se elimino
    #    def check_refund_with_invoice(self, cr, uid, ids, *args):

    #    TRESCLOUD - No le encontramos necesidad, se elimino
    #    def check_refund_without_invoice(self, cr, uid, ids, *args):
        
    #    TRESCLOUD - No le encontramos necesidad, se elimino
    #    def action_wait_invoice(self, cr, uid, ids, *args):
        
    #    TRESCLOUD - No le encontramos necesidad, se elimino
    #    def action_move_credit_note_create(self, cr, uid, ids, *args):
                
    #    TRESCLOUD - No le encontramos necesidad, se elimino
    #    def _create_voucher(self, cr, uid, invoice, credit_note, context):

    #    TRESCLOUD - No le encontramos necesidad, en todo caso deberia ir en un modulo de anulacion de facturas
    #    def _validate_credit_note(self, cr, uid, invoice, credit_note, context):

    #    TRESCLOUD - El tema de productos ICE no es base para la mayoria de empresas, no debe ir en este modulo, se elimino.
    #    def action_check_ice(self, cr, uid, ids, context=None):

    #    TRESCLOUD - Parece importante, pero no para el sprint 1
    #    def action_number(self, cr, uid, ids, context=None):
    #        if not context:
    #            context = {}
    #        inv_obj = self.pool.get('account.invoice')
    #        auth_obj = self.pool.get('sri.authorization')
    #        auth_s_obj = self.pool.get('sri.authorization.supplier')
    #        document_obj = self.pool.get('sri.type.document')
    #        for invoice in self.browse(cr, uid, ids, context):
    #            context['automatic'] = invoice.automatic
    #            if not invoice.partner_id.foreing and not invoice.partner_id.ref:
    #                raise osv.except_osv(_('Error!'), _("Partner %s doesn't have CEDULA/RUC, you must input for validate.") % invoice.partner_id.name)
    #            if invoice.type=='out_invoice':
    #                auth_data = self.pool.get('sri.authorization').check_if_seq_exist(cr, uid, 'invoice', invoice.invoice_number_out, invoice.printer_id.id, invoice.date_invoice, context)
    #                auth = auth_obj.browse(cr, uid, auth_data['authorization'])
    #                document_obj.add_document(cr, uid, [auth_data['document_type_id']], context)
    #                self.write(cr, uid, [invoice.id], {'authorization_sales': auth.id, 'invoice_number': invoice.invoice_number_out, 'authorization': auth.number }, context)
    #            elif invoice.type=='in_invoice':
    #                if invoice.invoice_number_in:
    #                    auth_s_obj.check_number_document(cr, uid, invoice.invoice_number_in, invoice.authorization_supplier_purchase_id, invoice.date_invoice, 'account.invoice', 'invoice_number_in', _('Invoice'), context, invoice.id, invoice.foreign)
    #                    if not invoice.foreign:
    #                        self.write(cr, uid, [invoice.id], {'invoice_number': invoice.invoice_number_in,'authorization_purchase': invoice.authorization_supplier_purchase_id.number}, context)
    #                    else:
    #                        self.write(cr, uid, [invoice.id], {'invoice_number': invoice.invoice_number_in}, context)
    #        result = super(account_invoice, self).action_number(cr, uid, ids, context)
    #        self.write(cr, uid, ids, {'internal_number': False,}, context)
    #        return result
    
    #    TRESCLOUD - No le encontramos necesidad, en todo caso deberia ir en un modulo de anulacion de facturas, se elimino
    #    def action_cancel_draft(self, cr, uid, ids, *args):

    #    TRESCLOUD - Revisar si debe ir en el codigo base, por ejemplo la localizacion venezolana lo tiene en un modulo separado
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
    
    # TRESCLOUD - TODO - Mejorar la funcion removiendo el campo invoice.foreing y basandose en la posicion fiscal en su lugar.
    # TRESCLOUD - TODO - Mejorar la funcion moviendola a un objeto global ya que la misma funcion aplica para todo documento tributario en EC
    def _check_number_invoice(self,cr,uid,ids, context=None):
    #        res = True
    #        for invoice in self.browse(cr, uid, ids):
    #            cadena='(\d{3})+\-(\d{3})+\-(\d{9})'
    #            if invoice.invoice_number_out:
    #                ref = invoice.invoice_number_out
    #                if re.match(cadena, ref):
    #                    res = True
    #                else:
    #                    res = False
    #            if invoice.invoice_number_in and not invoice.foreign:
    #                ref = invoice.invoice_number_in
    #                if re.match(cadena, ref):
    #                    res = True
    #                else:
    #                    res = False
    #            return res
    #    
    #            # TRESCLOUD - Esta validacion aplica para todos los documentos tributarios
    #            if invoice.number_liquidation:
    #                ref = invoice.number_liquidation
    #                if re.match(cadena, ref):
    #                    res = True
    #                else:
    #                    res = False
            return res

    # TRESCLOUD - TODO - Esta funcion ya no es necesaria en OE7 ya que es el comportamiento por defecto, se elimina
    def unlink(self, cr, uid, ids, context=None):
        #        invoices = self.read(cr, uid, ids, ['state'], context=context)
        #        unlink_ids = []
        #        for inv in invoices:
        #            if inv['state'] == 'draft':
        #                unlink_ids.append(inv['id'])
        #            else:
        #                raise osv.except_osv(_('Invalid action!'), _('You can delete Invoice in state Draft'))
        return super(account_invoice, self).unlink(cr, uid, unlink_ids, context)


    _constraints = [(_check_number_invoice,_('The number of Document is incorrect, it must be like 00X-00X-000XXXXXX, X is a number'),['invoice_number_out','invoice_number_in','number_liquidacion'])]
    
    #TRESCLOUD - se removio las lineas de la funcion ya que la evaluacion de extranjero se debe realizar en las posicioens fiscales
    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        # no hacemos nada
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        
        # actualizamos los campos nuevos de direccion y telefono
        partner_obj = self.pool.get('res.partner')
        if partner_id:
            partner = partner_obj.browse(cr, uid, partner_id)
            #TODO - Deberia ser la direccion y telefono de facturacion
            address_invoice = partner.street
            address_phone = partner.phone
        res['value']['invoice_address'] = address_invoice
        res['value']['invoice_phone'] = address_phone

        return res

    # TRESCLOUD - TODO - Evaluar como rehacer esta funcion, la idea es que los tipos de documentos no esten quemados
    #    def name_get(self, cr, uid, ids, context=None):
    #        if not ids:
    #            return []
    #        types = {
    #                'out_invoice': 'FACT-CLI: ',
    #                'in_invoice': 'FACT-PROV: ',
    #                'out_refund': 'NC-CLI: ',
    #                'in_refund': 'NC-PROV: ',
    #                'liquidation': 'LIQ-COMP: ',
    #                }
    #        res = []
    #        for r in self.read(cr, uid, ids, ['type', 'number', 'invoice_number_out', 'invoice_number_in', 'number_credit_note_in', 'number_credit_note_out','number_liquidation','name', 'liquidation'], context, load='_classic_write'):
    #            name = r['number'] or types[r['type']]  or ''
    #            if r['type'] == 'out_invoice':
    #                name = r['invoice_number_out'] or types[r['type']] or ''
    #            if r['type'] == 'in_invoice':
    #                name = r['invoice_number_in'] or types[r['type']] or ''
    #            if r['type'] == 'out_refund':
    #                name = r['number_credit_note_out'] or types[r['type']] or ''
    #            if r['type'] == 'in_refund':
    #                name = r['number_credit_note_in'] or types[r['type']] or ''
    #            if r['liquidation']:
    #                name = r['number_liquidation'] or types['liquidation']  or ''
    #            res.append((r['id'], name ))
    #        return res


    
account_invoice()
