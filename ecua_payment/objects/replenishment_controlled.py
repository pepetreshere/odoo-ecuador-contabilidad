# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Ing. Carlos Yumbillo                                                                          
# Copyright (C) 2015  TRESCLOUD CIA. LTDA.                                 
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

from openerp.osv import fields, osv
from tools.translate import _

import time

class replenishment_controlled(osv.osv):
    _name = 'replenishment.controlled'
        
    def _get_amount_due(self, cr, uid, ids, field, arg, context=None):
        '''
        Campo calculado por la diferencia del valor máximo del diario y el saldo pendiente.
        En el proceso, si el estado del fondo controlado no está en estado tramitado se actualiza
        el campo amount_paid_usr con el nuevo valor del campo calculado amount_paid, caso contrario
        utiliza el valor del campo amount_paid_usr para mostrarlo en la vista.
        NOTA: Utilizar el campo amount_paid_usr para los reportes respectivos.
        '''
        res = {}
        amount_paid = 0
        journal_obj = self.pool.get('account.journal')
        account_obj = self.pool.get('account.account')
        
        replenishment_data = self.read(cr, uid, ids, ['state','journal_to_id'])
               
        for replenishment in replenishment_data:
            id = replenishment['id']
            state = replenishment['state']
            journal_id = replenishment['journal_to_id']
                        
            if state != 'processed':                
                journal_data = journal_obj.read(cr, uid, journal_id[0], ['type','maximun','minimun','default_credit_account_id'])
                type = journal_data['type']
                
                if type=='bank':
                    maximun = journal_data['maximun']                    
                    account_data = account_obj.read(cr, uid, [journal_data['default_credit_account_id'][0]])
                    balance = account_data[0]['balance']
                    amount_paid = maximun - balance
                    self.write(cr, uid, id, {'amount_paid_usr':amount_paid})
                    res[id] = amount_paid
            else:
                replenishment_data = self.read(cr, uid, id, ['amount_paid_usr'])
                res[id] = replenishment_data['amount_paid_usr']
        
        return res
    
    _columns = {
                'name': fields.char('Replacement fund controlled', size=128,),
                'user_id': fields.many2one('res.users', 'User', required=True),
                'partner_id': fields.many2one('res.partner', 'Partner', required=True),
                'date': fields.date('Date', required=True,
                                    help="Indicates the date on which it was created replenishing controlled background."),
                'reference': fields.char('Reference', size=50, required=True),
                'state': fields.selection([('draft', 'Draft'),
                                           ('confirmed','Confirmed'),
                                           ('processed','Processed'),], 'State'),
                'journal_from_id': fields.many2one('account.journal', 'From', required=True),
                'journal_to_id': fields.many2one('account.journal', 'To', required=True),
                'amount_paid': fields.function(_get_amount_due, string='Amount paid',store=False, type='float',method=True, 
                                                                help='Indicates that this journal will be of controlled fund.'),
                'amount_paid_usr': fields.float('Amount paid', help='Used parallel used for internal control function type field.'),
                'account_voucher_id': fields.many2one('account.voucher','Reference to Pay'),
                }    

    _defaults = {
                 'state': 'draft',
                 'date': lambda *a: time.strftime('%Y-%m-%d'),
                 'partner_id': lambda obj, cr, uid, context: obj.pool.get('res.users').browse(cr, uid, uid).company_id.partner_id.id,
                 'user_id': lambda self, cr, uid, context: uid,
                 #'company_id': lambda obj, cr, uid, context: obj.pool.get('res.users').browse(cr, uid, uid).company_id.id,
                }    
    
    def create(self, cr, uid, vals, context=None):
        sequence_obj = self.pool.get('ir.sequence')
        seq_replenishmnet_id = sequence_obj.search(cr, uid,[('name','=','Replenishment-Controlled')])
        vals['name'] = sequence_obj.next_by_id(cr, uid, seq_replenishmnet_id)

        return super(replenishment_controlled, self).create(cr, uid, vals, context)
    
    def onchange_journal_to_id(self, cr, uid, ids, journal_to_id):
        '''
        Al escoger un diario de tipo "Banco y Cheques" se calcula el campo Importe Pagago
        calculado por la diferencia del valor máximo del diario y el saldo pendiente.
        '''
        res = {}
        amount_paid = 0
        
        if journal_to_id:
            journal_obj = self.pool.get('account.journal')
            journal_data = journal_obj.read(cr, uid, journal_to_id, ['type','maximun','minimun','default_credit_account_id'])
            type = journal_data['type']
            
            if type=='bank':
                maximun = journal_data['maximun']                
                account_obj = self.pool.get('account.account')
                account_data = account_obj.read(cr, uid, [journal_data['default_credit_account_id'][0]])
                balance = account_data[0]['balance']
                amount_paid = maximun - balance
                amount_paid_usr = amount_paid
    
            res = {'value':{'amount_paid':amount_paid,'amount_paid_usr':amount_paid_usr}}
        
        return res
        
    def button_draft_to_confirmed(self, cr, uid, ids, context=None):
        '''
        Función utilizada para cambiar el estado del Fondo Controlado de borrador a confirmado.
        El formulario respectivo se cambia a solo lectura.
        '''     
        return self.write(cr, uid, ids, {'state':'confirmed'}, context=None)
    
    def button_confirmed_to_draft(self, cr, uid, ids, context=None):
        '''
        Función utilizada para cambiar el estado del Fondo Controlado de confirmado a borrador.
        El formulario respectivo puede ser editable.
        '''
        return self.write(cr, uid, ids, {'state':'draft'}, context=None)
    
    def button_create_payment(self, cr, uid, ids, context=None):
        '''
        Función utilizada para crear un pago. Se pasa los valores del respectivo Fondo Controlado.
        '''
                
        replenishment_info = self.browse(cr, uid, ids[0], context=context)
        voucher_obj = self.pool.get("account.voucher")     
         
        voucher_res = {
                        'type': 'payment',
                        'name': replenishment_info.name,
                        'partner_id': replenishment_info.partner_id.id,
                        'journal_id': replenishment_info.journal_from_id.id,
                        'account_id': replenishment_info.journal_from_id.default_debit_account_id.id,
                        'date': replenishment_info.date or time.strftime('%Y-%m-%d'),
                        'amount': abs(replenishment_info.amount_paid_usr),
                        'writeoff_amount': abs(replenishment_info.amount_paid_usr),
                        'payment_option': 'with_writeoff',
                        # Es la cuenta del método de pago que se desea rebastecer
                        'writeoff_acc_id': replenishment_info.journal_to_id.default_debit_account_id.id,
                        'comment': replenishment_info.reference,
                      }
        voucher_id = voucher_obj.create(cr, uid, voucher_res, context=context)
        self.write(cr, uid, ids, {'state':'processed', 'account_voucher_id':voucher_id}, context=None)
        
        return voucher_id

replenishment_controlled()