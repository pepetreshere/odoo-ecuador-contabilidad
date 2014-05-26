# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Christopher Ormaza, Ecuadorenlinea.net
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

import time
import netsvc
from datetime import date, datetime, timedelta
import decimal_precision as dp

import tools
from osv import fields, osv
from tools import config
from tools.translate import _

class account_account(osv.osv):
    _name = 'account.account'
    #_inherits = {"mail.alias": "alias_id"}
    _inherit = ["account.account", "mail.thread"]    
    _columns = {
                    }
    
    def write(self, cr, uid, ids, vals, context=None):
        """
        This function write an entry in the openchatter whenever we change important information
        on the account like the model, the drive, the state of the account or its license plate
        """
        for account in self.browse(cr, uid, ids, context):  
            changes = []
            if 'code' in vals and account.code != vals['code']:
                value =  vals['code']
                oldmodel = account.type or _('None')
                changes.append(_("Code: from '%s'  '%s'") %(oldmodel, value))
            if 'name' in vals and account.name != vals['name']:
                value =  vals['name']
                oldmodel = account.name or _('None')
                changes.append(_("Name: from '%s' '%s'") %(oldmodel, value))
            if 'parent_id' in vals and account.parent_id.id != vals['parent_id']:
                #value = self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).name
                value =  self.pool.get('account.account').browse(cr,uid,vals['parent_id'],context=context).name
                oldmodel = account.parent_id.name or _('None')
                changes.append(_("Type: from '%s' to '%s'") %(oldmodel, value))
            if 'type' in vals and account.type != vals['type']:
                value =  vals['type']
                oldmodel = account.type or _('None')
                changes.append(_("Type: from '%s' to '%s'") %(oldmodel, value))
            if 'user_type' in vals and account.user_type != vals['user_type']:
                #value = self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).name
                value =  vals['user_type']
                oldmodel = account.user_type.name or _('None')
                changes.append(_("User type: from '%s' to '%s'") %(oldmodel, value))
#             if 'active' in vals and account.active != vals['active']:
#                 #value = self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).name
#                 value =  self.pool.get('account.account').browse(cr,uid,vals['active'],context=context)
#                 oldmodel = account.active or _('None')
#                 changes.append(_("Active: from '%s'  '%s'") %(oldmodel, value))
#             if not vals['tax_ids']
#                 print ""
#             print tax_ids
            if 'tax_ids' in vals and account.tax_ids != vals['tax_ids'][0][2]:
                list_tax = []
                list_tax_old = sorted(vals['tax_ids'][0][2])
                for a in account.tax_ids:
                    #oldmodel = self.pool.get('account.tax').browse(cr,uid,a.id,context=context).name or _('None')
                    #changes.append(_("Old Tax: '%s'") %(oldmodel))                
                    list_tax.append(a.id)
                i = 0
                sorted(list_tax)
                for a, t, in zip(list_tax,list_tax_old):
                    if a == t: 
                        del(list_tax_old[i])
                        del(list_tax[i])
                    else:
                        for a, t, in zip(sorted(list_tax, reverse = True),sorted(list_tax_old, reverse = True)):
                            k=len(list_tax_old)             
                            j=len(list_tax)
                            k=k-1
                            j=j-1
                            if a == t: 
                                del(list_tax_old[k])
                                del(list_tax[j])
                            else:
                                for a, t, in zip(sorted(list_tax),sorted(list_tax_old, reverse = True)):
                                    k=len(list_tax_old)
                                    k=k-1            
                                    if a == t: 
                                        del(list_tax_old[i])
                                        del(list_tax[k])
                                        list_tax_old
                                        list_tax                   
                        #i=i+1
                for o in list_tax_old:
                    oldmodel = self.pool.get('account.tax').browse(cr,uid,o,context=context).name or _('None')
                    changes.append(_("New Tax: '%s'") %(oldmodel)) 
                for p in list_tax:
                    value = self.pool.get('account.tax').browse(cr,uid,p,context=context).name or _('None')
                    changes.append(_("OldTax: '%s'") %(value))                     
#                     print list
#                 for t in vals['tax_ids'][0][2]:  
#                     value = self.pool.get('account.tax').browse(cr,uid,t,context=context).name                        
#                     #changes.append(_("Type: from '%s' to '%s' '-'") %(oldmodel, value))
#                     changes.append(_("Tax: '%s'") %(value))

#             if 'reconcile' in vals and account.reconcile != vals['reconcile']:
#                 #value = self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).name
#                 value =  self.pool.get('account.account').browse(cr,uid,vals['reconcile'],context=context).name
#                 oldmodel = account.reconcile or _('None')
#                 changes.append(_("Type: from '%s'  '%s'") %(oldmodel, value))
            if 'note' in vals and account.type != vals['note']:
                value =  vals['note']
                oldmodel = account.name or _('None')
                changes.append(_("Note: from '%s' to '%s'") %(oldmodel, value))
            
            if len(changes) > 0:
                self.message_post(cr, uid, [account.id], body=", ".join(changes), context=context)

        account_id = super(account_account,self).write(cr, uid, ids, vals, context)
        return True
#     def _construct_constraint_msg(self, cr, uid, ids, context=None):
#         res = super(account_account, self)._construct_constraint_msg(cr, uid, ids, context=context)
#         return res
#     _constraints = [(check_vat,_construct_constraint_msg, ["vat"])]

account_account()