# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Ecuadorenlinea.net.
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

import datetime
from dateutil.relativedelta import relativedelta
import logging
from operator import itemgetter
from os.path import join as opj
import time

from openerp import netsvc, tools
from openerp.tools.translate import _
from openerp.osv import fields, osv

_logger = logging.getLogger(__name__)

class ecua_company_installer(osv.osv_memory):

    _name = 'ecua.company.installer'
    _inherit = 'res.config.installer'
    _columns = {
                'ruc':fields.char('Ruc', size=13, required=True),
                'company_id':fields.many2one('res.company', 'Company', readonly=True, required=True),
             }
    
    def check_ref(self, cr, uid, ids):
        partner_obj = self.pool.get('res.partner')
        for data in self.browse(cr, uid, ids):
            return partner_obj.check_ced(data.ruc).get('valid', False)

    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False

    def execute(self, cr, uid, ids, context=None):
        company_obj = self.pool.get('res.company')
        for wizard in self.browse(cr, uid, ids, context=context):
            company_obj.write (cr, uid, [wizard.company_id.id] , {
                            'ruc':wizard.ruc,
                             }, context=context)
        return super(ecua_company_installer, self).execute(cr, uid, ids, context=context)
            
    _defaults = {'company_id':_default_company,
               }
    _constraints = [(check_ref, _(u'The number of RUC is incorrect'), ['ruc'])]
ecua_company_installer()
