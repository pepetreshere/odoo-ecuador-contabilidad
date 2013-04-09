# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2011  Christopher Ormaza, Ecuadorenlinea.net            #
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

from osv import osv, fields
import time
from tools.translate import _

class ir_sequence(osv.osv):
    _inherit = 'ir.sequence'
    
    def get_next_id(self, cr, uid, seq_ids, aditional_value=0, context=None):
        if not seq_ids:
            return False
        if context is None:
            context = {}
        if type(seq_ids) in (type(1), type(long)):
            seq_ids = [seq_ids]
        seq = self.read(cr, uid, seq_ids, ['company_id','implementation','number_next','prefix','suffix','padding'])[0]
        seq['number_next'] = seq['number_next'] + aditional_value
        d = self._interpolation_dict()
        interpolated_prefix = self._interpolate(seq['prefix'], d)
        interpolated_suffix = self._interpolate(seq['suffix'], d)
        return interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_next'] + interpolated_suffix

ir_sequence()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: