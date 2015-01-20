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
import re


class res_partner(osv.osv):
    _inherit = "res.partner"
    _name = "res.partner"

    _columns = {
        'comercial_name': fields.char('Comercial Name', size=256),
    }

    _defaults = {
        'comercial_name': "",
    }

    def write(self, cr, uid, ids, vals, context=None):
        """
        Este write tiene consideracion por el cambio en el campo commercial_name.
        """
        if not context: context = {}

        for partner in self.browse(cr, uid, ids, context):
            changes = []

            #Agregamos log de cambios
            if 'comercial_name' in vals and partner.comercial_name != vals['comercial_name']: # en el caso que sea un campo
                oldmodel = partner.comercial_name or _('None')
                newvalue = vals['comercial_name'] or _('None')
                changes.append(_("Comercial Name: from '%s' to '%s'") %(oldmodel,newvalue ))

            if len(changes) > 0:
                self.message_post(cr, uid, [partner.id], body=", ".join(changes), context=context)

        return super(res_partner, self).write(cr, uid, ids, vals, context=context)

    def onchange_type(self, cr, uid, ids, is_company, context=None):
        """
        Redefinición del método onchange_type para inicializar el campo comercial_name
          si es que este partner no es una empresa.
        :param cr:
        :param uid:
        :param ids:
        :param is_company:
        :param context:
        :return:
        """
        res = super(res_partner, self).onchange_type(cr, uid, ids, is_company, context)

        if not is_company:
            res['value']['comercial_name'] = ""
        return res

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        """
        Permite buscar ya sea por nombre, por codigo o por nombre comercial
        hemos copiado la idea de product.product
        No se llama a super porque name-search no estaba definida
        """
        args = args or []
        context = context or {}

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
        else:
            #cuando el usuario no ha escrito nada aun
            ids = self.search(cr, user, args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context=context)
