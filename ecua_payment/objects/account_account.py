# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2010  Christoher Ormaza, Ecuadorenlinea.net              #
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
from osv import fields,osv
from tools.translate import _

class account_account(osv.osv):
    _inherit = 'account.account'
    
    def _get_warning_msgs(self, cr, uid, ids, field, arg, context=None):
        '''
        Retorna una explicación del porque en la vista tree el diario está en color rojo.
        (Cuando el campo warning_msgs no está vacío la linea de diario se pinta de color rojo) 
        '''        
        res = {}
        journal_info = self.browse(cr, uid, ids, context)
        
        for journal in journal_info:
            res[journal.id]= self._warning_msgs(cr, uid, journal.id, context)
        
        return res

    def _warning_msgs(self, cr, uid, ids, context=None):
        '''
        Metodo helper: Ayuda a redefinir con facilidad el campo tipo función asociado al metodo _get_warning_msgs
        Retorna una mensaje.
        '''
        warning_msgs = ''
        account_info = self.browse(cr, uid, ids, context)
        
        if account_info.replenishment:
            warning_msgs += 'Se debe realizar reposición de fondos en la cuenta seleccionada.'
        
        return warning_msgs
    
    def _validate_replenishment(self, cr, uid, ids, field_name, arg, context=None):
        """
        Verifica si un diario necesita reposición de fondos.
        Retorna True or False
        """
        res = {}
        
        for account_data in self.browse(cr, uid, ids,context=context):
            if account_data.controlled_funds:
                maximun = account_data.maximun
                minimun = account_data.minimun
                balance = account_data.balance
                if balance < minimun:
                    res[account_data.id] = True
                else:
                    res[account_data.id] = False
        return res

    _columns = {
                'controlled_funds': fields.boolean('Controlled funds', help='Indicates that this journal will be of controlled fund.'),
                'maximun': fields.float('Maximum', help="Quantity of reference for calculating controlled fund replenishment. It is the maximum value that must be the controlled fund."),
                'minimun': fields.float('Minimum', help="Quantity of reference for calculating controlled fund replenishment. This field is to calculate the difference between the maximum fund and make replenishing it."),
                'replenishment': fields.function(_validate_replenishment, string="Replenishment", type='boolean', method=True,
                                                             help="Indicates that the journal should have replenishment"),
                'warning_msgs': fields.function(_get_warning_msgs, string='Warnings',store=False, type='char',method=True, 
                                                                   help='There are pending action in this transaction.'),
                }
    
    _defaults = {
                'controlled_funds': False, 
                }
    
    def onchange_validate_maximun(self, cr, uid, ids, field_max, field_min, type):
        """ 
        Valida que los campos field_max y field_max sean mayor a cero y que el 
        campo field_max sea siempre mayor al campo field_min.
        Se ejecuta siempre que se escoja los diarios efectivo o 'banco y cheques'.
        """
        res = {'warning':{}}
        
        if field_max!=0:
        
            if field_max<=0:
                raise osv.except_osv(_('Error!'), _('El campo máximo debe ser mayor a cero.'))
            
            if field_min >= field_max:
                res = {'warning': {'title': _('Warning!'),
                                   'message': _('El campo Máximo debe ser mayor al campo Mínimo.')}                   
                      }
            
        return res
    # TODO: Falta implementar el tipo de cuenta al que se quiere controlar los fondos. 
    def onchange_type(self, cr, uid, ids, controlled_funds):
        """ 
        Limpia que el campo controlled_funds y los respectivos campos máximo y mínimo.
        """        
        res = {'value':{}}
        if controlled_funds:
            res = {'value':{'maximun':False, 'minimun':False, 'replenishment':False}}
        else:
            res = {'value':{'controlled_funds':False, 'maximun':False, 'minimun':False, 'replenishment':False}}          
 
        return res
    
    def create(self, cr, uid, values, context=None):
        if not context: context = {}
        
        maximun = 0
        minimun = 0
        
        if values.get('controlled_funds'):
            if values.has_key('maximun') and values.has_key('minimun'):
                if 'maximun' in values:
                    maximun = values.get('maximun')
                    if maximun<=0:
                        raise osv.except_osv(_('Error!'), _('El campo máximo debe ser mayor a cero.'))
                if 'minimun' in values:
                    minimun = values.get('minimun')
                            
                if minimun >= maximun:
                    raise osv.except_osv(_('Error!'), _('El campo Máximo debe ser mayor al campo Mínimo.'))
            
        res = super(account_journal, self).create(cr, uid, values, context)
        
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        for account_data in self.browse(cr, uid, ids, context=context):
            if vals.has_key('controlled_funds'):
                controlled_funds = vals.get('controlled_funds')
            else:
                controlled_funds = account_data.controlled_funds
               
            if controlled_funds:
                if 'maximun' in vals:
                    maximun = vals.get('maximun')
                    if maximun<=0:
                        raise osv.except_osv(_('Error!'), _('El campo máximo debe ser mayor a cero.'))
                else:
                    maximun = account_data.maximun
                  
                if 'minimun' in vals:
                    minimun = vals.get('minimun')
                else:
                    minimun = account_data.minimun

                if minimun >= maximun:
                    raise osv.except_osv(_('Error!'), _('El campo Máximo debe ser mayor al campo Mínimo.'))
    
        account_id = super(account_account,self).write(cr, uid, ids, vals, context)
            
        return True
    
account_account()