# -*- coding: utf-8 -*-
from osv import osv, fields

class product_template(osv.osv):    
    """Modificamos el objeto product.template para cambiar la propiedad translate del atributo name.
    """

    _inherit = "product.template"
    
    _columns = {
        'name': fields.char('Name', size=128, required=True, select=True),          
    }

product_template()