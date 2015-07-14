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
    
    _columns = {
                'default_writeoff_acc_id': fields.many2one('account.account', 
                                                           'Default Open Balance Reconcile Account',
                                                           domain="['|',('force_reconcile','=',True),('type','!=','other')]", 
                                                           help="Default account for reconciling the open balance in vouchers, for withhold journals a payable accounts in favor of the partner should be used (ie 2011001 - ANTICIPOS DE CLIENTES)"
                                                           ),
                }
account_journal()