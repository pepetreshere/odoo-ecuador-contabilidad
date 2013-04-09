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

import time
import netsvc
from datetime import date, datetime, timedelta

from osv import fields, osv
from tools import config
from tools.translate import _

class stock_picking(osv.osv):
    
    _inherit = 'stock.picking'

    _columns = {
                'shop_id':fields.many2one('sale.shop', 'Shop', required=False,readonly=True, states={'draft':[('readonly',False)]} ), 
                'printer_id':fields.many2one('sri.printer.point', 'Printer Point', readonly=True, states={'draft':[('readonly',False)]}),
                'delivery_note_ids':fields.many2many('account.remision', 'delivery_note_picking_rel', 'picking_id', 'delivery_note_id', 'Delivery Notes', readonly=True, states={'draft':[('readonly',False)]}),
                'invoice_ids':fields.many2many('account.invoice', 'invoice_created_picking_rel', 'invoice_id', 'picking_id', 'Facturas Relacionadas'),
                    }
    

    def copy(self, cr, uid, id, default={}, context=None):
        if context is None:
            context = {}
        default.update({
            'delivery_note_ids':[],
        })
        return super(stock_picking, self).copy(cr, uid, id, default, context)

    def action_cancel(self, cr, uid, ids, context=None):
        res = super(stock_picking, self).action_cancel(cr, uid, ids, context)
        #TODO: cancelar cada una de las guias de remision relacionadas y desligar los documentos
        return res

    def _invoice_hook(self, cr, uid, picking, invoice_id):
        wf_service = netsvc.LocalService("workflow")
        invoice_obj = self.pool.get('account.invoice')
        wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)
        sale_obj = self.pool.get('sale.order')
        res = super(stock_picking, self)._invoice_hook(cr, uid, picking, invoice_id)
        inv_list = [invoice_id]
        if picking.type == 'out':
            while True:
                invoice_id = invoice_obj.split_invoice(cr, uid, invoice_id)
                if invoice_id:
                    inv_list.append(invoice_id)
                else:
                    break
        if picking.sale_id:
            for inv_id in inv_list:
                sale_obj.write(cr, uid, [picking.sale_id.id], {
                    'invoice_ids': [(4, inv_id)],
                    })
        self.write(cr, uid, picking.id, {
                                         'invoice_ids': [(6,0,inv_list)]
                                             })
        return

    def action_invoice_create(self, cr, uid, ids, journal_id=False, group=False, type='out_invoice', context=None):
        res = super(stock_picking, self).action_invoice_create(cr, uid, ids, journal_id, group, type, context)
        result = {}
        for picking in self.browse(cr, uid, res.keys()):
            if picking.type == 'out':
                for invoice in picking.invoice_ids:
                    result[invoice.id] = invoice.id
        if result: 
            return result
        else: 
            return res
                    
    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        if not context: context = {}
        #TODO realizar el paso de referencias para los documentos autorizados por medio del analisis del picking y los datos del partner
        doc_obj=self.pool.get('sri.type.document')
        now = time.strftime('%Y-%m-%d')
        res = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context)
        if picking.type == 'out':
            auth_line_id = doc_obj.search(cr, uid, [('name','=','invoice'), ('printer_id','=', picking.sale_id.printer_id.id), ('sri_authorization_id.start_date','<=',now), ('sri_authorization_id.expiration_date','>=',now)])
            auth_line = auth_line_id and doc_obj.browse(cr, uid, auth_line_id[0],context)
            if not auth_line:
                raise osv.except_osv(_(u'Error!!!'),_(u'No existe autorización activa para generar Facturas'))
            new_number = doc_obj.get_next_value_secuence(cr, uid, 'invoice', False, picking.sale_id.printer_id.id, 'account.invoice', 'invoice_number_out', context)
            res.update({
                        'automatic_number': new_number,
                        'invoice_number_out': new_number,
                        'shop_id': picking.sale_id.shop_id.id,
                        'printer_id':picking.sale_id.printer_id.id,
                        'authorization': auth_line.sri_authorization_id.number,
                        'authorization_sales': auth_line.sri_authorization_id.id,
                        })
        return res

stock_picking()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: