# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2012  Christopher Ormaza, Ecuadorenlinea.net            #
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
import netsvc
from osv import osv
from osv import fields
from tools.translate import _

class delivery_carrier(osv.osv):

    def check_ced(self, ced):
        try:
            valores = [ int(ced[x]) * (2 - x % 2) for x in range(9) ]
            suma = sum(map(lambda x: x > 9 and x - 9 or x, valores))
            veri = 10 - (suma - (10*(suma/10)))
            if int(ced[9]) == int(str(veri)[-1:]):
                return True
            else:
                return False
        except:
            return False

    def _check_ced(self, cr, uid, ids):
        val = True 
        for carrier in self.pool.get('delivery.carrier').browse(cr, uid, ids, None):
            if carrier.cedula:
                val = self.check_ced(carrier.cedula)
        return val
    
    def get_price(self, cr, uid, ids, field_name, arg=None, context=None):
        return super(delivery_carrier, self).get_price(cr, uid, ids, field_name, arg, context)
    
    _inherit = "delivery.carrier"
    _columns = {
        'name': fields.char("Driver's Name", size=64, required=True),
        'partner_id': fields.many2one('res.partner', 'Carrier Partner', required=False),
        'product_id': fields.many2one('product.product', 'Delivery Product', required=False),
        'grids_id': fields.one2many('delivery.grid', 'carrier_id', 'Delivery Grids'),
        'price' : fields.function(get_price, method=True,string='Price'),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the delivery carrier without removing it."),
        'placa':fields.char('Placa', size=8,), 
        'cedula':fields.char('Cédula', size=10, required=True, readonly=False), 
    }
    
    _constraints = [(_check_ced, 'Error de Validación: El numero de Cédula del Transportista no es correcto', ['cedula'])]
    
delivery_carrier()