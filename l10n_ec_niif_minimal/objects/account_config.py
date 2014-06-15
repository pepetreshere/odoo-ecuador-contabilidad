# -*- coding: utf-8 -*-

import logging

from openerp.osv import fields, osv
from openerp import pooler
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class process_configuration(osv.osv_memory):
    _inherit = 'account.config.settings'

    _columns = {
                'restrictions': fields.boolean('No restrictions', change_default=True, default_model='account.account', help="By checking this field, some restrictions are included by default in the system is removed."),   
            }

    _defaults = {
                 'restrictions': True
            }
    def get_default_restriction(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        restrictions  = ir_values.get_default(cr, uid, 'account.account', 'restrictions')
        return {
            'restrictions': restrictions ,
        }
    
    def set_default_restriction(self, cr, uid, ids, context=None):
        """ set default restrictions"""
        ir_values = self.pool.get('ir.values')
        config = self.browse(cr, uid, ids[0], context)
        ir_values.set_default(cr, uid, 'account.account', 'restrictions',
            config.restrictions or False)

process_configuration()       
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
