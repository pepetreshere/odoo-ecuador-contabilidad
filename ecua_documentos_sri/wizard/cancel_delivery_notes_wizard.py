# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2012  Ecuadorenlinea.net                                #
#            (Christopher Ormaza)                                       #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
from osv import fields, osv
import decimal_precision as dp
from tools.translate import _
import time
import netsvc
import re
from lxml import etree

class cancel_remision_wizard(osv.osv_memory):
    
    _name = 'account.cancel.remision.wizard' 
    
    _columns = {
                    'line_ids':fields.one2many('account.cancel.remision.line.wizard', 'wizard_id', 'Lines', required=True), 
                    'date': fields.date('Date', required=True),
                    'company_id':fields.many2one('res.company', 'Company', required=True), 
                    }
    
    _defaults = {  
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        }

    def action_cancel_remisions(self, cr, uid, ids, context=None):
        rem_obj = self.pool.get('account.remision')
        auth_obj = self.pool.get('sri.authorization')
        shop_obj = self.pool.get('sale.shop')
        printer_obj = self.pool.get('sri.printer.point')
        wiz_l_obj = self.pool.get('account.cancel.remision.line.wizard')
        wizards = self.browse(cr, uid, ids, context)
        ret_ids = []
        for wiz in wizards:
            for line in wiz.line_ids:
                ids = rem_obj.search(cr, uid, [('number', '=', line.number)])
                number = line.number.split('-')
                company_id = wiz.company_id.id
                shop_id = shop_obj.search(cr, uid, [('number', '=', number[0]), ('company_id','=',company_id)])[0]
                printer_id = printer_obj.search(cr, uid, [('number', '=', number[1]), ('shop_id','=', shop_id)])[0]
                if not ids:
                    auth_id = auth_obj.check_if_seq_exist(cr, uid, 'delivery_note', company_id, shop_id, line.number, printer_id, context)
                    if auth_id:
                        vals = {
                                'number': line.number,
                                'shop_id': shop_id,
                                'printer_id': printer_id,
                                'authorizacion_id': auth_id['authorization'],
                                'type': 'sales',
                                'state': 'canceled',
                                'motive': _('Cancel Delivery Note'),
                                'transfer_date': wiz.date,
                                'delivery_date': wiz.date,
                                'transaction_type': 'purchase',
                                }
                        ret_id = rem_obj.create(cr, uid, vals, context)
                        ret_ids.append(ret_id)
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_account_remision_tree')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'account.remision',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', ret_ids)],
            'context': context,
        }

    def action_close(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
cancel_remision_wizard()

class cancel_remision_line_wizard(osv.osv_memory):
    
    def _check_number(self, cr, uid, ids, context=None):
        cadena = '(\d{3})+\-(\d{3})+\-(\d{9})'
        for obj in self.browse(cr, uid, ids):
            ref = obj['number']
            if obj['number']:
                if re.match(cadena, ref):
                    return True
                else:
                    return False
            else:
                return True

    _constraints = [(_check_number, _('The number is incorrect, it must be like 001-00X-000XXXXXX, X is a number'), ['number'])]

    _name = 'account.cancel.remision.line.wizard'
    
    _columns = {
                    'wizard_id':fields.many2one('account.cancel.remision.wizard', 'Wizard', required=False),
                    'number':fields.char('Number', size=17, required=True, ),
                    'status':fields.boolean('Status', required=False),
                    }
    
cancel_remision_line_wizard()