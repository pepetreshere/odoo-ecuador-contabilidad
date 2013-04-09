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

from osv import osv, fields
import time
from tools.translate import _
class sri_type_document(osv.osv):
    
    def _verify_state(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for document in self.browse(cr, uid, ids, context=context):
            if document.sri_authorization_id.auto_printer:
                res[document.id] = document.expired
            else:
                if document.counter <= document.range:
                    res[document.id]=True
                else:
                    res[document.id]=False
        return res


    
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
    
    def _get_range(self, cr, uid, ids, name, args, context=None):
        result = {}
        for document in self.browse(cr, uid, ids, args):
            result[document.id] = document.last_secuence - document.first_secuence
        return result
    
    
    def add_document(self,cr, uid, ids, context=None):
        seq_obj = self.pool.get('ir.sequence')
        if not context:
            context = {}
        for document in self.browse(cr, uid, ids, context=context):
            if document.sri_authorization_id.auto_printer:
                self.write(cr, uid, [document.id,],{'last_secuence': document.last_secuence+1, 'counter': document.counter+1}, context=context )
            else:
                if context.get('automatic', False):
                    seq_obj.get_id(cr, uid, document.sequence_id.id)
                self.write(cr, uid, [document.id,],{'counter': document.counter+1}, context=context)
            
    def rest_document(self,cr, uid, ids, context=None):
        seq_obj = self.pool.get('ir.sequence')
        if not context:
            context = {}
        for document in self.browse(cr, uid, ids, context=context):
            if document.sri_authorization_id.auto_printer:
                self.write(cr, uid, [document.id,],{'last_secuence': document.last_secuence-1, 'counter': document.counter-1}, context=context )
            else:
                if context.get('automatic', False):
                    seq_obj.write(cr, uid, document.sequence_id.id, {'next_number':document.sequence_id - 1})
                self.write(cr, uid, [document.id,],{'counter': document.counter-1}, context=context )
    
    def _check_positive(self,cr,uid,ids, context=None):
        range = 0
        for std in self.browse(cr, uid, ids):
            if not std.auto_printer and (std.last_secuence < 0 or std.first_secuence < 0):
                return False
            elif std.first_secuence < 0: 
                return False
            else:
                return True
            
    def _check_sequence(self,cr,uid,ids, context=None):
        range = 0
        for std in self.browse(cr, uid, ids):
            range = std.last_secuence - std.first_secuence
            if not std.auto_printer and (range < 0):
                return False
            else:
                return True

    _constraints = [
                    (_check_positive,_('Error!!! Sequence number must be a positive number'),['first_secuence', 'last_secuence']),
                    (_check_sequence,_('Error!!! First sequence must be bigger than last sequence'),['first_secuence', 'last_secuence'])
                    ]
    
    _name = 'sri.type.document'

    _columns = {
                'sri_authorization_id':fields.many2one('sri.authorization', 'Authorization', required=True),
                'auto_printer': fields.related('sri_authorization_id','auto_printer', type='boolean', string='Autoimpresor?', store=True), 
                'sequence_id':fields.many2one('ir.sequence', 'Sequence', required=True),
                'state': fields.function(_verify_state, method=True, type='boolean', string='Active?',
                                         store={
                                                 'sri.type.document': (lambda self, cr, uid, ids, c={}: ids, ['counter', 'expired'], 8)}
                                         ),
                'printer_id':fields.many2one('sri.printer.point', 'Printer Point', required=True),
                'shop_id': fields.related('printer_id','shop_id', type='many2one', relation='sale.shop', string='Agency'), 
                'expired':fields.boolean('Expired?',),
                'name':fields.selection(_get_name, 'Name', size=32), 
                'first_secuence': fields.integer('Inicial Secuence'),
                'last_secuence': fields.integer('Last Secuence'),
                'counter': fields.integer('counter'),
                'range': fields.function(_get_range, method=True, type='integer',string='range', store=True),
                }

    _defaults = {
                 'counter': 0,
                 }

    def validate_unique_value_document(self, cr, uid, number=None, company_id=None, model=None, field=None, name='Factura', context=None):
        doc_obj = self.pool.get('sri.type.document')
        seq_obj = self.pool.get('ir.sequence')
        company_obj = self.pool.get('res.company')
        obj = self.pool.get(model)
        if not context:
            context = {}
        if not number or not company_id or not field or not name or not model:
            raise osv.except_osv(_('Error!'), _("There's not valid arguments to validate number of document"))
        company = company_obj.browse(cr, uid, company_id, context)
        ids = obj.search(cr, uid, [(field,'=',number),('company_id','=',company_id)])
        if not ids:
            return True
        else:
            raise osv.except_osv(_('Error!'), _("There is another document type %s with number '%s' for the company %s") % (name, number,company.name))

    def get_next_value_secuence(self, cr, uid, type, date, printer_id=None, model=None, field=None, context=None):
        doc_obj = self.pool.get('sri.type.document')
        seq_obj = self.pool.get('ir.sequence')
        printer_obj = self.pool.get('sri.printer.point')
        obj = self.pool.get(model)
        if not context:
            context = {}
        if not date:
            date = time.strftime('%Y-%m-%d')
        if not type or not printer_id:
            return False
        doc_ids = doc_obj.search(cr, uid, [('name','=',type),('printer_id','=',printer_id),('state','=',True)])
        printer = printer_obj.browse(cr, uid, printer_id)
        docs = doc_obj.browse(cr, uid, doc_ids, context)
        doc_finded = None
        for doc in docs:
            if date >= doc.sri_authorization_id.start_date and date <= doc.sri_authorization_id.expiration_date:
                 doc_finded = doc
                 break
        if not doc_finded:
            return False
        next_seq = seq_obj.get_next_id(cr, uid, [doc_finded.sequence_id.id], 0)
        #TODO: Hay que devolver la siguiente secuencia disponible en caso de encontrar documentos en estado de borrador
        flag = True
        count = 0
        company_id = printer.shop_id.company_id.id
        while flag:
            ids = obj.search(cr, uid, [(field,'=',next_seq),('company_id','=',company_id)])
            if not ids:
                flag = False
            else:
                count +=1
                #TODO: Verificar que el siguiente número no sobrepase el limite de números si es autorización de preimpreso 
                next_seq = seq_obj.get_next_id(cr, uid, doc_finded.sequence_id.id, count)            
        return next_seq
    
    #TODO: verificacion por compania
    def write(self, cr, uid, ids, values, context=None):
        td_obj = self.pool.get('sri.type.document')
        try:
            lines_ids = td_obj.search(cr, uid, [('name','=',values['name']),('sri_authorization_id','=',values['sri_authorization_id']),])
            #verifica que existe otra linea de autorizacion con el mismo tipo de documento en la misma autorizacion
            if lines_ids:
                raise osv.except_osv('Error!', _('There is another line with the same type of ducument in authorization'))
            #verifica que las secuencias no sean inversas
            if (values['last_secuence']  - values['first_secuence'] < 0):
                raise osv.except_osv('Error!', _('Your last sequence must be bigger first sequence'))
            return super(sri_type_document, self).write(cr, uid, ids, values, context)
        except:
            return super(sri_type_document, self).write(cr, uid, ids, values, context)

    #TODO: verificacion por compania
    def create(self, cr, uid, values, context=None):
        td_obj = self.pool.get('sri.type.document')
        auth_obj= self.pool.get('sri.authorization')
        doc_name = {
                    'invoice': _('Invoice'),
                    'delivery_note': _('Delivery Note'),
                    'withholding': _('Withholding'),
                    'liquidation': _('Purchase Liquidation'),
                    'credit_note': _('Credit Note'),
                    'debit_note': _('Debit Note'),
                    }
        shop_name = self.pool.get('sale.shop').browse(cr, uid, values['shop_id']).name
        printer_name = self.pool.get('sri.printer.point').browse(cr, uid, values['printer_id']).name
        lines_ids = td_obj.search(cr, uid, [('name','=',values['name']),
                                            ('sri_authorization_id','=',values['sri_authorization_id']),
                                            ('printer_id','=',values['printer_id'])])
        #verifica que existe otra linea de autorizacion con el mismo tipo de documento en la misma tienda y en el mismo punto de impresion
        if lines_ids:
            raise osv.except_osv('Error!', _('There is another line with the same type of document %s for printer point %s in agency %s') % (doc_name[values['name']], printer_name, shop_name))
        lines_ids = td_obj.search(cr, uid, [('name','=',values['name']),('printer_id','=',values['printer_id']), ('auto_printer','=',values['auto_printer'])])
        exist_other = False
        for td_line in td_obj.browse(cr, uid, lines_ids, context):
            #Se verifica que no se superpongan las lineas de autorización en sus números dentro de la misma autorización
            if values['first_secuence'] >= td_line.first_secuence and values['first_secuence'] <= td_line.last_secuence:
                exist_other = True
            if values['last_secuence'] >= td_line.first_secuence and values['last_secuence'] <= td_line.last_secuence:
                exist_other = True
        #TODO: Lanzar excepción por existencia de autorizaciones superpuestas en las secuencias
        if not values['auto_printer']:
            #Debe haber una unica linea de autorización activa por agencia y punto de impresion cuando son de tipo preimpreso
            lines_ids = td_obj.search(cr, uid, [('name','=',values['name']),('printer_id','=',values['printer_id']), ('state','=',True), ('auto_printer','=',False)])
            for line in td_obj.browse(cr, uid, lines_ids , context=context):
                values_doc={'counter':line.range + 1}
                td_obj.write(cr, uid, [line.id,], values_doc, context)
        return super(sri_type_document, self).create(cr, uid, values, context)

sri_type_document()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: