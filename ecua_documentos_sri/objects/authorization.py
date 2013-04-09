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

from osv import osv, fields, orm
import time
from tools.translate import _
import netsvc

class sri_authorization(osv.osv):

    def _verify_state(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for auth in self.browse(cr, uid, ids, context=context):
            state = False
            for line in auth.type_document_ids:
                if line.state == True:
                    state=True
            if auth.auto_printer:
                #TODO verificar la fecha de expiración
                if auth.expiration_date > time.strftime('%Y-%m-%d'):
                    state = False
            res[auth.id] = state
        return res
        
    def _get_authorization(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sri.type.document').browse(cr, uid, ids, context=context):
            result[line.sri_authorization_id.id] = True
        return result.keys()
        
    _name = 'sri.authorization'
    
    _columns = {
                'auto_printer':fields.boolean('Auto Printer?'),
                'number':fields.char('Authorization Number', size=10, required=True, readonly=False),
                'creation_date': fields.date('Creation Date'),
                'start_date': fields.date('Start Date'),
                'expiration_date': fields.date('Expiration Date'),
                'company_id':fields.many2one('res.company', 'Company', required=True),
                'type_document_ids':fields.one2many('sri.type.document', 'sri_authorization_id', 'Documents Types', required=True),
                'state': fields.function(_verify_state, method=True, type='boolean', string='Active',
                                        store={  
                                               'sri.authorization': (lambda self, cr, uid, ids, c={}: ids, ['type_document_ids'], 10),
                                               'sri.type.document': (_get_authorization , ['state','count'], 9),
                                               }),
               }
    
    _rec_name='number'

    _sql_constraints = [('number_uniq','unique(number,company_id)', _('The number of authorization must be unique per company'))]
    
    def find(self, cr, uid, dt=None, context=None):
        if not dt:
            dt = time.strftime('%Y-%m-%d')
        ids = self.search(cr, uid, [('expiration_date','>=',dt)])
        return ids
    
    #Funcion que valida la fecha del documento con la fecha de la autorizacion
    def check_date_document(self, cr, uid, date_document=None, auth_id=None, context=None):
        if not context: context = {}
        auth = self.browse(cr, uid, auth_id, context)
        if not auth: return False
        if (date_document >= auth.start_date) and (date_document <= auth.expiration_date):
            return True
        else:
            return False
    
    #Función que verifica que exista una secuencia
    def check_if_seq_exist(self, cr, uid, type='invoice', secuence=None, printer_id=None, date_document=None, context=None):
        if not context: context = {}
        name_type = {
                    'invoice':_('Invoice'),
                    'delivery_note':_('Delivery note'),
                    'withholding':_('Withholding'),
                    'credit_note':_('Credit Note'),
                    'liquidation':_('Liquidation of Purchases'),
                    'debit_note':_('Debit Note')
                     }
        if not date_document: date_document = time.strftime('%Y-%m-%d')
        res = {
               'authorization' : None,
               'document_type_id': None,
               }
        number = None
        printer = None
        #Se verifica que el número tenga el formato correcto
        try:
            number = secuence.split('-')
        except:
            return res
        line_auth_obj = self.pool.get('sri.type.document')
        printer_obj = self.pool.get('sri.printer.point')
        if printer_id:
            printer = printer_obj.browse(cr, uid, printer_id, context)
        if not printer:
            return res
        #Se verifica que exista alguna línea de autorización que cumpla con este criterio
        line_auth_ids = line_auth_obj.search(cr, uid, [('name','=',type), ('printer_id','=',printer.id)])
        for document in line_auth_obj.browse(cr, uid, line_auth_ids, context):
            if not document.sri_authorization_id.auto_printer:
                #Se verifica que el número este dentro de las secuencias de la autorización
                if (int(number[2])>= document.first_secuence and int(number[2])<= document.last_secuence):
                    res['authorization'] = document.sri_authorization_id.id
                    res['document_type_id'] = document.id
                    if not self.check_date_document(cr, uid, date_document, res['authorization'], context):
                        raise osv.except_osv(_('Error!!!'),('There\'s not authorization for this document %s with number %s in this date %s') % (name_type.get(type, _('Invoice')), secuence, date_document))
                    break
        #Se verifica que el número de la agencia sea el mismo que la primera secuencia
        if not printer.number == number[0]:
            res['authorization'] = None
            res['document_type_id'] = None
        #Se verifica que el número del punto de emisión sea el mismo que el de la secuencia
        if not printer.number == number[1]:
            res['authorization'] = None
            res['document_type_id'] = None
        if not res['authorization'] or not res['document_type_id']:
            raise osv.except_osv(_('Error!!!'),('There\'s not authorization for this document %s with number %s') % (name_type.get(type, _('Invoice')), secuence))       
        return res
    
    
    def get_auth_secuence(self, cr, uid, type, printer_id=None, context=None):
        if not context: context = {}
        line_auth_obj = self.pool.get('sri.type.document')
        printer_obj = self.pool.get('sri.printer.point')
        if not printer_id:
            printer_id = printer_obj.browse(cr, uid, printer_id, context)
        line_auth_ids = line_auth_obj.search(cr, uid, [('name','=',type),('state','=',True),('printer_id','=',printer_id)])
        auth_id = None
        seq_id = None
        for line_id in line_auth_ids:
            auth = line_auth_obj.browse(cr, uid, line_id, context).sri_authorization_id
            if auth.state:
                seq_id = line_auth_obj.browse(cr, uid, [line_id,], context)[0]['sequence_id']['id']
                auth_id = auth.id
        return{'authorization': auth_id, 'sequence':seq_id}
        
    def verify_expiration_date(self, cr, uid, context):
        auth_obj = self.pool.get('sri.authorization')
        seq_obj = self.pool.get('ir.sequence')
        ids = []
        for auth_id in auth_obj.search(cr, uid, [('auto_printer','=',True),('state','=',True)]):
            auth= auth_obj.browse(cr, uid, auth_id, context)
            if auth.expiration_date > time.strftime('%Y-%m-%d'):
                for line in auth.type_document_ids:
                    line_next_ids=self.pool.get('sri.type.document').search(cr, uid, [('expired','=',True),('name','=',line.name), ('shop_id','=',line.shop_id.id), ('printer_id','=',line.printer_id.id)])
                    for line_next in self.pool.get('sri.type.document').browse(cr, uid, line_next_ids, context):
                        if line_next.sri_authorization_id.start_date > auth.expiration_date and line_next.sri_authorization_id.auto_printer:
                            self.pool.get('sri.type.document').write(cr, uid, [line_next.id,], {'expired':False, 'first_secuence':line.last_secuence+1, 'last_secuence':line.last_secuence+1}, context)
                            self.pool.get('ir.sequence').write(cr, uid, [line_next.sequence_id.id, ], {'number_next':line.last_secuence+1}, context)
                            ids.append(line_next.sri_authorization_id.id)
                    self.pool.get('sri.type.document').write(cr, uid, [line.id,], {'expired':True}, context)
                    ids.append(line.sri_authorization_id.id)
        auth_obj.write(cr, uid, ids, {}, context)
        return True    

sri_authorization()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: