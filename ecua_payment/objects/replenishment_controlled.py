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
    _inherit = ['mail.thread']
    _description = 'Replenishment Controlled'
        
    def _get_amount_due(self, cr, uid, ids, field, arg, context=None):
        '''
        Campo calculado por la diferencia del valor máximo del diario y el saldo pendiente.
        En el proceso, se realiza el cálculo si el estado del fondo controlado no está en estado tramitado,
        caso contrario se utiliza el valor del campo amount_paid_usr para mostrarlo en la vista.
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
                        
            journal_data = journal_obj.browse(cr, uid, journal_id[0], context=context)
            type = journal_data.type
                
            if type in ('cash','bank') and state!='processed':
                maximun = journal_data.default_debit_account_id.maximun
                account_data = journal_data.default_debit_account_id
                balance = account_data.balance
                amount_paid = maximun - balance
                res[id] = amount_paid
            elif type in ('cash','bank') and state=='processed':
                replenishment_data = self.read(cr, uid, id, ['amount_paid_usr'])
                res[id] = replenishment_data['amount_paid_usr']
            else:
                res[id] = 0

        return res
    
    _columns = {
                'name': fields.char('Replenishment fund controlled', size=50,),
                'user_id': fields.many2one('res.users', 'User', required=True),
                'partner_id': fields.many2one('res.partner', 'Partner', required=True),
                'date': fields.date('Date', required=True,
                                    help="Indicates the date on which it was created replenishing controlled background.",
                                    track_visibility='onchange',),
                'reference': fields.char('Reference', size=50, required=True, track_visibility='onchange',),
                'state': fields.selection([('draft', 'Draft'),
                                           ('confirmed','Confirmed'),
                                           ('processed','Processed'),], 'State', track_visibility='onchange',),
                'journal_from_id': fields.many2one('account.journal', 'From', required=True, track_visibility='onchange',
                                                   help="Journal source for replenishment."),
                'journal_to_id': fields.many2one('account.journal', 'To', required=True, track_visibility='onchange',
                                                  help="Journal of the replacement destination."),
                'amount_paid': fields.function(_get_amount_due, string='Amount paid',store=False, type='float',method=True, 
                                               help='Indicates the value of the replenishment.', track_visibility='onchange'),
                'amount_paid_usr': fields.float('Amount paid', help='Used parallel used for internal control function type field.'),
                'account_voucher_id': fields.many2one('account.voucher','Reference to Pay'),
                'narration': fields.text('narration'),
                }    

    _defaults = {
                 'state': 'draft',
                 'date': lambda *a: time.strftime('%Y-%m-%d'),
                 'partner_id': lambda obj, cr, uid, context: obj.pool.get('res.users').browse(cr, uid, uid).company_id.partner_id.id,
                 'user_id': lambda self, cr, uid, context: uid,
                }
    
    _sql_constraints = [('name_unique', 'UNIQUE(name)', 'El código de la Reposición debe ser único.!')]   
    
    def create(self, cr, uid, vals, context=None):
        
        if vals.get('journal_from_id')==vals.get('journal_to_id'):
            raise osv.except_osv(_('Error!'), _('Los diarios origen y destino no pueden ser iguales.'))
        
        sequence_obj = self.pool.get('ir.sequence')
        seq_replenishmnet_id = sequence_obj.search(cr, uid,[('name','=','Replenishment-Controlled')])
        vals['name'] = sequence_obj.next_by_id(cr, uid, seq_replenishmnet_id)

        return super(replenishment_controlled, self).create(cr, uid, vals, context)
    
    def write(self, cr, uid, ids, vals, context=None):
        """
        Envía un warning si es que los diarios origen y destino son los mismos.
        """
        
        if vals.has_key('state') and vals.get('state')=='processed':
            replenishment_info = self.read(cr, uid, ids, ['amount_paid'])
            # Se actualiza el campo auxiliar con el valor del campo tipo función.
            vals['amount_paid_usr'] = replenishment_info[0]['amount_paid']
        
        msg = 'Los diarios origen y destino no pueden ser iguales.'
         
        if vals.has_key('journal_from_id') and vals.has_key('journal_to_id'):
            if vals.get('journal_from_id')==vals.get('journal_to_id'):
                raise osv.except_osv(_('Error'),_(msg))
        else:
            replenishment_data = self.read(cr, uid, ids, ['journal_from_id','journal_to_id'])
            
            if type(replenishment_data)==dict: #Si es diccionario
                journal_from_id = replenishment_data['journal_from_id'][0]
                journal_to_id = replenishment_data['journal_to_id'][0]
                
            elif type(replenishment_data)==list: # Si es una lista con un diccionario
                journal_from_id = replenishment_data[0]['journal_from_id'][0]
                journal_to_id = replenishment_data[0]['journal_to_id'][0]
             
            if vals.has_key('journal_from_id'):
                if vals.get('journal_from_id')==journal_to_id:
                    raise osv.except_osv(_('Error'), _(msg))
            elif vals.has_key('journal_to_id'):
                if vals.get('journal_to_id')==journal_from_id:
                    raise osv.except_osv(_('Error'),_(msg))
                  
        return super(replenishment_controlled,self).write(cr, uid, ids, vals, context)
    
    def onchange_journal_to_id(self, cr, uid, ids, journal_to_id, context=None):
        '''
        Al escoger un diario de tipo "Banco y Cheques o Efectivo" se calcula el campo Importe Pagado
        calculado por la diferencia del valor máximo del diario y el saldo pendiente.
        '''
        res = {}
        amount_paid = 0
        
        if journal_to_id:
            journal_obj = self.pool.get('account.journal')
            journal_data = journal_obj.browse(cr, uid, journal_to_id, context=context)
            type = journal_data.type
            
            if type in ('cash','bank'):
                maximun = journal_data.default_debit_account_id.maximun
                account_obj = self.pool.get('account.account')
                account_data = journal_data.default_debit_account_id
                balance = account_data.balance
                amount_paid = maximun - balance
                amount_paid_usr = amount_paid
    
            res = {'value':{'amount_paid':amount_paid,'amount_paid_usr':amount_paid_usr}}
        
        return res
        
    def button_draft_to_confirmed(self, cr, uid, ids, context=None):
        '''
        Función utilizada para cambiar el estado del Fondo Controlado de borrador a confirmado.
        El formulario respectivo se cambia a solo lectura.
        '''     
        replenishment_data = self.read(cr, uid, ids, ['amount_paid'])
        #Se actualiza el campo auxiliar con el valor del campo tipo función.
        #Esto se hace ya que puede darse el caso que alguien en el proceso edite el máximo o mínimo del diario.
        amount_paid = replenishment_data[0]['amount_paid']
        
        return self.write(cr, uid, ids, {'state':'confirmed', 'amount_paid_usr':amount_paid}, context=None)
    
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
                        #Secuencia de la reposición
                        'name': replenishment_info.name,
                        'partner_id': replenishment_info.partner_id.id,
                        'company_id': replenishment_info.partner_id.company_id.id,
                        #Método de pago con el cual se va a rebastecer
                        'journal_id': replenishment_info.journal_from_id.id,
                        'account_id': replenishment_info.journal_from_id.default_debit_account_id.id,
                        'date': replenishment_info.date or time.strftime('%Y-%m-%d'),
                        'amount': abs(replenishment_info.amount_paid_usr),
                        'writeoff_amount': abs(replenishment_info.amount_paid_usr),
                        'payment_option': 'with_writeoff',
                        # Es la cuenta del método de pago que se desea rebastecer
                        'writeoff_acc_id': replenishment_info.journal_to_id.default_debit_account_id.id,
                        'narration': 'Reposición de Fondo Controlado',
                        'comment': replenishment_info.reference,
                      }
        voucher_id = voucher_obj.create(cr, uid, voucher_res, context=context)
        self.write(cr, uid, ids, {'state':'processed', 'account_voucher_id':voucher_id}, context=None)
        
        return voucher_id

replenishment_controlled()