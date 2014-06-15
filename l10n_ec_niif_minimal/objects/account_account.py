# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 David  Romero,
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
    _inherit = ["account.account", "mail.thread"]    
    _columns = {
            'force_reconcile': fields.boolean('Force feconcile', help="Check this box if, this account amounts to reconcile differences in payments to customers and suppliers."),
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
                value =  self.pool.get('account.account').browse(cr,uid,vals['parent_id'],context=context).name
                oldmodel = account.parent_id.name or _('None')
                changes.append(_("Type: from '%s' to '%s'") %(oldmodel, value))
            if 'type' in vals and account.type != vals['type']:
                value =  vals['type']
                oldmodel = account.type or _('None')
                changes.append(_("Type: from '%s' to '%s'") %(oldmodel, value))
            if 'user_type' in vals and account.user_type != vals['user_type']:
                value =  self.pool.get('account.account.type').browse(cr,uid,vals['user_type'],context=context).name
                oldmodel = account.user_type.name or _('None')
                changes.append(_("User type: from '%s' to '%s'") %(oldmodel, value))
            if 'active' in vals and account.active != vals['active']:
                value =  vals['active']
                oldmodel = account.active or _('None')
                changes.append(_("Active: from '%s' to '%s'") %(oldmodel, value))
            if 'tax_ids' in vals and account.tax_ids != vals['tax_ids'][0][2]:
                list_tax = []
                list = []
                "Guarda en las listas los campos removidor o agragados"
                list_tax_new = sorted(vals['tax_ids'][0][2])
                for a in account.tax_ids:    
                    list_tax.append(a.id)
                sorted(list_tax)
                sorted(list_tax_new)
                "ve cuales son los camos q se mantienen"
                for a in list_tax:
                    for t in list_tax_new:
                        if a == t: 
                            list.append(a)
                "elimina de las listas los campos repetidos"
                for a in list:
                    del(list_tax_new[list_tax_new.index(a)])
                    del(list_tax[list_tax.index(a)])
                "Guarda e imprime los campos no repetidos en msn"
                for id in list_tax:
                    value = self.pool.get('account.tax').browse(cr,uid,id,context=context).name or _('None')
                    changes.append(_("Tax Removed: '%s'") %(value)) 
                for id in list_tax_new:
                    value = self.pool.get('account.tax').browse(cr,uid,id,context=context).name or _('None')
                    changes.append(_("Added tax: '%s'") %(value))                
            if 'reconcile' in vals and account.active != vals['reconcile']:
                value =  vals['reconcile']
                oldmodel = account.active or _('None')
                changes.append(_("Active: from '%s' to '%s'") %(oldmodel, value))
                
            if 'child_consol_ids' in vals and account.child_consol_ids != vals['child_consol_ids'][0][2]:
                list_consol = []
                list = []
                "Guarda en las listas los campos removidor o agragados"
                list_consol_new = sorted(vals['child_consol_ids'][0][2])
                for a in account.child_consol_ids:    
                    list_consol.append(a.id)
                sorted(list_consol)
                sorted(list_consol_new)
                "ve cuales son los camos q se mantienen"
                for a in list_consol:
                    for t in list_consol_new:
                        if a == t: 
                            list.append(a)
                "elimina de las listas los campos repetidos"
                for a in list:
                    del(list_consol_new[list_consol_new.index(a)])
                    del(list_consol[list_consol.index(a)])
                "Guarda e imprime los campos no repetidos en msn"
                for id in list_consol:
                    value = self.pool.get('account.account').browse(cr,uid,id,context=context).name or _('None')
                    changes.append(_("Consolidation Removed: '%s'") %(value)) 
                for id in list_consol_new:
                    value = self.pool.get('account.account').browse(cr,uid,id,context=context).name or _('None')
                    changes.append(_("Added Consolidation: '%s'") %(value))
            if 'note' in vals and account.type != vals['note']:
                value =  vals['note']
                oldmodel = account.name or _('None')
                changes.append(_("Note: from '%s' to '%s'") %(oldmodel, value))
            
            if len(changes) > 0:
                self.message_post(cr, uid, [account.id], body=", ".join(changes), context=context)

        account_id = super(account_account,self).write(cr, uid, ids, vals, context)
        return True
    
    def _check_allow_code_change(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        restrictions  = ir_values.get_default(cr, uid, 'account.account', 'restrictions')
        for account in self.browse(cr, uid, ids, context):
            if not restrictions:
                line_obj = self.pool.get('account.move.line')
                for account in self.browse(cr, uid, ids, context=context):
                    account_ids = self.search(cr, uid, [('id', 'child_of', [account.id])], context=context)
                    if line_obj.search(cr, uid, [('account_id', 'in', account_ids)], context=context):
                        raise osv.except_osv(_('Warning !'), _("You cannot change the code of account which contains journal items!"))
        return True
        
#     def _construct_constraint_msg(self, cr, uid, ids, context=None):
#         res = super(account_account, self)._construct_constraint_msg(cr, uid, ids, context=context)
#         return res
#     _constraints = [(check_vat,_construct_constraint_msg, ["vat"])]

account_account()