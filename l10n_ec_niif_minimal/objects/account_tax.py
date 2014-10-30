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
                'tax_system':fields.boolean('System Tax', required=False, help="Tax system facturadeuna.com, you can not change"),
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
