# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 TRESCloud (<http://www.trescloud.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from osv import fields, osv
import time

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Agregamos datos necesarios a la factura generada
           ej. numero factura, punto de impresion, direccion, telefono
        """
        #fragmento medio repetido en make_invoice de sale.order.LINE
        #al momento el framework no nos permite hacerlo mas DRY

        if context is None:
            context = {}
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context)
        
        inv_obj=self.pool.get('account.invoice')
        invoice_header_for_ecuador = inv_obj._prepare_invoice_header(cr, uid, invoice_vals['partner_id'], invoice_vals['type'], invoice_vals['date_invoice'] or None, context)

        invoice_vals.update(invoice_header_for_ecuador)

        return invoice_vals
    
sale_order()


