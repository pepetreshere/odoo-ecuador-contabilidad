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

import time
import datetime
from dateutil.relativedelta import relativedelta
from os.path import join as opj
from operator import itemgetter

from tools.translate import _
from osv import fields, osv
import netsvc
import tools

class auth_wizard(osv.osv_memory):
    
    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
    
    _name = 'auth.wizard'
    _columns = {
                'auto_printer':fields.boolean('Auto Printer?',), 
                'number':fields.char('Authorization Number', size=10, required=True, readonly=False),
                'start_date': fields.date('Start Date'),
                'expiration_date': fields.date('Expiration Date'),
                'company_id': fields.many2one('res.company', 'Company', required=True),
                'type_document_wizard_ids':fields.one2many('auth.wizard.line', 'auth_wizard_id', 'Document Description', required=True),
               }
    
    _defaults={'company_id':_default_company,
               'auto_printer': lambda *a: False
               }
    
    def crear_sufijo(self, cadena):
        entero = int(cadena)
        retorno = ""
        if entero < 10:
            retorno = "00" + str(entero)
        elif entero < 100:
            retorno = "0" + str(entero)
        else:
            retorno = str(entero)
        return retorno
    
    def button_execute(self, cr, uid, ids, context=None):
        if not context: context = {}
        seq_obj = self.pool.get('ir.sequence')
        journal_obj = self.pool.get('account.journal')
        aut_obj = self.pool.get('sri.authorization')
        dt_obj = self.pool.get('sri.type.document')
        printer_obj = self.pool.get('sri.printer.point')
        
        for wizard in self.browse(cr, uid, ids, context):
            #Se verifica si ya existe alguna autorización con este mismo número, y no sea autoimpresor
            auth_ids = aut_obj.search(cr, uid, [('number','=',wizard.number)])
            auth_id = None
            if not auth_ids:
                #Datos de Nueva Autorización
                auth_id = aut_obj.create(cr, uid, {
                                                  'number':wizard.number,
                                                  'start_date':wizard.start_date,
                                                  'expiration_date':wizard.expiration_date,
                                                  'company_id':wizard.company_id.id,
                                                  'auto_printer': wizard.auto_printer,
                                                }, context)
            else:
                auth_id = auth_ids and auth_ids[0] or None
            for line in wizard.type_document_wizard_ids:
                if not line.shop_id.number or not line.printer_id.number:
                    raise osv.except_osv(_(u'Configuration!!!'),_(u'You must configure number of agency in shop %s') % (line.shop_id.name))
                prefijo_documento = line.shop_id.number + '-' + line.printer_id.number + '-'
                seq_id = seq_obj.create(cr, uid, {
                                                    'name': _(u'Diario de ')+ line.name + ' - '+ wizard.number,
                                                    'prefix': prefijo_documento,
                                                    'company_id': wizard.company_id.id,
                                                    'padding': 9,
                                                    'number_next': line.first_secuence,
                                                    'number_increment':1,
                                                    'implementation': 'no_gap',
                                                    }, context)
                #Se crea linea de autorizacion para emision de documentos
                dt_id = dt_obj.create(cr, uid, {
                                                  'name':line.name,
                                                  'first_secuence': line.first_secuence,
                                                  'last_secuence': line.last_secuence,
                                                  'shop_id':line.shop_id.id,
                                                  'printer_id':line.printer_id.id,
                                                  'sri_authorization_id':auth_id,
                                                  'sequence_id':seq_id,
                                                  'auto_printer':line.auto_printer,
                                                  }, context)
                dt_obj.write(cr, uid, dt_id ,{}, context)
        return {'type':'ir.actions.act_window_close'}
    
auth_wizard()

class auth_wizard_line(osv.osv_memory):
    
    def _get_name(self, cr, uid, context=None):
        output = [
                ('invoice',_('Invoice')),
                ('delivery_note',_('Delivery note')),
                ('withholding',_('Withholding')),
                ('credit_note',_('Credit Note')),
                ('liquidation',_('Liquidation of Purchases')),
                ('debit_note',_('Debit Note'))
                  ]
        return output
    
    def onchange_name(self, cr, uid, ids, name, shop, printer, auto_printer, context=None):
        value = {}
        first_sequence=1
        last_sequence=100
        range_default=99
        if (not name) or (not shop) or (not printer):
            return {'value':value}
        dt_obj = self.pool.get('sri.type.document')
        if auto_printer:
            dt_ant_aut_act_ids = dt_obj.search(cr, uid, [('name','=', name ),('state','=',True), ('shop_id','=',shop),('printer_id','=',printer), ('auto_printer','=',True)])
            if not dt_ant_aut_act_ids:
                dt_ant_aut_ids = dt_obj.search(cr, uid, [('name','=', name ), ('shop_id','=',shop),('printer_id','=',printer), ('auto_printer','=',True)])
                if dt_ant_aut_ids:
                    first_sequence=dt_obj.browse(cr, uid, dt_ant_aut_ids, context)[-1].last_secuence + 1
                else:
                    first_sequence = 1
                value['last_secuence'] = first_sequence
        else:
            #Obtengo la last_sequence secuencia del documento anterior para asignar la siguiente por defecto
            dt_ant_ids = dt_obj.search(cr, uid, [('name','=', name ),('state','=',True), ('shop_id','=',shop),('printer_id','=',printer), ('auto_printer','=',False)])
            if not dt_ant_ids:
                first_sequence=1
            else:
                for dt in dt_obj.browse(cr, uid, dt_ant_ids , context=context):
                    first_sequence=dt['last_secuence']+1
            last_sequence=first_sequence + range_default
            value['last_secuence'] = last_sequence
        value['first_secuence'] = first_sequence
        return {'value':value}
    
    def onchange_number(self, cr, uid, ids, first_secuence, auto_printer, context=None):
        value = {}
        if auto_printer:
            result['last_secuence'] = first_secuence
        return {'value':value}
    
    def _check_sequence(self,cr,uid,ids, context=None):
        for std in self.browse(cr, uid, ids):
            if (std['last_secuence'] < 0 or std['first_secuence'] < 0):
                return False
            else:
                return True
        
    _name = 'auth.wizard.line'
    
    _columns={
              'name':fields.selection(_get_name, 'Name'),
              'first_secuence': fields.integer('Inicial Secuence'),
              'last_secuence': fields.integer('Last Secuence'),
              'shop_id':fields.many2one('sale.shop', 'Shop', required=True),
              'printer_id':fields.many2one('sri.printer.point', 'Printer Point', required=True),
              'auth_wizard_id':fields.many2one('auth.wizard', 'Installer'),
              'auto_printer':fields.boolean('Auto Impresor?', required=False),
              }
    
    _constraints = [
                    (_check_sequence,_('Sequence number must be a positive number'),['first_secuence', 'last_secuence'])
                    ]

    def default_get(self, cr, uid, fields_list, context=None):
        if not context:
            context={}
        values = super(auth_wizard_line, self).default_get(cr, uid, fields_list, context)
        values['auto_printer'] = context.get('auto_printer', False)
        return values
auth_wizard_line()