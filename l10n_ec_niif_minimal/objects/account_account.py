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
            if 'code' in vals and account.type != vals['code']:
                #value = self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).name
                value =  self.pool.get('account.account').browse(cr,uid,vals['code'],context=context).name
                oldmodel = account.type or _('None')
                changes.append(_("Code: from '%s'  '%s'") %(oldmodel, value))
            if 'name' in vals and account.name != vals['name']:
                #value = self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).name
                value =  self.pool.get('account.account').browse(cr,uid,vals['name'],context=context).name
                oldmodel = account.name or _('None')
                changes.append(_("Name: from '%s' '%s'") %(oldmodel, value))
            if 'parent_id' in vals and account.parent_id.id != vals['parent_id']:
                #value = self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).name
                value =  self.pool.get('account.account').browse(cr,uid,vals['parent_id'],context=context).name
                oldmodel = account.parent_id.name or _('None')
                changes.append(_("Type: from '%s' to '%s'") %(oldmodel, value))
            if 'type' in vals and account.type != vals['type']:
                #value = self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).name
                value =  self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).type
                oldmodel = account.type or _('None')
                changes.append(_("Type: from '%s'  '%s'") %(oldmodel, value))
            if 'user_type' in vals and account.user_type != vals['user_type']:
                #value = self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).name
                value =  self.pool.get('account.account').browse(cr,uid,vals['user_type'],context=context).name
                oldmodel = account.user_type.name or _('None')
                changes.append(_("User type: from '%s'  '%s'") %(oldmodel, value))
#             if 'active' in vals and account.active != vals['active']:
#                 #value = self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).name
#                 value =  self.pool.get('account.account').browse(cr,uid,vals['active'],context=context)
#                 oldmodel = account.active or _('None')
#                 changes.append(_("Active: from '%s'  '%s'") %(oldmodel, value))
                                
            if 'tax_ids' in vals and account.tax_ids != vals['tax_ids']:
                old_license_plate = account.tax_ids or _('None')
                changes.append(_("tax_ids: from '%s' '%s'") %(old_license_plate, vals['tax_ids']))
#             if 'reconcile' in vals and account.reconcile != vals['reconcile']:
#                 #value = self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).name
#                 value =  self.pool.get('account.account').browse(cr,uid,vals['reconcile'],context=context).name
#                 oldmodel = account.reconcile or _('None')
#                 changes.append(_("Type: from '%s'  '%s'") %(oldmodel, value))
            if 'note' in vals and account.type != vals['note']:
                #value = self.pool.get('account.account').browse(cr,uid,vals['type'],context=context).name
                value =  self.pool.get('account.account').browse(cr,uid,vals['note'],context=context).name
                oldmodel = account.name or _('None')
                changes.append(_("Note: from '%s'  '%s'") %(oldmodel, value))
            
            if len(changes) > 0:
                self.message_post(cr, uid, [account.id], body=", ".join(changes), context=context)

        account_id = super(account_account,self).write(cr, uid, ids, vals, context)
        return True
#     def _construct_constraint_msg(self, cr, uid, ids, context=None):
#         res = super(account_account, self)._construct_constraint_msg(cr, uid, ids, context=context)
#         return res
#     _constraints = [(check_vat,_construct_constraint_msg, ["vat"])]

account_account()