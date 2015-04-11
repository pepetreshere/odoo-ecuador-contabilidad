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

class account_journal(osv.osv):
    _inherit = 'account.journal'
    
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
        journal_info = self.browse(cr, uid, ids, context)
        
        if journal_info.replacement==True:
            warning_msgs += 'Se debe realizar reposición de fondos en el diario seleccionado.'
        
        return warning_msgs
    
    def _validate_replacement(self, cr, uid, ids, field_name, arg, context=None):
        """
        Verifica si un diario necesita reposición de fondos.
        Retorna True or False
        """
        res = {}
        
        journal_data = self.read(cr, uid, ids, ['type','maximun','minimun','default_credit_account_id'])
        type = journal_data[0]['type']
        
        if type=='bank':
            maximun = journal_data[0]['maximun']
            minimun = journal_data[0]['minimun']
            
            account_obj = self.pool.get('account.account')
            account_data = account_obj.read(cr, uid, [journal_data[0]['default_credit_account_id'][0]])
            balance = account_data[0]['balance']
            
            if balance < minimun:
                res[ids[0]] = True
            else:
                res[ids[0]] = False
        else:
            res[ids[0]]=False
        
        return res

    _columns = {
                'default_writeoff_acc_id': fields.many2one('account.account', 
                                                           'Default Open Balance Reconcile Account',
                                                           domain="['|',('force_reconcile','=',True),('type','!=','other')]", 
                                                           help="Default account for reconciling the open balance in vouchers, for withhold journals a payable accounts in favor of the partner should be used (ie 2011001 - ANTICIPOS DE CLIENTES)"
                                                           ),
                'controlled_funds': fields.boolean('Controlled funds', help='Indicates that this journal will be of controlled fund.'),
                'maximun': fields.float('Maximum'),
                'minimun': fields.float('Minimum'),
                'replacement': fields.function(_validate_replacement, string="Replacement", type='boolean', method=True,
                                                             help="Indicates that the journal should have replenishment"),
                'warning_msgs': fields.function(_get_warning_msgs, string='Warnings',store=False, type='char',method=True, 
                                                                   help='There are pending action in this transaction.'),
                }
    
    def onchange_valida_maximo(self, cr, uid, ids, field_max, field_min, type):
        """ 
        Valida que los campos field_max y field_max sean mayor a cero y que el 
        campo field_max sea siempre mayor al campo field_min.
        Se ejecuta siempre que se escoja el diario 'banco y cheques'.
        """
        res = {'warning':{}}
        
        if field_max!=0 and field_max!=0 and type=='bank':
        
            if field_max<=0:
                raise osv.except_osv(_('Error!'), _('El campo máximo debe ser mayor a cero.'))
            
            if field_min<=0:
                raise osv.except_osv(_('Error!'), _('El campo mínimo debe ser mayor a cero.'))
            
            if type=='bank' and field_min >= field_max:
                res = {'warning': {'title': _('Warning!'),
                                   'message': _('El campo Máximo debe ser mayor al campo Mínimo.')}                   
                      }
            
        return res
    
    def onchange_type(self, cr, uid, ids, type, controlled_funds):
        """ 
        Limpia que el campo controlled_funds y los respectivos campos máximo y mínimo.
        """        
        res = {'value':{}}
        
        if type!='bank':
            controlled_funds=False
        else:
            controlled_funds=True
        
        if controlled_funds==True:
            res = {'value':{'maximun':False, 'minimun':False, 'replacement':False}}
        else:
            res = {'value':{'controlled_funds':False, 'maximun':False, 'minimun':False, 'replacement':False}}          

        return res
    
    def create(self, cr, uid, values, context=None):
        if not context: context = {}
        
        maximun = 0
        minimun = 0
        
        if values.get('type')=='bank' and (values.has_key('maximun') or values.has_key('minimun')):
            if 'maximun' in values:
                maximun = values.get('maximun')
                if maximun<=0:
                    raise osv.except_osv(_('Error!'), _('El campo mínimo debe ser mayor a cero.'))
            if 'minimun' in values:
                minimun = values.get('minimun')
                if minimun<=0:
                    raise osv.except_osv(_('Error!'), _('El campo mínimo debe ser mayor a cero.'))
    
            if minimun >= maximun:
                raise osv.except_osv(_('Error!'), _('El campo Máximo debe ser mayor al campo Mínimo.'))
            
        res = super(account_journal, self).create(cr, uid, values, context)
        
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        
        if vals.has_key('controlled_funds'):
            controlled_funds = vals.get('controlled_funds')
        else:
            controlled_funds = self.read(cr, uid, ids, ['controlled_funds'])[0]['controlled_funds']
           
        if controlled_funds==True:
            if not vals.has_key('maximun') and not vals.has_key('minimun'):
                raise osv.except_osv(_('Error!'), _('Los valores de máximo y mínimo deben ser mayores a cero.'))
            else:
                if 'maximun' in vals:
                    maximun = vals.get('maximun')
                    if maximun<=0:
                        raise osv.except_osv(_('Error!'), _('El campo máximo debe ser mayor a cero.'))
                else:
                    journal_data = self.read(cr, uid, ids, ['maximun']) 
                    maximun = journal_data[0]['maximun']
                  
                if 'minimun' in vals:
                    minimun = vals.get('minimun')
                    if minimun<=0:
                        raise osv.except_osv(_('Error!'), _('El campo mínimo debe ser mayor a cero.'))
                else:
                    journal_data = self.read(cr, uid, ids, ['minimun'])
                    minimun = journal_data[0]['minimun']
                
                if minimun >= maximun:
                    raise osv.except_osv(_('Error!'), _('El campo Máximo debe ser mayor al campo Mínimo.'))

        journal_id = super(account_journal,self).write(cr, uid, ids, vals, context)
        
        return True
    
account_journal()