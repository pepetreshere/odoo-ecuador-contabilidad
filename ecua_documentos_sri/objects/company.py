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
import re

class res_company(osv.osv):

    _inherit = 'res.company'


    def _get_auto_printer_auth(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        auth_obj = self.pool.get('sri.authorization')
        for company in self.browse(cr, uid, ids, context=context):
            has_auto_printer_auth = False
            auth_ids = auth_obj.search(cr, uid, [('company_id','=',company.id),('auto_printer','=',True)])
            if auth_ids:
                has_auto_printer_auth = True
            res[company.id]=has_auto_printer_auth
        return res
    
    _columns = {
                'has_auto_printer_auth': fields.function(_get_auto_printer_auth, method=True, type='boolean', string='Auto Impresor?', store=True),
                'authotization_ids':fields.one2many('sri.authorization', 'company_id', 'SRI Authorizations', required=False),
                'shop_ids':fields.one2many('sale.shop', 'company_id', 'Shops', required=False),
                'lines_invoice':fields.integer('Invoice Lines',required=False, help="Number of lines per invoice"),
                'generate_automatic':fields.boolean('Generar Secuencias SRI Automáticamente?', required=False), 
                }

res_company()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: