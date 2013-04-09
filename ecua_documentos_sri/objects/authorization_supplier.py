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
from osv import osv, fields, orm
import time
from tools.translate import _
import re

class authorization_supplier(osv.osv):
    
    def _get_name(self, cr, uid, context=None):
        if not context:
            context = {}
        output = []
        if not context.get('document_type', False):
            module_ids = self.pool.get('ir.module.module').search(cr, uid, [('name','like','ecua')])
            module = self.pool.get('ir.module.module').browse(cr, uid, module_ids, context)
            for mod in module:
                if mod['state']=='installed':
                    if mod['name'] == 'ecua_facturas_manual':
                        output.append(('invoice',_('Invoice')))
                    if mod['name']== 'ecua_remision':
                        output.append(('delivery_note',_('Delivery_note')))
                    if mod['name'] == 'ecua_retenciones_manual':
                        output.append(('withholding',_('Withholding')))
                    if mod['name']== 'ecua_liquidacion_compras':
                        output.append(('liquidation',_('Liquidation')))
                    if mod['name']== 'ecua_notas_credito_manual':
                        output.append(('credit_note',_('Credit_note')))
                    if mod['name']== 'ecua_notas_debito_manual':
                        output.append(('debit_note',_('Debit_note')))
        else:
            string = context.get('document_type', False)
            if string:
                string = string[0].title() + string[1:]
            output.append((context.get('document_type', False),_(string)))
        return output
    
    def _check_agency_pp(self, cr, uid, ids, context=None): 
        cadena='(\d{3})'
        for auth in self.browse(cr, uid, ids):
            ref = auth['agency']
            if ref:
                if re.match(cadena, ref):
                    return True
                else:
                    return False
            ref = auth['printer_point']
            if ref:
                if re.match(cadena, ref):
                    return True
                else:
                    return False
        return True
    
    def _check_number(self, cr, uid, ids, context=None):
        cadena='(\d{10})'
        for auth in self.browse(cr, uid, ids):
            ref = auth['number']
            if ref:
                if re.match(cadena, ref):
                    return True
                else:
                    return False
        return True
    
    def _check_dates(self, cr, uid, ids, context=None):
        for auth in self.browse(cr, uid, ids):
            if auth.start_date >= auth.expiration_date:
                return False
            else:
                return True

    def _check_sequence(self, cr, uid, ids, context=None):
        for auth in self.browse(cr, uid, ids):
            if auth.autoprinter:
                return True
            if auth.first_sequence >= auth.last_sequence:
                return False
            else:
                return True
        
    _constraints = [(_check_agency_pp, _('Error: Invalid Number Format, It must be like 001'), ['agency', 'printer_point']), 
                    (_check_number, _('Error: Invalid Number Format, It must be like 0123456789'), ['number']),
                    (_check_dates, _('Error: Dates of authorization are not correct'), ['start_date','expiration_date']),
                    (_check_sequence, _('Error: Numbers of sequence are not correct'), ['first_sequence','last_sequence']),
                    ] 
    
    _name = "sri.authorization.supplier"
    
    _columns = {
                'autoprinter':fields.boolean('Autoprinter?', required=False), 
                'partner_id':fields.many2one('res.partner', 'Partner',),
                'number':fields.char('Number', size=10, required=True),
                'type': fields.selection(_get_name, 'Type', required=True, selected=True),
                'agency':fields.char('Agency', size=3, required=True),
                'printer_point':fields.char('Printer Point', size=3, required=True),
                'start_date': fields.date('Start Date', required=True),
                'expiration_date': fields.date('Expiration Date', required=True),
                'first_sequence': fields.integer('First Secuence', ),
                'last_sequence': fields.integer('Last Secuence', ),
                    }
    
    _rec_name = "number"

    
    def check_number_document(self, cr, uid, number, authorization, date=None, model=False, field=None, type='Factura', context=None, id_model=None, foreing=False):
        if not number:
            raise osv.except_osv(_('Programming Error !'), _('You must set number to verify authorization'))
        if not authorization and not foreing:
            raise osv.except_osv(_('Programming Error !'), _('You must set authorization to verify authorization'))
        numero = number.split('-')
        obj = model and self.pool.get(model) or None
        partner = authorization and authorization.partner_id or None
        partner_id = authorization and authorization.partner_id and authorization.partner_id.id or None
        seq = None
        ids_supplier = []
        if not foreing:
            if not date:
                date = time.strftime('%Y-%m-%d')
            if date > authorization.expiration_date or date < authorization.start_date:
                raise osv.except_osv(_('Authorization Error!'), _('%s is not between range of this authorization %s and %s') % (date, authorization.start_date, authorization.expiration_date))
            if numero[0] != authorization.agency:
                raise osv.except_osv(_('Authorization Error!'), _('Agency number %s not correct for this authorization, it must be %s') % (numero[0], authorization.agency))
            if numero[1] != authorization.printer_point:
                raise osv.except_osv(_('Authorization Error!'), _('Printer Point Number %s not correct for this authorization, it must be %s') % (numero[1], authorization.printer_point))
            if not authorization.autoprinter:
                if int(numero[2]) < authorization.first_sequence or int(numero[2]) > authorization.last_sequence:
                    raise osv.except_osv(_('Authorization Error!'), _('Sequence Number %s is not between rage of authorization %s and %s') % (int(numero[2]), authorization.first_sequence, authorization.last_sequence))             
        if number:
            try:
                seq = numero and int(numero[2]) or None
                pattern = authorization.agency + '-' + authorization.printer_point + '-'
                if pattern and seq and partner_id and obj:
                    ids_supplier = seq and obj.search(cr, uid, [(field,'like',(str(pattern) + "%")),(field,'like',("%" + str(seq))),('partner_id','=',partner_id)]) or None
            except:
                seq = number
                if seq and partner_id and obj:
                    ids_supplier = seq and obj.search(cr, uid, [(field,'like',seq),('partner_id','=',partner_id)]) or None
        if not foreing:
            list_ids_exist = []
            if ids_supplier:
                for id_obj in ids_supplier:
                    if id_obj != id_model:
                        list_ids_exist.append(id_obj)
            if len(list_ids_exist) > 0 and partner:
                raise osv.except_osv(_('Error!'), _("There is another document type %s with number '%s' for the partner %s") % (type, number,partner.name))
        return True
    
    def create(self, cr, uid, values, context=None):
        #TODO verificar por empresa, que no exista otra con el mismo número, tipo y secuencia
        auth_obj = self.pool.get('sri.authorization.supplier')
        partner_obj = self.pool.get('res.partner')
        agency = values.get('agency', False)
        printer_point = values.get('printer_point', False)
        partner_id = values.get('partner_id', False)
        partner = partner_obj.browse(cr, uid, partner_id, context)
        number = values.get('number', False)
        type = values.get('type', False)
        first_seq = values.get('first_sequence', False)        
        last_seq = values.get('last_sequence', False)
        ids = auth_obj.search(cr, uid, [('partner_id','=',partner_id),('type','=',type),('number','>=',number), ('agency','=',agency), ('printer_point','=',printer_point)])
        res = super(authorization_supplier, self).create(cr, uid, values, context)
        return res

    def write(self, cr, uid, ids, values, context=None):
        auth_obj = self.pool.get('sri.authorization.supplier')
        partner_obj = self.pool.get('res.partner')
        for auth in auth_obj.browse(cr, uid, ids, context):
            agency = values.get('agency', auth.agency)
            printer_point = values.get('printer_point', auth.printer_point)
            partner_id = values.get('partner_id', auth.partner_id.id)
            partner = partner_obj.browse(cr, uid, partner_id, context)
            number = values.get('number', auth.number)
            type = values.get('type', auth.type)
            first_seq = values.get('first_sequence', auth.first_sequence)
            last_seq = values.get('last_sequence', auth.last_sequence)
            ids_find = auth_obj.search(cr, uid, [('partner_id','=',partner_id),('type','=',type),('number','>=',number), ('agency','=',agency), ('printer_point','=',printer_point), ('id','!=',auth.id)])
        res = super(authorization_supplier, self).write(cr, uid, ids, values, context)
        return res

    def validate_unique_document_partner(self, cr, uid, number=None, partner_id=None, model=None, field=None, name='Factura', context=None):
        doc_obj = self.pool.get('sri.type.document')
        seq_obj = self.pool.get('ir.sequence')
        partner_obj = self.pool.get('res.partner')
        obj = self.pool.get(model)
        if not context:
            context = {}
        if not number or not partner_id or not field or not name or not model:
            raise osv.except_osv(_('Error!'), _("There's not valid arguments to validate number of document"))
        partner = partner_obj.browse(cr, uid, partner_id, context)
        seq = None
        if number:
            try:
                seq = number.split('-')[2]
            except:
                seq = number
        ids = seq and obj.search(cr, uid, [(field,'like',("%" + str(seq))),('partner_id','=',partner_id)]) or None
        if not ids:
            return True
        else:
            raise osv.except_osv(_('Error!'), _("There is another document type %s with number '%s' for the partner %s") % (name, number,partner.name))


authorization_supplier()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
