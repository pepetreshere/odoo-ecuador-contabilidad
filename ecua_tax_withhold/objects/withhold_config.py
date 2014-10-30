# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://www.trescloud.com>). David Romero
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
import datetime
from dateutil.relativedelta import relativedelta

import openerp
from openerp import SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF_memory
from openerp.tools.translate import _
from openerp.osv import fields, osv

class account_config_settings(osv.osv_memory):
    _inherit = 'account.config.settings'

    _columns = {
        'tax_wi_id': fields.related('company_id', 'tax_wi_id', type='many2one', relation='account.tax', required=True,
            string='Default company tax withhold', help="This withhold tax will be assigned by default on new products."),
        
#         'tax_wi_id': fields.many2one('account.tax', 'Default withhold tax',
#             help="This withhold tax will be assigned by default on new products."),
    }

    _defaults = {
        
    }
    
    
#     def get_default_withhold(self, cr, uid, ids, context=None):
#         ir_values = self.pool.get('ir.values')
#         tax_wi_id = ir_values.get_default(cr, uid, 'account.withhold.line', 'tax_wi_id')
#         return {
#             'tax_wi_id': tax_wi_id,
#         }
#     
#         
#     def set_default_withhold(self, cr, uid, ids, context=None):
#         """ set default claim for contracts"""
#         if uid != SUPERUSER_ID and not self.pool['res.users'].has_group(cr, uid, 'base.group_erp_manager'):
#             raise openerp.exceptions.AccessError(_("Only administrators can change the settings"))
#         ir_values = self.pool.get('ir.values')
#         config = self.browse(cr, uid, ids[0], context)
#         ir_values.set_default(cr, SUPERUSER_ID, 'account.withhold.line', 'tax_wi_id',
#             config.tax_wi_id and [config.tax_wi_id.id] or False, company_id=config.company_id.id)

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = super(account_config_settings, self).onchange_company_id(cr, uid, ids, company_id, context=context)
        if company_id:
            company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
            
            res['value'].update({ 'tax_wi_id': company.tax_wi_id.id,})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
