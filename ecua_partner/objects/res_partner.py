# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Andres Calle, Patricio Rangles, Pablo Vizhnay
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

from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
from openerp.tools.misc import ustr
import time
import re #para busqueda por cedula
import unicodedata


class res_partner(osv.osv):
    _inherit = "res.partner"
    
    # agregamos codigo de ecuador al modulo base_vat
    #_ref_vat['ec']='EC1234567891001'
    _ref_vat = {
                'ec': 'EC1234567891001',
                }
    
    RE_EMAIL = re.compile("^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    
    def is_valid_email_address(self, email):
        """
        Returns whether a specific email address is valid or
            not. It is intended to be used by other objects,
            so this should work:
                pool.get('res.partner').is_valid_email_address("foo@bar.com")
        """
        return bool(self.RE_EMAIL.match(email.strip()))
        
    def _get_user_default_sales_team(self, cr, uid, ids, context={}):
        user= self.pool.get('res.users').browse(cr,uid,uid)
        sale_team_id=user.default_section_id.id
        return sale_team_id or False

    def _get_user_country_id(self, cr, uid, ids, context={}):
        #TODO - Validar si sirve para entorno multicompania
        company_id = self.pool.get('res.users').browse(cr,uid,uid).company_id
        country_id = company_id.country_id.id
        if country_id:
            return country_id
        return    
    
    def _get_default_validation(self, cr, uid, context=None):
        ir_values = self.pool.get('ir.values')
        company_id = self.pool.get('res.users').browse(cr,uid,uid).company_id
        is_validation=company_id.is_validation
        return is_validation or False

    def _calculate_vat(self, identification, is_company):
        """
        This function calculates, in a separate fashion, whether the partner's identification
          is a passport number, a citizen id, or a contributor unique record's number. Considerations
          for end-customers, distinction between foreign persons/companies, and other types of
          elements are being taken into account as well.
        :param identification:
        :param is_company:
        :return:
        """
        if identification and len(identification) > 2:
            pais, identificador = identification[0:2], identification[2:]
            if pais == 'EC':
                if len(identificador) == 10:
                    return "CEDULA"
                elif identificador == '9999999999999':
                    return "CONSUMIDOR FINAL"
                elif len(identificador) == 13:
                    return "RUC"
                else:
                    return "OTROS"
            else:
                if is_company:
                    return 'PERS. JURÍDICA EXTRANJERA'
                else:
                    return 'PERS. NATURAL EXTRANJERA'
        else:
            return "OTROS"

    #FUNCION QUE NOS VALIDA  EL TIPO DE iDENTIFICACIoN DE LOS CLIENTES Y PROVEEDORES
    def _get_vat(self, cr, uid, ids, vat, arg, context):
        return {obj.id: self._calculate_vat(obj.vat, obj.is_company)
                for obj in self.browse(cr, uid, ids, context=context)}

    def _calculate_type_vat(self, identification):
        """
        This is the same logic as implemented before, but in a separate function.
        This one considers whether the vat is citizen id or contributor unique record's number.
        The returned value is the type of ecuadorean person.

        This implementation has many bugs fixed wrt the previous implementation.
        :param identification:
        :param is_company:
        :return:
        """
        if not identification:
            return "NINGUNO"
        else:
            vat_ = self._calculate_vat(identification, False)
            if vat_ == 'CEDULA' or vat_ == 'RUC':
                digit = int(identification[4])
                if digit == 6:
                    return 'PUBLICOS'
                if digit in (7, 8):
                    return 'Error en el Ingreso de los datos'
                if digit == 9:
                    return 'JURIDICO Y EXTRANJEROS SIN CEDULA'
                if digit in (0, 1, 2, 3, 4, 5):
                    return 'PERSONA NATURAL'
            else:
                return "OTROS"

    #FUNCION QUE NOS MUESTRA  LOS TIPOS DE RUC DE ACUERDO  AL TIPO DE CONTRIBUYENTE
    def _get_type_vat(self, cr, uid, ids, vat, arg, context):
        return {obj.id: self._calculate_type_vat(obj.vat) for obj in self.browse(cr, uid, ids, context=context)}

    def onchange_vat(self, cr, uid, ids, identification, is_company, context=None):
        """
        When VAT changes, we perform the functional algorithm to determine types and other stuff.
          Once there, we determine if the gotten VAT type is valid for the current state of the field
          is_company
        :param cr:
        :param uid:
        :param ids:
        :param identification:
        :param is_company:
        :param context:
        :return:
        """
        result = self.vat_change(cr, uid, ids, identification, context=context)
        type_ = self._calculate_vat(identification, is_company)
        if type_ == "RUC" and not is_company:
            result['warning'] = {
                'title': 'Advertencia',
                'message': u'Está asignando un RUC a un contacto que no es una empresa. '
                           u'Debería marcar la casilla titulada "¿Es una empresa?".'
            }
        elif type_ == "CEDULA" and is_company:
            result['warning'] = {
                'title': 'Advertencia',
                'message': u'Está asignando una cédula a un contacto que es una empresa. '
                           u'Debería desmarcar la casilla titulada "¿Es una empresa?".'
            }
        return result

    def onchange_address(self, cr, uid, ids, use_parent_address, parent_id, context=None):
        """
        Se alerta sobre la sobreescritura de datos contables 
        """
        res = super(res_partner, self).onchange_address(cr, uid, ids, use_parent_address, parent_id, context)

        if parent_id is not False: #la advertencia solo al asignar una empresa padre, al removerla no hace falta
            if not 'warning' in res:
                res['warning'] = {}
            
            if not 'message' in res['warning']:
                res['warning']['message'] = ''
            oldwarning = res['warning']['message']
            newwarning = oldwarning + "\n" + _('When associating a contact to a company, the accounting data from the conctact is lost (ie vat number, RUC number, etc)')
            res['warning']['message'] = newwarning
        return res
        
    def copy(self, cr, uid, id, default=None, context=None):
        '''
        No se copia la cedula pues el sistema no permite cedulas repetidas
        '''
        if not default:
            default = {}
        d = {
            'vat' : '',
        }
        d.update(default)
        return super(res_partner, self).copy(cr, uid, id, d, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        if not context: context = {}
        
        for partner in self.browse(cr, uid, ids, context):
            changes = []
            
            #El RUC de un contacto era siempre igual al RUC de la empresa padre
            #por compatibilidad se permite remover el contacto de la empresa padre
            #eliminando el valor del RUC del contacto (el sistema no permite RUCs duplicados)
            #esta funcionalidad del modulo base esta en el metodo _commercial_fields
            if partner.parent_id:
                if partner.parent_id.vat == partner.vat:
                    vals['vat'] = ''
            
            #Agregamos log de cambios
            if 'name' in vals and partner.name != vals['name']: # en el caso que sea un campo
                oldmodel = partner.name or _('None')
                vals['name'] = self._with_single_spaces(vals['name'])
                newvalue = self._with_single_spaces(vals['name'])  or _('None')
                changes.append(_("Name: from '%s' to '%s'") %(oldmodel,newvalue ))
            if 'comercial_name' in vals and partner.comercial_name != vals['comercial_name']: # en el caso que sea un campo
                oldmodel = partner.comercial_name or _('None')
                newvalue = vals['comercial_name'] or _('None')
                changes.append(_("Comercial Name: from '%s' to '%s'") %(oldmodel,newvalue ))
            if 'is_company' in vals and partner.is_company != vals['is_company']: # en el caso que sea un campo booleano
               
                if partner.is_company:
                    oldmodel=_('True')
                else:
                    oldmodel=_('False')
                if vals['is_company']:
                    newvalue=_('rue')
                else:
                    newvalue=_('False')
                changes.append(_("Is Company: from '%s' to '%s'") %(oldmodel,newvalue ))
            # DR verifica cuando existe un campo m2m elimina repedidos y guarda los campos nuevos 
            if 'category_id' in vals and partner.category_id != vals['category_id'][0][2]:
                list_tag = []
                list = []
                "Guarda en las listas los campos removidor o agragados"
                list_tag_new = sorted(vals['category_id'][0][2])
                for a in partner.category_id:    
                    list_tag.append(a.id)
                sorted(list_tag)
                sorted(list_tag_new)
                "ve cuales son los camos q se mantienen"
                for a in list_tag:
                    for t in list_tag_new:
                        if a == t: 
                            list.append(a)
                "elimina de las listas los campos repetidos"
                for a in list:
                    del(list_tag_new[list_tag_new.index(a)])
                    del(list_tag[list_tag.index(a)])
                "Guarda e imprime los campos no repetidos en msn"
                for id in list_tag:
                    value = self.pool.get('res.partner.category').browse(cr,uid,id,context=context).name or _('None')
                    changes.append(_("Tag Removed: '%s'") %(value)) 
                for id in list_tag_new:
                    value = self.pool.get('res.partner.category').browse(cr,uid,id,context=context).name or _('None')
                    changes.append(_("Added tag: '%s'") %(value))
            if 'street' in vals and partner.street != vals['street']: # en el caso que sea un campo
                oldmodel = partner.street or _('None')
                newvalue = vals['street'] or _('None')
                changes.append(_("Street: from '%s' to '%s'") %(oldmodel,newvalue ))
            if 'street2' in vals and partner.street2 != vals['street2']:
                oldmodel = partner.street2 or _('None')
                newvalue = vals['street2'] or _('None')
                changes.append(_("Street 2: from '%s' to '%s'") %(oldmodel, newvalue))
            if 'city' in vals and partner.city != vals['city']:
                oldmodel = partner.city or _('None')
                newvalue = vals['city'] or _('None')
                changes.append(_("City: from '%s' to '%s'") %(oldmodel, newvalue))
            if 'zip' in vals and partner.zip != vals['zip']: # en el caso que sea un campo
                oldmodel = partner.zip or _('None')
                newvalue = vals['zip'] or _('None')
                changes.append(_("ZIP: from '%s' to '%s'") %(oldmodel,newvalue ))      
            if 'state_id' in vals and partner.state_id != vals['state_id']: # en el caso que sea un objeto
                oldmodel = partner.state_id.name or _('None')
                if vals['state_id']:
                    newvalue=self.pool.get('res.country.state').browse(cr,uid,vals['state_id'],context=context).name
                else:
                    newvalue=_('None')
                changes.append(_("State: from '%s' to '%s'") %(oldmodel, newvalue))                
            if 'country_id' in vals and partner.country_id != vals['country_id']: # en el caso que sea un objeto
                oldmodel = partner.country_id.name or _('None')

                if vals['country_id']:
                    newvalue=self.pool.get('res.country').browse(cr,uid,vals['country_id'],context=context).name
                else:
                    newvalue=_('None')
                changes.append(_("Country: from '%s' to '%s'") %(oldmodel, newvalue))
            if 'website' in vals and partner.website != vals['website']: # en el caso que sea un campo
                oldmodel = partner.website or _('None')
                newvalue = vals['website'] or _('None')
                changes.append(_("Web Site: from '%s' to '%s'") %(oldmodel,newvalue ))
            if 'phone' in vals and partner.phone != vals['phone']: # en el caso que sea un campo
                oldmodel = partner.phone or _('None')
                newvalue = vals['phone'] or _('None')
                changes.append(_("Phone: from '%s' to '%s'") %(oldmodel,newvalue ))
            if 'mobile' in vals and partner.mobile != vals['mobile']: # en el caso que sea un campo
                oldmodel = partner.mobile or _('None')
                newvalue = vals['mobile'] or _('None')
                changes.append(_("Mobile: from '%s' to '%s'") %(oldmodel,newvalue ))
            if 'fax' in vals and partner.fax != vals['fax']: # en el caso que sea un campo
                oldmodel = partner.fax or _('None')
                newvalue = vals['fax'] or _('None')
                changes.append(_("Fax: from '%s' to '%s'") %(oldmodel,newvalue ))
            if 'email' in vals and partner.email != vals['email']: # en el caso que sea un campo
                oldmodel = partner.email or _('None')
                vals['email'] = vals['email'].strip()
                newvalue = vals['email'] or _('None')
                changes.append(_("Email: from '%s' to '%s'") %(oldmodel,newvalue ))
            
            if 'property_account_position' in vals and partner.property_account_position != vals['property_account_position']: # en el caso que sea un objeto
                oldmodel = partner.property_account_position.name or _('None')
                if vals['property_account_position']:
                    newvalue=self.pool.get('account.fiscal.position').browse(cr,uid,vals['property_account_position'],context=context).name
                else:
                    newvalue=_('None')
                changes.append(_("Fiscal position: from '%s' to '%s'") %(oldmodel, newvalue))
            
            if 'vat' in vals and partner.vat != vals['vat']: # en el caso que sea un campo
                oldmodel = partner.vat or _('None')
                newvalue = (vals['vat'] or '').upper() or _('None')
                changes.append(_("NIF: from '%s' to '%s'") %(oldmodel, newvalue ))
                
            if 'property_account_receivable' in vals and partner.property_account_receivable != vals['property_account_receivable']: # en el caso que sea un objeto
                oldmodel = partner.property_account_receivable.name or _('None')
                if vals['property_account_receivable']:
                    newvalue=self.pool.get('account.account').browse(cr,uid,vals['property_account_receivable'],context=context).name or _('None')
                else:
                    newvalue=_('None')
                changes.append(_("Account Receivable: from '%s' to '%s'") %(oldmodel, newvalue))
            
            if 'property_account_payable' in vals and partner.property_account_payable != vals['property_account_payable']: # en el caso que sea un objeto
                oldmodel = partner.property_account_payable.name or _('None')
                if vals['property_account_payable']:
                    newvalue=self.pool.get('account.account').browse(cr,uid,vals['property_account_payable'],context=context).name or _('None')
                else:
                    newvalue=_('None')
                changes.append(_("Account Payable: from '%s' to '%s'") %(oldmodel, newvalue))
                
            if 'user_id' in vals and partner.user_id != vals['user_id']: # en el caso que sea un objeto
                oldmodel = partner.user_id.name or _('None')
                if vals['user_id']:
                    newvalue=self.pool.get('res.users').browse(cr,uid,vals['user_id'],context=context).name
                else:
                    newvalue=_('None')
                changes.append(_("Sales Person: from '%s' to '%s'") %(oldmodel, newvalue))
            if 'section_id' in vals and partner.section_id != vals['section_id']: # en el caso que sea un objeto
                oldmodel = partner.section_id.name or _('None')
                if vals['section_id']:
                    newvalue=self.pool.get('crm.case.section').browse(cr,uid,vals['section_id'],context=context).name
                else:
                    newvalue=_('None')
                changes.append(_("Sales Team: from '%s' to '%s'") %(oldmodel, newvalue))
            if 'property_product_pricelist' in vals and partner.property_product_pricelist != vals['property_product_pricelist']: # en el caso que sea un objeto
                oldmodel = partner.property_product_pricelist.name or _('None')
                if vals['property_product_pricelist']:
                    newvalue=self.pool.get('product.pricelist').browse(cr,uid,vals['property_product_pricelist'],context=context).name
                else:
                    newvalue=_('None')
                changes.append(_("Sale Pricelist: from '%s' to '%s'") %(oldmodel, newvalue))   
            if 'payment_responsible_id' in vals and partner.payment_responsible_id != vals['payment_responsible_id']: # en el caso que sea un objeto
                oldmodel = partner.payment_responsible_id.name or _('None')
                if vals['payment_responsible_id']:
                    newvalue=self.pool.get('res.users').browse(cr,uid,vals['payment_responsible_id'],context=context).name
                else:
                    newvalue=_('None')
                changes.append(_("Follow-up Responsible: from '%s' to '%s'") %(oldmodel, newvalue))   
           
            
            if len(changes) > 0:
                self.message_post(cr, uid, [partner.id], body=", ".join(changes), context=context)
        
        result = super(res_partner, self).write(cr, uid, ids, vals, context=context)
        return result

    def create(self, cr, uid, values, context=None):
        if not context: context = {}
        if 'name' in values:
            values['name'] = self._with_single_spaces(values['name'])
        if 'email' in values and values['email']:
            values['email'] = values['email'].strip()
        if 'vat' in values and values['vat']:
            values['vat'] = (values['vat'] or '').upper()
        else:
            pass
            #values['vat'] = _('None')
        res = super(res_partner, self).create(cr, uid, values, context)
        return res

    def onchange_type(self, cr, uid, ids, is_company, context=None):
        res=super(res_partner,self).onchange_type(cr, uid, ids,is_company, context)

        if is_company==False:
            res['value']['comercial_name'] = ""
        return res

    def _avoid_duplicated_vat(self, cr, uid, ids, context=None):
        '''
        Valida que solo exista un RUC o cedula
        '''
        #verificamos si la opcion de evitar duplicidad esta activa  
        company_obj = self.pool.get('res.users').browse(cr,uid,uid).company_id
        avoid_duplicated_vat=company_obj.avoid_duplicated_vat
        if not avoid_duplicated_vat:
            return True

        for partner in self.browse(cr, uid, ids, context=context):
            if partner.vat: #si tiene cedula la valida, caso contrario no hace nada
                if not partner.parent_id :
                    #vals = self.search(cr, uid, [('vat','=',partner.vat),('is_company','=',True)], context=context)
                    vat = partner.vat
                    if (len(vat) == 12 or len(vat) == 15) and vat[0:2].lower() == 'ec':
                        vat = vat[0:12]
                        #es un RUC o una cedula, validamos que no exista uno que haga ilike positivo con EC0987654321
                        #(siendo ese valor solamente de referencia).
                        criterion = ('vat', '=ilike', vat + '%')
                    else:
                        criterion = ('vat', '=', partner.vat)
                    vals = self.search(cr, uid, [criterion,('parent_id','=',None)], context=context)
                    return not len(vals)>1
        return True    
    
    _columns = {
                'comercial_name': fields.char('Comercial Name', size=256),
                'type_vat': fields.function(_get_vat, type="char", method=True, string='Name', store=True),
                'type_vat_type': fields.function(_get_type_vat, type="char", method=True, string='Name', store=True),
               }
    
    _defaults = {
                 'customer':True,
                 'supplier':True,
                 'comercial_name': "",
                 'user_id': lambda self, cr, uid, context: uid,
                 'section_id': _get_user_default_sales_team,
                 'country_id': _get_user_country_id,
                 'date': fields.date.context_today,
                 
                 # TODO - Evaluar los modulos account_fiscal_position_rule, account_fiscal_position_country, y account_fiscal_position_country_sale
                 #'property_account_position': _get_default_fiscal_position_id,
                 }
    #    _sql_constraints = [
    #    ]
    #    _order = 'name asc'


    def get_company_address(self, cr, uid, contact_id, printer_id=None, company_id=None, context=None):
        '''
        Retorna la direccion para facturacion, puede diferir de la direccion de contacto
        Ej. Si como partner selecciono a Maria de la empresa Trescloud, la direccion sera la de Trescloud 
        TODO: Integrarlo con modulos comunidad de multiples direcciones
        TODO: Implementar printer_id (segun el punto de impresion puede cambiar la direccion)
        '''
        invoice_address = None
        contact_obj=self.pool.get('res.partner')
        contact = contact_obj.browse(cr,uid,[contact_id])[0]
        invoice_address = contact.street
        if contact.parent_id:
            invoice_address = contact.parent_id.street
        return invoice_address

    def get_company_phone(self, cr, uid, contact_id, printer_id=None, company_id=None, context=None):
        '''
        Retorna el telefono para facturacion, puede diferir del telefono de contacto
        Ej. Si como partner selecciono a Maria de la empresa Trescloud, el telefono sera la de Trescloud 
        TODO: Integrarlo con modulos comunidad de multiples direcciones
        TODO: Implementar printer_id (segun el punto de impresion puede cambiar la direccion)
        '''
        invoice_phone = None
        contact_obj=self.pool.get('res.partner')
        contact = contact_obj.browse(cr,uid,[contact_id])[0]
        invoice_phone = contact.phone or contact.mobile
        if contact.parent_id:
            invoice_phone = contact.parent_id.phone or contact.parent_id.mobile
        return invoice_phone

    def _get_company_vat(self, cr, uid, contact_id, printer_id=None, company_id=None, context=None):
        '''
        Si es una empresa retorna un string con el  RUC/Cedula de la empresa
        Si es un contacto retorna un string con el el RUC/Cedula del contacto
        Podria obviarse la fucnion pero en el futuro se planea que el contacto pueda tener cedula distinta
        '''
        vat = ''
        contact_obj=self.pool.get('res.partner')
        contact = contact_obj.browse(cr,uid,[contact_id])[0]
        vat = contact.vat
        if contact.parent_id:
            vat = contact.parent_id.vat
        return vat
    
    def check_vat(self, cr, uid, ids, context=None):
        res = super(res_partner, self).check_vat(cr, uid, ids, context=context)
        valid=0
        vat_country=False
        vat_number=False
        if context:
            valid=context.get('default_vat_subjected')     
        if valid!=1:
            for partner in self.browse(cr, uid, ids, context=context):
                if not partner.vat:
                    continue
                vat_country, vat_number = self._split_vat(partner.vat)
            if not ustr(vat_country).encode('utf-8').isalpha():
                res=True
        return res
    
    def _with_single_spaces(self, s):
        """
        Ensure a text value does not hold multiple
        spaces, by converting it to a single-spaced value.
        
        It also strips the leading and trailing spaces
        from the given value.
        
        Example:
           << self._with_single_spaces("  lorem  ipsum  dolor  ")
           >> "lorem ipsum dolor"
        """
        return re.sub('\s+', ' ', s.strip())
    
    def _strip_accents(self, s):
        """
        Strips accents from a string. This is used only to validate
        the string as a name, and NOT to alter the name string in the
        database.
        
        Examples:
            << self._strip_accents("Jose Miguel Rivero")
            >> "Jose Miguel Rivero"
            << self._strip_accents("Nestor Carlos Kirchner")
            >> "Nestor Carlos Kirchner"
            << self._strip_accents("Carlos Arguello")
            >> "Carlos Arguello"
            << self._strip_accents("Maria Fernanda Bonanni")
            >> "Maria Fernanda Bonanni"
        """
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                       if unicodedata.category(c) != 'Mn')

    def _check_valid_name(self, cr, uid, ids, context=None):
        """
        Checks whether the company name is valid, by
        sub-checking whether it is a company or a natural person
        and disallowing, for the latter, the chance to have a
        name with stuff other than letters. Note that accented
        letters ARE allowed and they do not count as special
        characters, but numbers, dots, commas, dashes, slashes,
        etc. count as special characters.
        
        Example for natural person names:
            Jose Miguel Rivero
            Nestor Carlos Kirchner
            Carlos Argüello
            Maria Fernanda Bonanni
        
        Examples for company names:
            1, 2, 3 Shop
            99¢ Shop
            C&A
            Dunkin' & Donuts
        """
        res = True
        natural_check = re.compile("^[a-zA-Z\' ]+$")
        company_check = re.compile("^[a-zA-Z0-9\' .,&/-]+$")
        for partner in self.browse(cr, uid, ids, context=context):
            unaccented_name = self._strip_accents(partner.name)
            match = natural_check.match(unaccented_name) if not partner.is_company else company_check.match(unaccented_name)
            if not match:
                res = False
        return res
    
    def _construct_constraint_msg(self, cr, uid, ids, context=None):
        res = super(res_partner, self)._construct_constraint_msg(cr, uid, ids, context=context)
        return res
    
    def _valid_email(self, cr, uid, ids, context=None):
        """
        Validates an email address by calling
            is_valid_email_address.
        """
        res = True
        for partner in self.browse(cr, uid, ids, context=context):
            if partner.email and not self.is_valid_email_address(partner.email):
                res = False
        return res
    
    _constraints = [
                    (check_vat,_construct_constraint_msg, ["vat"]),
                    (
                     _avoid_duplicated_vat, 
                     _('Error: The VAT Number must be unique, there is already another person/company with this vat number. You should search the conflicting partner by VAT before proceeding'),
                     ['vat']
                    ),
                    (
                     _check_valid_name,
                     _('Error: El nombre de un contacto que sea persona natural debe contener solamente letras. Los nombres de las empresas pueden tener adicionalmente números y otros caracteres.'),
                     ['name']
                     ),
                    (
                     _valid_email,
                     _(u'Error: La direccion de correo electronico es invalida'),
                     ['email']
                    )
                   ]

    def _display_name_compute(self, cr, uid, ids, name, args, context=None):
        '''
        El modulo account_report_company agrega un tratamiento especial a res.partner
        Se debe por tanto cambiar la funcion name_get cuando se utiliza para guardar
        el display_name de una empresa.
        Se agrega un flag al context para que el metodo name_get no altere el resultado anterior
        '''
        context = dict(context or {})
        context.update({'display_name_compute': True})
        return super(res_partner,self)._display_name_compute(cr, uid, ids, name, args, context)

    def name_get(self, cr, uid, ids, context=None):
        '''
        Agrega el numero de RUC/CEdula al final del nombre
        '''
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if 'display_name_compute' in context:
            if context['display_name_compute']:
                return super(res_partner,self).name_get(cr, uid, ids, context=context)
            
        res = super(res_partner,self).name_get(cr, uid, ids, context=context)
        res2 = []
        if not context.get('show_email'): #evitamos el escneario de formularios de email
            for partner_id, name in res:
                record = self.read(cr, uid, partner_id, ['ref','vat'], context=context)
                new_name = (record['ref'] and '[' + record['ref'] + '] ' or '') + ((record['vat'] and '[' + record['vat'] + '] ' or '')) + name
                res2.append((partner_id, new_name))
            return res2
        return res

    def __init__(self, pool, cr):
        """
        TODO eliminar este script luego de una vez de uso!!
        :param pool:
        :param cr:
        :return:
        """
        super(res_partner, self).__init__(pool, cr)
        cr.execute('update res_partner set vat=upper(vat)')
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        '''
        Permite buscar ya sea por nombre, por codigo o por nombre comercial
        hemos copiado la idea de product.product
        No se llama a super porque name-search no estaba definida
        '''
        if not args:
            args = []
        if not context:
            context = {}
        ids = []
        if name: #no ejecutamos si el usaurio no ha tipeado nada
 
            #buscamos por codigo completo
            ids = self.search(cr, user, ['|',('vat','=',name),('ref','=',name)]+ args, limit=limit, context=context)
            if not ids: #buscamos por fraccion de palabra o fraccion de codigo
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + ['|','|',('vat',operator,name),('ref',operator,name),('comercial_name',operator,name)], limit=limit, context=context))
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
                ids = list(ids)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, ['|','|',('vat','=', res.group(2)),('ref','=', res.group(2)),('comercial_name','=', res.group(2))] + args, limit=limit, context=context)
 
        else: #cuando el usuario no ha escrito nada aun
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
        
    # Ecuador VAT validation, contributed by TRESCLOUD (info@trescloud.com)
    # and based on https://launchpad.net/openerp-ecuador
    # TRESCLOUD TODO - Incluir estas funciones en el espacio de nombres de check_vat_ec
    def verifica_ruc_spri(self,ruc):
        try:
            #validate VAT has 10 or 13 digits
            #This part is modified because Ecuador add 2 states, this mean we have 24 states
            # also control the first 2 digits don't be "00"
            state_num = (int(ruc[0]+ruc[1]))
            
            if state_num > 0 and state_num < 25 :
                 prueba1=True
            else:
                 prueba1=False
            
            if (int(ruc[2])==9):
                 prueba2=True
            else:
                 prueba2=False    
        
            #split VAT and take first 9 digits
            val0=int(ruc[0])*4
            val1=int(ruc[1])*3
            val2=int(ruc[2])*2
            val3=int(ruc[3])*7
            val4=int(ruc[4])*6
            val5=int(ruc[5])*5
            val6=int(ruc[6])*4
            val7=int(ruc[7])*3
            val8=int(ruc[8])*2
         
            tot=val0+val1+val2+val3+val4+val5+val6+val7+val8
            veri=tot-((tot/11))*11
         
            if(veri==0):
                if((int(ruc[9]))== 0):
                    prueba3=True
                else:
                    prueba3=False
            else:
                if((int(ruc[9]))==(11-veri)):
                    prueba3=True
                else:
                    prueba3=False
        
            if((int(ruc[10]))+(int(ruc[11]))+(int(ruc[12]))>0):
                prueba4=True
            else:
                prueba4=False
        
            if(prueba1 and prueba2 and prueba3 and prueba4):
                return True
            else: 
                return False
        except:
            return False
        
    # TRESCLOUD TODO - Incluir estas funciones en el espacio de nombres de check_vat_ec  
    #SECTOR PUBLICO
    def verifica_ruc_spub(self,ruc):
        try: 
            #This part is modified because Ecuador add 2 states, this mean we have 24 states
            # also control the first 2 digits don't be "00"
            state_num = (int(ruc[0]+ruc[1]))
            
            if state_num > 0 and state_num < 25 :
                 prueba1=True
            else:
                 prueba1=False
            
            if (int(ruc[2])==6):
                prueba2=True
            else:
                prueba2=False    
        
            val0=int(ruc[0])*3
            val1=int(ruc[1])*2
            val2=int(ruc[2])*7
            val3=int(ruc[3])*6
            val4=int(ruc[4])*5
            val5=int(ruc[5])*4
            val6=int(ruc[6])*3
            val7=int(ruc[7])*2
         
            tot=val0+val1+val2+val3+val4+val5+val6+val7
            veri=tot-((tot/11))*11
         
            if(veri==0):
                if((int(ruc[8]))== 0):
                    prueba3=True
                else:
                    prueba3=False
            else:
                if((int(ruc[8]))==(11-veri)):
                    prueba3=True
                else:
                    prueba3=False
        
            if((int(ruc[9]))+(int(ruc[10]))+(int(ruc[11]))+(int(ruc[12]))>0):
                prueba4=True
            else:
                prueba4=False
        
            if(prueba1 and prueba2 and prueba3 and prueba4):
                 return True
            else: 
                return False
        except:
            return False

    # TRESCLOUD TODO - Incluir estas funciones en el espacio de nombres de check_vat_ec
    def verifica_ruc_pnat(self,ruc):
        try:
            #This part is modified because Ecuador add 2 states, this mean we have 24 states
            # also control the first 2 digits don't be "00"
            state_num = (int(ruc[0]+ruc[1]))
            
            if state_num > 0 and state_num < 25 :
                 prueba1=True
            else:
                 prueba1=False
            
            if (int(ruc[2])<6):
                prueba2=True
            else:
                prueba2=False    
        
            valores = [ int(ruc[x]) * (2 - x % 2) for x in range(9) ]
            suma = sum(map(lambda x: x > 9 and x - 9 or x, valores))
            veri = 10 - (suma - (10*(suma/10)))
            if int(ruc[9]) == int(str(veri)[-1:]):
                prueba3= True
            else:
                prueba3= False
                
            if((int(ruc[10]))+(int(ruc[11]))+(int(ruc[12]))>0):
                prueba4=True
            else:
                prueba4=False
        
            if(prueba1 and prueba2 and prueba3 and prueba4):
                return True
            else: 
                return False
        except:
            return False
        
    # TRESCLOUD TODO - Incluir estas funciones en el espacio de nombres de check_vat_ec
    def verifica_cedula(self,ced):
        try:
            if ced!='9999999999':
                valores = [ int(ced[x]) * (2 - x % 2) for x in range(9) ]
                suma = sum(map(lambda x: x > 9 and x - 9 or x, valores))
                veri = 10 - (suma - (10*(suma/10)))
                if int(ced[9]) == int(str(veri)[-1:]):
                    return True
                else:
                    return False
            else:
                return False
        except:
            return False
        
    # TRESCLOUD TODO - Incluir estas funciones en el espacio de nombres de check_vat_ec
    def verifica_id_cons_final(self,id):
        b=True
        try:
            for n in id:
                if int(n) != 9:
                    b=False
            return b
        except:
            return False
   
    # TRESCLOUD TODO - Incluir estas funciones en el espacio de nombres de check_vat_ec
    # TRESCLOUD TODO - Revisar la necesidad de esta funcion
    #    def _defined_type_ref(self, cr, uid, ids, field_name, arg, context=None):
    #        res={}
    #        for partner in self.browse(cr, uid, ids, context):
    #            ref = partner['ref']
    #            if(len(ref)==13):
    #                if self.verifica_ruc_pnat(ref) or self.verifica_ruc_spri(ref) or self.verifica_ruc_spub(ref):
    #                    res[partner.id]= 'ruc'
    #                elif self.verifica_id_cons_final(ref):
    #                    res[partner.id]= 'consumidor'
    #            elif (len(ref)==10):
    #                if self.verifica_cedula(ref):
    #                    res[partner.id]= 'cedula'
    #        return res

    # Ecuador VAT validation, contributed by TRESCLOUD (info@trescloud.com)
    # and based on https://launchpad.net/openerp-ecuador
    def check_vat_ec(self, vat):
        #Separa companias de personas naturales
        # P.R. This version Don't return a dictionary, must return True or False
        
        #type_identification = ''
        valid = False
        
        #validamos que solo se utilicen caracteres numericos
        for i in vat:
            try:
                int(i)
            except:
                #return {
                #'type_ref' : type_identification,
                #'valid': valid
                #}
                return valid
        
        if(len(vat)==13):
            #Se verifica que el cliente es una compañia privada
            if(int(vat[2])==9):
                if self.verifica_ruc_spri(vat):
                    valid = True
                    #type_identification='ruc'
                elif self.verifica_id_cons_final(vat):
                    valid = True
                    #type_identification='consumidor'
            #Se verifica que sea una empresa estatal
            elif(int(vat[2])==6) and self.verifica_ruc_spub(vat):
                valid = True
                #type_identification='ruc'
            #Se verifica que el ruc sea de una persona natural
            elif(int(vat[2])<6) and self.verifica_ruc_pnat(vat):
                valid = True
                #type_identification='ruc'
        #Se verifica el número de cedula
        elif(len(vat)==10) and self.verifica_cedula(vat):
            valid = True
            #type_identification='cedula'
        #return {
               # 'type_ref' : type_identification,
               # 'valid': valid
               # }
        return valid
    
    def get_number_identification(self, vat):
        '''Funcion que toma como argumento el campo vat, se hace un slicing para tomar la parte númerica.'''  
       
        identification=''        
        if vat:
            identification = vat[2:]
        
        return identification
    
    def get_code_country(self, vat):
        '''Funcion que toma como argumento el campo vat, se hace un slicing para tomar la parte del codigo de pais.'''
        
        code_country=''
        if vat:
            code_country = vat[:2] 
       
        return code_country
        
res_partner()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: