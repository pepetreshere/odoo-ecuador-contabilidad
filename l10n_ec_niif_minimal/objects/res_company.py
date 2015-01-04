import logging

from openerp.osv import fields, osv
from openerp import pooler
from openerp.tools.translate import _


class res_company(osv.Model):
    _name='res.company'
    _inherit = ['res.company','mail.thread']

    _columns = {
        'special_tax_contributor_number':fields.char('Special Contributor Number', required=False, help='Special Contributors are designed by the Ecuadorian Tax Authority, the number is used in tax reporting', track_visibility='onchange'),
        'comercial_name':fields.related('partner_id','comercial_name',type='char',relation='res.partner',string='Comercial Name',store=False, track_visibility='onchange'),
        'forced_accounting': fields.boolean('Forced to maintain accounting books', track_visibility='onchange')
    }
    _defaults = {
        'forced_accounting': False
    }
res_company()        
