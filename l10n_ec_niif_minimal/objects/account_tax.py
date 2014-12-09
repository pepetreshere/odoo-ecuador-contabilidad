# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013 Christopher Ormaza, Ecuadorenlinea.net
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import netsvc
from datetime import date, datetime, timedelta
import decimal_precision as dp

import tools
from osv import fields, osv
from tools import config
from tools.translate import _


class account_tax(osv.osv):
    
    def _is_account_editor(self, cr, uid, ids, field_name, arg, context):
        """
        Implementation for `is_account_editor` functional field.

        This function determines whether the current user belongs to group 'l10n_ec_niif_minimal.ecua_group_account_editor'.
        Users in such group are the only allowed to edit certain special items about -in this case- the taxes.
        """
        #Impl. details:
        #    We get the groups ids from the current user. a list of integer values (i.e. database ids) is returned.
        #    We get the group named 'l10n_ec_niif_minimal.ecua_group_account_editor' and keep only its database id.
        #    We check whether such database id is among the user groups id list.
        #    We return whether such check is True or not (for each asked id).
        groups = self.pool.get('res.users').read(cr, uid, uid)['groups_id']
        group = self.pool.get('ir.model.data').get_object(cr, uid, 'l10n_ec_niif_minimal', 'ecua_group_account_editor', context=context).id
        return {id: (group in groups) for id in ids if id}
            
    _inherit = "account.tax"
    _columns = {
                'type_ec':fields.selection([
                    ('iva','IVA'),
                    ('renta','Renta'),
                    ('ice','ICE'),
                    ('other','Otro'),
                    ],    'Ecuadorian Type', select=True, help="Name the types of Ecuadorian taxes" ),
                'assets':fields.boolean('Assets', required=False),
                'imports':fields.boolean('Imports', required=False),
                'exports':fields.boolean('Exports', required=False),
                'tax_system':fields.boolean('Tax system', required=False, help="Systems tax, this tax is used by the internal system setup, you should not change. Ask your accountant for support.", write=['l10n_ec_niif_minimal.ecua_group_account_editor']),
                'is_account_editor':fields.function(_is_account_editor, type='boolean', method=True, string='Is Account Editor')
    }

    def _unit_compute_inv(self, cr, uid, taxes, price_unit, product=None, partner=None):
        res = super(account_tax, self)._unit_compute_inv(cr, uid, taxes, price_unit, product, partner)
        tax_obj = self.pool.get('account.tax')
        res_aux = []
        for r in res:
            tax = tax_obj.browse(cr, uid, r['id'])
            r.update({
                      'type_ec': tax.type_ec
                      })
            res_aux.append(r)
        return res_aux

    def _unit_compute(self, cr, uid, taxes, price_unit, product=None, partner=None, quantity=0):
        res = super(account_tax, self)._unit_compute(cr, uid, taxes, price_unit, product, partner, quantity)
        tax_obj = self.pool.get('account.tax')
        res_aux = []
        for r in res:
            tax = tax_obj.browse(cr, uid, r['id'])
            r.update({
                      'type_ec': tax.type_ec
                      })
            res_aux.append(r)
        return res

account_tax()

class account_tax_template(osv.osv):
    _inherit = "account.tax.template"
    _columns = {
                'type_ec':fields.selection([
                    ('iva','IVA'),
                    ('renta','Renta'),
                    ('ice','ICE'),
                     ('other','Otro'),
                   ],    'Ecuadorian Type', select=True, ),
                'assets':fields.boolean('Assets', required=False), 
                'imports':fields.boolean('Imports', required=False),
                'exports':fields.boolean('Exports', required=False),
                    }
    
    def _generate_tax(self, cr, uid, tax_templates, tax_code_template_ref, company_id, context=None):
        if not context: {}
        res = super(account_tax_template, self)._generate_tax(cr, uid, tax_templates, tax_code_template_ref, company_id, context)
        tax_obj = self.pool.get('account.tax')
        tax_template_obj = self.pool.get('account.tax.template')
        for template_id in res.get('tax_template_to_tax', {}).keys():
            tax_template = tax_template_obj.browse(cr, uid, template_id)
            tax_obj.write(cr, uid, res.get('tax_template_to_tax', {})[template_id], {
                                                                                     'type_ec': tax_template.type_ec
                                                                                     })
        return res
account_tax_template()
