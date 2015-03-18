# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
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

import logging

from openerp.osv import fields, osv
from openerp import pooler
from openerp.tools.translate import _


class res_company(osv.Model):
    _name = 'res.company'
    _inherit = ['res.company', 'mail.thread']
    _columns = {
        'avoid_duplicated_vat':fields.boolean('Avoid duplicated vat numbers', required=False,
                                              help='Evita la creación de contactos con el número de Cédula/RUC/Pasaporte duplicado',
                                              track_visibility='onchange'),
        'comercial_name':fields.related('partner_id','comercial_name',type='char',relation='res.partner',string='Comercial Name',store=False, track_visibility='onchange'),
    }
    _defaults = {
        'avoid_duplicated_vat': True,
    }
res_company()        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
