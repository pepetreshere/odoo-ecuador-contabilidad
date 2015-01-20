# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Andres Calle, Andrea García, Patricio Rangles
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
    _name = "account.invoice"

    def _amount_all_3(self, cr, uid, ids, name, args, context=None):
        res = {}
        amount_untaxed = 0
        
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'base_doce_iva': 0.00,
                'base_cero_iva': 0.00,
                'vat_doce_subtotal': 0.00,
                'vat_cero_subtotal': 0.00,
                'total_iva': 0.00,
                'total_with_vat': 0.00,
                'total_to_withhold':0.00,
            }
            
        for line in invoice.invoice_line:
            amount_untaxed += line.price_subtotal

        for line in invoice.tax_line:               
            if line.amount > 0:
                if line.type_ec == 'iva' and line.amount > 0:
                    res[invoice.id]['base_doce_iva'] += line.base
                    res[invoice.id]['vat_doce_subtotal'] += line.amount
                if line.type_ec == 'iva':
                    res[invoice.id]['total_iva'] += line.amount          
            else:
                if line.type_ec == 'iva' and line.amount == 0:
                    res[invoice.id]['base_cero_iva'] += line.base
                    res[invoice.id]['vat_cero_subtotal'] += line.amount
                res[invoice.id]['total_to_withhold'] += line.amount

        res[invoice.id]['total_with_vat'] = amount_untaxed + res[invoice.id]['vat_cero_subtotal'] + res[invoice.id]['vat_doce_subtotal']
        
        return res
    
    _columns = {
                #TODO hacer obligatorio el campo name que almacenara el numero de la factura
                'internal_number': fields.char('Invoice Number', size=17, readonly=False, help="Unique number of the invoice, computed automatically when the invoice is created."),
                #'supplier_invoice_number': fields.char('Supplier Invoice Number', size=18, help="The reference of this invoice as provided by the supplier.", readonly=True, states={'draft':[('readonly',False)]}),
               # 'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
                'printer_id':fields.many2one('sri.printer.point', 'Printer Point', required=False),
                'invoice_address':fields.char("Invoice address", help="Invoice address as in VAT document, saved in invoice only not in partner"),
                'invoice_phone':fields.char("Invoice phone", help="Invoice phone as in VAT document, saved in invoice only not in partner"),
                'base_doce_iva': fields.function(_amount_all_3, digits_compute=dp.get_precision('Account'), string='IVA 12 Base',
                            store=True,
                            multi='all1'),
                'base_cero_iva': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='IVA 0 Base',
                            store=True,
                            multi='all1'),        
                'vat_doce_subtotal': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='IVA 12 %',
                            store=True, 
                            multi='all1'),
                'vat_cero_subtotal': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='IVA 0 %',
                            store=True,
                            multi='all1'),
                'total_iva': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='Total IVA',
                            store=True,
                            multi='all1'),
                'total_with_vat': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='Total with taxes',
                            store=True,
                            multi='all1'),
                'total_to_withhold': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='Total to withhold',
                            store=True,
                            multi='all1'),
               }

    def __init__(self, pool, cr):
        """
        Durante la inicialización del modelo correremos un SQL para borrar una
        constraint de SQL que de alguna manera nunca fue borrada, y no tenemos
        en este OpenERP un mecanismo que gestione migraciones, por lo que este
        proceso deberíamos hacerlo manualmente.

        Cuando el módulo se inicializa (se construye) toma dos valores: el pool
        para poder obtener otros objetos, y el cr para ejecutar consultas de
        postgresql. Tomando ese cursor ejecutamos -LUEGO de llamar al super-
        una sentencia SQL de borrado de constraint:

        ALTER TABLE account_invoice DROP CONSTRAINT IF EXISTS account_invoice_number_uniq

        (http://www.postgresql.org/docs/9.1/static/sql-altertable.html).

        El nombre de la tabla está dado a falta de un nombre preconfigurado para
        la tabla en este modelo, por el nombre de la propia clase (account_invoice).

        El nombre de la constraint viene dado por lo reportado en FDU-636.

        Se envuelve todo en un try ... finally ya que, si no existen las tablas al momento
        de crear este modulo, entonces no deberia importarnos el hecho de que esta consulta
        sql falle por una tabla que no exista.
        :param pool:
        :param cr:
        :return:
        """
        super(account_invoice, self).__init__(pool, cr)
        try:
            cr.execute('ALTER TABLE account_invoice DROP CONSTRAINT IF EXISTS account_invoice_number_uniq')
            pass
        finally:
            pass #ignoramos cualquier error.

    def _check_number_invoice(self,cr,uid,ids, context=None):
            res = True

    def unlink(self, cr, uid, ids, context=None):
        """
        Allow delete a invoice in draft state
        """
        invoices = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        
        for inv in invoices:
            if inv['state'] == 'draft':
                unlink_ids.append(inv['id'])
                # write False in the invoice number, this allow eliminate the invoice
                self.write(cr, uid, inv['id'], {'internal_number':False}) 
            else:
                raise osv.except_osv(_('Invalid action!'), _('You can delete Invoice in state Draft'))
            
        return super(account_invoice, self).unlink(cr, uid, unlink_ids, context)


    def onchange_internal_number(self, cr, uid, ids, internal_number, context=None):
        
        value = {}
        
        if not internal_number:
            return {'value': value}
        
        number_split = str.split(internal_number,"-")

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
                    'internal_number': number_split[0] + "-" + number_split[1] + "-" + number_split[2],
                            })
            
        return {'value': value}
    
    def onchange_date_invoice(self, cr, uid, ids, date_invoice, context=None):
        '''
        Asigna un periodo fiscal acorde a la fecha
        '''
        res = {}  
        warning = {}
        periodo = ""
        if not date_invoice:
            return {}
        obj_period = self.pool.get('account.period')
        period_id = obj_period.search(cr,uid,[('date_start','<=',date_invoice),('date_stop','>=',date_invoice)])
        if not period_id:
            warning = {
                    'title': _('Warning!'),
                    'message': _('No existe un período contable para esta fecha. There is no date for this accounting period.')
                }
        else:
            period = obj_period.browse(cr, uid, period_id, context=context)
            periodo = period.pop().id
        res = {'value': {'period_id': periodo} ,
               'warning': warning, 
               'domain': {} }
        return res     

    
    def _default_printer_point(self, cr, uid, context=None):
        '''
        Si el usuario tiene configurado un printer point lo selecciona
        Caso contrario intenta con el 001-001
        '''
    
        printer_point_id = False
        #intenta el printer_point del usuario
        user_obj=self.pool.get('res.users')
        printer = user_obj.browse(cr,uid,uid).printer_id
        if printer:
            printer_point_id = printer.id
            return printer_point_id
        
        #si no esta definido usamos el primero que exista, usuallmente sera el 001-001
        printer_point_obj = self.pool.get('sri.printer.point')
        printer_point_id = printer_point_obj.search(cr,uid,[],limit = 1)

        if printer_point_id:
            return printer_point_id[0]

        return None
    
    def _suggested_internal_number(self, cr, uid, printer_id=None, type=None, company_id=None, context=None):
        '''Numero de factura sugerida para facturas de venta y compra, depende del punto de impresion
           Puede ser redefinida posteriormente por ejemplo para numeracion automatica
        '''
        if context is None:
            context = {}
        
        if context.has_key('type'):
            type = context ['type']
            
        if not printer_id:
            printer_id = _default_printer_point(cr, uid, context)

        number = False #por ejemplo para facturas de tipo hr_advance

        if type in ['out_invoice','in_refund']:
            number = '001-001-'
            printer = self.pool.get('sri.printer.point').browse(cr, uid, printer_id, context=context)
            number = printer.shop_id.number + "-" + printer.name + "-"
        if type in ['in_invoice','out_refund']:
            number = '001-001-'
        return number

    def _get_internal_number_by_sequence(self, cr, uid, obj_inv, context=None):
        """
        Generates, for the given object and number, a valid autogenerated number
          (if it can do  and neither the current user has,
        """

        #we must ensure there's an available printer point by invoice, by user, or the first one
        printer_id = obj_inv.printer_id or self.pool.get('res.users').browse(cr, uid, uid).printer_id
        if not printer_id:
            ppobj = self.pool.get('sri.printer.point')
            pprecs_limit1 = ppobj.search(cr, uid, [], limit=1)
            pprec_first = pprecs_limit1[0] if pprecs_limit1 else False
            printer_id = ppobj.browse(cr, uid, pprec_first) if pprec_first else False

        #if no invoice is found, we return the number as-is
        if not printer_id:
            return obj_inv.number

        #we get the document type to fetch from the printer.
        #if the invoice has a wrong type, the passed type is
        #  None, which will cause the number to be returned.
        document_type = {
            'out_invoice': 'invoice',
            'out_refund': 'refund'
        }.get(obj_inv.type)

        return self.pool.get('sri.printer.point').get_next_sequence_number(cr, uid, printer_id, document_type,
                                                                           obj_inv.number, context)

    def action_number(self, cr, uid, ids, context=None):
        """
        This method allows the usage of custom sequentials for the printer point.

        The code was rewritten completely instead of calling super for one reason:
          This method executes a write, and we need to execute another write because
          we cannot intercept the write part or the invoice number between the lines:
          * number = obj_inv.number
          and
          * self.write(cr, uid, ids, {'internal_number': number})

        So, to avoid making TWO calls to database (which is proven to be painful if you
        run the workflow for 100.000 invoices), I've chosen to completely edit this method
        (notes: it is basically the same, except that I replace the write call with a write call
        for a transformed value: the number is transformed into an auto-generated number, or respected
        if the number comes "good").
        """
        super(account_invoice, self).action_number(cr, uid, ids, context)
        for obj_inv in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, ids, {'internal_number': self._get_internal_number_by_sequence(cr, uid, obj_inv, context)})
        return True

    def _default_internal_number(self, cr, uid, context=None):
        '''Numero de factura sugerida para facturas de venta y compra, depende del punto de impresion
           Puede ser redefinida posteriormente por ejemplo para numeracion automatica
        '''
        number = ''
        type = ''
        printer_id = None
        
        if context is None:
            context = {}
        
        if context.has_key('type'):
            type = context['type']
            
        if context.has_key('printer_id'):
            printer_id = context['printer_id']
        
        if not printer_id:
            printer_id = self._default_printer_point(cr, uid, context)
        
        if printer_id and type:
            number = self._suggested_internal_number(cr, uid, printer_id, type, None, context)
        
        return number

    def _default_date_invoice(self, cr, uid, context=None):
        '''Fecha por defecto es hoy
        '''
        #TODO: Incluir el calculo de zona horaria
        #TODO: Colocar esta funcion en el default
        return str(lambda *a: time.strftime('%Y-%m-%d'),)
    
    _defaults = {
       'printer_id': _default_printer_point,
       'internal_number': _default_internal_number,
       'date_invoice': lambda *a: time.strftime('%Y-%m-%d'),
    } 
    
    def _prepare_invoice_header(self, cr, uid, partner_id, type, inv_date=None, context=None):
        """Retorna los valores ecuatorianos para el header de una factura
           Puede ser usado en ordenes de compra, venta, proyectos, facturacion desde bodegas, etc
           @partner_id es un objeto partner
           @type es el tipo de factura, ej. out_invoice
           @inv_date es la fecha prevista de la factura, si no se provee se asume hoy
        """

        if context is None:
            context = {}
        invoice_vals = {}
        
        partner_obj=self.pool.get('res.partner')
        invoice_address = partner_obj.get_company_address(cr,uid,partner_id) 
        invoice_phone = partner_obj.get_company_phone(cr,uid,partner_id)
        
        inv_obj=self.pool.get('account.invoice')
        printer_id=inv_obj._default_printer_point(cr,uid,uid)
        if printer_id:
            internal_number = inv_obj._suggested_internal_number(cr, uid, printer_id, type, context)
        
        invoice_vals.update({
                        'invoice_address': invoice_address or '',
                        'invoice_phone': invoice_phone or '',
                        'internal_number': internal_number or '',
                        'printer_id': printer_id
                        })
        return invoice_vals
account_invoice()
